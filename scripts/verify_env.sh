#!/usr/bin/env bash
# Verify project-local Python env (run outside sandbox / on your Mac).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/.venv/bin/python3"

if [ ! -x "$PY" ]; then
  echo "FAIL: $PY missing — run: $ROOT/scripts/setup_venv.sh" >&2
  exit 1
fi

echo "python: $PY"
"$PY" --version
"$PY" -c "
import yaml, longport, lark_oapi, pandas
from config import config
print('imports ok')
print('strategy:', config['strategy']['name'])
print('log_path:', config['log_path'])
"
echo "OK: local venv is ready at $ROOT/.venv"
