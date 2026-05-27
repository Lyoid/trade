#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

.venv/bin/pip install -U pip
.venv/bin/pip install -r requirement.txt -i https://mirrors.aliyun.com/pypi/simple

chmod +x "$ROOT/scripts/verify_env.sh" "$ROOT/scripts/run_callmacd_once.sh" 2>/dev/null || true
"$ROOT/scripts/verify_env.sh"
