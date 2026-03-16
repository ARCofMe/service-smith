from pathlib import Path

from service_smith.formats import get_adapter
from service_smith.importer import load_rows, validate_rows


def test_load_rows_uses_adapter_mapping(tmp_path: Path):
    csv_path = tmp_path / "vendor_a.csv"
    csv_path.write_text(
        "Account Name,Contact Email,Problem Summary,Street Address,City,State,Postal Code\n"
        "Acme,ops@example.com,No cool,123 Main St,Portland,ME,04101\n",
        encoding="utf-8",
    )

    rows = load_rows(csv_path, field_map=get_adapter("vendor_a").field_map)

    assert len(rows) == 1
    assert rows[0]["customer_name"] == "Acme"
    assert rows[0]["customer_email"] == "ops@example.com"
    assert rows[0]["subject"] == "No cool"
    assert rows[0]["address"] == "123 Main St"
    assert rows[0]["source_row_number"] == "2"


def test_validate_rows_flags_missing_required_fields():
    issues = validate_rows(
        [
            {
                "source_row_number": "2",
                "customer_name": "",
                "description": "",
                "subject": "",
                "address": "",
                "city": "",
                "state": "",
                "external_id": "",
            }
        ]
    )

    levels = {(issue["level"], issue["message"]) for issue in issues}
    assert ("error", "Missing customer_name") in levels
    assert ("error", "Missing subject/description") in levels
    assert ("warning", "Missing address") in levels
    assert ("warning", "Missing city/state") in levels


def test_validate_rows_flags_duplicate_batch_rows():
    rows = [
        {
            "source_row_number": "2",
            "customer_name": "Acme",
            "description": "No cool",
            "subject": "",
            "address": "123 Main St",
            "city": "Portland",
            "state": "ME",
            "external_id": "WO-1",
        },
        {
            "source_row_number": "3",
            "customer_name": "Acme",
            "description": "No cool",
            "subject": "",
            "address": "123 Main St",
            "city": "Portland",
            "state": "ME",
            "external_id": "WO-1",
        },
    ]

    issues = validate_rows(rows)
    messages = [issue["message"] for issue in issues]
    assert "Duplicate external_id WO-1" in messages
    assert "Potential duplicate row in import batch" in messages
