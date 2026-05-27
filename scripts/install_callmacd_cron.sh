#!/usr/bin/env bash
# Merge CallMacd cron jobs into the current user's crontab (idempotent).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MARKER="# trade CallMacd"
RUN_SCRIPT="$ROOT/scripts/run_callmacd_once.sh"
chmod +x "$RUN_SCRIPT"

if [ ! -x "$RUN_SCRIPT" ]; then
  echo "error: not executable: $RUN_SCRIPT" >&2
  exit 1
fi

# macOS cron uses system local timezone; keep machine TZ at Asia/Shanghai or adjust hours.
JOB_HK="35 9 * * 1-5 $RUN_SCRIPT"
JOB_US="35 21 * * 1-5 $RUN_SCRIPT"

existing="$(crontab -l 2>/dev/null || true)"
filtered="$(printf '%s\n' "$existing" | grep -v "$MARKER" | grep -Fv "$RUN_SCRIPT" || true)"

{
  printf '%s\n' "$filtered" | sed '/^[[:space:]]*$/d'
  echo "$MARKER"
  echo "$JOB_HK"
  echo "$JOB_US"
} | crontab -

echo "Installed CallMacd cron (weekdays 09:35 and 21:35, local time):"
crontab -l | grep -A2 "$MARKER"
echo ""
echo "Logs: $ROOT/log/cron.log"
echo "Test now: $RUN_SCRIPT && tail -20 $ROOT/log/cron.log"
