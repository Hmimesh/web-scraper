"""Generate CSV/Excel contact lists from the scraped JSON file."""

import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]


def load_contacts(path: Path | None = None) -> dict:
    """Load contacts JSON from ``path`` or the default data directory."""
    if path is None:
        path = BASE_DIR / "data" / "smart_contacts.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)

def save_outputs(df: pd.DataFrame) -> None:
    df.to_csv("all_contacts.csv", index=False, encoding="utf-8-sig")
    print("✅ הקובץ נשמר: all_contacts.csv")

    df.to_excel("all_contacts.xlsx", index=False, engine="openpyxl")
    print(" הקובץ נשמר גם כ־ all_contacts.xlsx")


def main(json_path: str | None = None) -> None:
    data = load_contacts(Path(json_path) if json_path else None)

    rows = []
    for city, people in data.items():
        for name, info in people.items():
            rows.append(
                {
                    "עיר": city,
                    "שם": name,
                    "טלפון": info.get("phone"),
                    "אימייל": info.get("email"),
                    "תפקיד": info.get("job_title"),
                    "מחלקה": info.get("department"),
                }
            )

    df = pd.DataFrame(rows)
    save_outputs(df)


if __name__ == "__main__":
    import sys

    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(path_arg)
