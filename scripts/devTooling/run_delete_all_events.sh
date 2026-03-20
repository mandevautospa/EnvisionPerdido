#!/usr/bin/env bash
set -euo pipefail

# Cross-platform helper to run the Python delete script using the project's venv helper when available.
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PY_WRAPPER="$BASE_DIR/scripts/run_with_venv.sh"

if [ -x "$PY_WRAPPER" ]; then
  "$PY_WRAPPER" scripts/maintenance/delete_all_events.py "${@:-}"
else
  python3 scripts/maintenance/delete_all_events.py "${@:-}"
fi
