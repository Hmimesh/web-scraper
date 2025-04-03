import json
import pandas as pd

# Load the JSON data
with open("smart_contacts.json", encoding="utf-8") as f:
    contacts = json.load(f)

# Flatten into rows
rows = []
for city, people in contacts.items():
    for name, info in people.items():
        rows.append({
            "עיר": city,
            "שם": name,
            "טלפון": info.get("phone"),
            "אימייל": info.get("email"),
            "תפקיד": info.get("job_title"),
            "מחלקה": info.get("department")
        })

# Save to CSV
df = pd.DataFrame(rows)
df.to_csv("all_contacts.csv", index=False, encoding="utf-8-sig")
print("✅ הקובץ נשמר: all_contacts.csv")

# Save to Excel
df.to_excel("all_contacts.xlsx", index=False, engine="openpyxl")
print(" הקובץ נשמר גם כ־ all_contacts.xlsx")
