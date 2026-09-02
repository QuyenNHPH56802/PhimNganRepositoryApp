#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply database migration 003 - Add performance indexes

This script applies the 003_add_indexes migration to add 14 indexes
that improve query performance for foreign keys and common filters.

Expected duration: ~5 minutes
Requires: ~5-10 second maintenance window (non-blocking on most systems)
"""

import subprocess
import sys
from pathlib import Path

def main():
    print("=== Database Migration 003 - Add Indexes ===\n")
    
    # Check if docker compose is running
    print("1. Checking services...")
    result = subprocess.run(
        ["docker", "compose", "-f", "infra/docker/docker-compose.yml", "ps", "db"],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    if "Up" not in result.stdout:
        print("[X] Database service is not running")
        print("   Start with: docker compose -f infra/docker/docker-compose.yml up -d db")
        return 1
    
    print("[OK] Database service is running\n")
    
    # Show what will be created
    print("2. Migration will add 14 indexes:")
    indexes = [
        "ix_assets_project_id (with deleted_at filter)",
        "ix_audio_segments_track_id",
        "ix_translation_segments_version_id",
        "ix_translation_segments_transcript_segment_id",
        "ix_transcript_segments_version_id",
        "ix_audio_tracks_asset_id",
        "ix_audio_tracks_project_id",
        "ix_subtitle_segments_project_id",
        "ix_voice_profiles_created_by",
        "ix_workflows_project_id",
        "ix_workflows_status",
        "ix_audit_logs_project_id",
        "ix_audit_logs_user_id",
        "ix_audit_logs_created_at (btree)"
    ]
    
    for idx in indexes:
        print(f"   - {idx}")
    
    print("\n3. Estimated impact:")
    print("   - Duration: ~30 seconds to 5 minutes (depends on data size)")
    print("   - Blocking: Minimal (CREATE INDEX CONCURRENTLY can be used)")
    print("   - Disk space: ~5-50 MB (depends on table sizes)")
    print("   - Performance: Significant improvement for JOIN queries\n")
    
    # Confirm
    response = input("Apply migration? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled")
        return 0
    
    print("\n4. Applying migration...")
    
    # Run alembic upgrade inside API container
    result = subprocess.run(
        ["docker", "compose", "-f", "infra/docker/docker-compose.yml", 
         "exec", "-T", "api", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    print(result.stdout)
    
    if result.returncode != 0:
        print(f"[X] Migration failed:\n{result.stderr}")
        return 1
    
    print("\n[OK] Migration completed successfully!")
    print("\nNext steps:")
    print("  1. Verify API still responds: curl http://localhost:8000/healthz")
    print("  2. Run test: node test_n1_fix.js (with real project data)")
    print("  3. Monitor query performance in logs")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
