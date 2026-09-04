"""Add indexes for foreign keys to improve query performance.

Revision ID: 003_add_indexes
Revises: 0005_phase5_voice_profile_columns
Create Date: 2026-09-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_indexes'
down_revision = '0005_phase5_voice_profile_columns'
branch_labels = None
depends_on = None


def upgrade():
    """Add indexes for foreign keys."""
    
    # Assets table - no deleted_at column exists
    op.create_index(
        'ix_assets_project_id',
        'assets',
        ['project_id']
    )
    
    # Audio segments table
    op.create_index(
        'ix_audio_segments_track_id',
        'audio_segments',
        ['track_id']
    )
    
    # Translation segments table
    op.create_index(
        'ix_translation_segments_version_id',
        'translation_segments',
        ['version_id']
    )
    op.create_index(
        'ix_translation_segments_transcript_segment_id',
        'translation_segments',
        ['transcript_segment_id']
    )
    
    # Transcript segments table
    op.create_index(
        'ix_transcript_segments_version_id',
        'transcript_segments',
        ['version_id']
    )
    
    # Audio tracks table
    op.create_index(
        'ix_audio_tracks_asset_id',
        'audio_tracks',
        ['asset_id']
    )
    op.create_index(
        'ix_audio_tracks_project_id',
        'audio_tracks',
        ['project_id']
    )
    
    # Subtitle segments table (if exists)
    op.create_index(
        'ix_subtitle_segments_project_id',
        'subtitle_segments',
        ['project_id']
    )
    
    # Voice profiles
    op.create_index(
        'ix_voice_profiles_created_by',
        'voice_profiles',
        ['created_by']
    )
    
    # Workflows
    op.create_index(
        'ix_workflows_project_id',
        'workflows',
        ['project_id']
    )
    op.create_index(
        'ix_workflows_status',
        'workflows',
        ['status']
    )
    
    # Audit logs
    op.create_index(
        'ix_audit_logs_project_id',
        'audit_logs',
        ['project_id']
    )
    op.create_index(
        'ix_audit_logs_user_id',
        'audit_logs',
        ['user_id']
    )
    op.create_index(
        'ix_audit_logs_created_at',
        'audit_logs',
        ['created_at'],
        postgresql_using='btree'
    )


def downgrade():
    """Remove indexes."""
    
    op.drop_index('ix_assets_project_id')
    op.drop_index('ix_audio_segments_track_id')
    op.drop_index('ix_translation_segments_version_id')
    op.drop_index('ix_translation_segments_transcript_segment_id')
    op.drop_index('ix_transcript_segments_version_id')
    op.drop_index('ix_audio_tracks_asset_id')
    op.drop_index('ix_audio_tracks_project_id')
    op.drop_index('ix_subtitle_segments_project_id')
    op.drop_index('ix_voice_profiles_created_by')
    op.drop_index('ix_workflows_project_id')
    op.drop_index('ix_workflows_status')
    op.drop_index('ix_audit_logs_project_id')
    op.drop_index('ix_audit_logs_user_id')
    op.drop_index('ix_audit_logs_created_at')
