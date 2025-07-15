"""Generate CSV/Excel contact lists from the scraped JSON file."""

import json
from pathlib import Path
import re

import pandas as pd

import jobs

BASE_DIR = Path(__file__).resolve().parents[1]


def is_valid_name(name: str) -> bool:
    """Check if a name looks like a real person's name."""
    if not name or len(name.strip()) < 2:
        return False

    name = name.strip()

    # Reject obvious garbage patterns
    garbage_patterns = [
        r'.*טלפון.*',  # Contains "phone"
        r'.*פקס.*',    # Contains "fax"
        r'.*מס.*',     # Contains "number"
        r'.*המחלקה.*', # Contains "department"
        r'.*מנהל המחלקה.*', # Contains "department manager"
        r'.*שם מנהל.*', # Contains "manager name"
        r'.*לא נמצא.*', # Contains "not found"
        r'.*שעות עבודה.*', # Contains "work hours"
        r'.*קבלת קהל.*', # Contains "public reception"
        r'.*נציגי ציבור.*', # Contains "public representatives"
        r'.*דרישה.*',   # Contains "requirement"
        r'.*מכרז.*',    # Contains "tender"
        r'.*מחשוב.*',   # Contains "computing"
        r'.*אבטחת מידע.*', # Contains "information security"
        r'.*הארכת.*',   # Contains "extension"
        r'.*שיפור.*',   # Contains "improvement"
        r'.*לתשלום.*',  # Contains "for payment"
        r'.*בקרדיט.*',  # Contains "credit"
        r'.*בביט.*',    # Contains "bit"
        r'.*בית מילגם.*', # Contains "milgam house"
        r'.*התנדבות.*', # Contains "volunteering"
        r'.*תרומה.*',   # Contains "donation"
        r'.*השתלבות.*', # Contains "integration"
        r'.*מגשרים.*',  # Contains "mediators"
        r'.*תנאי.*',    # Contains "conditions"
        r'.*הצטרפות.*', # Contains "joining"
        r'.*טופס.*',    # Contains "form"
        r'.*קישור.*',   # Contains "link"
        r'.*מצורף.*',   # Contains "attached"
        r'.*פייסבוק.*', # Contains "facebook"
        r'.*מפת האתר.*', # Contains "site map"
        r'.*עמוד.*',    # Contains "page"

        # Additional patterns based on the output we saw
        r'.*מועצה.*',   # Contains "council"
        r'.*עירייה.*',  # Contains "municipality"
        r'.*מוקד.*',    # Contains "center/hotline"
        r'.*לשכת.*',    # Contains "office of"
        r'.*מחלקת.*',   # Contains "department of"
        r'.*אגף.*',     # Contains "wing/division"
        r'.*גבייה.*',   # Contains "collection"
        r'.*שומה.*',    # Contains "assessment"
        r'.*הנהלת.*',   # Contains "management of"
        r'.*מבקר.*',    # Contains "auditor"
        r'.*מענה.*',    # Contains "response"
        r'.*זימון.*',   # Contains "appointment"
        r'.*תור.*',     # Contains "turn/appointment"
        r'.*חיפוש.*',   # Contains "search"
        r'.*תוצאות.*',  # Contains "results"
        r'.*סינון.*',   # Contains "filtering"
        r'.*נפתח.*',    # Contains "opens"
        r'.*חלון.*',    # Contains "window"
        r'.*חדש.*',     # Contains "new"
        r'.*שירות.*',   # Contains "service"
        r'.*ארצי.*',    # Contains "national"
        r'.*מידע.*',    # Contains "information"
        r'.*סיוע.*',    # Contains "assistance"
        r'.*דיווח.*',   # Contains "reporting"
        r'.*תרבות.*',   # Contains "culture"
        r'.*תורנית.*',  # Contains "duty"
        r'.*כתובת.*',   # Contains "address"
        r'.*תאם.*',     # Contains "coordinate"
        r'.*פגישה.*',   # Contains "meeting"
        r'.*טלפונית.*', # Contains "telephone"
        r'.*פקידת.*',   # Contains "clerk"
        r'.*זכאות.*',   # Contains "eligibility"
        r'.*עדיף.*',    # Contains "preferable"

        r'^[0-9]+$',    # Only numbers
        r'^[a-zA-Z]+$', # Only English letters (likely not Hebrew names)
        r'.*@.*',       # Contains @ (email)
        r'.*\..*',      # Contains dots (likely not names)
        r'.*http.*',    # Contains http
        r'.*www.*',     # Contains www
    ]

    for pattern in garbage_patterns:
        if re.match(pattern, name, re.IGNORECASE):
            return False

    # Must contain Hebrew characters for Israeli contacts
    if not re.search(r'[\u0590-\u05FF]', name):
        return False

    # Reject if too long (likely a sentence, not a name)
    if len(name) > 50:
        return False

    # Reject if contains too many spaces (likely a sentence)
    if name.count(' ') > 3:
        return False

    # Additional check: looks like a real person's name
    # Real names typically have 1-3 words and don't contain organizational terms
    words = name.split()
    if len(words) > 4:  # Too many words for a name
        return False

    # Check if it looks like a person's name pattern
    # Hebrew names often have patterns like "שם משפחה" or "שם פרטי שם משפחה"
    # But reject things that are clearly organizational
    org_indicators = [
        'מנהל', 'מנהלת', 'ראש', 'סגן', 'מזכיר', 'מזכירת',
        'רכז', 'רכזת', 'פקיד', 'פקידה', 'עובד', 'עובדת'
    ]

    for word in words:
        if word in org_indicators:
            return False

    return True


def clean_phone_number(phone: str) -> str:
    """Clean and validate phone number."""
    if not phone:
        return ""

    # Remove all non-digits
    phone_digits = re.sub(r'[^\d]', '', str(phone))

    # Israeli phone numbers should be 9-10 digits
    if len(phone_digits) < 9 or len(phone_digits) > 10:
        return ""

    # Add leading zero if missing (Israeli format)
    if len(phone_digits) == 9:
        phone_digits = "0" + phone_digits

    return phone_digits


def load_contacts(path: Path | None = None) -> dict:
    """Load contacts JSON from ``path`` or the default data directory."""
    if path is None:
        # Try to find the most recent contacts file
        possible_paths = [
            BASE_DIR / "output" / "contacts.json",
            BASE_DIR / "contacts.json",
            BASE_DIR / "data" / "smart_contacts.json"
        ]
        path = None
        for p in possible_paths:
            if p.exists():
                path = p
                break
        if path is None:
            raise FileNotFoundError("No contacts JSON file found. Please run the scraper first.")

    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_outputs(df: pd.DataFrame, base_filename: str = "all_contacts") -> None:
    csv_file = f"{base_filename}.csv"
    excel_file = f"{base_filename}.xlsx"

    df.to_csv(csv_file, index=False, encoding="utf-8-sig")
    print(f"✅ הקובץ נשמר: {csv_file}")

    df.to_excel(excel_file, index=False, engine="openpyxl")
    print(f" הקובץ נשמר גם כ־ {excel_file}")


def main(json_path: str | None = None) -> None:
    json_file_path = Path(json_path) if json_path else None
    data = load_contacts(json_file_path)

    rows = []
    phone_seen = set()  # Track phone numbers to prevent duplicates

    print(f"Processing contacts from {len(data)} cities...")

    for city, people in data.items():
        city_contacts = 0
        for name, info in people.items():
            # Clean and validate the name first
            clean_name = jobs._clean_text(name) if name else ""
            if not is_valid_name(clean_name):
                continue  # Skip invalid names

            # Handle both Hebrew keys (from main JSON) and English keys (from incremental JSON)
            phone = info.get("phone") or info.get("טלפון פרטי") or info.get("טלפון משרד") or ""
            email = info.get("email") or info.get("מייל") or ""
            job_title = info.get("job_title") or info.get("תפקיד") or ""
            department = info.get("department") or info.get("מחלקה") or ""

            # Clean and validate phone number
            clean_phone = clean_phone_number(phone)

            # Skip if no valid contact info
            clean_email = jobs._clean_text(str(email) if email else "")
            if not clean_phone and not clean_email:
                continue

            # Skip if phone number already seen (aggressive deduplication)
            if clean_phone and clean_phone in phone_seen:
                continue

            if clean_phone:
                phone_seen.add(clean_phone)

            rows.append(
                {
                    "עיר": jobs._clean_text(city),
                    "שם": clean_name,
                    "טלפון": clean_phone,
                    "אימייל": clean_email,
                    "תפקיד": jobs._clean_text(str(job_title) if job_title else ""),
                    "מחלקה": jobs._clean_text(str(department) if department else ""),
                }
            )
            city_contacts += 1

        if city_contacts > 0:
            print(f"  {city}: {city_contacts} valid contacts")

    df = pd.DataFrame(rows)
    print(f"\nTotal valid contacts: {len(df)}")
    print(f"Unique phone numbers: {len(phone_seen)}")

    # Generate output filename based on input JSON filename
    if json_file_path:
        base_name = json_file_path.stem  # filename without extension
        output_base = f"contacts_{base_name}" if base_name != "contacts" else "all_contacts"
    else:
        output_base = "all_contacts"

    save_outputs(df, output_base)


if __name__ == "__main__":
    import sys

    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(path_arg)
