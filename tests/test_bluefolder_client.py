from types import SimpleNamespace
import xml.etree.ElementTree as ET

from service_smith.bluefolder_client import ServiceSmithBlueFolderClient
from service_smith.utils.config import Settings


def _settings() -> Settings:
    return Settings(
        bluefolder_api_key="key",
        bluefolder_account_name="acct",
        bluefolder_base_url=None,
        bluefolder_host_header=None,
        bluefolder_verify_ssl=False,
        service_smith_log_level="INFO",
        service_smith_default_sheet=None,
        service_smith_report_dir="reports",
        service_smith_default_customer_type="Residential",
        service_smith_default_sr_status="New",
        service_smith_default_sr_priority=None,
        service_smith_default_contact_title=None,
    )


def _customer_list_xml() -> ET.Element:
    root = ET.Element("response")
    customer = ET.SubElement(root, "customer")
    ET.SubElement(customer, "customerId").text = "123"
    ET.SubElement(customer, "customerName").text = "Acme Service"
    ET.SubElement(customer, "email").text = "ops@example.com"
    ET.SubElement(customer, "phone").text = "2075551212"
    return root


def _client_with_stubs() -> ServiceSmithBlueFolderClient:
    svc = ServiceSmithBlueFolderClient.__new__(ServiceSmithBlueFolderClient)
    svc.settings = _settings()
    svc._customer_cache = None
    svc.client = SimpleNamespace(
        customers=SimpleNamespace(
            list=lambda filters: _customer_list_xml(),
            add=lambda **fields: _id_response("customerId", "999"),
        ),
        customer_locations=SimpleNamespace(
            get_by_customer_id=lambda customer_id: [],
            add=lambda customer_id, **fields: _id_response("customerLocationId", "456"),
        ),
        customer_contacts=SimpleNamespace(
            list_for_customer=lambda customer_id: [],
            add=lambda customer_id, **fields: _id_response("id", "789"),
        ),
        service_requests=SimpleNamespace(
            add=lambda **fields: _id_response("serviceRequestId", "555"),
        ),
    )
    return svc


def _id_response(tag: str, value: str) -> ET.Element:
    root = ET.Element("response")
    ET.SubElement(root, tag).text = value
    return root


def test_find_customer_matches_from_xml_cache():
    svc = _client_with_stubs()
    row = {
        "customer_name": "Acme Service",
        "customer_email": "ops@example.com",
        "customer_phone": "2075551212",
    }

    customer = svc.find_customer(row)

    assert customer is not None
    assert customer["customerId"] == "123"


def test_plan_import_reports_existing_customer_and_new_dependents():
    svc = _client_with_stubs()
    row = {
        "source_row_number": "2",
        "customer_name": "Acme Service",
        "customer_email": "ops@example.com",
        "customer_phone": "2075551212",
        "address": "123 Main St",
        "city": "Portland",
        "state": "ME",
        "zip": "04101",
        "description": "No cool",
        "external_id": "WO-1",
    }

    plan = svc.plan_import(row)

    assert plan.customer_action == "use_existing"
    assert plan.location_action == "create_location"
    assert plan.contact_action == "create_contact"
    assert plan.service_request_action == "create_service_request"
    assert plan.existing_customer_id == "123"


def test_ensure_customer_and_import_creates_missing_records():
    svc = _client_with_stubs()
    row = {
        "source_row_number": "3",
        "customer_name": "New Customer",
        "customer_email": "new@example.com",
        "customer_phone": "2075559999",
        "contact_first_name": "Jane",
        "contact_last_name": "Smith",
        "address": "55 River Rd",
        "city": "Augusta",
        "state": "ME",
        "zip": "04330",
        "description": "Leaking washer",
        "subject": "Washer leak",
    }

    result = svc.ensure_customer_and_import(row)

    assert result.customer_id == "999"
    assert result.customer_location_id == "456"
    assert result.customer_contact_id == "789"
    assert result.service_request_id == "555"
    assert result.created_customer is True
    assert result.created_location is True
    assert result.created_contact is True
    assert result.status == "imported"
