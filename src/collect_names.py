from __future__ import annotations
import json
from pathlib import Path


def collect_names(base_dir: Path | str | None = None) -> None:
    """Parse scraper_io log and collect unique names into name_pull.txt."""
    if base_dir is None:
        base_dir = Path(__file__).resolve().parents[1]
    else:
        base_dir = Path(base_dir)

    logs_dir = base_dir / "logs"
    log_file = logs_dir / "scraper_io.jsonl"
    output_file = logs_dir / "name_pull.txt"

    names = set()
    if log_file.exists():
        with log_file.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                name = data.get("Name") or data.get("שם")
                if name:
                    names.add(str(name).strip())

    logs_dir.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        for name in sorted(names):
            f.write(f"{name}\n")
