"""CLI orchestration for ServiceSmith."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from service_smith.bluefolder_client import ServiceSmithBlueFolderClient
from service_smith.formats import (
    ADAPTERS,
    adapter_headers,
    get_adapter,
    list_adapters,
    load_field_map_override,
    merge_field_maps,
)
from service_smith.importer import load_rows, preview_rows, select_rows, validate_rows
from service_smith.profiles import resolve_profile
from service_smith.utils.config import load_settings
from service_smith.utils.logging import configure_logging, get_logger
from service_smith.utils.reporting import summarize_rows, write_report, write_summary_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import service requests from a spreadsheet into BlueFolder.")
    parser.add_argument("spreadsheet", type=Path, nargs="?", help="Path to the source spreadsheet.")
    parser.add_argument("--dry-run", action="store_true", default=None, help="Parse and preview rows without creating anything.")
    parser.add_argument("--validate-only", action="store_true", default=None, help="Validate rows and write a validation report without planning or importing.")
    parser.add_argument("--payload-preview", action="store_true", default=None, help="In dry-run mode, write the exact BlueFolder payload previews instead of action summaries.")
    parser.add_argument("--report-dir", type=Path, default=None, help="Directory for JSON/CSV import reports.")
    parser.add_argument("--fail-fast", action="store_true", default=None, help="Stop on the first import failure.")
    parser.add_argument("--format", dest="spreadsheet_format", default=None, choices=sorted(ADAPTERS), help="Named spreadsheet adapter.")
    parser.add_argument("--field-map", type=Path, default=None, help="Optional JSON override mapping canonical names to source headers.")
    parser.add_argument("--profile", default=None, help="Named import profile from a JSON profile file.")
    parser.add_argument("--profile-file", type=Path, default=None, help="Path to a JSON file containing named import profiles.")
    parser.add_argument("--duplicate-mode", choices=["skip", "error", "allow"], default=None, help="How to handle rows whose external_id already exists in BlueFolder.")
    parser.add_argument("--row-start", type=int, default=None, help="First source spreadsheet row number to include.")
    parser.add_argument("--row-end", type=int, default=None, help="Last source spreadsheet row number to include.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of rows to process after filtering.")
    parser.add_argument("--list-formats", action="store_true", help="List supported spreadsheet adapters and exit.")
    parser.add_argument("--print-headers", action="store_true", help="Print the expected spreadsheet headers for the selected adapter and exit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    raw_argv = argv if argv is not None else sys.argv[1:]

    settings = load_settings()
    configure_logging(settings)
    logger = get_logger(__name__)

    if args.list_formats:
        for adapter in list_adapters():
            logger.info("%s: %s", adapter.name, adapter.description)
        return 0

    profile = {}
    profile_file = args.profile_file or (Path(settings.service_smith_profile_file) if settings.service_smith_profile_file else None)
    if args.profile:
        if profile_file is None:
            parser.error("--profile requires --profile-file or SERVICE_SMITH_PROFILE_FILE")
        profile = resolve_profile(args.profile, profile_file)
        logger.info("Loaded profile '%s' from %s", args.profile, profile_file)

    defaults = {
        "dry_run": False,
        "validate_only": False,
        "payload_preview": False,
        "fail_fast": False,
        "spreadsheet_format": "default",
        "duplicate_mode": "skip",
        "row_start": None,
        "row_end": None,
        "limit": None,
        "report_dir": None,
        "field_map": None,
    }
    option_flags = {
        "dry_run": "--dry-run",
        "validate_only": "--validate-only",
        "payload_preview": "--payload-preview",
        "fail_fast": "--fail-fast",
        "spreadsheet_format": "--format",
        "field_map": "--field-map",
        "duplicate_mode": "--duplicate-mode",
        "row_start": "--row-start",
        "row_end": "--row-end",
        "limit": "--limit",
        "report_dir": "--report-dir",
    }
    effective = dict(defaults)
    for key, value in profile.items():
        if key in {"report_dir", "field_map"} and value is not None:
            effective[key] = Path(value)
        else:
            effective[key] = value
    for key, flag in option_flags.items():
        if flag in raw_argv and getattr(args, key) is not None:
            effective[key] = getattr(args, key)

    args.dry_run = effective["dry_run"]
    args.validate_only = effective["validate_only"]
    args.payload_preview = effective["payload_preview"]
    args.fail_fast = effective["fail_fast"]
    args.spreadsheet_format = effective["spreadsheet_format"]
    args.field_map = effective["field_map"]
    args.duplicate_mode = effective["duplicate_mode"]
    args.row_start = effective["row_start"]
    args.row_end = effective["row_end"]
    args.limit = effective["limit"]
    args.report_dir = effective["report_dir"]

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
    rows = select_rows(rows, row_start=args.row_start, row_end=args.row_end, limit=args.limit)
    logger.info("Loaded %d row(s) from %s using adapter '%s'", len(rows), args.spreadsheet, adapter.name)
    issues = validate_rows(rows)
    for issue in issues:
        log_fn = logger.error if issue["level"] == "error" else logger.warning
        log_fn("Row %s: %s", issue["row"], issue["message"])

    report_dir = args.report_dir or Path(settings.service_smith_report_dir)
    if args.validate_only:
        json_path, csv_path = write_report(report_dir, "validation", issues)
        summary = summarize_rows(issues, status_field="message", issue_level_field="level")
        md_path = write_summary_report(
            report_dir,
            "validation_summary",
            issues,
            title="ServiceSmith Validation Summary",
            status_field="message",
            issue_level_field="level",
        )
        logger.info("Validation summary: %s", summary)
        logger.info("Validation report written to %s, %s, and %s", json_path, csv_path, md_path)
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
        summary = summarize_rows(plans, status_field="service_request_action", issue_level_field="notes")
        md_path = write_summary_report(
            report_dir,
            f"{stem}_summary",
            plans,
            title="ServiceSmith Dry Run Summary",
            status_field="service_request_action",
            issue_level_field="notes",
        )
        logger.info("Dry-run summary: %s", summary)
        logger.info("Dry-run report written to %s, %s, and %s", json_path, csv_path, md_path)
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
    summary = summarize_rows(results)
    md_path = write_summary_report(
        report_dir,
        "import_results_summary",
        results,
        title="ServiceSmith Import Summary",
    )
    logger.info("Import summary: %s", summary)
    logger.info("Import report written to %s, %s, and %s", json_path, csv_path, md_path)
    return 0
