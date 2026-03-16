"""Configuration loading placeholders for ServiceSmith."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback for lean test environments

    def load_dotenv(*args, **kwargs):
        return False


@dataclass(slots=True)
class Settings:
    bluefolder_api_key: str | None
    bluefolder_account_name: str | None
    bluefolder_base_url: str | None
    bluefolder_host_header: str | None
    bluefolder_verify_ssl: bool
    service_smith_log_level: str
    service_smith_default_sheet: str | None
    service_smith_report_dir: str
    service_smith_default_customer_type: str
    service_smith_default_sr_status: str
    service_smith_default_sr_priority: str | None
    service_smith_default_contact_title: str | None


def load_settings(env_path: str | Path | None = None) -> Settings:
    """Load environment-backed settings.

    This is intentionally minimal for now and can be replaced by pydantic-settings
    or a richer config layer later without changing the rest of the project layout.
    """
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv()

    return Settings(
        bluefolder_api_key=os.getenv("BLUEFOLDER_API_KEY"),
        bluefolder_account_name=os.getenv("BLUEFOLDER_ACCOUNT_NAME"),
        bluefolder_base_url=os.getenv("BLUEFOLDER_BASE_URL"),
        bluefolder_host_header=os.getenv("BLUEFOLDER_HOST_HEADER"),
        bluefolder_verify_ssl=str(os.getenv("BLUEFOLDER_VERIFY_SSL", "false")).lower() in {"1", "true", "yes"},
        service_smith_log_level=os.getenv("SERVICE_SMITH_LOG_LEVEL", "INFO"),
        service_smith_default_sheet=os.getenv("SERVICE_SMITH_DEFAULT_SHEET"),
        service_smith_report_dir=os.getenv("SERVICE_SMITH_REPORT_DIR", "reports"),
        service_smith_default_customer_type=os.getenv("SERVICE_SMITH_DEFAULT_CUSTOMER_TYPE", "Residential"),
        service_smith_default_sr_status=os.getenv("SERVICE_SMITH_DEFAULT_SR_STATUS", "New"),
        service_smith_default_sr_priority=os.getenv("SERVICE_SMITH_DEFAULT_SR_PRIORITY"),
        service_smith_default_contact_title=os.getenv("SERVICE_SMITH_DEFAULT_CONTACT_TITLE"),
    )
