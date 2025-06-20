import sys
from pathlib import Path
import types

# ensure src directory on path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

# provide a dummy playwright module so database_func can be imported without
# installing the real dependency
fake_sync = types.ModuleType("sync_api")
fake_sync.sync_playwright = lambda: None
fake_playwright = types.ModuleType("playwright")
fake_playwright.sync_api = fake_sync
sys.modules.setdefault("playwright", fake_playwright)
sys.modules.setdefault("playwright.sync_api", fake_sync)

# minimal pandas stub for pd.isna
fake_pd = types.SimpleNamespace(isna=lambda x: x != x or x is None)
sys.modules.setdefault("pandas", fake_pd)

# minimal nameparser stub
fake_nameparser = types.ModuleType("nameparser")
fake_nameparser.HumanName = lambda x: x
sys.modules.setdefault("nameparser", fake_nameparser)

import database_func


def test_process_city_string_profile(monkeypatch):
    profiles = {"example.com": "deprecated"}
    monkeypatch.setattr(database_func, "site_profiles", profiles)
    row = {"עיר": "Example", "קישור": "http://example.com"}

    city, data = database_func.process_city(row, {})

    assert city == "Example"
    assert data == {}
    assert database_func.site_profiles["example.com"]["skip"] is True
