from playwright.sync_api import sync_playwright
import pandas as pd
import re
import time
import json
import logging
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import sys
from jobs import Contacts
from datafunc import apply_hebrew_transliteration
from nameparser import HumanName
from collect_names import collect_names
from tqdm import tqdm
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=os.path.join(base_dir, "logs", "scraper.log"),
)

input_output_logger = logging.getLogger("io_logger")
input_output_logger.setLevel(logging.INFO)
io_handler = logging.FileHandler(
    os.path.join(base_dir, "logs", "scraper_io.jsonl"), encoding="utf-8"
)
io_handler.setFormatter(logging.Formatter("%(message)s"))
input_output_logger.addHandler(io_handler)

failed_logger = logging.getLogger("failed_logger")
failed_logger.setLevel(logging.INFO)
failed_handler = logging.FileHandler(
    os.path.join(base_dir, "logs", "failed_cities.jsonl"), encoding="utf-8"
)
failed_handler.setFormatter(logging.Formatter("%(message)s"))
failed_logger.addHandler(failed_handler)

site_profiles_path = os.path.join(base_dir, "data", "site_profiles.json")
site_profiles = {}
if os.path.exists(site_profiles_path):
    with open(site_profiles_path, encoding="utf-8") as f:
        site_profiles = json.load(f)


def find_deep_contact_links(page, base_url, depth=2, visited=None):
    if visited is None:
        visited = set()

    if depth == 0 or base_url in visited:
        return []

    visited.add(base_url)
    links_to_visit = []

    try:
        page.goto(base_url, timeout=30000, wait_until="networkidle")
        anchors = page.query_selector_all("a")
        for a in anchors:
            try:
                text = a.inner_text().strip()
                href = a.get_attribute("href")
                if not href:
                    continue
                full_url = urljoin(base_url, href)
                if full_url in visited:
                    continue
                if any(kw in text or kw in href for kw in [
                    "צור_קשר", "צור-קשר", "צור קשר", "מחלקות", "אנשי קשר", "טלפונים",
                    "הנהלה", "עובדים", "צוות", "staff", "contacts", "directory",
                    "contact", "dept", "department", "office", "אגפים", "אגף",
                    "אגפיה", "שירותים", "שירותי", "דברו איתנו", "דברו", "מחלקה",
                    "מועצה", "חברי מועצה", "תפקידי מועצה", "טלפון", "טלפונים",
                    "פניית ציבור", "רשימת", "קשרי ציבור", "מזכירות", "לשכה"]):
                    links_to_visit.append(full_url)
                    links_to_visit.extend(find_deep_contact_links(page, full_url, depth - 1, visited))
            except:
                continue
    except Exception as e:
        logging.warning(f"Failed to load {base_url}: {e}")

    return links_to_visit


def extract_text_from_url(page, url):
    for _ in range(3):
        try:
            page.goto(url, timeout=30000, wait_until="networkidle")
            return page.inner_text("body")
        except:
            time.sleep(2)
    logging.error(f"[FAILED] Could not fetch {url} after retries")
    return ""


def extract_relevant_contacts_from_text(text, city_name, source_url=None):
    people = {}
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for i in range(len(lines)):
        block = " ".join(lines[i:i+5])
        if "@" in block or re.search(r"0[2-9][-\s]?\d{7}", block):
            contact_obj = Contacts(block, city_name, url=source_url)
            if not contact_obj.name and contact_obj.email:
                parsed = HumanName(contact_obj.email.split("@")[0])
                contact_obj.name = str(parsed)
            elif contact_obj.name and not any(c in contact_obj.name for c in "אבגדהוזחטיכלמנסעפצקרשת"):
                if contact_obj.email:
                    parsed = HumanName(contact_obj.email.split("@")[0])
                    contact_obj.role = contact_obj.name
                    contact_obj.name = str(parsed)
            if contact_obj.name in people and not contact_obj.email and people[contact_obj.name].get("מייל"):
                continue
            people[contact_obj.name] = contact_obj.to_dict()

    return {city_name: people}


def process_city(row, existing_data):
    city = row["עיר"]
    url = str(row["קישור"]).strip() if isinstance(row["קישור"], str) else None

    # Check for NaN values (both pandas NaN and string representations)
    if (pd.isna(url) or
        url is None or
        url.lower().strip() in ['nan', 'none', 'null', ''] or
        city in existing_data and existing_data[city]):
        logging.info(f"[SKIP] {city}: Already scraped or no URL")
        return city, existing_data.get(city, {})

    hostname = urlparse(url).hostname
    profile = site_profiles.get(hostname, {})
    if isinstance(profile, str):
        profile = {"skip": True, "reason": profile}
        site_profiles[hostname] = profile

    if profile.get("skip"):
        logging.info(f"[SKIP] {city}: marked to skip ({profile.get('reason', 'no reason')})")
        return city, {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        city_data = {}

        try:
            for _ in range(3):
                try:
                    page.goto(url, timeout=30000, wait_until="networkidle")
                    break
                except:
                    time.sleep(2)

            links = find_deep_contact_links(page, url)
            logging.info(f"{city}: Found {len(links)} contact-related links")

            for link in links:
                text = extract_text_from_url(page, link)
                if not text.strip():
                    continue

                html_dump_dir = os.path.join(base_dir, "logs", "html_dump")
                os.makedirs(html_dump_dir, exist_ok=True)
                with open(os.path.join(html_dump_dir, f"{city}.txt"), "w", encoding="utf-8") as f:
                    f.write(text)

                extracted_data = extract_relevant_contacts_from_text(text, city, link).get(city, {})
                city_data.update(extracted_data)

                for name, contact in extracted_data.items():
                    input_output_logger.info(json.dumps({"City": city, "Link": link, "Name": name, **contact}, ensure_ascii=False))

            os.makedirs(os.path.join(base_dir, "incremental_results"), exist_ok=True)
            city_file = os.path.join(base_dir, "incremental_results", f"{city}.json")
            with open(city_file, "w", encoding="utf-8") as f:
                json.dump(city_data, f, ensure_ascii=False, indent=2)

            apply_hebrew_transliteration(city_file)

            if not city_data:
                failed_logger.info(json.dumps({"City": city, "url": url, "status": "empty"}, ensure_ascii=False))

            return city, city_data
        except Exception as e:
            logging.error(f"[ERROR] {city}: {e}")
            failed_logger.info(json.dumps({"City": city, "url": url, "error": str(e), "status": "exception"}, ensure_ascii=False))
            return city, {}
        finally:
            browser.close()


def scrape_with_browser(file_path: str | None = None):
    if file_path is None:
        file_name = input("Enter the name of the output file (e.g., 'contacts.json'): ")
        if not file_name.endswith(".json"):
            file_name += ".json"
        dict_path = os.path.join(base_dir, file_name)
    else:
        dict_path = file_path if file_path.endswith(".json") else file_path + ".json"
        file_name = os.path.basename(dict_path)

    start_time = time.time()
    df = pd.read_csv(os.path.join(base_dir, "data", "cities_links.csv"), encoding="utf-8-sig")
    total_items = len(df)

    results = {}
    if not os.path.exists(dict_path):
        with open(dict_path, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

    with open(dict_path, encoding="utf-8") as f:
        results = json.load(f)

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_city = {executor.submit(process_city, row, results): row["עיר"] for _, row in df.iterrows()}
        completed = 0

        for future in tqdm(as_completed(future_to_city), total=total_items, desc="scraping cities"):
            city = future_to_city[future]
            try:
                city, data = future.result(timeout=60)
                results[city] = data
            except Exception as exc:
                logging.error(f"[TIMEOUT/ERROR] {city}: {exc}")
                failed_logger.info(json.dumps({"City": city, "error": str(exc), "status": "timeout"}, ensure_ascii=False))
            finally:
                completed += 1
                if completed % 100 == 0 and completed > 0:
                    elapsed_time = time.time() - start_time
                    avg_time = elapsed_time / completed
                    est_time = avg_time * (total_items - completed)
                    print("--- Estimated remaining time: %.2f minutes ---" % (est_time / 60))

    with open(dict_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    apply_hebrew_transliteration(dict_path)

    with open(os.path.join(base_dir, "incremental_results", "contacts.json"), "w", encoding="utf-8") as f:
        json.dump(Contacts.contacts, f, ensure_ascii=False, indent=2)

    collect_names()
    logging.info(f"Done scraping all cities into {file_name}, there were {Contacts.contacts}")
    print(" File saved:", dict_path)


if __name__ == "__main__":
    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    scrape_with_browser(path_arg)
