import sys
from pathlib import Path

# Ensure src directory is on sys.path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import jobs
from jobs import Contacts


def test_contact_with_all_fields():
    text = "יוסי כהן example@example.com 05-1234567 02-7654321"
    c = Contacts(text, "תל אביב")
    assert c.email == "example@example.com"
    assert c.phone_mobile == "051234567"
    assert c.phone_office == "027654321"


def test_contact_mobile_only():
    text = "דני dani@test.org 05-8765432"
    c = Contacts(text, "חיפה")
    assert c.email == "dani@test.org"
    assert c.phone_mobile == "058765432"
    assert c.phone_office is None
    assert c.name == "דני"


def test_first_name_only():
    text = "צבי 05-5555555"
    c = Contacts(text, "גבעתיים")
    assert c.name == "צבי"
    assert c.phone_mobile == "055555555"


def test_contact_office_only():
    text = "שרה sarah@domain.com 03 1234567"
    c = Contacts(text, "ירושלים")
    assert c.email == "sarah@domain.com"
    assert c.phone_mobile is None
    assert c.phone_office == "031234567"


def test_non_name_phrase_lifratim_nosefim():
    text = "לפרטים נוספים נא לפנות example@example.com"
    c = Contacts(text, "אשדוד")
    assert c.name == "לא נמצא שם"


def test_non_name_phrase_email_address():
    text = "כתובת דואר אלקטרוני info@test.com"
    c = Contacts(text, "באר שבע")
    assert c.name == "לא נמצא שם"


def test_name_from_email(monkeypatch):
    monkeypatch.setattr(jobs, "guess_hebrew_name", lambda n: "נוא דרי")
    text = "noa_adari@example.org"
    c = Contacts(text, "אשקלון")
    assert c.name == "נוא דרי"


def test_non_personal_email_ignored():
    text = "info@example.org"
    c = Contacts(text, "אשקלון")
    assert c.name == "לא נמצא שם"


def test_lishka_email_ignored():
    text = "lishka@tel-aviv.gov.il"
    c = Contacts(text, "תל אביב")
    assert c.name == "לא נמצא שם"


def test_invalid_name_digits():
    assert not Contacts.is_valid_name("user123")


def test_hebrew_name_not_in_db():
    # Without a preloaded name database, unknown Hebrew names are allowed
    assert Contacts.is_valid_name("שםשאינובמאגר")


def test_trailing_char_single_segment(monkeypatch):
    monkeypatch.setattr(jobs, "guess_hebrew_name", lambda n: "נואם")
    text = "noamk@example.com"
    c = Contacts(text, "תל אביב")
    assert c.name == "נואם"


def test_english_name_from_text(monkeypatch):
    monkeypatch.setattr(jobs, "guess_hebrew_name", lambda n: "יוחנן דו")
    text = "Contact John Doe for info"
    c = Contacts(text, "תל אביב")
    assert c.name == "יוחנן דו"


def test_english_department_keyword():
    text = "education john@example.com"
    c = Contacts(text, "תל אביב")
    assert c.department == "מחלקת חינוך"


def test_department_from_email():
    text = "john@youngdept.org"
    c = Contacts(text, "תל אביב")
    assert c.department == "מחלקת צעירים"


def test_english_department_keyword_sports():
    text = "sports jane@example.com"
    c = Contacts(text, "תל אביב")
    assert c.department == "מחלקת ספורט"


def test_department_from_email_engineering():
    text = "bob@engineering-city.org"
    c = Contacts(text, "תל אביב")
    assert c.department == "מחלקת הנדסה"


def test_department_from_url_finance():
    text = "bob@example.com"
    c = Contacts(text, "תל אביב", url="https://city.gov.il/finance/team")
    assert c.department == "מחלקת כספים"
