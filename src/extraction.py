import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time

def extract_details_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        text = soup.get_text(separator="\n")

        # Regular expressions
        phone_matches = re.findall(r'0[2-9]-?\d{7}', text)
        email_matches = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)

        # Define keywords for relevant departments
        keywords = [
            "נוער", "צעירים", "תרבות", "אירועים", "חינוך",
            "קהילה", "רווחה", "קליטה", "קיימות", "סביבה", "אזרחים ותיקים", "הגיל השלישי"
        ]

        relevant_lines = []
        for line in text.split("\n"):
            if any(keyword in line for keyword in keywords):
                relevant_lines.append(line)

        # Try to extract name/title from nearby lines with contact info
        dept_contacts = []
        for line in relevant_lines:
            nearby = text.split("\n")
            index = nearby.index(line)
            snippet = "\n".join(nearby[max(0, index-3):index+3])
            phones = re.findall(r'0[2-9]-?\d{7}', snippet)
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', snippet)
            if phones or emails:
                dept_contacts.append({"line": line, "phones": phones, "emails": emails})

        return dept_contacts

    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def main():
    df = pd.read_csv("cities_links.csv")
    all_contacts = []

    for i, row in df.iterrows():
        url = row["קישור"]
        name = row["עיר"]
        print(f"[{i+1}/{len(df)}] Scraping: {name}")
        if pd.notna(url):
            contacts = extract_details_from_url(url)
        else:
            contacts = []

        all_contacts.append({"עיר": name, "contacts": contacts})
        time.sleep(1)

    # Save raw JSON-style output for easier review or further transformation
    pd.DataFrame(all_contacts).to_json("relevant_contacts.json", force_ascii=False, indent=2)
    print("Saved relevant_contacts.json!")

if __name__ == "__main__":
    main()
