#!/usr/bin/env bash
# Install dependencies with local python3 -m pip (no virtualenv).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then
  echo "error: python3 not found in PATH" >&2
  exit 1
fi

echo "using: $PY ($("$PY" --version))"

"$PY" -m pip install --user -U pip
"$PY" -m pip install --user --no-compile-bytecode \
  -r requirement.txt -i https://mirrors.aliyun.com/pypi/simple

chmod +x "$ROOT/scripts/verify_env.sh" "$ROOT/scripts/run_callmacd_once.sh" 2>/dev/null || true
"$ROOT/scripts/verify_env.sh"
