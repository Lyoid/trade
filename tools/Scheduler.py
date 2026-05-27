"""Daily run-time scheduling (stdlib + pytz, no extra dependencies)."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import List, Optional, Tuple

import pytz


def get_scheduler_config(config: dict) -> dict:
    sched = config.get("scheduler") or {}
    run_times = sched.get("run_times") or ["09:35:00"]
    if isinstance(run_times, str):
        run_times = [run_times]
    return {
        "enabled": bool(sched.get("enabled", False)),
        "mode": sched.get("mode", "continuous"),
        "timezone": sched.get("timezone", "Asia/Shanghai"),
        "run_times": list(run_times),
    }


def parse_run_time(value: str) -> time:
    parts = value.strip().split(":")
    if len(parts) < 2:
        raise ValueError(f"Invalid run_time {value!r}, expected HH:MM or HH:MM:SS")
    hour, minute = int(parts[0]), int(parts[1])
    second = int(parts[2]) if len(parts) > 2 else 0
    return time(hour, minute, second)


def next_run_at(run_times: List[str], tz_name: str, now: Optional[datetime] = None) -> datetime:
    tz = pytz.timezone(tz_name)
    if now is None:
        now = datetime.now(tz)
    elif now.tzinfo is None:
        now = tz.localize(now)
    else:
        now = now.astimezone(tz)

    candidates: List[datetime] = []
    for run_time in run_times:
        t = parse_run_time(run_time)
        candidate = now.replace(
            hour=t.hour, minute=t.minute, second=t.second, microsecond=0
        )
        if candidate <= now:
            candidate += timedelta(days=1)
        candidates.append(candidate)
    return min(candidates)


def seconds_until(target: datetime, now: Optional[datetime] = None) -> float:
    if now is None:
        now = datetime.now(target.tzinfo)
    elif now.tzinfo is None:
        now = target.tzinfo.localize(now)
    else:
        now = now.astimezone(target.tzinfo)
    return max(0.0, (target - now).total_seconds())


def wait_until_next(
    run_times: List[str],
    tz_name: str,
    logger,
    poll_seconds: int = 30,
) -> datetime:
    """Block until the next configured run time; returns that moment."""
    import time as time_module

    target = next_run_at(run_times, tz_name)
    logger.info(
        f"Next scheduled run at {target.strftime('%Y-%m-%d %H:%M:%S %Z')} "
        f"(timezone={tz_name}, slots={run_times})"
    )
    while True:
        remaining = seconds_until(target)
        if remaining <= 0:
            return target
        sleep_for = min(remaining, poll_seconds)
        time_module.sleep(sleep_for)
