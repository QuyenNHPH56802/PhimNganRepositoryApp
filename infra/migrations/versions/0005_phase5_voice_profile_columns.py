"""Phase 5 schema fixes.

Adds missing columns to voice_profiles table to match the ORM model:
- speaker_id (FK to speakers, ON DELETE SET NULL)
- embedding_storage_key (varchar 1024)
- updated_at (timestamptz, default now())
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_phase5_voice_cols"
down_revision = "0004_phase4_rbac_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "voice_profiles",
        sa.Column("speaker_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("speakers.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "voice_profiles",
        sa.Column("embedding_storage_key", sa.String(1024), nullable=True),
    )
    op.add_column(
        "voice_profiles",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("voice_profiles", "updated_at")
    op.drop_column("voice_profiles", "embedding_storage_key")
    op.drop_column("voice_profiles", "speaker_id")
