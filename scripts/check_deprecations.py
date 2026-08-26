"""Deprecation policy + scan.

Phase 10 ships:
- `@deprecated` docstring conventions for Python.
- `DeprecationWarning` enforcement.
- `docs/deprecation.md` timeline.

`scripts/check_deprecations.py` walks the codebase, finds every symbol
flagged `@deprecated` with a `Removal: YYYY-MM-DD` line, and fails if
today is past that date.
"""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re


REMOVAL_RE = re.compile(r"Removal:\s*(\d{4}-\d{2}-\d{2})")
DEPRECATED_RE = re.compile(r"@deprecated\b")


def scan(root: pathlib.Path) -> list[tuple[pathlib.Path, int, dt.date]]:
    today = dt.date.today()
    findings: list[tuple[pathlib.Path, int, dt.date]] = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if "@deprecated" not in line:
                continue
            match = REMOVAL_RE.search(line) or _find_in_window(text, line_number, REMOVAL_RE)
            if not match:
                continue
            removal = dt.date.fromisoformat(match.group(1))
            if removal <= today:
                findings.append((path, line_number, removal))
    return findings


def _find_in_window(text: str, line_number: int, pattern: re.Pattern[str]) -> re.Match[str] | None:
    lines = text.splitlines()
    for offset in range(1, 6):
        if line_number + offset >= len(lines):
            break
        match = pattern.search(lines[line_number + offset])
        if match:
            return match
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path("."))
    args = parser.parse_args()
    overdue = scan(args.root)
    if overdue:
        for path, line, removal in overdue:
            print(f"OVERDUE: {path}:{line} removal_at={removal}", file=__import__("sys").stderr)
        return 1
    print("[check_deprecations] no overdue deprecations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())