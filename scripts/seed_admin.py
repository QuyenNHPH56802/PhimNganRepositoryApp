"""Seed an admin user (development convenience)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "apps" / "api" / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "apps" / "api" / "python"))

from sqlalchemy.orm import Session  # noqa: E402

from translator_api.db import get_engine  # noqa: E402
from translator_api.models import User  # noqa: E402
from translator_api.auth import hash_password  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    engine = get_engine()
    with Session(engine) as session:
        user = session.query(User).filter_by(email=args.email).one_or_none()
        if user is None:
            user = User(email=args.email, password_hash=hash_password(args.password), is_admin=True)
            session.add(user)
        else:
            user.password_hash = hash_password(args.password)
            user.is_admin = True
        session.commit()
    print(f"admin user upserted: {args.email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())