import json
from pathlib import Path

try:
    import requests  # type: ignore
except ImportError:
    print("The 'requests' module is not installed. Please run 'pip install -r requirements.txt'.")
    requests = None

# URL of the open dataset of given names from data.gov.il
DATA_URL = "https://data.gov.il/api/3/action/datastore_search?resource_id=8fbc7cc8-9426-4a39-b996-6b8d75ee4fc3&limit=5000"

# Location to store the downloaded mapping
NAMES_FILE = Path(__file__).resolve().parents[1] / "data" / "gov_names.json"

_names_cache: dict[str, str] | None = None

def _download_names() -> dict[str, str]:
    """Download the names dataset from data.gov.il if possible."""
    if requests is None:
        return {}

    try:
        resp = requests.get(DATA_URL, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        records = data.get("result", {}).get("records", [])
        mapping: dict[str, str] = {}

        for rec in records:
            heb = rec.get("שם פרטי") or rec.get("שם") or rec.get("name_he") or rec.get("heb")
            eng = rec.get("שם_לועזי") or rec.get("שם באנגלית") or rec.get("name_en") or rec.get("eng")
            if eng and heb:
                mapping[eng.strip()] = heb.strip()

        if mapping:
            NAMES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(NAMES_FILE, "w", encoding="utf-8") as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)

        return mapping

    except requests.RequestException as e:
        print(f"Failed to fetch data from the API: {e}")
        return {}


def load_names() -> dict[str, str]:
    """Return mapping of English names to Hebrew from the dataset."""
    global _names_cache
    if _names_cache is not None:
        return _names_cache

    if NAMES_FILE.exists():
        try:
            with open(NAMES_FILE, encoding="utf-8") as f:
                _names_cache = json.load(f)
            return _names_cache
        except Exception as e:
            print(f"Error reading cached names file: {e}")

    _names_cache = _download_names()
    return _names_cache or {}

