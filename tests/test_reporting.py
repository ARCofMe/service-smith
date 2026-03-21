from service_smith.utils.reporting import summarize_rows, write_summary_report


def test_summarize_rows_counts_statuses():
    rows = [
        {"status": "imported"},
        {"status": "imported"},
        {"status": "skipped_duplicate"},
    ]

    summary = summarize_rows(rows)

    assert summary["total"] == 3
    assert summary["status:imported"] == 2
    assert summary["status:skipped_duplicate"] == 1


def test_summarize_rows_counts_extra_fields():
    rows = [
        {"status": "imported", "created_customer": True, "created_location": True},
        {"status": "imported", "created_customer": False, "created_location": True},
    ]

    summary = summarize_rows(rows, extra_fields=("created_customer", "created_location"))

    assert summary["created_customer:True"] == 1
    assert summary["created_customer:False"] == 1
    assert summary["created_location:True"] == 2


def test_write_summary_report_creates_markdown_summary(tmp_path):
    rows = [
        {"status": "imported", "row_number": "2"},
        {"status": "skipped_duplicate", "row_number": "3"},
    ]

    summary_path = write_summary_report(tmp_path, "import_results_summary", rows, title="Import Summary")

    content = summary_path.read_text(encoding="utf-8")
    assert summary_path.suffix == ".md"
    assert "# Import Summary" in content
    assert "- total: 2" in content
    assert "- status:imported: 1" in content


def test_write_summary_report_includes_extra_field_breakdowns(tmp_path):
    rows = [
        {"status": "imported", "created_customer": True},
        {"status": "imported", "created_customer": False},
    ]

    summary_path = write_summary_report(
        tmp_path,
        "import_results_summary",
        rows,
        title="Import Summary",
        extra_fields=("created_customer",),
    )

    content = summary_path.read_text(encoding="utf-8")
    assert "- created_customer:True: 1" in content
    assert "- created_customer:False: 1" in content
