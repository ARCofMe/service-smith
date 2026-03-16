"""Import report writers for ServiceSmith."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Any


def write_report(report_dir: str | Path, stem: str, rows: Iterable[Any]) -> tuple[Path, Path]:
    target_dir = Path(report_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = target_dir / f"{stem}_{timestamp}.json"
    csv_path = target_dir / f"{stem}_{timestamp}.csv"

    normalized = [_normalize(item) for item in rows]
    json_path.write_text(json.dumps(normalized, indent=2), encoding="utf-8")
    fieldnames = sorted({key for row in normalized for key in row.keys()})
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in normalized:
            writer.writerow(row)
    return json_path, csv_path


def _normalize(item: Any) -> dict[str, Any]:
    if is_dataclass(item):
        data = asdict(item)
    elif isinstance(item, dict):
        data = dict(item)
    else:
        data = {"value": str(item)}

    for key, value in list(data.items()):
        if isinstance(value, list):
            data[key] = "; ".join(str(entry) for entry in value)
    return data
