"""Phase 4 RBAC baseline.

Adds an index on project_members(user_id) to speed up lookup-by-user, and a
secondary index on project_members(role) for auditor queries. Schema is
unchanged; the migration is data-only.
"""

from __future__ import annotations

from alembic import op

revision = "0004_phase4_rbac_indexes"
down_revision = "0003_phase2_create_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_project_members_user_id", "project_members", ["user_id"])
    op.create_index("ix_project_members_role", "project_members", ["role"])


def downgrade() -> None:
    op.drop_index("ix_project_members_role", table_name="project_members")
    op.drop_index("ix_project_members_user_id", table_name="project_members")