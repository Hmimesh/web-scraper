"""Generate CSV/Excel contact lists from the scraped JSON file."""

import json
from pathlib import Path

import pandas as pd

import jobs

BASE_DIR = Path(__file__).resolve().parents[1]


def load_contacts(path: Path | None = None) -> dict:
    """Load contacts JSON from ``path`` or the default data directory."""
    if path is None:
        # Try to find the most recent contacts file
        possible_paths = [
            BASE_DIR / "output" / "contacts.json",
            BASE_DIR / "contacts.json",
            BASE_DIR / "data" / "smart_contacts.json"
        ]
        path = None
        for p in possible_paths:
            if p.exists():
                path = p
                break
        if path is None:
            raise FileNotFoundError("No contacts JSON file found. Please run the scraper first.")

    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_outputs(df: pd.DataFrame, base_filename: str = "all_contacts") -> None:
    csv_file = f"{base_filename}.csv"
    excel_file = f"{base_filename}.xlsx"

    df.to_csv(csv_file, index=False, encoding="utf-8-sig")
    print(f"✅ הקובץ נשמר: {csv_file}")

    df.to_excel(excel_file, index=False, engine="openpyxl")
    print(f" הקובץ נשמר גם כ־ {excel_file}")


def main(json_path: str | None = None) -> None:
    json_file_path = Path(json_path) if json_path else None
    data = load_contacts(json_file_path)

    rows = []
    for city, people in data.items():
        for name, info in people.items():
            # Handle both Hebrew keys (from main JSON) and English keys (from incremental JSON)
            phone = info.get("phone") or info.get("טלפון פרטי") or info.get("טלפון משרד") or ""
            email = info.get("email") or info.get("מייל") or ""
            job_title = info.get("job_title") or info.get("תפקיד") or ""
            department = info.get("department") or info.get("מחלקה") or ""

            rows.append(
                {
                    "עיר": jobs._clean_text(city),
                    "שם": jobs._clean_text(name),
                    "טלפון": jobs._clean_text(str(phone) if phone else ""),
                    "אימייל": jobs._clean_text(str(email) if email else ""),
                    "תפקיד": jobs._clean_text(str(job_title) if job_title else ""),
                    "מחלקה": jobs._clean_text(str(department) if department else ""),
                }
            )

    df = pd.DataFrame(rows)

    # Generate output filename based on input JSON filename
    if json_file_path:
        base_name = json_file_path.stem  # filename without extension
        output_base = f"contacts_{base_name}" if base_name != "contacts" else "all_contacts"
    else:
        output_base = "all_contacts"

    save_outputs(df, output_base)


if __name__ == "__main__":
    import sys

    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(path_arg)
