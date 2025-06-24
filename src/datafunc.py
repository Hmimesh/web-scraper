import json
import re
from pathlib import Path
from jobs import transliterate_to_hebrew

def apply_hebrew_transliteration(json_path: str | Path) -> None:
    """Transliterate English contact names in `json_path` to Hebrew, with safeguards."""
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
            if not name:
                continue

            # Skip if already in Hebrew or fallback/invalid
            if re.search(r"[א-ת]", name) or name.startswith("לא נמצא"):
                continue

            heb = transliterate_to_hebrew(name)
            if not heb or heb in people:
                continue

            # Log change (optional)
            print(f"Transliterated: '{orig_key}' → '{heb}'")

            # Update safely
            people.pop(orig_key)
            info["שם"] = heb
            people[heb] = info
            updated = True

    # Detect structure: flat {name: {...}} vs nested {city: {name: {...}}}
    if data and all(isinstance(v, dict) and "שם" in v for v in data.values()):
        transliterate_dict(data)  # flat structure
    else:
        for city, people in data.items():
            if isinstance(people, dict):
                transliterate_dict(people)

    if updated:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Hebrew transliteration applied and saved to: {json_path}")
    else:
        print(f"ℹ️ No transliteration changes made to: {json_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: datafunc.py path/to/contacts.json")
        raise SystemExit(1)

    apply_hebrew_transliteration(sys.argv[1])
