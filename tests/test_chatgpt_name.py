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

    dummy = types.SimpleNamespace(
        ChatCompletion=types.SimpleNamespace(create=fake_create)
    )
    monkeypatch.setattr(chatgpt_name, "openai", dummy)

    assert chatgpt_name.guess_hebrew_name("Dan") == "דן"


def test_contacts_chatgpt_fallback(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_create(**kwargs):
        return {"choices": [{"message": {"content": "דן"}}]}

    dummy = types.SimpleNamespace(
        ChatCompletion=types.SimpleNamespace(create=fake_create)
    )
    monkeypatch.setattr(chatgpt_name, "openai", dummy)

    c = Contacts("some text without name", "תל אביב")
    assert c.name == "דן"
