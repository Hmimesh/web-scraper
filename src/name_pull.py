# Utility for collecting unique names from scraping logs and transliterating
# them to Hebrew if they are written in English letters.

from __future__ import annotations
import json
import os
import re
from pathlib import Path

import jobs
from jobs import Contacts
from gov_names import load_names
from chatgpt_name import guess_hebrew_name

CACHE_FILE = Path(__file__).resolve().parents[1] / "data" / "translation_cache.json"
_translation_cache: dict[str, str] | None = None
_gov_names: dict[str, str] | None = None


def _load_cache() -> dict[str, str]:
    global _translation_cache
    if _translation_cache is None:
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, encoding="utf-8") as f:
                    _translation_cache = json.load(f)
            except Exception:
                _translation_cache = {}
        else:
            _translation_cache = {}
    return _translation_cache


def _save_cache(cache: dict[str, str]) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _load_gov_names() -> dict[str, str]:
    global _gov_names
    if _gov_names is None:
        try:
            _gov_names = {k.lower(): v for k, v in load_names().items()}
        except Exception:
            _gov_names = {}
    return _gov_names


def transliterate_to_hebrew(name: str) -> str | None:
    """Return a Hebrew version of ``name`` using the shared ``jobs`` helper."""

    # ``jobs.transliterate_to_hebrew`` already handles caching and the official
    # government name dataset. We delegate to it so the logic remains in one
    # place. Tests expect that ``guess_hebrew_name`` from this module is used
    # when patched, so temporarily swap it in for the call.
    original = jobs.guess_hebrew_name
    jobs.guess_hebrew_name = guess_hebrew_name
    try:
        return jobs.transliterate_to_hebrew(name)
    finally:
        jobs.guess_hebrew_name = original


def extract_name_from_email(email: str) -> str | None:
    """Guess a personal name from an email address."""
    local = email.split("@", 1)[0]
    parts = re.split(r"[._-]+", local)
    parts = [p for p in parts if p.isalpha()]
    if not parts:
        return None
    if len(parts) == 1 and len(parts[0]) > 3 and parts[0][-1].isalpha():
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
            names.add(name)

    with open(output_file, "w", encoding="utf-8") as f:
        for nm in sorted(names):
            f.write(nm + "\n")

    return names


if __name__ == "__main__":
    collect_names()
