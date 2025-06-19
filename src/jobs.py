import re
import json
import urllib.request
import urllib.parse
from pathlib import Path
from difflib import get_close_matches


LATIN_TO_HEBREW = {
    "a": "א",
    "b": "ב",
    "c": "ק",
    "d": "ד",
    "e": "י",
    "f": "פ",
    "g": "ג",
    "h": "ה",
    "i": "י",
    "j": "ג",
    "k": "ק",
    "l": "ל",
    "m": "מ",
    "n": "נ",
    "o": "ו",
    "p": "פ",
    "q": "ק",
    "r": "ר",
    "s": "ס",
    "t": "ט",
    "u": "ו",
    "v": "ו",
    "w": "ו",
    "x": "קס",
    "y": "י",
    "z": "ז",
}

FINAL_FORMS = {
    "m": "ם",
    "n": "ן",
    "p": "ף",
    "f": "ף",
    "k": "ך",
    "c": "ך",
    "t": "ת",
}


def transliterate_to_hebrew(name: str) -> str:
    """Transliterate a simple English name into Hebrew letters.

    The resulting name is cross-referenced against the official Israeli name
    database loaded from data.gov.il. If a close match is found, that spelling
    is used to avoid common transliteration mistakes (e.g. "Noam" -> "נועם").
    """
    result: list[str] = []
    clean = name.strip().lower()

    for i, ch in enumerate(clean):
        if ch == " ":
            result.append(" ")
            continue

        if (
            ch in {"e", "a"}
            and 0 < i < len(clean) - 1
            and clean[i - 1] not in "aeiou"
            and clean[i + 1] not in "aeiou"
        ):
            continue

        heb = LATIN_TO_HEBREW.get(ch)
        if not heb:
            continue

        if i == len(clean) - 1 and ch in FINAL_FORMS:
            heb = FINAL_FORMS[ch]

        result.append(heb)

    hebrew = "".join(result)

    if hebrew in ISRAELI_NAME_DB:
        return hebrew

    match = get_close_matches(hebrew, ISRAELI_NAME_DB, n=1, cutoff=0.7)
    if match:
        return match[0]

    return hebrew


def _load_name_db() -> set[str]:
    """Load known Israeli first names from local file or the gov.il API."""
    names = set()
    data_path = Path(__file__).resolve().parent.parent / "data/israeli_names.txt"

    if data_path.exists():
        try:
            with open(data_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        names.add(line)
        except Exception:
            pass

    # If the file wasn't found or was empty, try to fetch from the API
    if not names:
        try:
            offset = 0
            while True:
                url = (
                    "https://data.gov.il/api/3/action/datastore_search?"
                    "resource_id=c4fb2685-381f-4e99-a88e-b9b7ed703117"
                    f"&limit=1000&offset={offset}"
                )
                with urllib.request.urlopen(url, timeout=10) as resp:
                    data = json.load(resp)
                records = data.get("result", {}).get("records", [])
                for rec in records:
                    for key in ("שם פרטי", "first_name", "name"):
                        if key in rec and rec[key]:
                            names.add(str(rec[key]).strip())
                            break
                total = data.get("result", {}).get("total", 0)
                offset += 1000
                if offset >= total:
                    break
        except Exception:
            # Network or parsing errors are ignored; best-effort only
            pass

    return names


ISRAELI_NAME_DB = _load_name_db()

# Mapping of English keywords to their Hebrew department names. This allows
# detecting the department from contact lines that use English terms.
ENGLISH_DEPT_KEYWORDS = {
    "youth": "מחלקת נוער",
    "young": "מחלקת צעירים",
    "culture": "מחלקת תרבות",
    "events": "מחלקת אירועים",
    "education": "מחלקת חינוך",
    "community": "מחלקת קהילה",
    "welfare": "מחלקת רווחה",
    "absorption": "מחלקת קליטה",
    "environment": "מחלקת איכות סביבה",
    "veterans": "מחלקת אזרחים וותיקים",
}


def _dept_from_email(email: str) -> str | None:
    """Guess department from email address using ENGLISH_DEPT_KEYWORDS."""
    lower = email.lower()
    for keyword, dept in ENGLISH_DEPT_KEYWORDS.items():
        if keyword in lower:
            return dept
    return None

class Contacts:
    contacts = 0
    # Common phrases that might look like names but aren't
    NON_NAME_PHRASES = [
        "לפרטים נוספים",
        "כתובת דואר אלקטרוני",
        "לשכה",
        "אגף",
    ]

    # Non-personal words often used in departmental email addresses
    NON_PERSONAL_USERNAMES = {
        "info", "contact", "office", "admin", "support", "service",
        "team", "mail", "email", "example", "lishka", "agaf", "department"
    }

    @staticmethod
    def is_valid_name(name: str) -> bool:
        """Return True if the provided name looks like a real person's name."""
        if not name:
            return False
        if re.search(r"\d", name):
            return False
        if any(phrase in name for phrase in Contacts.NON_NAME_PHRASES):
            return False
        lower = name.lower()
        if any(word in lower for word in Contacts.NON_PERSONAL_USERNAMES):
            return False
        letters = re.sub(r"[^A-Za-zא-ת]", "", name)
        if len(letters) < 2:
            return False

        # If the name appears to be Hebrew and we have a database, ensure the
        # first name is part of the official list
        if ISRAELI_NAME_DB and re.search(r"[א-ת]", name):
            first = name.split()[0]
            if first not in ISRAELI_NAME_DB:
                return False
        return True

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
            "אגף נוער": "אגף נוער",
            "אגף צעירים": "אגף צעירים",
            "אגף תרבות": "אגף תרבות",
            "אגף אירועים": "אגף אירועים",
            "אגף חינוך": "אגף חינוך",
            "אגף קהילה": "אגף קהילה",
            "אגף רווחה": "אגף רווחה",
            "אגף קליטה": "אגף קליטה",
            "אגף סביבה": "אגף איכות סביבה",
            "אגף ותיקים": "אגף אזרחים וותיקים",
        }

        for keyword, dept in department_keywords.items():
            if keyword in self.raw_text:
                self.department = dept
                break

        # If no Hebrew keyword matched, look for English department keywords
        if not self.department:
            lower_text = self.raw_text.lower()
            for keyword, dept in ENGLISH_DEPT_KEYWORDS.items():
                if keyword in lower_text:
                    self.department = dept
                    break

        if not self.department and self.email:
            guessed = _dept_from_email(self.email)
            if guessed:
                self.department = guessed

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

        if candidate and Contacts.is_valid_name(candidate):
            self.name = candidate

        # Fall back to email-derived name if no Hebrew name detected
        if not self.name and self.email:
            # Skip when text contains known non-name phrases
            if not any(phrase in self.raw_text for phrase in Contacts.NON_NAME_PHRASES):
                local = self.email.split('@')[0]
                parts = re.split(r'[._-]+', local)
                parts = [p for p in parts if p.isalpha()]
                if parts and all(p.lower() not in Contacts.NON_PERSONAL_USERNAMES for p in parts):
                    if len(parts) == 1 and parts[0][-1].isalpha():
                        parts[0] = parts[0][:-1]
                    name_guess = " ".join(p.capitalize() for p in parts)
                    if Contacts.is_valid_name(name_guess):
                        self.name = name_guess

        if not self.name:
            self.name = f"לא נמצא שם ({self.role})" if self.role else "לא נמצא שם"

        if self.name and not re.search(r"[א-ת]", self.name):
            heb = transliterate_to_hebrew(self.name)
            if heb:
                self.name = heb

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
