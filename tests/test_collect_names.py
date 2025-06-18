import sys
from pathlib import Path
import json

sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))

from collect_names import collect_names


def test_collect_names_creates_file(tmp_path):
    logs_dir = tmp_path / 'logs'
    logs_dir.mkdir()
    log_file = logs_dir / 'scraper_io.jsonl'
    sample = {"Name": "Example Person"}
    log_file.write_text(json.dumps(sample, ensure_ascii=False), encoding='utf-8')

    collect_names(base_dir=tmp_path)

    output_file = logs_dir / 'name_pull.txt'
    assert output_file.exists()
    assert "Example Person" in output_file.read_text(encoding='utf-8')

