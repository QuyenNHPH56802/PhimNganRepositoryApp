"""Add is_admin column to users table.

Revision ID: 004_add_users_is_admin
Revises: 003_add_indexes
Create Date: 2026-09-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_users_is_admin'
down_revision = '003_add_indexes_fixed'
branch_labels = None
depends_on = None


def upgrade():
    """Add is_admin column to users table."""
    op.add_column(
        'users',
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.text('true'))
    )


def downgrade():
    """Remove is_admin column from users table."""
    op.drop_column('users', 'is_admin')
