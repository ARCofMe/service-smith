"""Import profile support for repeatable ServiceSmith workflows."""

from __future__ import annotations

import json
from pathlib import Path

from service_smith.formats import ADAPTERS

PROFILE_KEYS = {
    "dry_run",
    "validate_only",
    "payload_preview",
    "report_dir",
    "fail_fast",
    "spreadsheet_format",
    "field_map",
    "duplicate_mode",
    "row_start",
    "row_end",
    "limit",
}


def load_profiles(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Profile file must contain a top-level object keyed by profile name.")
    profiles: dict[str, dict] = {}
    for name, profile in data.items():
        if not isinstance(profile, dict):
            raise ValueError(f"Profile '{name}' must be an object.")
        unknown = sorted(set(profile) - PROFILE_KEYS)
        if unknown:
            raise ValueError(f"Profile '{name}' has unsupported keys: {', '.join(unknown)}")
        profiles[name] = _validate_profile(name, profile)
    return profiles


def resolve_profile(name: str, path: Path) -> dict:
    profiles = load_profiles(path)
    try:
        return profiles[name]
    except KeyError as exc:
        supported = ", ".join(sorted(profiles)) or "none"
        raise ValueError(f"Unknown profile '{name}'. Supported profiles: {supported}") from exc


def _validate_profile(name: str, profile: dict) -> dict:
    validated = dict(profile)

    for key in ("dry_run", "validate_only", "payload_preview", "fail_fast"):
        value = validated.get(key)
        if value is not None and not isinstance(value, bool):
            raise ValueError(f"Profile '{name}' key '{key}' must be a boolean.")

    format_name = validated.get("spreadsheet_format")
    if format_name is not None:
        if not isinstance(format_name, str) or format_name not in ADAPTERS:
            supported = ", ".join(sorted(ADAPTERS))
            raise ValueError(f"Profile '{name}' key 'spreadsheet_format' must be one of: {supported}")

    duplicate_mode = validated.get("duplicate_mode")
    if duplicate_mode is not None and duplicate_mode not in {"skip", "error", "allow"}:
        raise ValueError(f"Profile '{name}' key 'duplicate_mode' must be one of: skip, error, allow")

    for key in ("report_dir", "field_map"):
        value = validated.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"Profile '{name}' key '{key}' must be a non-empty string.")

    for key in ("row_start", "row_end", "limit"):
        value = validated.get(key)
        if value is not None and (not isinstance(value, int) or value < 1):
            raise ValueError(f"Profile '{name}' key '{key}' must be a positive integer.")

    return validated
