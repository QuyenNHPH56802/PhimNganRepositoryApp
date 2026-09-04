"""Add indexes for foreign keys (fixed to match actual schema).

Revision ID: 003_add_indexes_fixed
Revises: 0005_phase5_voice_cols
Create Date: 2026-09-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_indexes_fixed'
down_revision = '0005_phase5_voice_cols'
branch_labels = None
depends_on = None


def upgrade():
    """Add indexes for foreign keys that actually exist."""
    
    # Assets table
    op.create_index(
        'ix_assets_project_id',
        'assets',
        ['project_id'],
        if_not_exists=True
    )
    
    # Audio segments table
    op.create_index(
        'ix_audio_segments_audio_track_id',
        'audio_segments',
        ['audio_track_id'],
        if_not_exists=True
    )
    
    # Translation segments table
    op.create_index(
        'ix_translation_segments_translation_version_id',
        'translation_segments',
        ['translation_version_id'],
        if_not_exists=True
    )
    op.create_index(
        'ix_translation_segments_transcript_segment_id',
        'translation_segments',
        ['transcript_segment_id'],
        if_not_exists=True
    )
    
    # Transcript segments table
    op.create_index(
        'ix_transcript_segments_transcript_id',
        'transcript_segments',
        ['transcript_id'],
        if_not_exists=True
    )
    
    # Audio tracks table
    op.create_index(
        'ix_audio_tracks_asset_id',
        'audio_tracks',
        ['asset_id'],
        if_not_exists=True
    )
    
    # Subtitle segments table
    op.create_index(
        'ix_subtitle_segments_subtitle_track_id',
        'subtitle_segments',
        ['subtitle_track_id'],
        if_not_exists=True
    )
    op.create_index(
        'ix_subtitle_segments_translation_segment_id',
        'subtitle_segments',
        ['translation_segment_id'],
        if_not_exists=True
    )
    
    # Voice profiles
    op.create_index(
        'ix_voice_profiles_speaker_id',
        'voice_profiles',
        ['speaker_id'],
        if_not_exists=True
    )
    
    # Workflows
    op.create_index(
        'ix_workflows_project_id',
        'workflows',
        ['project_id'],
        if_not_exists=True
    )
    op.create_index(
        'ix_workflows_status',
        'workflows',
        ['status'],
        if_not_exists=True
    )
    
    # Audit logs
    op.create_index(
        'ix_audit_logs_project_id',
        'audit_logs',
        ['project_id'],
        if_not_exists=True
    )
    op.create_index(
        'ix_audit_logs_user_id',
        'audit_logs',
        ['user_id'],
        if_not_exists=True
    )
    op.create_index(
        'ix_audit_logs_created_at',
        'audit_logs',
        ['created_at'],
        postgresql_using='btree',
        if_not_exists=True
    )


def downgrade():
    """Remove indexes."""
    
    op.drop_index('ix_assets_project_id', if_exists=True)
    op.drop_index('ix_audio_segments_audio_track_id', if_exists=True)
    op.drop_index('ix_translation_segments_translation_version_id', if_exists=True)
    op.drop_index('ix_translation_segments_transcript_segment_id', if_exists=True)
    op.drop_index('ix_transcript_segments_transcript_id', if_exists=True)
    op.drop_index('ix_audio_tracks_asset_id', if_exists=True)
    op.drop_index('ix_subtitle_segments_subtitle_track_id', if_exists=True)
    op.drop_index('ix_subtitle_segments_translation_segment_id', if_exists=True)
    op.drop_index('ix_voice_profiles_speaker_id', if_exists=True)
    op.drop_index('ix_workflows_project_id', if_exists=True)
    op.drop_index('ix_workflows_status', if_exists=True)
    op.drop_index('ix_audit_logs_project_id', if_exists=True)
    op.drop_index('ix_audit_logs_user_id', if_exists=True)
    op.drop_index('ix_audit_logs_created_at', if_exists=True)
