import json
import pandas as pd

# Load full contacts data
with open("smart_contacts.json", encoding="utf-8") as f:
    contacts = json.load(f)

# Load empty cities list from your file
with open("empty_contacts_cleaned.txt", encoding="utf-8") as f:
    empty_cities = [line.strip() for line in f if line.strip()]

# Build the table with city + how many contacts were found (even if 0)
rows = []
for city in empty_cities:
    count = len(contacts.get(city.strip(), {}))
    rows.append({
        "עיר": city,
        "מספר אנשי קשר": count if count > 0 else "אין אנשי קשר"
    })

df = pd.DataFrame(rows)
df.to_csv("empty_cities_contacts.csv", index=False, encoding="utf-8-sig")
print("הקובץ נשמר: empty_cities_contacts.csv")
