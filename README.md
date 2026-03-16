# ServiceSmith

`ServiceSmith` imports service requests from spreadsheet files into BlueFolder.

## Structure

- `service_smith/bluefolder_client.py`: thin wrapper around the BlueFolder API package
- `service_smith/importer.py`: spreadsheet parsing and field mapping
- `service_smith/utils/config.py`: configuration loading placeholder
- `service_smith/utils/logging.py`: application logging setup
- `service_smith/main.py`: orchestration entry point
- `main.py`: convenience launcher for local execution

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
servicesmith path/to/service_requests.csv
```

List supported spreadsheet adapters:

```bash
servicesmith --list-formats placeholder.csv
```

Use a named adapter:

```bash
servicesmith vendor_export.xlsx --format vendor_a --dry-run
```

Layer a one-off JSON field-map override on top of an adapter:

```bash
servicesmith vendor_export.xlsx --format vendor_a --field-map custom_map.json --dry-run
```

Print the expected headers for one adapter:

```bash
servicesmith --format default --print-headers
```

## Templates

Sample CSV templates live in [`templates/`](/home/ner0tic/Documents/Projects/ARCoM/service-smith/templates):

- [`default_template.csv`](/home/ner0tic/Documents/Projects/ARCoM/service-smith/templates/default_template.csv)
- [`vendor_a_template.csv`](/home/ner0tic/Documents/Projects/ARCoM/service-smith/templates/vendor_a_template.csv)
- [`vendor_b_template.csv`](/home/ner0tic/Documents/Projects/ARCoM/service-smith/templates/vendor_b_template.csv)

Use these as starting points for vendors or internal requesters instead of asking them to guess the schema.

## Field Map Overrides

For one-off vendor exports, you can provide a JSON file that maps canonical field names to source headers:

```json
{
  "customer_name": "Client",
  "subject": "Issue Summary",
  "address": "Service Address"
}
```

This override is layered on top of the selected adapter instead of replacing it wholesale.

## Packaging

The project exposes a `servicesmith` console script through `pyproject.toml`, which
is a clean base for packaging into an executable with a tool such as PyInstaller later.
