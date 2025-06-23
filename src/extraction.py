"""Post-process contacts CSV using ChatGPT helpers."""

from __future__ import annotations

import argparse
import pandas as pd
import re

from jobs import transliterate_to_hebrew, _dept_from_email
from chatgpt_name import guess_hebrew_department
from gov_names import load_names


HEBREW_RANGE = re.compile(r"[\u0590-\u05FF]")
MISSING_NAME = re.compile(r"^\s*לא\s*נמצ")


def _normalize_row(row: pd.Series) -> pd.Series:
    """Return ``row`` with translated name/department when missing."""
    name = str(row.get("שם", "")).strip()
    if MISSING_NAME.search(name):
        row["שם"] = ""
    elif name and not HEBREW_RANGE.search(name):
        heb = transliterate_to_hebrew(name)
        if heb:
            row["שם"] = heb

    if not row.get("מחלקה"):
        email = row.get("אימייל") or ""
        dept = _dept_from_email(email)
        if not dept:
            dept = guess_hebrew_department(row.get("תפקיד"), email)
        if dept:
            row["מחלקה"] = dept
    return row


def main(input_csv: str, output_csv: str) -> None:
    names = load_names()
    if not names:
        print("⚠️ Unable to load official names dataset")

    df = pd.read_csv(input_csv, encoding="utf-8-sig")
    df = df.apply(_normalize_row, axis=1)

    df.dropna(subset=["טלפון", "אימייל"], how="all", inplace=True)
    df.drop_duplicates(subset=["עיר", "שם", "טלפון", "אימייל"], inplace=True)

    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"✅ CSV saved: {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize contacts CSV")
    parser.add_argument("input_csv", nargs="?", default="all_contacts.csv")
    parser.add_argument(
        "output_csv", nargs="?", default="extracted_contacts_fillter.csv"
    )
    args = parser.parse_args()
    main(args.input_csv, args.output_csv)
