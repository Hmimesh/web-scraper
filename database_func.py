from playwright.sync_api import sync_playwright
import pandas as pd
import re
from bs4 import BeautifulSoup
import time
import json
import logging
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
import os

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='scraper.log')

def clean_phone(phone):
    return re.sub(r'[^\d]', '', phone) if phone else None

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

    department_keywords = {
        "מחלקות נוער": ["נוער", "רכז נוער", "מנהלת נוער"],
        "מחלקות צעירים": ["צעירים", "רכז צעירים", "נוער וצעירים"],
        "מחלקות תרבות": ["תרבות", "רכז תרבות", "מנהלת תרבות"],
        "מחלקות אירועים": ["אירועים", "מארגנת אירועים"],
        "מחלקת חינוך": ["חינוך", "מפקחת חינוך"],
        "מחלקת קהילה": ["קהילה", "רכז קהילה", "פעילות קהילתית"],
        "מחלקת רווחה": ["רווחה", "עובד סוציאלי"],
        "מחלקת קליטה": ["קליטה", "עולים"],
        "מחלקת איכות סביבה": ["סביבה", "קיימות", "ירוק"],
        "מחלקת אזרחים וותיקים": ["וותיקים", "הגיל השלישי"],
        "מועצה": ["חבר מועצה", "חברי מועצה", "יושב ראש מועצה", "סגן ראש המועצה", "תפקידי מועצה"]
    }

    excluded_keywords = [
        "וטרינר", "ביטחון", "הנדסה", "ספורט", "תחבורה",
        "חנייה", "גבייה", "מכרזים", "מיסוי", "ארנונה", "תשתיות"
    ]

    non_person_keywords = [
        "פרטי קשר", "אגף", "אגפים", "מחלקה", "מחלקת", "צוות",
        "פרטי התקשרות", "רשימת בעלי", "טלפון", "מייל", "אימייל", "דוא\"ל",
        "מידע כללי", "שעות פעילות", "שעות קבלת קהל"
    ]

    people = {}
    seen = set()
    lines = text.split("\n")

    for i, line in enumerate(lines):
        if any(ex_kw in line for ex_kw in excluded_keywords):
            continue

        for dept, keywords in department_keywords.items():
            if any(kw in line for kw in keywords):
                context = "\n".join(lines[max(0, i - 2): i + 3])

                name_match = re.search(r'(?:[א-ת][\'"״׳]?){2,}(?:\s+(?:[א-ת][\'"״׳]?){2,})+', context)
                phone_match = re.search(r'\b0[2-9](?:[-\s]?\d){7}\b', context)

                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', context)

                name = name_match.group(0) if name_match else f"אין שם ({dept})"
                phone = clean_phone(phone_match.group(0)) if phone_match else None
                email = email_match.group(0) if email_match else None

                if not phone and not email:
                    continue

                if any(kw in name for kw in non_person_keywords):
                    continue

                contact_key = (name, phone, email, dept)
                if contact_key not in seen:
                    seen.add(contact_key)
                    people[name] = {
                        "phone": phone,
                        "email": email,
                        "job_title": line.strip(),
                        "department": dept
                    }

    return {city_name: people}

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

            os.makedirs("incremental_results", exist_ok=True)
            with open(f"incremental_results/{city}.json", "w", encoding="utf-8") as f:
                json.dump(city_data, f, ensure_ascii=False, indent=2)

            return city, city_data
        except Exception as e:
            logging.error(f"[ERROR] {city}: {e}")
            return city, {}
        finally:
            browser.close()

def scrape_with_browser():
    df = pd.read_csv("cities_links.csv")
    results = {}

    if os.path.exists("smart_contacts.json"):
        with open("smart_contacts.json", encoding="utf-8") as f:
            results = json.load(f)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = executor.map(lambda row: process_city(row, results), [row for _, row in df.iterrows()])
        for city, data in futures:
            results[city] = data

    with open("smart_contacts.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logging.info("Done scraping all cities into smart_contacts.json")

if __name__ == "__main__":
    scrape_with_browser()
