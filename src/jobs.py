import json
import re
from pathlib import Path

from chatgpt_name import guess_hebrew_name, guess_hebrew_department
from gov_names import load_names


CACHE_FILE = Path(__file__).resolve().parents[1] / "data" / "translation_cache.json"
_translation_cache: dict[str, str] | None = None
_gov_names: dict[str, str] | None = None


def _load_cache() -> dict[str, str]:
    """Load the transliteration cache from ``CACHE_FILE``."""
    global _translation_cache
    if _translation_cache is None:
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, encoding="utf-8") as f:
                    _translation_cache = json.load(f)
            except Exception:
                _translation_cache = {}
        else:
            _translation_cache = {}
    return _translation_cache


def _save_cache(cache: dict[str, str]) -> None:
    """Persist ``cache`` to ``CACHE_FILE``."""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _load_gov_names() -> dict[str, str]:
    """Load the government names list or return an empty mapping."""
    global _gov_names
    if _gov_names is None:
        try:
            _gov_names = {k.lower(): v for k, v in load_names().items()}
        except Exception:
            _gov_names = {}
    return _gov_names


def _clean_text(text: str) -> str:
    """Return ``text`` without tabs, newlines, or duplicate whitespace."""
    # Replace newlines and tabs with spaces, then collapse multiple spaces
    return re.sub(r"\s+", " ", text.replace("\n", " ").replace("\t", " ")).strip()


def transliterate_to_hebrew(name: str) -> str | None:
    """Return a Hebrew version of ``name`` using dataset lookup and ChatGPT."""
    cache = _load_cache()
    cached = cache.get(name)
    if cached:
        return cached

    gov_names = _load_gov_names()
    match = gov_names.get(name.lower())
    if match:
        cache[name] = match
        _save_cache(cache)
        return match

    result = guess_hebrew_name(name)
    if result:
        cache[name] = result
        _save_cache(cache)
    return result


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
    "sport": "מחלקת ספורט",
    "sports": "מחלקת ספורט",
    "finance": "מחלקת כספים",
    "finances": "מחלקת כספים",
    "engineering": "מחלקת הנדסה",
    "transport": "מחלקת תחבורה",
    "traffic": "מחלקת תחבורה",
    "security": "מחלקת ביטחון",
}


def _dept_from_email(email: str) -> str | None:
    """Guess department from email address using ENGLISH_DEPT_KEYWORDS."""
    lower = re.sub(r"[-_.]+", " ", email.lower())
    for keyword, dept in ENGLISH_DEPT_KEYWORDS.items():
        if keyword in lower:
            return dept
    return None


def _dept_from_url(url: str) -> str | None:
    """Guess department from a URL using ENGLISH_DEPT_KEYWORDS."""
    lower = re.sub(r"[-_.]+", " ", url.lower())
    for keyword, dept in ENGLISH_DEPT_KEYWORDS.items():
        if keyword in lower:
            return dept
    return None


class Contacts:
    contacts = 0
    NON_NAME_PHRASES = [
        "לפרטים נוספים",
        "כתובת דואר אלקטרוני",
        "דואר אלקטרוני",
        'דוא"ל',
        "דוא",
        "לשכה",
        "אגף",
    ]

    NON_PERSONAL_USERNAMES = {
        "info",
        "contact",
        "office",
        "admin",
        "support",
        "service",
        "team",
        "mail",
        "email",
        "example",
        "lishka",
        "agaf",
        "department",
    }

    @staticmethod
    def is_valid_name(name: str) -> bool:
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
        return True

    def __init__(self, raw_text, city, url: str | None = None):
        self.raw_text = raw_text
        self.city = city
        self.url = url
        self.name = None
        self.role = None
        self.department = None
        self.email = None
        self.phone_mobile = None
        self.phone_office = None
        self.parse()
        Contacts.contacts += 1

    def parse(self):
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", self.raw_text)
        if email_match:
            self.email = email_match.group(0)

        phones = re.findall(r"0[2-9][-\s]?\d{7}", self.raw_text)
        for phone in phones:
            clean_phone = re.sub(r"[^\d]", "", phone)
            if clean_phone.startswith("05") or clean_phone.startswith("+972"):
                self.phone_mobile = clean_phone
            else:
                self.phone_office = clean_phone

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

        if not self.department:
            match = re.search(r"(מחלק(?:ה|ת)|אגף)\s*[\u05d0-\u05ea\s]{2,20}", self.raw_text)
            if match:
                dept = match.group(0).strip().replace("מחלקה", "מחלקת")
                self.department = dept

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

        if not self.department and self.url:
            guessed = _dept_from_url(self.url)
            if guessed:
                self.department = guessed

        if not self.department:
            guessed = guess_hebrew_department(self.raw_text, self.url)
            if guessed:
                self.department = guessed

        possible_roles = [
            "רכז", "רכזת", "מנהל", "מנהלת", "יועץ", "יועצת", "מפקח", "מפקחת",
            "אחראי", "אחראית", 'יו"ר', "עובד", "עובדת", "סגן", "ראש", 'מנכ"ל',
        ]

        for word in self.raw_text.split():
            if any(role in word for role in possible_roles):
                self.role = word
                break

        if self.name is None:
            candidate = None
            name_candidates = re.findall(r"[א-ת]{2,}(?:\s+[א-ת\"׳]{2,})+", self.raw_text)
            if name_candidates:
                candidate = name_candidates[0].strip()
            if not candidate:
                first_match = re.search(r"\b[א-ת]{2,}\b", self.raw_text)
                if first_match:
                    candidate = first_match.group(0).strip()
            if not candidate:
                eng_candidates = [
                    m.group(1)
                    for m in re.finditer(r"(?=([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+))", self.raw_text)
                ]
                for cand in eng_candidates:
                    if Contacts.is_valid_name(cand):
                        candidate = cand.strip()
                        break
            if candidate and Contacts.is_valid_name(candidate):
                self.name = candidate

        if not self.name and self.email:
            if not any(phrase in self.raw_text for phrase in Contacts.NON_NAME_PHRASES):
                local = self.email.split("@")[0]
                if local.lower() in Contacts.NON_PERSONAL_USERNAMES:
                    self.name = "לא נמצא שם"
                elif not any(phrase in self.raw_text for phrase in Contacts.NON_NAME_PHRASES): 
                    # Split the local part of the email into parts
                    # and try to guess a name from it
                    local = local.replace(".", " ").replace("_", " ").replace("-", " ")
                    local = re.sub(r"\d", "", local)  # Remove digits
                    local = local.strip()
                parts = re.split(r"[._-]+", local)
                parts = [p for p in parts if p.isalpha()]
                if parts and all(p.lower() not in Contacts.NON_PERSONAL_USERNAMES for p in parts):
                    if len(parts) == 1 and parts[0][-1].isalpha():
                        parts[0] = parts[0][:-1]
                    name_guess = " ".join(p.capitalize() for p in parts)
                    if Contacts.is_valid_name(name_guess):
                        self.name = name_guess

        if not self.name:
            guess = guess_hebrew_name(self.raw_text)
            if guess:
                self.name = guess
            else:
                self.name = f"לא נמצא שם ({self.role})" if self.role else "לא נמצא שם"
        else:
            if not re.search(r"[א-ת]", self.name):
                guess = guess_hebrew_name(self.name)
                if guess:
                    self.name = guess

        if self.name:
            self.name = _clean_text(self.name)
        if self.role:
            self.role = _clean_text(self.role)
        if self.department:
            self.department = _clean_text(self.department)

    def to_dict(self):
        return {
            "שם": self.name,
            "תפקיד": self.role,
            "מחלקה": self.department,
            "רשות": self.city,
            "מייל": self.email,
            "טלפון פרטי": self.phone_mobile,
            "טלפון משרד": self.phone_office,
        }
    def __repr__(self):
        return f"Contacts(name={self.name}, role={self.role}, department={self.department}, email={self.email})"