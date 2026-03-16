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

## Packaging

The project exposes a `servicesmith` console script through `pyproject.toml`, which
is a clean base for packaging into an executable with a tool such as PyInstaller later.
