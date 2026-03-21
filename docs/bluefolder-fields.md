# BlueFolder Field Mapping

This document maps `ServiceSmith` canonical import fields to the BlueFolder payload fields currently used by the importer.

## Canonical Fields

These are the internal field names used after a spreadsheet adapter or field-map override is applied:

- `customer_name`
- `customer_email`
- `customer_phone`
- `customer_type`
- `contact_first_name`
- `contact_last_name`
- `contact_title`
- `location_name`
- `subject`
- `description`
- `priority`
- `status`
- `external_id`
- `address`
- `city`
- `state`
- `zip`

## Customer Payload

Built in [`build_customer_payload()`](/home/ner0tic/Documents/Projects/ARCoM/service-smith/service_smith/bluefolder_client.py).

| Canonical field | BlueFolder payload field |
| --- | --- |
| `customer_name` | `customerName` |
| `customer_type` | `customerType` |
| `customer_email` | `email` |
| `customer_phone` | `phone` |

## Customer Location Payload

Built in [`build_location_payload()`](/home/ner0tic/Documents/Projects/ARCoM/service-smith/service_smith/bluefolder_client.py).

| Canonical field | BlueFolder payload field |
| --- | --- |
| `location_name` | `locationName` |
| `address` | `addressStreet` |
| `city` | `addressCity` |
| `state` | `addressState` |
| `zip` | `addressPostalCode` |

## Customer Contact Payload

Built in [`build_contact_payload()`](/home/ner0tic/Documents/Projects/ARCoM/service-smith/service_smith/bluefolder_client.py).

| Canonical field | BlueFolder payload field |
| --- | --- |
| `contact_first_name` | `firstName` |
| `contact_last_name` | `lastName` |
| `contact_title` | `title` |
| `customer_email` | `email` |
| `customer_phone` | `phone` |
| derived from matched/created location | `customerLocationId` |

Notes:
- if `contact_first_name` is missing, `ServiceSmith` falls back to the first token of `customer_name`
- if `contact_last_name` is missing, `ServiceSmith` falls back to the remaining tokens of `customer_name`

## Service Request Payload

Built in [`build_service_request_payload()`](/home/ner0tic/Documents/Projects/ARCoM/service-smith/service_smith/bluefolder_client.py).

| Canonical field | BlueFolder payload field |
| --- | --- |
| matched/created customer | `customerId` |
| matched/created location | `customerLocationId` |
| matched/created contact | `customerContactId` |
| `subject` | `subject` |
| `description` or fallback `subject` | `description` |
| `priority` | `priority` |
| `status` | `status` |
| `external_id` | `externalId` |
| `address` | `customerLocationStreetAddress` |
| `city` | `customerLocationCity` |
| `state` | `customerLocationState` |
| `zip` | `customerLocationPostalCode` |

## Defaults

These fields can be defaulted from environment-backed settings when the spreadsheet does not provide them:

- `customer_type` via `SERVICE_SMITH_DEFAULT_CUSTOMER_TYPE`
- `status` via `SERVICE_SMITH_DEFAULT_SR_STATUS`
- `priority` via `SERVICE_SMITH_DEFAULT_SR_PRIORITY`
- `contact_title` via `SERVICE_SMITH_DEFAULT_CONTACT_TITLE`

## Duplicate Protection

Duplicate service request protection currently relies on `external_id` mapping to BlueFolder `externalId`.

If the source spreadsheet does not include a stable external ID, duplicate detection will be weaker.
