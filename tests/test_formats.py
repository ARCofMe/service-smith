import json

from service_smith.formats import (
    DEFAULT_ADAPTER,
    adapter_headers,
    get_adapter,
    list_adapters,
    load_field_map_override,
    merge_field_maps,
)


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
