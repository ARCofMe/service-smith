"""CLI orchestration for ServiceSmith."""

from __future__ import annotations

import argparse
from pathlib import Path

from service_smith.bluefolder_client import ServiceSmithBlueFolderClient
from service_smith.importer import load_rows, preview_rows, validate_rows
from service_smith.utils.config import load_settings
from service_smith.utils.logging import configure_logging, get_logger
from service_smith.utils.reporting import write_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import service requests from a spreadsheet into BlueFolder.")
    parser.add_argument("spreadsheet", type=Path, help="Path to the source spreadsheet.")
    parser.add_argument("--dry-run", action="store_true", help="Parse and preview rows without creating anything.")
    parser.add_argument("--report-dir", type=Path, default=None, help="Directory for JSON/CSV import reports.")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on the first import failure.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = load_settings()
    configure_logging(settings)
    logger = get_logger(__name__)

    rows = load_rows(args.spreadsheet)
    logger.info("Loaded %d row(s) from %s", len(rows), args.spreadsheet)
    issues = validate_rows(rows)
    for issue in issues:
        log_fn = logger.error if issue["level"] == "error" else logger.warning
        log_fn("Row %s: %s", issue["row"], issue["message"])
    if any(issue["level"] == "error" for issue in issues):
        logger.error("Validation failed; fix the spreadsheet before importing.")
        return 2

    report_dir = args.report_dir or Path(settings.service_smith_report_dir)
    client = ServiceSmithBlueFolderClient()

    if args.dry_run:
        plans = [client.plan_import(row) for row in rows]
        for idx, row in enumerate(preview_rows(rows), start=1):
            logger.info("Preview row %d: %s", idx, row)
        json_path, csv_path = write_report(report_dir, "dry_run", plans)
        logger.info("Dry-run report written to %s and %s", json_path, csv_path)
        return 0

    imported = 0
    results = []
    for idx, row in enumerate(rows, start=1):
        result = client.ensure_customer_and_import(row)
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
    logger.info("Import report written to %s and %s", json_path, csv_path)
    return 0
