from playwright.sync_api import sync_playwright
import pandas as pd
import re
import time
import json
import logging
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from jobs import Contacts

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='scraper.log')


def get_contact_page_links_with_browser(page, base_url):
    contact_keywords = [
        "צור_קשר", "צור-קשר", "צור קשר",
        "מחלקות", "אנשי קשר", "טלפונים",
        "הנהלה", "עובדים", "צוות",
        "staff", "contacts", "directory",
        "אגפים", "אגף", "אגפיה", "שירותים",
        "שירותי", "דברו איתנו", "דברו",
        "מחלקה", "מחלקות",
        "מועצה", "חברי מועצה", "תפקידי מועצה"
    ]
    found_links = set()

    anchors = page.query_selector_all("a")
    for a in anchors:
        try:
            text = a.inner_text().strip()
            href = a.get_attribute("href")
            if href and any(kw in text or kw in href for kw in contact_keywords):
                full_url = urljoin(page.url, href)
                found_links.add(full_url)
        except:
            continue

    return list(found_links)

def extract_text_from_url(page, url):
    try:
        retry_count = 0
        while retry_count < 3:
            try:
                page.goto(url, timeout=30000, wait_until="networkidle")
                text = page.inner_text("body")
                return text
            except Exception as e:
                retry_count += 1
                time.sleep(2)
        logging.error(f"[FAILED] Could not fetch {url} after retries")
        return ""
    except:
        return ""

def extract_relevant_contacts_from_text(text, city_name):
    arabic_authorities = {
        "כפר קרע", "באקה אל גרבייה", "טמרה", "סח'נין", "אום אל-פחם", "טייבה",
        "ג'ת", "עראבה", "ג'לג'וליה", "כפר מנדא", "דיר אל אסד", "עילוט",
        "בסמה", "מג'דל אל כרום", "ריינה", "נחף", "כאוכב אבו אל-היג'א",
        "עין מאהל", "טורעאן", "דבוריה", "עילבון", "כאבול", "בוקעאתא",
        "ביר אל-מכסור", "מסעדה", "עין קניא", "ג'דיידה-מכר", "ראמה",
        "אבו גוש", "אכסאל", "בית ג'ן", "ג'סר א-זרקא", "דליית אל כרמל",
        "חורה", "חורפיש", "יאנוח-ג'ת", "יפיע", "ירכא", "כסיפה",
        "כסרא-סמיע", "כעביה-טבאש-חג'אג'רה", "כפר ברא", "כפר יאסיף",
        "מג'דל שמס", "מעיליא", "משהד", "נאעורה", "נין", "נצרת",
        "סאג'ור", "ע'ג'ר", "עוספיה", "עין ראפה", "פסוטה", "פקיעין",
        "שבלי - אום אל - גנם", "שפרעם"
    }

    if city_name in arabic_authorities:
        return {city_name: {}}

    people = {}
    seen = set()
    buffer = []

    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue

        buffer.append(line)

        if re.search(r'@|0[2-9]', line):
            contact_raw = " ".join(buffer)
            contact_obj = Contacts(contact_raw, city_name)

            unique_key = (contact_obj.email, contact_obj.phone_office, contact_obj.phone_mobile)
            if any(unique_key) and unique_key not in seen:
                people[contact_obj.name] = contact_obj.to_dict()
                seen.add(unique_key)

            buffer = []

    return {city_name: people}


def split_contacts_block(text, city):
    segments = re.split(r'\t+|\s{2,}', text)
    buffer = []
    contacts = []

    for item in segments:
        buffer.append(item.strip())

        if any(re.search(p, item) for p in [r'@', r'0[2-9]\d{7,8}']):
            contact_raw = " ".join(buffer).strip()
            if contact_raw:
                contacts.append(Contacts(contact_raw, city))
            buffer = []

    return contacts

def process_city(row, existing_data):
    city = row["עיר"]
    url = row["קישור"]

    if pd.isna(url) or city in existing_data and existing_data[city]:
        logging.info(f"[SKIP] {city}: Already scraped or no URL")
        return city, existing_data.get(city, {})

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            retry_count = 0
            while retry_count < 3:
                try:
                    page.goto(url, timeout=30000, wait_until="networkidle")
                    break
                except:
                    retry_count += 1
                    time.sleep(2)

            links = get_contact_page_links_with_browser(page, url)
            logging.info(f"{city}: Found {len(links)} potential contact links")

            city_data = {}
            for link in links:
                text = extract_text_from_url(page, link)
                if not text.strip():
                    continue
                contact_info = extract_relevant_contacts_from_text(text, city)
                city_data.update(contact_info.get(city, {}))

            os.makedirs(os.path.join(base_dir, "incremental_results"), exist_ok=True)
            with open(os.path.join(base_dir, "incremental_results", f"{city}.json"), "w", encoding="utf-8") as f:
                json.dump(city_data, f, ensure_ascii=False, indent=2)

            return city, city_data
        except Exception as e:
            logging.error(f"[ERROR] {city}: {e}")
            return city, {}
        finally:
            browser.close()

def scrape_with_browser():
    df = pd.read_csv(os.path.join(base_dir, "data", "cities_links.csv"))
    results = {}

    dict_path = os.path.join(base_dir, "third_test.json")
    if not os.path.exists(dict_path):
        with open(dict_path, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

    with open(dict_path, encoding="utf-8") as f:
        results = json.load(f)

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_city = {
            executor.submit(process_city, row, results): row["עיר"]
            for _, row in df.iterrows()
        }

        for future in as_completed(future_to_city):
            city = future_to_city[future]
            try:
                city, data = future.result(timeout=60)
                results[city] = data
            except Exception as exc:
                logging.error(f"[TIMEOUT/ERROR] {city}: {exc}")

    with open(dict_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logging.info(f"Done scraping all cities into third_test.json, there were {Contacts.contacts}")
    print(" File saved:", dict_path)

if __name__ == "__main__":
    scrape_with_browser()
