import re

class Contacts:
    contacts = 0
    # Common phrases that might look like names but aren't
    NON_NAME_PHRASES = [
        "לפרטים נוספים",
        "כתובת דואר אלקטרוני",
    ]

    def __init__(self, raw_text, city):
        self.raw_text = raw_text
        self.city = city
        self.name = None
        self.role = None
        self.department = None
        self.email = None
        self.phone_mobile = None
        self.phone_office = None

        self.parse()
        Contacts.contacts += 1

    def parse(self):
        # Match email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', self.raw_text)
        if email_match:
            self.email = email_match.group(0)

        # Find all phone numbers with or without dash/space
        phones = re.findall(r'0[2-9][-\s]?\d{7}', self.raw_text)
        for phone in phones:
            clean_phone = re.sub(r'[^\d]', '', phone)
            if clean_phone.startswith("05") or clean_phone.startswith("+972"):
                self.phone_mobile = clean_phone
            else:
                self.phone_office = clean_phone

        # Try to guess department based on keywords
        department_keywords = {
            "נוער": "מחלקת נוער",
            "צעירים": "מחלקת צעירים",
            "תרבות": "מחלקת תרבות",
            "אירועים": "מחלקת אירועים",
            "חינוך": "מחלקת חינוך",
            "קהילה": "מחלקת קהילה",
            "רווחה": "מחלקת רווחה",
            "קליטה": "מחלקת קליטה",
            "סביבה": "מחלקת איכות סביבה",
            "וותיקים": "מחלקת אזרחים וותיקים",
        }

        for keyword, dept in department_keywords.items():
            if keyword in self.raw_text:
                self.department = dept
                break

        # Try to guess role from line
        possible_roles = [
            "רכז", "רכזת", "מנהל", "מנהלת", "יועץ", "יועצת", "מפקח", "מפקחת",
            "אחראי", "אחראית", "יו\"ר", "עובד", "עובדת", "סגן", "ראש", "מנכ\"ל"
        ]
        for word in self.raw_text.split():
            if any(role in word for role in possible_roles):
                self.role = word
                break

        # Try to extract full Hebrew name first
        candidate = None
        name_candidates = re.findall(r"[א-ת]{2,}(?:\s+[א-ת\"׳]{2,})+", self.raw_text)
        if name_candidates:
            candidate = name_candidates[0].strip()

        # If no full name found, fall back to a single Hebrew word (first name)
        if not candidate:
            first_match = re.search(r"\b[א-ת]{2,}\b", self.raw_text)
            if first_match:
                candidate = first_match.group(0).strip()

        if candidate and not any(candidate in phrase or phrase in candidate for phrase in Contacts.NON_NAME_PHRASES):
            self.name = candidate

        # Fall back to email-derived name if no Hebrew name detected
        if not self.name and self.email:
            # Skip when text contains known non-name phrases
            if not any(phrase in self.raw_text for phrase in Contacts.NON_NAME_PHRASES):
                local = self.email.split('@')[0]
                parts = re.split(r'[._-]+', local)
                parts = [p for p in parts if p.isalpha()]
                non_personal = {"info", "contact", "office", "admin", "support", "service", "team", "mail", "email", "example"}
                if parts and all(p.lower() not in non_personal for p in parts):
                    self.name = " ".join(p.capitalize() for p in parts)

        if not self.name:
            self.name = f"לא נמצא שם ({self.role})" if self.role else "לא נמצא שם"

    def to_dict(self):
        return {
            "שם": self.name,
            "תפקיד": self.role,
            "מחלקה": self.department,
            "רשות": self.city,
            "מייל": self.email,
            "טלפון פרטי": self.phone_mobile,
            "טלפון משרד": self.phone_office
        }
