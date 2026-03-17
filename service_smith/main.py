"""CLI orchestration for ServiceSmith."""

from __future__ import annotations

import argparse
from pathlib import Path

from service_smith.bluefolder_client import ServiceSmithBlueFolderClient
from service_smith.formats import (
    ADAPTERS,
    adapter_headers,
    get_adapter,
    list_adapters,
    load_field_map_override,
    merge_field_maps,
)
from service_smith.importer import load_rows, preview_rows, validate_rows
from service_smith.utils.config import load_settings
from service_smith.utils.logging import configure_logging, get_logger
from service_smith.utils.reporting import summarize_rows, write_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import service requests from a spreadsheet into BlueFolder.")
    parser.add_argument("spreadsheet", type=Path, nargs="?", help="Path to the source spreadsheet.")
    parser.add_argument("--dry-run", action="store_true", help="Parse and preview rows without creating anything.")
    parser.add_argument("--validate-only", action="store_true", help="Validate rows and write a validation report without planning or importing.")
    parser.add_argument("--payload-preview", action="store_true", help="In dry-run mode, write the exact BlueFolder payload previews instead of action summaries.")
    parser.add_argument("--report-dir", type=Path, default=None, help="Directory for JSON/CSV import reports.")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on the first import failure.")
    parser.add_argument("--format", dest="spreadsheet_format", default="default", choices=sorted(ADAPTERS), help="Named spreadsheet adapter.")
    parser.add_argument("--field-map", type=Path, default=None, help="Optional JSON override mapping canonical names to source headers.")
    parser.add_argument("--duplicate-mode", choices=["skip", "error", "allow"], default="skip", help="How to handle rows whose external_id already exists in BlueFolder.")
    parser.add_argument("--list-formats", action="store_true", help="List supported spreadsheet adapters and exit.")
    parser.add_argument("--print-headers", action="store_true", help="Print the expected spreadsheet headers for the selected adapter and exit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = load_settings()
    configure_logging(settings)
    logger = get_logger(__name__)

    if args.list_formats:
        for adapter in list_adapters():
            logger.info("%s: %s", adapter.name, adapter.description)
        return 0

    adapter = get_adapter(args.spreadsheet_format)

    if args.print_headers:
        for header in adapter_headers(adapter.name):
            print(header)
        return 0

    if args.spreadsheet is None:
        parser.error("the following arguments are required: spreadsheet")

    field_map = dict(adapter.field_map)
    if args.field_map:
        field_map = merge_field_maps(field_map, load_field_map_override(args.field_map))
        logger.info("Applied field-map override from %s", args.field_map)

    rows = load_rows(args.spreadsheet, field_map=field_map)
    logger.info("Loaded %d row(s) from %s using adapter '%s'", len(rows), args.spreadsheet, adapter.name)
    issues = validate_rows(rows)
    for issue in issues:
        log_fn = logger.error if issue["level"] == "error" else logger.warning
        log_fn("Row %s: %s", issue["row"], issue["message"])

    report_dir = args.report_dir or Path(settings.service_smith_report_dir)
    if args.validate_only:
        json_path, csv_path = write_report(report_dir, "validation", issues)
        summary = summarize_rows(issues, status_field="message", issue_level_field="level")
        logger.info("Validation summary: %s", summary)
        logger.info("Validation report written to %s and %s", json_path, csv_path)
        return 2 if any(issue["level"] == "error" for issue in issues) else 0

    if any(issue["level"] == "error" for issue in issues):
        logger.error("Validation failed; fix the spreadsheet before importing.")
        return 2

    client = ServiceSmithBlueFolderClient(settings)

    if args.dry_run:
        plans = (
            [client.preview_payloads(row, duplicate_mode=args.duplicate_mode) for row in rows]
            if args.payload_preview
            else [client.plan_import(row, duplicate_mode=args.duplicate_mode) for row in rows]
        )
        for idx, row in enumerate(preview_rows(rows), start=1):
            logger.info("Preview row %d: %s", idx, row)
        stem = "payload_preview" if args.payload_preview else "dry_run"
        json_path, csv_path = write_report(report_dir, stem, plans)
        logger.info("Dry-run summary: %s", summarize_rows(plans, status_field="service_request_action", issue_level_field="notes"))
        logger.info("Dry-run report written to %s and %s", json_path, csv_path)
        return 0

    imported = 0
    results = []
    for idx, row in enumerate(rows, start=1):
        result = client.ensure_customer_and_import(row, duplicate_mode=args.duplicate_mode)
        results.append(result)
        imported += 1
        logger.info(
            "Imported row %s customer_id=%s service_request_id=%s created_customer=%s status=%s",
            result.row_number or idx,
            result.customer_id,
            result.service_request_id,
            result.created_customer,
            result.status,
        )
        if args.fail_fast and result.status != "imported":
            logger.error("Stopping early because --fail-fast was requested.")
            break

    logger.info("Finished importing %d row(s).", imported)
    json_path, csv_path = write_report(report_dir, "import_results", results)
    logger.info("Import summary: %s", summarize_rows(results))
    logger.info("Import report written to %s and %s", json_path, csv_path)
    return 0
