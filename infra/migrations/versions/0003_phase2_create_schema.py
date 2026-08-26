"""Phase 2 baseline schema.

Creates the full schema from Base.metadata using raw SQL extracted by
Alembic. Hand-authoring the DDL keeps the migration deterministic and
removes dependency on autogenerate drift. The order matches the FK graph
so that Postgres accepts the statements in one transaction.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_phase2_create_schema"
down_revision = "0002_phase2_reset"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("source_language", sa.String(8), nullable=False, server_default="zh"),
        sa.Column("target_language", sa.String(8), nullable=False, server_default="vi"),
        sa.Column("quality_mode", sa.String(32), nullable=False, server_default="standard_dubbing"),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("language_profile", sa.String(32), nullable=False, server_default="zh-vi"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "project_members",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("role", sa.String(16), nullable=False, server_default="editor"),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "project_settings",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("genre", sa.String(64)),
        sa.Column("style_preset", sa.String(32)),
        sa.Column("subtitle_mode", sa.String(32)),
        sa.Column("accent_preference", sa.String(32)),
        sa.Column("audio_mode", sa.String(32)),
        sa.Column("music_level", sa.String(16)),
        sa.Column("dubbing_overrides", postgresql.JSONB),
    )

    op.create_table(
        "voice_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("provider_id", sa.String(64), nullable=False),
        sa.Column("model_id", sa.String(128), nullable=False),
        sa.Column("voice_id", sa.String(128), nullable=False),
        sa.Column("default_accent", sa.String(32)),
        sa.Column("reference_audio_key", sa.String(1024)),
        sa.Column("reference_audio_hash", sa.String(64)),
        sa.Column("consent_status", sa.String(32), nullable=False),
        sa.Column("consent_evidence_key", sa.String(1024)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "character_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("gender", sa.String(16)),
        sa.Column("age_group", sa.String(16)),
        sa.Column("role", sa.String(64)),
        sa.Column("preferred_pronouns", postgresql.JSONB),
        sa.Column("preferred_honorifics", postgresql.JSONB),
        sa.Column(
            "default_voice_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("voice_profiles.id"),
        ),
    )

    op.create_table(
        "character_aliases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("character_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("character_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alias", sa.String(255), nullable=False),
        sa.Column("locale", sa.String(16)),
        sa.Column("source_pattern", sa.String(255)),
    )

    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("storage_key", sa.String(1024), nullable=False, unique=True),
        sa.Column("mime", sa.String(128)),
        sa.Column("size", sa.BigInteger),
        sa.Column("duration_ms", sa.BigInteger),
        sa.Column("probe", postgresql.JSONB),
        sa.Column("checksum_sha256", sa.String(64)),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
    )

    op.create_table(
        "transcripts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("language_detected", sa.String(16)),
        sa.Column("language_profile", sa.String(32)),
        sa.Column("model_id", sa.String(128)),
        sa.Column("signature", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("asset_id", "signature", name="uq_transcripts_asset_signature"),
    )

    op.create_table(
        "transcript_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("transcript_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("idx", sa.Integer, nullable=False),
        sa.Column("start_ms", sa.Integer, nullable=False),
        sa.Column("end_ms", sa.Integer, nullable=False),
        sa.Column("raw_text", sa.Text, nullable=False),
        sa.Column("normalized_text", sa.Text),
        sa.Column("quality_flags", postgresql.JSONB),
        sa.Column("speaker_label", sa.String(64)),
    )

    op.create_table(
        "transcript_words",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transcript_segments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("idx", sa.Integer, nullable=False),
        sa.Column("text", sa.String(255), nullable=False),
        sa.Column("start_ms", sa.Integer, nullable=False),
        sa.Column("end_ms", sa.Integer, nullable=False),
        sa.Column("confidence", sa.Float),
    )

    op.create_table(
        "speakers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_label", sa.String(64), nullable=False),
        sa.Column("character_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("character_profiles.id")),
        sa.Column("display_name", sa.String(255)),
        sa.Column("gender", sa.String(16)),
        sa.Column("age_group", sa.String(16)),
    )

    op.create_table(
        "speaker_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("speaker_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("speakers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_ms", sa.Integer, nullable=False),
        sa.Column("end_ms", sa.Integer, nullable=False),
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transcript_segments.id")),
        sa.Column("confidence", sa.Float),
    )

    op.create_table(
        "glossaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
    )

    op.create_table(
        "glossary_terms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("glossary_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("glossaries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chinese", sa.Text, nullable=False),
        sa.Column("vietnamese", sa.Text, nullable=False),
        sa.Column("category", sa.String(64)),
        sa.Column("rule", sa.String(64)),
        sa.Column("priority", sa.Integer, server_default="0"),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.UniqueConstraint("glossary_id", "chinese", name="uq_glossary_terms_zh"),
    )

    op.create_table(
        "translation_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transcript_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("provider_id", sa.String(64), nullable=False),
        sa.Column("model_id", sa.String(128), nullable=False),
        sa.Column("prompt_version", sa.String(64), nullable=False),
        sa.Column("glossary_snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("glossaries.id")),
        sa.Column("character_bible_snapshot", postgresql.JSONB),
        sa.Column("style_preset", sa.String(32)),
        sa.Column("signature", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.UniqueConstraint("project_id", "transcript_id", "version", name="uq_translation_versions"),
        sa.UniqueConstraint("transcript_id", "signature", name="uq_translation_signature"),
    )

    op.create_table(
        "translation_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("translation_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("translation_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transcript_segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transcript_segments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("display_text", sa.Text, nullable=False),
        sa.Column("tts_text", sa.Text),
        sa.Column("applied_glossary_terms", postgresql.JSONB),
        sa.Column("applied_aliases", postgresql.JSONB),
        sa.Column("qa_status", sa.String(16)),
        sa.Column("qa_issues", postgresql.JSONB),
        sa.Column("confidence", sa.Float),
    )

    op.create_table(
        "audio_tracks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("storage_key", sa.String(1024), nullable=False),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("sample_rate", sa.Integer),
        sa.Column("channels", sa.Integer),
    )

    op.create_table(
        "audio_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("audio_track_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audio_tracks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_ms", sa.Integer, nullable=False),
        sa.Column("end_ms", sa.Integer, nullable=False),
        sa.Column("storage_key", sa.String(1024), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("signature", sa.String(128), nullable=False),
    )

    op.create_table(
        "tts_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("voice_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("voice_profiles.id"), nullable=False),
        sa.Column("translation_segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("translation_segments.id")),
        sa.Column("audio_segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audio_segments.id")),
        sa.Column("signature", sa.String(128), nullable=False),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("sample_rate", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "subtitle_tracks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("language_code", sa.String(8)),
        sa.Column("format", sa.String(8), nullable=False),
    )

    op.create_table(
        "subtitle_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("subtitle_track_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subtitle_tracks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("idx", sa.Integer, nullable=False),
        sa.Column("start_ms", sa.Integer, nullable=False),
        sa.Column("end_ms", sa.Integer, nullable=False),
        sa.Column("display_text", sa.Text, nullable=False),
        sa.Column("translation_segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("translation_segments.id")),
        sa.Column("signature", sa.String(128), nullable=False),
    )

    op.create_table(
        "workflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("temporal_workflow_id", sa.String(255), nullable=False),
        sa.Column("temporal_run_id", sa.String(255), nullable=False),
        sa.Column("quality_mode", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="processing"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", postgresql.JSONB),
        sa.UniqueConstraint("temporal_workflow_id", "temporal_run_id", name="uq_workflows_temporal"),
    )

    op.create_table(
        "workflow_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("attempt", sa.Integer, server_default="0"),
        sa.Column("progress_pct", sa.Integer, server_default="0"),
        sa.Column("progress_message", sa.Text),
        sa.Column("artifact_signature", sa.String(128)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "render_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("output_storage_key", sa.String(1024)),
        sa.Column("progress_pct", sa.Integer, server_default="0"),
        sa.Column("validation", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "exports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("render_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("render_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("format", sa.String(8), nullable=False),
        sa.Column("storage_key", sa.String(1024), nullable=False),
        sa.Column("size", sa.BigInteger),
        sa.Column("checksum_sha256", sa.String(64)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("signed_url_expires_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("render_job_id", "format", name="uq_exports_render_format"),
    )

    op.create_table(
        "ocr_detections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("bbox", postgresql.JSONB, nullable=False),
        sa.Column("frame_ts_ms", sa.Integer, nullable=False),
        sa.Column("confidence", sa.Float),
        sa.Column("model_id", sa.String(128)),
        sa.Column("language", sa.String(8)),
    )

    op.create_table(
        "text_removal_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("strategy", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("output_storage_key", sa.String(1024)),
        sa.Column("bbox_payload", postgresql.JSONB),
    )

    op.create_table(
        "provider_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("provider_kind", sa.String(32), nullable=False),
        sa.Column("provider_id", sa.String(64), nullable=False),
        sa.Column("config", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "audit_logs",
        "provider_configs",
        "text_removal_jobs",
        "ocr_detections",
        "exports",
        "render_jobs",
        "workflow_steps",
        "workflows",
        "subtitle_segments",
        "subtitle_tracks",
        "tts_segments",
        "audio_segments",
        "audio_tracks",
        "translation_segments",
        "translation_versions",
        "glossary_terms",
        "glossaries",
        "speaker_segments",
        "speakers",
        "transcript_words",
        "transcript_segments",
        "transcripts",
        "assets",
        "character_aliases",
        "character_profiles",
        "voice_profiles",
        "project_settings",
        "project_members",
        "projects",
        "users",
    ]:
        op.drop_table(table)