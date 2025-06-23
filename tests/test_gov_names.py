import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import jobs
import name_pull
import gov_names


def test_dataset_transliteration(monkeypatch, tmp_path):
    cache_file = tmp_path / "cache.json"
    monkeypatch.setattr(jobs, "CACHE_FILE", cache_file)
    monkeypatch.setattr(jobs, "_translation_cache", None, raising=False)
    monkeypatch.setattr(jobs, "_gov_names", None, raising=False)
    monkeypatch.setattr(name_pull, "_translation_cache", None, raising=False)
    monkeypatch.setattr(name_pull, "_gov_names", None, raising=False)

    monkeypatch.setattr(gov_names, "load_names", lambda: {"Dan": "דן"})
    monkeypatch.setattr(jobs, "load_names", lambda: {"Dan": "דן"})

    calls = []
    monkeypatch.setattr(jobs, "guess_hebrew_name", lambda n: calls.append(n) or None)
    monkeypatch.setattr(
        name_pull, "guess_hebrew_name", lambda n: calls.append(n) or None
    )

    result = jobs.transliterate_to_hebrew("Dan")
    assert result == "דן"
    assert calls == []
    assert json.loads(cache_file.read_text(encoding="utf-8")) == {"Dan": "דן"}

    # name_pull should delegate to jobs and also avoid calling ChatGPT
    result2 = name_pull.transliterate_to_hebrew("Dan")
    assert result2 == "דן"
    assert calls == []
