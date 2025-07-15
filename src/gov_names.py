import json
from pathlib import Path

try:
    import requests  # type: ignore
except ImportError:
    print("The 'requests' module is not installed. Please run 'pip install -r requirements.txt'.")
    requests = None

# URL of the open dataset of given names from data.gov.il
# Updated with the correct resource ID
DATA_URL = "https://data.gov.il/api/3/action/datastore_search?resource_id=c4fb2685-381f-4e99-a88e-b9b7ed703117&limit=5000"

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

        # Note: The current dataset only contains Hebrew names without English equivalents
        # This is different from the original bilingual dataset that was used before
        print(f"⚠️  Note: The data.gov.il dataset has changed structure.")
        print(f"   Found {len(records)} Hebrew names, but no English equivalents.")
        print(f"   The Hebrew name transliteration will rely on ChatGPT only.")

        # We could potentially use this for validation, but for now return empty
        # to fall back to ChatGPT-only transliteration
        return {}

    except requests.RequestException as e:
        print(f"Failed to fetch data from the API: {e}")
        print("Falling back to ChatGPT-only name transliteration.")
        return {}


def _get_static_name_mappings() -> dict[str, str]:
    """Return a static fallback mapping of common English to Hebrew names."""
    return {
        # Common male names
        "David": "דוד",
        "Daniel": "דניאל",
        "Michael": "מיכאל",
        "Jonathan": "יונתן",
        "Joseph": "יוסף",
        "Benjamin": "בנימין",
        "Samuel": "שמואל",
        "Aaron": "אהרון",
        "Jacob": "יעקב",
        "Isaac": "יצחק",
        "Abraham": "אברהם",
        "Moses": "משה",
        "Adam": "אדם",
        "Noah": "נח",
        "Eli": "עלי",
        "Uri": "אורי",
        "Avi": "אבי",
        "Yosef": "יוסף",
        "Moshe": "משה",
        "Avraham": "אברהם",

        # Common female names
        "Sarah": "שרה",
        "Rachel": "רחל",
        "Rebecca": "רבקה",
        "Leah": "לאה",
        "Miriam": "מרים",
        "Ruth": "רות",
        "Esther": "אסתר",
        "Hannah": "חנה",
        "Tamar": "תמר",
        "Naomi": "נעמי",
        "Judith": "יהודית",
        "Deborah": "דבורה",
        "Rivka": "רבקה",
        "Chana": "חנה",
        "Shira": "שירה",
        "Noa": "נועה",
        "Maya": "מיה",
        "Tal": "טל",
        "Dana": "דנה",
        "Yael": "יעל",

        # Common Arabic names (for Israeli Arabs)
        "Ahmad": "אחמד",
        "Mohammed": "מוחמד",
        "Ali": "עלי",
        "Omar": "עומר",
        "Hassan": "חסן",
        "Fatima": "פאטמה",
        "Aisha": "עאישה",
        "Layla": "ליילה",
        "Nour": "נור",
        "Salam": "סלאם",

        # Common international names
        "Alex": "אלכס",
        "Mark": "מרק",
        "John": "ג'ון",
        "Robert": "רוברט",
        "Lisa": "ליסה",
        "Anna": "אנה",
        "Maria": "מריה",
        "Elena": "אלנה",
    }


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

    # If download failed, use static fallback with common names
    if not _names_cache:
        _names_cache = _get_static_name_mappings()

    return _names_cache or {}

