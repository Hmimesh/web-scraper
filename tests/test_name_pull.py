import json
import re
from pathlib import Path

from name_pull import collect_names, transliterate_to_hebrew, extract_name_from_email


def test_collect_names_from_log(tmp_path):
    log = tmp_path / "io.jsonl"
    entries = [
        {"Name": "Dan", "Email": "dan@example.com"},
        {"Name": "לא נמצא שם", "מייל": "eladr@info.example"},
        {"Name": "לא נמצא שם", "Email": "danz@example.com"},
        {"Name": "Dan", "Email": "dan@example.com"},
    ]
    with open(log, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    out_file = tmp_path / "names.txt"
    names = collect_names(str(log), str(out_file))

    assert len(names) == len(set(names))  # unique
    assert any(re.search(r"[א-ת]", n) for n in names)
    assert "דן" in names

    with open(out_file, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    assert lines == sorted(names)


def test_transliterate_short_vowel():
    assert transliterate_to_hebrew("Ben") == "בן"
    assert transliterate_to_hebrew("Dan") == "דן"
    assert transliterate_to_hebrew("Noam") == "נואם"


def test_extract_name_from_email():
    assert extract_name_from_email("danz@example.com") == "Dan"
