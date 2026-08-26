"""Migration runner — idempotent schema + data migrations.

Usage:
    python scripts/migrate.py --dry-run
    python scripts/migrate.py
    python scripts/migrate.py --target 0002
    python scripts/migrate.py --direction down --target 0001

Migrations live in `migrations/`. Each file must expose:

    VERSION = "0002"
    def up(db) -> None: ...
    def down(db) -> None: ...

`db` is a cursor shim with `.execute(text, params)`.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT / "migrations"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--target", type=str, default=None)
    parser.add_argument("--direction", choices=["up", "down"], default="up")
    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL")
    if db_url and db_url.startswith("sqlite"):
        from scripts.migrate_runner import apply_sqlite

        apply_sqlite(Path(db_url.replace("sqlite:///", "")))
        return 0

    sys.path.insert(0, str(ROOT / "apps" / "api" / "python"))
    sys.path.insert(0, str(ROOT / "packages" / "shared" / "python"))
    sys.path.insert(0, str(MIGRATIONS_DIR))

    from translator_api.db import get_engine
    from sqlalchemy.orm import sessionmaker

    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as session:
        session.execute(
            __import__("sqlalchemy").text(
                "CREATE TABLE IF NOT EXISTS schema_versions (version TEXT PRIMARY KEY, applied_at TIMESTAMP NOT NULL)"
            )
        )
        session.commit()

        rows = session.execute(
            __import__("sqlalchemy").text("SELECT version FROM schema_versions")
        ).all()
        applied = {row[0] for row in rows}

        for path in sorted(MIGRATIONS_DIR.glob("*.py")):
            stem = path.stem
            version = stem.split("_", 1)[0]
            mod = __import__(stem)

            if args.direction == "up":
                if version in applied:
                    continue
                if args.target and version > args.target:
                    break
                print(f"[migrate] applying {stem}")
                if not args.dry_run:
                    mod.up(session)
                    session.execute(
                        __import__("sqlalchemy").text(
                            "INSERT INTO schema_versions (version, applied_at) VALUES (:v, CURRENT_TIMESTAMP)"
                        ),
                        {"v": version},
                    )
                    session.commit()
            else:
                if version not in applied:
                    continue
                if args.target and version < args.target:
                    continue
                print(f"[migrate] reverting {stem}")
                if not args.dry_run:
                    mod.down(session)
                    session.execute(
                        __import__("sqlalchemy").text(
                            "DELETE FROM schema_versions WHERE version=:v"
                        ),
                        {"v": version},
                    )
                    session.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
