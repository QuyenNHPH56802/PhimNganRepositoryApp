"""Release manager — semver bump, CHANGELOG generation, version pin."""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import subprocess
import sys


VERSION_PATH = pathlib.Path("VERSION")


def _read_version() -> str:
    return VERSION_PATH.read_text(encoding="utf-8").strip()


def _bump(version: str, kind: str) -> str:
    major, minor, patch = (int(x) for x in version.split("."))
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    if kind == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"unknown bump kind: {kind}")


def _git_log(since_tag: str) -> list[str]:
    result = subprocess.run(
        ["git", "log", "--oneline", f"{since_tag}..HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _previous_tag() -> str:
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() or "v0.0.0"


def _write_changelog(version: str, lines: list[str], out_dir: pathlib.Path) -> pathlib.Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"v{version}.md"
    body = [f"# v{version} — {dt.datetime.now().strftime('%Y-%m-%d')}", ""]
    if lines:
        body.append("## Changes")
        body.append("")
        body.extend(f"- {line}" for line in lines)
    path.write_text("\n".join(body), encoding="utf-8")
    return path


def _pin_version_in_files(version: str, files: list[pathlib.Path]) -> None:
    for path in files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        new = re.sub(r'(__version__\s*=\s*)"[^"]+"', rf'\1"{version}"', text)
        new = re.sub(r'("version"\s*:\s*)"[^"]+"', rf'\1"{version}"', new)
        if new != text:
            path.write_text(new, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bump", choices=["major", "minor", "patch"], required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("releases"))
    args = parser.parse_args()

    current = _read_version()
    new = _bump(current, args.bump)
    print(f"[release] {current} -> {new}")
    if args.dry_run:
        print("[release] dry-run, no files changed")
        return 0

    VERSION_PATH.write_text(new, encoding="utf-8")
    _pin_version_in_files(new, [
        pathlib.Path("apps/api/python/translator_api/__init__.py"),
        pathlib.Path("apps/web/sdk/package.json"),
    ])
    log = _git_log(_previous_tag())
    notes = _write_changelog(new, log, args.out)
    print(f"[release] wrote {notes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())