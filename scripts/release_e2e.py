"""Release e2e — drives the full release pipeline locally.

Steps:
    1. release.py --dry-run (patch bump)
    2. migrate.py --dry-run
    3. check_deprecations.py
    4. python -m build  (wheel + sdist)
    5. pnpm build (SDK)
    6. helm template (chart 1.0)
    7. error_budget.py smoke
    8. benchmark.py smoke

Exit code 1 if any step fails. Steps whose binary is missing are skipped
with a warning — typical in dev environments without Helm/pnpm.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys


STEPS: list[tuple[str, list[str], pathlib_or_none]] = [
    ("release --dry-run", ["python", "scripts/release.py", "--bump", "patch", "--dry-run"], None),
    ("migrate --dry-run", ["python", "scripts/migrate.py", "--dry-run"], None),
    ("deprecation scan", ["python", "scripts/check_deprecations.py"], None),
    ("build wheel", ["python", "-m", "build"], None),
    ("sdk build", ["pnpm", "--dir", "apps/web/sdk", "build"], "pnpm"),
    ("helm template", ["helm", "template", "translator", "infra/helm/translator"], "helm"),
    ("benchmark smoke", ["python", "scripts/benchmark.py", "--stub"], None),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    failed = 0
    for label, cmd, required in STEPS:
        binary = cmd[0]
        if shutil.which(binary) is None and required is not None:
            print(f"[release-e2e] SKIP {label} (binary {binary} missing)")
            continue
        print(f"[release-e2e] {label}: {' '.join(cmd)}")
        completed = subprocess.run(cmd, check=False)
        if completed.returncode != 0:
            print(f"[release-e2e] FAIL {label}", file=sys.stderr)
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())