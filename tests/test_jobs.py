import sys
from pathlib import Path

# Ensure src directory is on sys.path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))

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


def test_contact_office_only():
    text = "שרה sarah@domain.com 03 1234567"
    c = Contacts(text, "ירושלים")
    assert c.email == "sarah@domain.com"
    assert c.phone_mobile is None
    assert c.phone_office == "031234567"
