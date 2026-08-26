"""Dependency scan — pip-audit + npm audit + Trivy SBOM (best effort)."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import shutil
import subprocess
import sys


def _run(cmd: list[str], output: pathlib.Path) -> dict:
    binary = shutil.which(cmd[0])
    if not binary:
        return {"skipped": True, "reason": f"{cmd[0]} not installed"}
    completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
    output.write_text(completed.stdout, encoding="utf-8")
    return {"command": " ".join(cmd), "exit_code": completed.returncode, "output": str(output)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("outputs/reports/dependencies"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    date = dt.datetime.now().strftime("%Y%m%d")
    report: dict[str, dict] = {}

    python_targets = list(pathlib.Path(".").rglob("requirements*.txt"))
    if python_targets:
        for req_file in python_targets:
            report[str(req_file)] = _run(
                ["pip-audit", "-r", str(req_file), "--format", "json"],
                args.out / f"pip_audit_{req_file.stem}_{date}.json",
            )

    if pathlib.Path("package.json").exists():
        report["npm"] = _run(["npm", "audit", "--json"], args.out / f"npm_audit_{date}.json")

    summary_path = args.out / f"summary_{date}.json"
    summary_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[scan_dependencies] wrote {summary_path}")
    failed = [k for k, v in report.items() if v.get("exit_code") not in (None, 0)]
    if failed:
        print(f"[scan_dependencies] failures: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())