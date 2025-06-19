import json
import re
from pathlib import Path

from jobs import transliterate_to_hebrew


def apply_hebrew_transliteration(json_path: str | Path) -> None:
    """Load the contact JSON file and transliterate English names to Hebrew."""
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(json_path)

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    updated = False
    for city, people in data.items():
        for orig_key in list(people.keys()):
            info = people[orig_key]
            name = info.get("שם")
            if not name or re.search(r"[א-ת]", name):
                continue
            heb = transliterate_to_hebrew(name)
            if not heb:
                continue
            # update both key and name field
            people.pop(orig_key)
            info["שם"] = heb
            people[heb] = info
            updated = True

    if updated:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: datafunc.py path/to/contacts.json")
        raise SystemExit(1)
    apply_hebrew_transliteration(sys.argv[1])
