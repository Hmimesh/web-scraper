import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

dummy_pandas = types.ModuleType("pandas")
dummy_pandas.isna = lambda x: x is None
sys.modules.setdefault("pandas", dummy_pandas)

dummy_nameparser = types.ModuleType("nameparser")
dummy_nameparser.HumanName = lambda x: x
sys.modules.setdefault("nameparser", dummy_nameparser)

dummy_sync_api = types.ModuleType("playwright.sync_api")
dummy_sync_api.sync_playwright = lambda *a, **k: None
dummy_playwright = types.ModuleType("playwright")
dummy_playwright.sync_api = dummy_sync_api
sys.modules.setdefault("playwright", dummy_playwright)
sys.modules.setdefault("playwright.sync_api", dummy_sync_api)

import database_func


def test_process_city_skips_nan_url(monkeypatch):
    row = {"עיר": "TestCity", "קישור": " NaN "}

    def fake_sync_playwright(*args, **kwargs):
        raise AssertionError("sync_playwright should not be called")

    monkeypatch.setattr(database_func, "sync_playwright", fake_sync_playwright)

    city, data = database_func.process_city(row, {})
    assert city == "TestCity"
    assert data == {}
