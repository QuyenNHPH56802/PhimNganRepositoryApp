"""Dry-run the full release pipeline locally."""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys


STEPS: list[tuple[str, list[str]]] = [
    ("release --dry-run", ["python", "scripts/release.py", "--bump", "patch", "--dry-run"]),
    ("migrate --dry-run", ["python", "scripts/migrate.py", "--dry-run"]),
    ("deprecation scan", ["python", "scripts/check_deprecations.py"]),
    ("build wheel", ["python", "-m", "build"]),
    ("sdk build", ["pnpm", "--dir", "apps/web/sdk", "build"]),
    ("helm template", ["helm", "template", "translator", "infra/helm/translator"]),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    failed = 0
    for label, cmd in STEPS:
        binary = cmd[0]
        if shutil.which(binary) is None and binary not in {"pnpm"}:
            print(f"[dryrun] SKIP {label} (binary {binary} missing)")
            continue
        print(f"[dryrun] {label}: {' '.join(cmd)}")
        completed = subprocess.run(cmd, check=False)
        if completed.returncode != 0:
            print(f"[dryrun] FAIL {label}", file=sys.stderr)
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())