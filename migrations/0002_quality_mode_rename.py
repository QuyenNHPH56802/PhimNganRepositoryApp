"""Rename legacy quality_mode values introduced before v1.0.0.

Before Phase 11 the API stored three values:
    only_subtitle | standard_dubbing | quality_dubbing

After Phase 11 the canonical values are:
    fast | balanced | high

This migration rewrites the column. It is idempotent: a second run
performs no UPDATE because no legacy values remain.
"""

from __future__ import annotations

VERSION = "0002"

_RENAMES = {
    "only_subtitle": "fast",
    "standard_dubbing": "balanced",
    "quality_dubbing": "high",
}


def up(db):
    from sqlalchemy import text

    stmt = text(
        "UPDATE projects SET quality_mode = :new "
        "WHERE quality_mode = :old"
    )
    for old, new in _RENAMES.items():
        db.execute(stmt, {"old": old, "new": new})


def down(db):
    from sqlalchemy import text

    reverses = {new: old for old, new in _RENAMES.items()}
    stmt = text(
        "UPDATE projects SET quality_mode = :old "
        "WHERE quality_mode = :new"
    )
    for new, old in reverses.items():
        db.execute(stmt, {"new": new, "old": old})
