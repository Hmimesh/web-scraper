"""Simple English to Hebrew transliteration helpers."""

from __future__ import annotations


# Map of common digraphs and vowel patterns to their Hebrew equivalents
_DIGRAPH_MAP: dict[str, str] = {
    "sch": "ש",
    "sh": "ש",
    "ch": "ח",
    "ph": "פ",
    "th": "ת",
    "tz": "צ",
    "oo": "ו",
    "ee": "י",
    "ai": "יי",
    "ei": "יי",
}

# Mapping of single letters. Vowels default to empty string as they are often
# implicit. The mappings are intentionally simple and only cover the common
# cases needed for names in tests.
_LETTER_MAP: dict[str, str] = {
    "a": "א",
    "b": "ב",
    "c": "ק",
    "d": "ד",
    "e": "",
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

_FINAL_MAP = {
    "מ": "ם",
    "נ": "ן",
    "פ": "ף",
    "צ": "ץ",
    "כ": "ך",
}


def basic_transliterate(text: str) -> str:
    """Very small heuristic transliteration from English to Hebrew."""
    lower = text.lower()
    result: list[str] = []
    i = 0
    while i < len(lower):
        matched = False
        for dg, heb in sorted(_DIGRAPH_MAP.items(), key=lambda item: -len(item[0])):
            if lower.startswith(dg, i):
                result.append(heb)
                i += len(dg)
                matched = True
                break
        if matched:
            continue
        ch = lower[i]
        result.append(_LETTER_MAP.get(ch, ""))
        i += 1

    if result:
        last = result[-1]
        if last in _FINAL_MAP:
            result[-1] = _FINAL_MAP[last]
    return "".join(result)
