"""Named spreadsheet adapters for ServiceSmith."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


CANONICAL_FIELDS = (
    "customer_name",
    "customer_email",
    "customer_phone",
    "customer_type",
    "contact_first_name",
    "contact_last_name",
    "contact_title",
    "location_name",
    "subject",
    "description",
    "priority",
    "status",
    "external_id",
    "address",
    "city",
    "state",
    "zip",
)


@dataclass(frozen=True, slots=True)
class SpreadsheetAdapter:
    name: str
    description: str
    field_map: dict[str, str]


DEFAULT_ADAPTER = SpreadsheetAdapter(
    name="default",
    description="Preferred ServiceSmith spreadsheet template.",
    field_map={
        "customer_name": "Customer Name",
        "customer_email": "Email",
        "customer_phone": "Phone",
        "customer_type": "Customer Type",
        "contact_first_name": "Contact First Name",
        "contact_last_name": "Contact Last Name",
        "contact_title": "Contact Title",
        "location_name": "Location Name",
        "subject": "Subject",
        "description": "Description",
        "priority": "Priority",
        "status": "Status",
        "external_id": "External ID",
        "address": "Address",
        "city": "City",
        "state": "State",
        "zip": "Zip",
    },
)


VENDOR_A_ADAPTER = SpreadsheetAdapter(
    name="vendor_a",
    description="Example vendor export with split site/contact naming.",
    field_map={
        "customer_name": "Account Name",
        "customer_email": "Contact Email",
        "customer_phone": "Contact Phone",
        "customer_type": "Account Type",
        "contact_first_name": "First Name",
        "contact_last_name": "Last Name",
        "contact_title": "Role",
        "location_name": "Site Name",
        "subject": "Problem Summary",
        "description": "Work Order Notes",
        "priority": "Priority",
        "status": "Status",
        "external_id": "Work Order ID",
        "address": "Street Address",
        "city": "City",
        "state": "State",
        "zip": "Postal Code",
    },
)


VENDOR_B_ADAPTER = SpreadsheetAdapter(
    name="vendor_b",
    description="Example vendor export with site columns and ticket IDs.",
    field_map={
        "customer_name": "Customer",
        "customer_email": "Email Address",
        "customer_phone": "Phone Number",
        "customer_type": "Type",
        "contact_first_name": "Contact First",
        "contact_last_name": "Contact Last",
        "contact_title": "Contact Title",
        "location_name": "Location",
        "subject": "Issue",
        "description": "Details",
        "priority": "Urgency",
        "status": "Ticket Status",
        "external_id": "Ticket #",
        "address": "Site Address 1",
        "city": "Site City",
        "state": "Site State",
        "zip": "Site Zip",
    },
)


ADAPTERS: dict[str, SpreadsheetAdapter] = {
    adapter.name: adapter
    for adapter in (DEFAULT_ADAPTER, VENDOR_A_ADAPTER, VENDOR_B_ADAPTER)
}


def get_adapter(name: str) -> SpreadsheetAdapter:
    try:
        return ADAPTERS[name]
    except KeyError as exc:
        supported = ", ".join(sorted(ADAPTERS))
        raise ValueError(f"Unknown spreadsheet format '{name}'. Supported formats: {supported}") from exc


def list_adapters() -> list[SpreadsheetAdapter]:
    return [ADAPTERS[name] for name in sorted(ADAPTERS)]


def adapter_headers(name: str) -> list[str]:
    adapter = get_adapter(name)
    return list(adapter.field_map.values())


def load_field_map_override(path: str | Path) -> dict[str, str]:
    override_path = Path(path)
    data = json.loads(override_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Field map override must be a JSON object of canonical_name -> source_header.")

    normalized: dict[str, str] = {}
    for key, value in data.items():
        if key not in CANONICAL_FIELDS:
            supported = ", ".join(CANONICAL_FIELDS)
            raise ValueError(f"Unknown canonical field '{key}'. Supported fields: {supported}")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Field map override for '{key}' must be a non-empty string.")
        normalized[key] = value.strip()
    return normalized


def merge_field_maps(base: dict[str, str], override: dict[str, str]) -> dict[str, str]:
    merged = dict(base)
    merged.update(override)
    return merged
