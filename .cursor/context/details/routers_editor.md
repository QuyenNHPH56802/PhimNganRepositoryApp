# routers_editor.py

**Path:** `apps/api/python/translator_api/routers_editor.py`

## Purpose
Per-project data read endpoints (transcript / translation / speakers / voices / subtitles / audio). Used by the editor workspace.

## Key Responsibilities
- Serve real-time data to editor UI
- Return HTTP 404 when artifacts not ready yet
- Provide presign URLs for uploads (music, voice references)
- Handle segment-level CRUD operations

## Dependencies
- `translator_api.auth_dependency` - Authentication
- `translator_api.db` - Database session
- `translator_api.models` - ORM models (Transcript, Translation, Speaker, etc.)
- `translator_api.security.identity` - User identity management
- `translator_api.storage_pkg` - File storage abstraction
- `translator_api.providers.tts.edge` - Edge TTS provider
- `translator_api.providers.subtitle.cps_wrapper` - Subtitle generation

## Key Endpoints
- `POST /projects/{project_id}/music:presign` - Presign music upload
- `GET /projects/{project_id}/transcript` - Get transcript segments
- `GET /projects/{project_id}/translation` - Get translation segments
- `GET /projects/{project_id}/speakers` - List speakers
- `GET /projects/{project_id}/voices` - List voice profiles
- `GET /projects/{project_id}/subtitles` - Get subtitle tracks
- `GET /projects/{project_id}/audio` - Get audio tracks

## Design Patterns
- **Single-user mode**: `_require_viewer()` checks project exists
- **Lazy loading**: Returns 404 when artifacts not ready
- **Pydantic schemas**: `_Segment`, `_ListResponse` for type safety

## Recent Changes
- Added presign music upload endpoint
- Integrated CPS subtitle wrapper
- Added Edge TTS provider support

## Testing Notes
- All endpoints require valid project_id
- Check 404 handling when artifacts missing
- Verify presign URL expiration logic

## Related Files
- Frontend: `apps/web/app/projects/[id]/workspace/page.tsx`
- Worker: `apps/worker/python/translator_worker/activities_phase3.py`
- Models: `apps/api/python/translator_api/models/*.py`
