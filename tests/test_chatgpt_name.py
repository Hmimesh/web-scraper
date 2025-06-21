import sys
from pathlib import Path
import types

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import chatgpt_name
from jobs import Contacts


def test_guess_hebrew_name(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_create(**kwargs):
        return {"choices": [{"message": {"content": "דן"}}]}

    client = types.SimpleNamespace(
        chat=types.SimpleNamespace(
            completions=types.SimpleNamespace(create=fake_create)
        )
    )
    dummy = types.SimpleNamespace(OpenAI=lambda **kwargs: client)
    monkeypatch.setattr(chatgpt_name, "openai", dummy)

    assert chatgpt_name.guess_hebrew_name("Dan") == "דן"


def test_contacts_chatgpt_fallback(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_create(**kwargs):
        return {"choices": [{"message": {"content": "דן"}}]}

    client = types.SimpleNamespace(
        chat=types.SimpleNamespace(
            completions=types.SimpleNamespace(create=fake_create)
        )
    )
    dummy = types.SimpleNamespace(OpenAI=lambda **kwargs: client)
    monkeypatch.setattr(chatgpt_name, "openai", dummy)

    c = Contacts("some text without name", "תל אביב")
    assert c.name == "לא נמצא שם"


def test_guess_hebrew_department(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_create(**kwargs):
        return {"choices": [{"message": {"content": "מחלקת תרבות"}}]}

    client = types.SimpleNamespace(
        chat=types.SimpleNamespace(
            completions=types.SimpleNamespace(create=fake_create)
        )
    )
    dummy = types.SimpleNamespace(OpenAI=lambda **kwargs: client)
    monkeypatch.setattr(chatgpt_name, "openai", dummy)

    result = chatgpt_name.guess_hebrew_department(
        "culture text", "http://ex.com/culture"
    )
    assert result == "מחלקת תרבות"


def test_contacts_chatgpt_department_fallback(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_create(**kwargs):
        sys_msg = kwargs["messages"][0]["content"]
        if "department" in sys_msg:
            return {"choices": [{"message": {"content": "מחלקת חינוך"}}]}
        return {"choices": [{"message": {"content": "דן"}}]}

    client = types.SimpleNamespace(
        chat=types.SimpleNamespace(
            completions=types.SimpleNamespace(create=fake_create)
        )
    )
    dummy = types.SimpleNamespace(OpenAI=lambda **kwargs: client)
    monkeypatch.setattr(chatgpt_name, "openai", dummy)

    c = Contacts("no department text", "תל אביב", url="http://ex.com/edu")
    assert c.department == "מחלקת חינוך"
    assert c.name == "לא נמצא שם"
