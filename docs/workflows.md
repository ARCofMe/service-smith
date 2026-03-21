# ServiceSmith Workflows

## Default Template

Use the built-in default template when you control the spreadsheet format.

```bash
servicesmith templates/default_template.csv --format default --dry-run
```

Or via the helper script:

```bash
scripts/run_import_workflow.sh dry-run templates/default_template.csv
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

Or via the helper script:

```bash
scripts/run_import_workflow.sh dry-run vendor_export.xlsx vendor_a
```

## Vendor Adapter With Override

Use an adapter plus a field-map override when the vendor export is close to a known format but a few headers differ.

```bash
servicesmith vendor_export.xlsx \
  --format vendor_a \
  --field-map examples/custom_map.json \
  --dry-run --payload-preview
```

Or via the helper script:

```bash
scripts/run_import_workflow.sh payload-preview vendor_export.xlsx vendor_a examples/custom_map.json
```

## Saved Profile

Use a saved profile when the same import settings come up repeatedly.

```bash
servicesmith vendor_export.xlsx \
  --profile vendor_a_review \
  --profile-file examples/import_profiles.json
```

Use CLI flags on top when you need a one-off override:

```bash
servicesmith vendor_export.xlsx \
  --profile vendor_a_review \
  --profile-file examples/import_profiles.json \
  --duplicate-mode allow
```

## Real Import

Only run a real import after validation passes and the dry-run report looks correct.

```bash
servicesmith vendor_export.xlsx --format default
```

Add `--fail-fast` if you want the import to stop on the first failed row.
