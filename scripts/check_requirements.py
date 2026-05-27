"""Verify top-level packages listed in requirement.txt are installed (offline)."""

from __future__ import annotations

import importlib.metadata as im
import re
import sys
from pathlib import Path


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def installed_names() -> set[str]:
    names: set[str] = set()
    for dist in im.distributions():
        try:
            names.add(normalize(dist.metadata["Name"]))
        except Exception:
            continue
    return names


def parse_requirement(line: str) -> str | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    spec = line.split(";")[0].strip()
    name = re.split(r"[<>=!~]", spec)[0].strip()
    return name.split("[")[0].strip() or None


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    req_file = root / "requirement.txt"
    if not req_file.is_file():
        print(f"FAIL: {req_file} not found", file=sys.stderr)
        return 1

    installed = installed_names()
    missing: list[str] = []

    for line in req_file.read_text(encoding="utf-8").splitlines():
        name = parse_requirement(line)
        if name is None:
            continue
        if normalize(name) not in installed:
            missing.append(name)

    if missing:
        print("FAIL: not installed:", ", ".join(missing), file=sys.stderr)
        return 1

    print("OK: all packages in requirement.txt are installed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
