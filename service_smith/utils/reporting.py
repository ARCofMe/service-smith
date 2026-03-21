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


def write_summary_report(
    report_dir: str | Path,
    stem: str,
    rows: Iterable[Any],
    *,
    title: str,
    status_field: str = "status",
    issue_level_field: str = "level",
) -> Path:
    target_dir = Path(report_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = target_dir / f"{stem}_{timestamp}.md"

    normalized = [_normalize(item) for item in rows]
    summary = summarize_rows(normalized, status_field=status_field, issue_level_field=issue_level_field)

    lines = [f"# {title}", "", "## Summary", ""]
    for key in sorted(summary):
        lines.append(f"- {key}: {summary[key]}")

    if normalized:
        lines.extend(["", "## Sample Rows", ""])
        for row in normalized[:10]:
            row_bits = [f"{key}={value}" for key, value in sorted(row.items()) if value not in ("", None)]
            lines.append(f"- {'; '.join(row_bits)}")

    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_path


def summarize_rows(rows: Iterable[Any], *, status_field: str = "status", issue_level_field: str = "level") -> dict[str, int]:
    summary: dict[str, int] = {"total": 0}
    for item in rows:
        normalized = _normalize(item)
        summary["total"] += 1
        status = normalized.get(status_field)
        if status:
            key = f"{status_field}:{status}"
            summary[key] = summary.get(key, 0) + 1
        level = normalized.get(issue_level_field)
        if level:
            key = f"{issue_level_field}:{level}"
            summary[key] = summary.get(key, 0) + 1
    return summary


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
