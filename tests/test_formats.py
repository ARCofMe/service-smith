import json

from service_smith.formats import (
    DEFAULT_ADAPTER,
    analyze_headers,
    adapter_headers,
    detect_adapter_matches,
    get_adapter,
    list_adapters,
    load_field_map_override,
    merge_field_maps,
)
from service_smith.profiles import load_profiles


def test_get_adapter_returns_named_adapter():
    adapter = get_adapter("default")
    assert adapter.name == "default"
    assert adapter.field_map == DEFAULT_ADAPTER.field_map


def test_list_adapters_contains_default():
    names = [adapter.name for adapter in list_adapters()]
    assert "default" in names
    assert "vendor_a" in names
    assert "vendor_b" in names


def test_get_adapter_rejects_unknown_name():
    try:
        get_adapter("nope")
    except ValueError as exc:
        assert "Supported formats" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown adapter")


def test_adapter_headers_match_declared_field_order():
    headers = adapter_headers("default")
    assert headers[0] == "Customer Name"
    assert "External ID" in headers


def test_load_field_map_override_accepts_known_canonical_fields(tmp_path):
    path = tmp_path / "field_map.json"
    path.write_text(json.dumps({"customer_name": "Client", "subject": "Issue"}), encoding="utf-8")

    override = load_field_map_override(path)

    assert override == {"customer_name": "Client", "subject": "Issue"}


def test_load_field_map_override_rejects_unknown_fields(tmp_path):
    path = tmp_path / "field_map.json"
    path.write_text(json.dumps({"nope": "Client"}), encoding="utf-8")

    try:
        load_field_map_override(path)
    except ValueError as exc:
        assert "Unknown canonical field" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid field override")


def test_merge_field_maps_overrides_selected_headers():
    merged = merge_field_maps(DEFAULT_ADAPTER.field_map, {"customer_name": "Client"})
    assert merged["customer_name"] == "Client"
    assert merged["subject"] == DEFAULT_ADAPTER.field_map["subject"]


def test_analyze_headers_reports_missing_and_unexpected():
    analysis = analyze_headers(
        ["Customer Name", "Subject", "Address", "Mystery Column"],
        DEFAULT_ADAPTER.field_map,
    )

    assert analysis["matched_count"] == 3
    assert "Email" in analysis["missing_headers"]
    assert "Mystery Column" in analysis["unexpected_headers"]


def test_detect_adapter_matches_ranks_best_candidate_first():
    matches = detect_adapter_matches(
        ["Account Name", "Contact Email", "Problem Summary", "Street Address", "City", "State", "Postal Code"]
    )

    assert matches[0]["name"] == "vendor_a"


def test_load_profiles_rejects_invalid_duplicate_mode(tmp_path):
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps({"bad_profile": {"duplicate_mode": "warn"}}), encoding="utf-8")

    try:
        load_profiles(path)
    except ValueError as exc:
        assert "duplicate_mode" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid duplicate_mode")


def test_load_profiles_rejects_unknown_adapter(tmp_path):
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps({"bad_profile": {"spreadsheet_format": "vendor_z"}}), encoding="utf-8")

    try:
        load_profiles(path)
    except ValueError as exc:
        assert "spreadsheet_format" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid spreadsheet_format")
