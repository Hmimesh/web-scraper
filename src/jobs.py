import re


from chatgpt_name import guess_hebrew_name, guess_hebrew_department


def _clean_text(text: str) -> str:
    """Return ``text`` without tabs, stray punctuation or duplicate whitespace."""
    text = text.replace("\t", " ")
    text = re.sub(r"[,:;]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -_,;:")


def transliterate_to_hebrew(name: str) -> str | None:
    """Return a Hebrew version of ``name`` using ChatGPT only."""

    return guess_hebrew_name(name)


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


def _dept_from_url(url: str) -> str | None:
    """Guess department from a URL using ENGLISH_DEPT_KEYWORDS."""
    lower = url.lower()
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
        # Match email
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", self.raw_text)
        if email_match:
            self.email = email_match.group(0)
        sanitized_text = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "", self.raw_text)

        # Find all phone numbers with or without dash/space
        phones = re.findall(r"0[2-9][-\s]?\d{7}", self.raw_text)
        for phone in phones:
            clean_phone = re.sub(r"[^\d]", "", phone)
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

        if not self.department and self.url:
            guessed = _dept_from_url(self.url)
            if guessed:
                self.department = guessed

        if not self.department:
            guessed = guess_hebrew_department(self.raw_text, self.url)
            if guessed:
                self.department = guessed

        # Try to guess role from line
        possible_roles = [
            "רכז",
            "רכזת",
            "מנהל",
            "מנהלת",
            "יועץ",
            "יועצת",
            "מפקח",
            "מפקחת",
            "אחראי",
            "אחראית",
            'יו"ר',
            "עובד",
            "עובדת",
            "סגן",
            "ראש",
            'מנכ"ל',
        ]
        for word in self.raw_text.split():
            if any(role in word for role in possible_roles):
                self.role = word
                break

        # Split patterns like "Name-Role" or "Name (Role)"
        combined = re.search(
            r"([A-Za-zא-ת ]{2,})\s*[-–]\s*([A-Za-zא-ת\"׳ ]{2,})",
            sanitized_text,
        )
        if (
            combined
            and "@" not in combined.group(0)
            and Contacts.is_valid_name(combined.group(1).strip())
        ):
            self.name = combined.group(1).strip()
            self.role = combined.group(2).strip()
        else:
            paren = re.search(
                r"([A-Za-zא-ת ]{2,})\(([^)]+)\)",
                sanitized_text,
            )
            if (
                paren
                and "@" not in paren.group(0)
                and Contacts.is_valid_name(paren.group(1).strip())
            ):
                self.name = paren.group(1).strip()
                self.role = paren.group(2).strip()

        if self.name is None:
            candidate = None
            # Try to extract full Hebrew name first
            name_candidates = re.findall(
                r"[א-ת]{2,}(?:\s+[א-ת\"׳]{2,})+", self.raw_text
            )
            if name_candidates:
                candidate = name_candidates[0].strip()

            # If no full name found, fall back to a single Hebrew word (first name)
            if not candidate:
                first_match = re.search(r"\b[א-ת]{2,}\b", self.raw_text)
                if first_match:
                    candidate = first_match.group(0).strip()

            # If still none, try to extract an English name
            if not candidate:
                eng_candidates = [
                    m.group(1)
                    for m in re.finditer(
                        r"(?=([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+))", self.raw_text
                    )
                ]
                for cand in eng_candidates:
                    if Contacts.is_valid_name(cand):
                        candidate = cand.strip()
                        break

            if candidate and Contacts.is_valid_name(candidate):
                self.name = candidate

            # Fall back to email-derived name if no name detected
            if not self.name and self.email:
                # Skip when text contains known non-name phrases
                if not any(
                    phrase in self.raw_text for phrase in Contacts.NON_NAME_PHRASES
                ):
                    local = self.email.split("@")[0]
                    parts = re.split(r"[._-]+", local)
                    parts = [p for p in parts if p.isalpha()]
                    if parts and all(
                        p.lower() not in Contacts.NON_PERSONAL_USERNAMES for p in parts
                    ):
                        if len(parts) == 1 and parts[0][-1].isalpha():
                            parts[0] = parts[0][:-1]
                        name_guess = " ".join(p.capitalize() for p in parts)
                        if Contacts.is_valid_name(name_guess):
                            self.name = name_guess

        if not self.name:
            self.name = f"לא נמצא שם ({self.role})" if self.role else "לא נמצא שם"
        else:
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
