#!/usr/bin/env bash
# One-shot CallMacd scan — invoked by system cron at 09:35 and 21:35 (local time).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p "$ROOT/log"

PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then
  echo "error: python3 not found. Run: $ROOT/scripts/setup_venv.sh" >&2
  exit 1
fi

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
LOG="$ROOT/log/cron.log"

echo "=== $(date '+%Y-%m-%d %H:%M:%S %Z') pid=$$ ===" >>"$LOG"
if "$PY" main.py --once >>"$LOG" 2>&1; then
  echo "=== finished ok ===" >>"$LOG"
else
  code=$?
  echo "=== finished with error exit=$code ===" >>"$LOG"
  exit "$code"
fi
