# ServiceSmith Templates

Use these templates when you can control the spreadsheet shape up front.

## Which Template To Use

- `default_template.csv`: preferred internal template when you want the canonical ServiceSmith headers directly
- `vendor_a_template.csv`: sample layout for a vendor export that already aligns with the `vendor_a` adapter
- `vendor_b_template.csv`: sample layout for a vendor export that already aligns with the `vendor_b` adapter

## Practical Guidance

- Prefer `default_template.csv` for new intake workflows.
- Use a vendor template only when the source system already exports that header shape.
- If a vendor file is close but not exact, use the nearest adapter plus a `--field-map` override instead of creating a new template immediately.
- Run `servicesmith --validate-only` first for any new spreadsheet source.
- Run `servicesmith --dry-run --payload-preview` before the first real import for a vendor.
