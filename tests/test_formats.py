from service_smith.formats import DEFAULT_ADAPTER, get_adapter, list_adapters


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
