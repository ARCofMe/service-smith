from pathlib import Path

from service_smith import main as cli
from service_smith.utils.config import Settings


class DummyClient:
    def __init__(self, settings):
        self.settings = settings

    def plan_import(self, row, duplicate_mode="skip"):
        return {
            "row_number": row.get("source_row_number"),
            "service_request_action": "create_service_request",
            "duplicate_mode": duplicate_mode,
        }

    def preview_payloads(self, row, duplicate_mode="skip"):
        return {
            "row_number": row.get("source_row_number"),
            "service_request_payload": {"externalId": row.get("external_id")},
            "duplicate_mode": duplicate_mode,
        }

    def ensure_customer_and_import(self, row, duplicate_mode="skip"):
        return {
            "row_number": row.get("source_row_number"),
            "status": "imported",
            "service_request_id": "555",
            "customer_id": "123",
            "created_customer": False,
        }


def _settings() -> Settings:
    return Settings(
        bluefolder_api_key="key",
        bluefolder_account_name="acct",
        bluefolder_base_url=None,
        bluefolder_host_header=None,
        bluefolder_verify_ssl=False,
        service_smith_log_level="INFO",
        service_smith_default_sheet=None,
        service_smith_report_dir="reports",
        service_smith_profile_file=None,
        service_smith_default_customer_type="Residential",
        service_smith_default_sr_status="New",
        service_smith_default_sr_priority=None,
        service_smith_default_contact_title=None,
    )


def test_cli_validate_only_writes_validation_report(tmp_path, monkeypatch):
    csv_path = tmp_path / "jobs.csv"
    csv_path.write_text(
        "Customer Name,Subject,Address,City,State,Zip\n"
        "Acme,No cool,123 Main St,Portland,ME,04101\n",
        encoding="utf-8",
    )
    written = {}

    monkeypatch.setattr(cli, "load_settings", lambda: _settings())
    monkeypatch.setattr(cli, "write_report", lambda report_dir, stem, rows: _capture_report(written, stem, rows, tmp_path))

    exit_code = cli.main([str(csv_path), "--validate-only", "--report-dir", str(tmp_path)])

    assert exit_code == 0
    assert written["stem"] == "validation"
    assert written["rows"] == []


def test_cli_dry_run_uses_field_map_override(tmp_path, monkeypatch):
    csv_path = tmp_path / "jobs.csv"
    csv_path.write_text(
        "Client,Issue Summary,Service Address,City,State,Zip\n"
        "Acme,No cool,123 Main St,Portland,ME,04101\n",
        encoding="utf-8",
    )
    field_map = tmp_path / "map.json"
    field_map.write_text(
        '{"customer_name":"Client","subject":"Issue Summary","address":"Service Address"}',
        encoding="utf-8",
    )
    written = {}

    monkeypatch.setattr(cli, "load_settings", lambda: _settings())
    monkeypatch.setattr(cli, "ServiceSmithBlueFolderClient", DummyClient)
    monkeypatch.setattr(cli, "write_report", lambda report_dir, stem, rows: _capture_report(written, stem, rows, tmp_path))

    exit_code = cli.main(
        [
            str(csv_path),
            "--dry-run",
            "--field-map",
            str(field_map),
            "--report-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert written["stem"] == "dry_run"
    assert written["rows"][0]["row_number"] == "2"


def test_cli_payload_preview_passes_duplicate_mode(tmp_path, monkeypatch):
    csv_path = tmp_path / "jobs.csv"
    csv_path.write_text(
        "Customer Name,Subject,External ID,Address,City,State,Zip\n"
        "Acme,No cool,WO-1,123 Main St,Portland,ME,04101\n",
        encoding="utf-8",
    )
    written = {}

    monkeypatch.setattr(cli, "load_settings", lambda: _settings())
    monkeypatch.setattr(cli, "ServiceSmithBlueFolderClient", DummyClient)
    monkeypatch.setattr(cli, "write_report", lambda report_dir, stem, rows: _capture_report(written, stem, rows, tmp_path))

    exit_code = cli.main(
        [
            str(csv_path),
            "--dry-run",
            "--payload-preview",
            "--duplicate-mode",
            "error",
            "--report-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert written["stem"] == "payload_preview"
    assert written["rows"][0]["duplicate_mode"] == "error"
    assert written["rows"][0]["service_request_payload"]["externalId"] == "WO-1"


def test_cli_profile_applies_defaults(tmp_path, monkeypatch):
    csv_path = tmp_path / "jobs.csv"
    csv_path.write_text(
        "Client,Issue Summary,External ID,Service Address,City,State,Zip\n"
        "Acme,No cool,WO-1,123 Main St,Portland,ME,04101\n",
        encoding="utf-8",
    )
    field_map = tmp_path / "map.json"
    field_map.write_text(
        '{"customer_name":"Client","subject":"Issue Summary","address":"Service Address"}',
        encoding="utf-8",
    )
    profiles = tmp_path / "profiles.json"
    profiles.write_text(
        (
            '{"vendor_review":{"spreadsheet_format":"default","field_map":"%s",'
            '"dry_run":true,"payload_preview":true,"duplicate_mode":"error"}}'
        )
        % field_map.as_posix(),
        encoding="utf-8",
    )
    written = {}
    settings = _settings()
    settings.service_smith_profile_file = str(profiles)

    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    monkeypatch.setattr(cli, "ServiceSmithBlueFolderClient", DummyClient)
    monkeypatch.setattr(cli, "write_report", lambda report_dir, stem, rows: _capture_report(written, stem, rows, tmp_path))

    exit_code = cli.main([str(csv_path), "--profile", "vendor_review", "--report-dir", str(tmp_path)])

    assert exit_code == 0
    assert written["stem"] == "payload_preview"
    assert written["rows"][0]["duplicate_mode"] == "error"


def test_cli_explicit_args_override_profile(tmp_path, monkeypatch):
    csv_path = tmp_path / "jobs.csv"
    csv_path.write_text(
        "Customer Name,Subject,External ID,Address,City,State,Zip\n"
        "Acme,No cool,WO-1,123 Main St,Portland,ME,04101\n",
        encoding="utf-8",
    )
    profiles = tmp_path / "profiles.json"
    profiles.write_text(
        '{"strict_review":{"dry_run":true,"payload_preview":true,"duplicate_mode":"error"}}',
        encoding="utf-8",
    )
    written = {}
    settings = _settings()
    settings.service_smith_profile_file = str(profiles)

    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    monkeypatch.setattr(cli, "ServiceSmithBlueFolderClient", DummyClient)
    monkeypatch.setattr(cli, "write_report", lambda report_dir, stem, rows: _capture_report(written, stem, rows, tmp_path))

    exit_code = cli.main(
        [
            str(csv_path),
            "--profile",
            "strict_review",
            "--duplicate-mode",
            "allow",
            "--report-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert written["stem"] == "payload_preview"
    assert written["rows"][0]["duplicate_mode"] == "allow"


def _capture_report(target: dict, stem: str, rows, tmp_path: Path):
    target["stem"] = stem
    target["rows"] = list(rows)
    return tmp_path / f"{stem}.json", tmp_path / f"{stem}.csv"
