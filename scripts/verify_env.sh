#!/usr/bin/env bash
# Check that every top-level package in requirement.txt is installed (offline).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$(command -v python3 || true)"

if [ -z "$PY" ]; then
  echo "FAIL: python3 not found in PATH" >&2
  exit 1
fi

echo "python: $PY ($("$PY" --version))"
exec "$PY" "$ROOT/scripts/check_requirements.py"
