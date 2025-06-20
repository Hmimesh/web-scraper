import json
import re
from pathlib import Path

from jobs import transliterate_to_hebrew


def apply_hebrew_transliteration(json_path: str | Path) -> None:
    """Transliterate English contact names in ``json_path`` to Hebrew.

    The function originally expected files structured as ``{city: {name: {...}}}``.
    Some intermediate files contain a flat ``{name: {...}}`` mapping instead.
    This helper now supports both layouts by detecting whether the top-level
    values are contact dictionaries or nested dictionaries of contacts.
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(json_path)

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    updated = False

    def transliterate_dict(people: dict) -> None:
        nonlocal updated
        for orig_key in list(people.keys()):
            info = people[orig_key]
            if not isinstance(info, dict):
                continue
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

    # Determine whether this is a flat mapping {name: info} or
    # a nested mapping {city: {name: info}}
    if data and all(isinstance(v, dict) and ("שם" in v) for v in data.values()):
        # flat structure
        transliterate_dict(data)
    else:
        for city, people in data.items():
            if isinstance(people, dict):
                transliterate_dict(people)

    if updated:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: datafunc.py path/to/contacts.json")
        raise SystemExit(1)
    apply_hebrew_transliteration(sys.argv[1])
