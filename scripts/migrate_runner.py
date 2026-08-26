"""SQLite migration driver.

Extracted from `scripts/migrate.py` so the dry-run can exercise the
exact code path without a Postgres instance.
"""

from __future__ import annotations

import importlib
import pathlib
import sys
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT / "migrations"


def apply_sqlite(db_path: pathlib.Path) -> None:
    import sqlite3

    sys.path.insert(0, str(MIGRATIONS_DIR))
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_versions (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )
    conn.commit()

    cur.execute("SELECT version FROM schema_versions")
    applied = {row[0] for row in cur.fetchall()}

    for path in sorted(MIGRATIONS_DIR.glob("*.py")):
        stem = path.stem
        version = stem.split("_", 1)[0]
        if version in applied:
            continue
        mod = importlib.import_module(stem)
        mod.up(_SqliteCursorShim(conn))
        cur.execute(
            "INSERT INTO schema_versions (version, applied_at) VALUES (?, ?)",
            (version, datetime.utcnow().isoformat()),
        )
        conn.commit()
        print(f"[migrate] applied {stem}")
    conn.close()


class _SqliteCursorShim:
    """Minimal shim wrapping sqlite3.Cursor.

    Accepts either a plain str or a `sqlalchemy.sql.expression.TextClause`
    (from `sqlalchemy.text()`) so that migrations work with both SQLite
    and PostgreSQL.
    """

    def __init__(self, conn) -> None:
        self._conn = conn

    def execute(self, statement, params=None) -> None:
        cur = self._conn.cursor()
        # Unwrap SQLAlchemy text() objects.
        sql = getattr(statement, "text", None) or statement
        if isinstance(sql, str) and params is None:
            cur.execute(sql)
        elif isinstance(sql, str):
            cur.execute(sql, params or {})
        else:
            cur.execute(str(sql), params or {})
        return cur
