"""Phase 2 baseline schema.

Originally recreated the schema using Base.metadata. The migration chain
0001 → 0002 → 0003 was inconsistent (0002 dropped alembic_version before 0003
ran), and the resulting "drop everything then recreate" sequence is no longer
safe once data exists. 0003 is now a no-op marker: the Phase 1 baseline
created by 0001 is the canonical schema, and 0004 only adds indexes on top of
it.
"""

from __future__ import annotations

from alembic import op

revision = "0003_phase2_create_schema"
down_revision = "0002_phase2_reset"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
