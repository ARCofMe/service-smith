from pathlib import Path

from service_smith.formats import get_adapter
from service_smith.importer import load_rows, read_headers, select_rows, validate_rows


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


def test_read_headers_returns_csv_header_row(tmp_path: Path):
    csv_path = tmp_path / "default.csv"
    csv_path.write_text(
        "Customer Name,Email,Phone\n"
        "Acme,ops@example.com,207-555-1212\n",
        encoding="utf-8",
    )

    headers = read_headers(csv_path)

    assert headers == ["Customer Name", "Email", "Phone"]


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


def test_load_rows_normalizes_common_fields(tmp_path: Path):
    csv_path = tmp_path / "default.csv"
    csv_path.write_text(
        "Customer Name,Email,Phone,Subject,Address,City,State,Zip\n"
        "Acme,OPS@EXAMPLE.COM,(207) 555-1212,No cool,123 Main St,Portland,me,04101 \n",
        encoding="utf-8",
    )

    rows = load_rows(csv_path)

    assert rows[0]["customer_email"] == "ops@example.com"
    assert rows[0]["customer_phone"] == "207-555-1212"
    assert rows[0]["state"] == "ME"
    assert rows[0]["zip"] == "04101"


def test_select_rows_filters_by_source_row_and_limit():
    rows = [
        {"source_row_number": "2", "customer_name": "A"},
        {"source_row_number": "3", "customer_name": "B"},
        {"source_row_number": "4", "customer_name": "C"},
    ]

    selected = select_rows(rows, row_start=3, row_end=4, limit=1)

    assert selected == [{"source_row_number": "3", "customer_name": "B"}]


def test_validate_rows_flags_questionable_contact_formats():
    issues = validate_rows(
        [
            {
                "source_row_number": "2",
                "customer_name": "Acme",
                "description": "No cool",
                "subject": "",
                "address": "123 Main St",
                "city": "Portland",
                "state": "Maine",
                "zip": "0410",
                "customer_email": "not-an-email",
                "customer_phone": "55512",
                "external_id": "",
            }
        ]
    )

    messages = [issue["message"] for issue in issues]
    assert "Questionable email format: not-an-email" in messages
    assert "Questionable phone format: 55512" in messages
    assert "State should usually be 2 letters: Maine" in messages
    assert "Questionable zip format: 0410" in messages
