from service_smith.utils.reporting import summarize_rows


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
