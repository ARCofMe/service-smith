#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  cat <<'EOF'
Usage:
  scripts/run_import_workflow.sh <validate|dry-run|payload-preview> <spreadsheet> [adapter] [field-map]

Examples:
  scripts/run_import_workflow.sh validate templates/default_template.csv
  scripts/run_import_workflow.sh dry-run vendor_export.xlsx vendor_a
  scripts/run_import_workflow.sh payload-preview vendor_export.xlsx vendor_a examples/custom_map.json
EOF
  exit 1
fi

MODE="$1"
SPREADSHEET="$2"
ADAPTER="${3:-default}"
FIELD_MAP="${4:-}"

CMD=(servicesmith "$SPREADSHEET" --format "$ADAPTER")

if [[ -n "$FIELD_MAP" ]]; then
  CMD+=(--field-map "$FIELD_MAP")
fi

case "$MODE" in
  validate)
    CMD+=(--validate-only)
    ;;
  dry-run)
    CMD+=(--dry-run)
    ;;
  payload-preview)
    CMD+=(--dry-run --payload-preview)
    ;;
  *)
    echo "Unknown mode: $MODE" >&2
    exit 2
    ;;
esac

printf 'Running:'
printf ' %q' "${CMD[@]}"
printf '\n'
"${CMD[@]}"
