"""BlueFolder wrapper helpers for ServiceSmith."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import xml.etree.ElementTree as ET


@dataclass(slots=True)
class BlueFolderImportResult:
    row_number: str | None
    customer_id: str | None
    service_request_id: str | None
    created_customer: bool = False
    status: str = "imported"
    notes: list[str] | None = None


@dataclass(slots=True)
class BlueFolderImportPlan:
    row_number: str | None
    customer_action: str
    service_request_action: str
    existing_customer_id: str | None = None
    notes: list[str] | None = None


class ServiceSmithBlueFolderClient:
    """Thin adapter over the shared bluefolder-api package."""

    def __init__(self) -> None:
        try:
            from bluefolder_api.client import BlueFolderClient
        except Exception as exc:
            raise RuntimeError(
                "bluefolder_api is not available. Add it to PYTHONPATH or install it."
            ) from exc

        self.client = BlueFolderClient()
        self._customer_cache: list[dict[str, str]] | None = None

    def find_customer(self, row: dict[str, Any]) -> dict[str, Any] | None:
        """Find a customer by email, phone, or exact name."""
        email = (row.get("customer_email") or "").strip()
        phone = (row.get("customer_phone") or "").strip()
        name = (row.get("customer_name") or "").strip()

        for customer in self._list_customers():
            if email and customer.get("email", "").casefold() == email.casefold():
                return customer
            if phone and customer.get("phone", "") == phone:
                return customer
            if name and customer.get("name", "").casefold() == name.casefold():
                return customer
        return None

    def create_customer(self, row: dict[str, Any]) -> str | None:
        """Placeholder customer creation hook."""
        payload = {
            "customerName": row.get("customer_name"),
            "customerType": row.get("customer_type") or "Residential",
            "email": row.get("customer_email"),
            "phone": row.get("customer_phone"),
        }
        response = self.client.customers.add(**{k: v for k, v in payload.items() if v})
        return self._extract_id(response, ("customerId", "id"))

    def create_service_request(self, row: dict[str, Any], customer_id: str | None) -> str | None:
        """Submit one service request to BlueFolder."""
        payload = {
            "customerId": customer_id,
            "description": row.get("description") or row.get("subject"),
            "priority": row.get("priority"),
            "status": row.get("status") or "New",
            "externalId": row.get("external_id"),
            "customerLocationStreetAddress": row.get("address"),
            "customerLocationCity": row.get("city"),
            "customerLocationState": row.get("state"),
            "customerLocationPostalCode": row.get("zip"),
        }
        response = self.client.service_requests.add(**{k: v for k, v in payload.items() if v})
        return self._extract_id(response, ("serviceRequestId", "id"))

    def ensure_customer_and_import(self, row: dict[str, Any]) -> BlueFolderImportResult:
        notes: list[str] = []
        customer = self.find_customer(row)
        created_customer = False
        customer_id = None
        if customer:
            customer_id = str(customer.get("customerId") or customer.get("id") or "")
            notes.append("matched existing customer")
        elif row.get("customer_name"):
            customer_id = self.create_customer(row)
            created_customer = bool(customer_id)
            if created_customer:
                notes.append("created customer")
                self._customer_cache = None

        service_request_id = self.create_service_request(row, customer_id)
        return BlueFolderImportResult(
            row_number=row.get("source_row_number"),
            customer_id=customer_id,
            service_request_id=service_request_id,
            created_customer=created_customer,
            status="imported" if service_request_id else "failed",
            notes=notes,
        )

    def plan_import(self, row: dict[str, Any]) -> BlueFolderImportPlan:
        customer = self.find_customer(row)
        notes: list[str] = []
        if customer:
            notes.append("customer already exists in BlueFolder")
        elif row.get("customer_name"):
            notes.append("customer would be created")
        else:
            notes.append("service request would be created without a matched customer")
        if row.get("external_id"):
            notes.append(f"external_id={row['external_id']}")
        return BlueFolderImportPlan(
            row_number=row.get("source_row_number"),
            customer_action="use_existing" if customer else "create_customer",
            service_request_action="create_service_request",
            existing_customer_id=str(customer.get("id") or customer.get("customerId")) if customer else None,
            notes=notes,
        )

    def _list_customers(self) -> list[dict[str, str]]:
        if self._customer_cache is not None:
            return self._customer_cache
        try:
            xml = self.client.customers.list({})
        except Exception:
            self._customer_cache = []
            return self._customer_cache

        customers: list[dict[str, str]] = []
        if isinstance(xml, ET.Element):
            for node in xml.findall(".//customer"):
                customers.append(
                    {
                        "id": node.findtext("customerId") or node.findtext("id") or "",
                        "customerId": node.findtext("customerId") or node.findtext("id") or "",
                        "name": node.findtext("customerName") or "",
                        "email": node.findtext("email") or "",
                        "phone": node.findtext("phone") or node.findtext("phoneNumber") or "",
                    }
                )
        self._customer_cache = customers
        return customers

    @staticmethod
    def _extract_id(response: Any, candidate_tags: tuple[str, ...]) -> str | None:
        if response is None:
            return None
        if isinstance(response, dict):
            for tag in candidate_tags:
                value = response.get(tag)
                if value:
                    return str(value)
            return None
        for tag in candidate_tags:
            try:
                value = response.findtext(f".//{tag}")
            except Exception:
                value = None
            if value:
                return str(value)
        return None
