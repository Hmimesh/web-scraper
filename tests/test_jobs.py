import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import jobs
from jobs import Contacts

import pytest


@pytest.mark.parametrize("text, expected", [
    ("info@example.com", "לא נמצא שם"),
    ("admin@city.gov.il", "לא נמצא שם"),
    ("webmaster@domain.com", "לא נמצא שם"),
    ("noreply@service.org", "לא נמצא שם"),
    ("support@helpdesk.net", "לא נמצא שם"),
    ("office@municipality.gov.il", "לא נמצא שם"),
    ("contact@ngo.org", "לא נמצא שם"),
    ("lishka@tel-aviv.gov.il", "לא נמצא שם"),
    ("dan@realname.com", "דן"),  # should still work
    ("noa_adari@org.org", "נוא דרי")
])
def test_email_prefix_blacklist(monkeypatch, text, expected):
    monkeypatch.setattr(jobs, "guess_hebrew_name", lambda email: {
        "info": "אינפו",
        "admin": "אדמין",
        "webmaster": "ובמסטר",
        "noreply": "נוריפליי",
        "support": "ספורט",
        "office": "אופיס",
        "contact": "קונטקט",
        "lishka": "לישקה",
        "dan": "דן",
        "noa_adari": "נוא דרי"
    }.get(email.split("@")[0].lower(), None))

    c = Contacts(text, "קריית ביאליק")
    assert c.name == expected


def test_blacklisted_name_detection(monkeypatch):
    # Add test to ensure names like "info" are not considered valid
    assert not Contacts.is_valid_name("info")
    assert not Contacts.is_valid_name("lishka")
    assert Contacts.is_valid_name("דני")
    assert Contacts.is_valid_name("אביגיל")
    assert not Contacts.is_valid_name("user123")


def test_name_from_clean_email(monkeypatch):
    monkeypatch.setattr(jobs, "guess_hebrew_name", lambda n: "נואם")
    c = Contacts("noam@example.com", "תל אביב")
    assert c.name == "נואם"


def test_blacklist_behavior_with_long_text(monkeypatch):
    monkeypatch.setattr(jobs, "guess_hebrew_name", lambda n: "קונטקט")
    c = Contacts("לתמיכה טכנית אנא פנו contact@helpdesk.gov.il", "בת ים")
    assert c.name == "לא נמצא שם"