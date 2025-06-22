import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import jobs


def test_transliteration_uses_cache(tmp_path, monkeypatch):
    cache_file = tmp_path / "cache.json"
    monkeypatch.setattr(jobs, "CACHE_FILE", cache_file)
    # reset any existing cache state
    jobs._translation_cache = None

    calls = []

    def fake_guess(name: str) -> str:
        calls.append(name)
        return f"HB-{name}"

    monkeypatch.setattr(jobs, "guess_hebrew_name", fake_guess)

    # first call populates cache
    assert jobs.transliterate_to_hebrew("Dan") == "HB-Dan"
    assert calls == ["Dan"]
    assert cache_file.exists()

    # second call should use cache and not call guess_hebrew_name again
    assert jobs.transliterate_to_hebrew("Dan") == "HB-Dan"
    assert calls == ["Dan"]

    # simulate new session by clearing in-memory cache
    jobs._translation_cache = None
    assert jobs.transliterate_to_hebrew("Dan") == "HB-Dan"
    # still no new calls
    assert calls == ["Dan"]
