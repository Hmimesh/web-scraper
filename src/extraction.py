"""Post-process contacts CSV using ChatGPT helpers and name databases."""

import argparse
import pandas as pd
import re

from jobs import transliterate_to_hebrew, _dept_from_email
from chatgpt_name import guess_hebrew_department
from gov_names import load_names


HEBREW_CHARS = re.compile(r"[\u0590-\u05FF]")
FALLBACK_NAME = re.compile(r"^\s*לא\s*נמצ")

def _normalize_row(row: pd.Series) -> pd.Series:
    """Normalize name and department using heuristics and ChatGPT."""
    # --- Normalize name ---
    name = str(row.get("שם", "")).strip()
    if FALLBACK_NAME.search(name):
        row["שם"] = ""

    elif name and not HEBREW_CHARS.search(name):
        heb = transliterate_to_hebrew(name)
        if heb:
            row["שם"] = heb

    # --- Normalize department ---
    dept = row.get("מחלקה", "")
    if not dept or pd.isna(dept):
        email = row.get("אימייל", "")
        role = row.get("תפקיד", "")
        dept = _dept_from_email(email)

        if not dept:
            context = f"{role} {email}".strip()
            dept = guess_hebrew_department(context, email)

        if dept:
            row["מחלקה"] = dept

    return row


def main(input_csv: str, output_csv: str) -> None:
    try:
        df = pd.read_csv(input_csv, encoding="utf-8-sig")
    except FileNotFoundError:
        print(f"❌ Input file not found: {input_csv}")
        return

    if df.empty:
        print("⚠️ Empty input file.")
        return

    names_dataset = load_names()
    if not names_dataset:
        print("⚠️ Could not load government names dataset.")

    df = df.apply(_normalize_row, axis=1)

    # Drop rows with no phone or email
    df.dropna(subset=["טלפון", "אימייל"], how="all", inplace=True)

    # Drop exact duplicates
    df.drop_duplicates(subset=["עיר", "שם", "טלפון", "אימייל"], inplace=True)

    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"✅ Cleaned CSV saved to: {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize Hebrew contact rows using ChatGPT")
    parser.add_argument("input_csv", nargs="?", default="all_contacts.csv")
    parser.add_argument("output_csv", nargs="?", default="extracted_contacts_filtered.csv")
    args = parser.parse_args()
    main(args.input_csv, args.output_csv)
