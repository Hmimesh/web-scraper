import json
from pathlib import Path

from datafunc import apply_hebrew_transliteration


def test_transliteration_updates_file(tmp_path):
    data = {
        "אלעד": {
            "john": {"שם": "john", "מייל": "john@example.com"}
        }
    }
    file = tmp_path / "contacts.json"
    file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    apply_hebrew_transliteration(file)

    loaded = json.loads(file.read_text(encoding="utf-8"))
    assert "john" not in loaded["אלעד"]
    assert "גוהן" in loaded["אלעד"]
