"""Generate CycloneDX SBOM for Python and Node."""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import shutil
import subprocess


def _run(cmd: list[str], output: pathlib.Path) -> bool:
    binary = shutil.which(cmd[0])
    if not binary:
        return False
    completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
    output.write_text(completed.stdout, encoding="utf-8")
    return completed.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("outputs/sbom"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    date = dt.datetime.now().strftime("%Y%m%d")

    ok = True
    if pathlib.Path("requirements.txt").exists():
        ok &= _run(["cyclonedx-py", "requirements", "-o", str(args.out / f"python_{date}.cdx.json")], args.out / f"python_{date}.cdx.json")
    if pathlib.Path("package.json").exists():
        ok &= _run(["cyclonedx-npm", "--output-format", "JSON", "--output-file", str(args.out / f"node_{date}.cdx.json")], args.out / f"node_{date}.cdx.json")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())