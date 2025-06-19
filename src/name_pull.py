# Utility for collecting unique names from scraping logs and transliterating
# them to Hebrew if they are written in English letters.

from __future__ import annotations
import json
import os
import re
from pathlib import Path

from jobs import Contacts, ISRAELI_NAME_DB
from chatgpt_name import guess_hebrew_name
from difflib import get_close_matches


LATIN_TO_HEBREW = {
    "a": "א",
    "b": "ב",
    "c": "ק",
    "d": "ד",
    "e": "י",
    "f": "פ",
    "g": "ג",
    "h": "ה",
    "i": "י",
    "j": "ג",
    "k": "ק",
    "l": "ל",
    "m": "מ",
    "n": "נ",
    "o": "ו",
    "p": "פ",
    "q": "ק",
    "r": "ר",
    "s": "ס",
    "t": "ט",
    "u": "ו",
    "v": "ו",
    "w": "ו",
    "x": "קס",
    "y": "י",
    "z": "ז",
}

# Final forms for certain Hebrew letters when they appear at the end of a word
FINAL_FORMS = {
    "m": "ם",
    "n": "ן",
    "p": "ף",
    "f": "ף",
    "k": "ך",
    "c": "ך",
    "t": "ת",  # no special final form but kept for completeness
}


def transliterate_to_hebrew(name: str) -> str:
    """Transliterate a simple English name into Hebrew letters.

    The resulting name is cross-checked against a list of Hebrew names fetched
    from data.gov.il to catch common transliteration errors.
    """
    result: list[str] = []
    clean = name.strip().lower()

    for i, ch in enumerate(clean):
        if ch == " ":
            result.append(" ")
            continue

        # Skip a short vowel between two consonants
        if (
            ch in {"e", "a"}
            and 0 < i < len(clean) - 1
            and clean[i - 1] not in "aeiou"
            and clean[i + 1] not in "aeiou"
        ):
            continue

        heb = LATIN_TO_HEBREW.get(ch)
        if not heb:
            continue

        # Use final form if this is the last letter of the word
        if i == len(clean) - 1 and ch in FINAL_FORMS:
            heb = FINAL_FORMS[ch]

        result.append(heb)

    hebrew = "".join(result)

    if hebrew in ISRAELI_NAME_DB:
        return hebrew

    match = get_close_matches(hebrew, ISRAELI_NAME_DB, n=1, cutoff=0.7)
    if match:
        return match[0]

    return hebrew


def extract_name_from_email(email: str) -> str | None:
    """Guess a personal name from an email address."""
    local = email.split("@", 1)[0]
    parts = re.split(r"[._-]+", local)
    parts = [p for p in parts if p.isalpha()]
    if not parts:
        return None
    if len(parts) == 1 and len(parts[0]) > 2 and len(parts[0][-1]) == 1:
        # Drop single trailing letter (likely a last-name initial)
        parts[0] = parts[0][:-1]
    guess = " ".join(p.capitalize() for p in parts)
    return guess if Contacts.is_valid_name(guess) else None


def collect_names(
    log_file: str = "logs/scraper_io.jsonl",
    output_file: str = "logs/name_pull.txt",
) -> set[str]:
    """Collect names from the JSONL log file and write them to a text file."""
    names: set[str] = set()

    if os.path.exists(output_file):
        with open(output_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    names.add(line)

    log_path = Path(log_file)
    if not log_path.exists():
        return names

    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            name = data.get("שם") or data.get("Name")
            if not name or name.startswith("לא נמצא"):
                email = data.get("מייל") or data.get("Email")
                if email:
                    name = extract_name_from_email(email)
            if not name:
                name = guess_hebrew_name(data.get("raw_text", ""))
                if not name:
                    continue
            if not re.search(r"[א-ת]", name):
                heb = transliterate_to_hebrew(name)
                if heb:
                    name = heb
                else:
                    gpt_guess = guess_hebrew_name(name)
                    if gpt_guess:
                        name = gpt_guess
            names.add(name)

    with open(output_file, "w", encoding="utf-8") as f:
        for nm in sorted(names):
            f.write(nm + "\n")

    return names


if __name__ == "__main__":
    collect_names()
