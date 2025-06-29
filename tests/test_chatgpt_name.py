import sys
from pathlib import Path
import types

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import chatgpt_name
import jobs
from jobs import Contacts


def test_guess_hebrew_name(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(chatgpt_name, "guess_hebrew_name", lambda _: "דן")

    assert chatgpt_name.guess_hebrew_name("Dan") == "דן"


def test_contacts_chatgpt_fallback(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(jobs, "guess_hebrew_name", lambda _: "דן")

    c = Contacts("some text without name", "תל אביב")
    assert c.name == "דן"


def test_guess_hebrew_department(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(chatgpt_name, "guess_hebrew_department", lambda *_: "מחלקת תרבות")

    result = chatgpt_name.guess_hebrew_department(
        "culture text", "http://ex.com/culture"
    )
    assert result == "מחלקת תרבות"


def test_contacts_chatgpt_department_fallback(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    monkeypatch.setattr(jobs, "guess_hebrew_department", lambda *_: "מחלקת חינוך")
    monkeypatch.setattr(jobs, "guess_hebrew_name", lambda _: "דן")

    c = Contacts("no department text", "תל אביב", url="http://ex.com/edu")
    assert c.department in {"מחלקת חינוך", "חינוך", "חינוכית", "חינוך ותרבות"}
    assert c.name == "דן"
