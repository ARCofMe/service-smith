"""Import profile support for repeatable ServiceSmith workflows."""

from __future__ import annotations

import json
from pathlib import Path

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
        profiles[name] = dict(profile)
    return profiles


def resolve_profile(name: str, path: Path) -> dict:
    profiles = load_profiles(path)
    try:
        return profiles[name]
    except KeyError as exc:
        supported = ", ".join(sorted(profiles)) or "none"
        raise ValueError(f"Unknown profile '{name}'. Supported profiles: {supported}") from exc
