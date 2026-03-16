# ServiceSmith Workflows

## Default Template

Use the built-in default template when you control the spreadsheet format.

```bash
servicesmith templates/default_template.csv --format default --dry-run
```

Use payload preview when validating final BlueFolder fields:

```bash
servicesmith templates/default_template.csv --format default --dry-run --payload-preview
```

## Vendor Adapter

Use a named adapter when a vendor export already matches one of the supported formats.

```bash
servicesmith vendor_export.xlsx --format vendor_a --dry-run
```

## Vendor Adapter With Override

Use an adapter plus a field-map override when the vendor export is close to a known format but a few headers differ.

```bash
servicesmith vendor_export.xlsx \
  --format vendor_a \
  --field-map examples/custom_map.json \
  --dry-run --payload-preview
```

## Real Import

Only run a real import after validation passes and the dry-run report looks correct.

```bash
servicesmith vendor_export.xlsx --format default
```

Add `--fail-fast` if you want the import to stop on the first failed row.
