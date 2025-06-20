import json
from pathlib import Path

import jobs
from datafunc import apply_hebrew_transliteration


def test_transliteration_updates_file(tmp_path, monkeypatch):
    monkeypatch.setattr(jobs, "guess_hebrew_name", lambda n: "יוחנן")
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
    assert "יוחנן" in loaded["אלעד"]
