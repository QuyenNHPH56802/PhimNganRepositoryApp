# Smoke Test Suite

Quick verification tests for the Translator API and Web frontend.

## Quick Start

```powershell
# Terminal 1: Start backend
cd apps/api/python
uv run fastapi dev translator_api/main.py

# Terminal 2: Start frontend
cd apps/web
npm run dev

# Terminal 3: Run all smoke tests
cd ../..
.\run_smoke.cmd
```

## Individual Test Files

### Core Tests (must pass)
- **smoke_tier1.js** — Health checks, project CRUD, asset upload/delete
- **smoke_tier1_api.js** — Backend APIs accessed via Next.js proxy routes
- **smoke_tier1_content.js** — SSR rendering verification for all pages
- **smoke_workspace_pages.js** — Workspace SSR, SSE streams, video proxy
- **smoke_panel_apis.js** — Transcript, translation, speaker, voice, subtitle, audio APIs

### Data-Dependent Tests (may fail without workflow execution)
- **smoke_upload_flow.js** — Full upload flow including workflow creation
- **smoke_render_tts.js** — TTS generation, subtitle, audio, and video rendering

## Test Output

Tests print to console with ✓/✗ status markers:
```
✓ GET /healthz                 200  {"ok":true}
✓ GET /projects                200  {"items":[],"total":0}
✗ DELETE /workflows/{id}       404  (expected: endpoint not implemented)
```

Exit codes:
- `0` = all tests passed
- `1` = one or more tests failed

## Prerequisites

- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:3000`
- Node.js (for running test scripts)

## Test Coverage

**✅ Verified:**
- API health and routing
- Database CRUD operations
- File upload and storage
- SSR page rendering
- Error handling (404, 400, 500)
- Empty state handling
- Video streaming and proxying

**⚠️ Not Tested (requires worker):**
- Workflow execution (transcribe, translate, TTS, render)
- Temporal task queue integration
- Provider calls (WhisperX, Pyannote, Edge TTS, FFmpeg)

## Troubleshooting

**Tests fail immediately:**
- Check backend is running: `curl http://localhost:8000/healthz`
- Check frontend is running: `curl http://localhost:3000/api/healthz`

**"Cannot find module":**
- Tests use Node.js built-in `http` module only (no npm install needed)

**"ECONNREFUSED":**
- Backend or frontend not running
- Wrong port (should be 8000 for API, 3000 for web)

**All panel APIs return 500:**
- Fixed in current version (logger import added)
- Update `apps/api/python/translator_api/routers_editor.py`

## Report

Full test report and bug fixes documented in `docs/TEST_BUGS.md`.
