"""Local migration dry-run using SQLite.

Production uses PostgreSQL; this script uses SQLite so the full
migration runner can be exercised in environments without a Postgres
daemon. The SQL used by `migrations/0002_quality_mode_rename.py` is
dialect-neutral.

Usage:
    python scripts/migrate_dryrun.py
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _seed(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE projects (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            quality_mode TEXT NOT NULL
        )
        """
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS schema_versions (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    rows = [
        ("p1", "A", "only_subtitle"),
        ("p2", "B", "standard_dubbing"),
        ("p3", "C", "quality_dubbing"),
        ("p4", "D", "balanced"),
    ]
    cur.executemany(
        "INSERT INTO projects (id, title, quality_mode) VALUES (?, ?, ?)", rows
    )
    conn.commit()
    conn.close()


def _run_migrations(tmpdir: Path) -> None:
    sys.path.insert(0, str(ROOT / "apps" / "api" / "python"))
    sys.path.insert(0, str(ROOT / "packages" / "shared" / "python"))
    sys.path.insert(0, str(ROOT / "scripts"))
    sys.path.insert(0, str(ROOT / "migrations"))

    from migrate_runner import apply_sqlite  # type: ignore[import]

    apply_sqlite(tmpdir / "dryrun.db")


def main() -> int:
    tmpdir = tempfile.mkdtemp()
    try:
        tmpdir_path = Path(tmpdir)
        db_path = tmpdir_path / "dryrun.db"
        _seed(db_path)
        conn = sqlite3.connect(db_path)
        before = sorted(row[0] for row in conn.execute(
            "SELECT quality_mode FROM projects ORDER BY id"
        ))
        print(f"[dryrun] BEFORE: {before}")
        conn.close()
        _run_migrations(tmpdir_path)
        conn = sqlite3.connect(db_path)
        after = sorted(row[0] for row in conn.execute(
            "SELECT quality_mode FROM projects ORDER BY id"
        ))
        print(f"[dryrun] AFTER:  {after}")
        versions = [row[0] for row in conn.execute("SELECT version FROM schema_versions ORDER BY version")]
        print(f"[dryrun] applied: {versions}")
        conn.close()
        expected = ["balanced", "balanced", "fast", "high"]
        if after != expected:
            print(f"[dryrun] FAIL expected {expected}", file=sys.stderr)
            return 1
        if "0002" not in versions:
            print("[dryrun] FAIL migration 0002 not applied", file=sys.stderr)
            return 1
        _run_migrations(tmpdir_path)
        conn = sqlite3.connect(db_path)
        again = sorted(row[0] for row in conn.execute(
            "SELECT quality_mode FROM projects ORDER BY id"
        ))
        conn.close()
        assert again == after, "second run altered data"
        print("[dryrun] idempotent OK")
        return 0
    finally:
        try:
            shutil.rmtree(tmpdir)
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
