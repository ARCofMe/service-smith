"""Spreadsheet parsing and field mapping."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from service_smith.formats import DEFAULT_ADAPTER


def load_rows(spreadsheet_path: str | Path, field_map: dict[str, str] | None = None) -> list[dict[str, str]]:
    """Load rows from a CSV or spreadsheet-like export into canonical field names."""
    path = Path(spreadsheet_path)
    mapped_fields = field_map or DEFAULT_ADAPTER.field_map

    if path.suffix.lower() == ".csv":
        with path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            return [
                _map_row(row, mapped_fields, row_number=index)
                for index, row in enumerate(reader, start=2)
            ]

    if path.suffix.lower() in {".xlsx", ".xlsm"}:
        try:
            from openpyxl import load_workbook
        except Exception as exc:
            raise RuntimeError("openpyxl is required to import Excel workbooks.") from exc

        workbook = load_workbook(path, read_only=True, data_only=True)
        sheet = workbook.active
        header_row = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True), None)
        if not header_row:
            return []
        headers = [str(cell).strip() if cell is not None else "" for cell in header_row]
        rows: list[dict[str, str]] = []
        for index, values in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            raw = {headers[idx]: _stringify(value) for idx, value in enumerate(values) if idx < len(headers)}
            rows.append(_map_row(raw, mapped_fields, row_number=index))
        return rows

    raise ValueError(f"Unsupported spreadsheet format: {path.suffix}")


def _map_row(row: dict[str, str], field_map: dict[str, str], row_number: int) -> dict[str, str]:
    mapped = {
        canonical_name: _stringify(row.get(source_name))
        for canonical_name, source_name in field_map.items()
    }
    mapped["source_row_number"] = str(row_number)
    return mapped


def _stringify(value: object) -> str:
    return "" if value is None else str(value).strip()


def preview_rows(rows: Iterable[dict[str, str]], limit: int = 5) -> list[dict[str, str]]:
    return list(rows)[:limit]


def validate_rows(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    seen_external_ids: set[str] = set()
    seen_keys: set[tuple[str, str, str]] = set()

    for row in rows:
        row_number = row.get("source_row_number", "?")
        if not row.get("customer_name"):
            issues.append({"row": row_number, "level": "error", "message": "Missing customer_name"})
        if not row.get("description") and not row.get("subject"):
            issues.append({"row": row_number, "level": "error", "message": "Missing subject/description"})
        if not row.get("address"):
            issues.append({"row": row_number, "level": "warning", "message": "Missing address"})
        if not row.get("city") or not row.get("state"):
            issues.append({"row": row_number, "level": "warning", "message": "Missing city/state"})

        external_id = row.get("external_id", "")
        if external_id:
            if external_id in seen_external_ids:
                issues.append({"row": row_number, "level": "warning", "message": f"Duplicate external_id {external_id}"})
            seen_external_ids.add(external_id)

        key = (
            row.get("customer_name", "").casefold(),
            row.get("address", "").casefold(),
            (row.get("description") or row.get("subject") or "").casefold(),
        )
        if any(key) and key in seen_keys:
            issues.append({"row": row_number, "level": "warning", "message": "Potential duplicate row in import batch"})
        seen_keys.add(key)

    return issues
