"""Initial schema migration placeholder (Phase 10)."""

VERSION = "0001"


def up(db):
    # Initial schema is created by `translator_api.db.create_all()`. This
    # migration exists as the baseline for the migration runner.
    return None


def down(db):
    # Drop the schema_versions table only; production data is not managed
    # by this migration.
    db.execute(__import__("sqlalchemy").text("DROP TABLE IF EXISTS schema_versions"))