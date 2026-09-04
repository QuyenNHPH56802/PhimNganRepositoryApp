# Project State - L1 Index

**Last Updated:** 2026-09-04 08:15 AM
**Branch:** develop (ahead 2 commits)
**Status:** Phase 4 Complete, Ready for Next Developer

---

## 📋 Quick Overview

| Metric | Value |
|--------|-------|
| Total Files Modified | 164+ |
| Untracked Files | 9 |
| Last Commit | Security & workflow fixes |
| Active Features | Voice cloning, TTS providers, workflow optimization |
| Phase 4 Status | ✅ Complete (5/5 technical debt items resolved) |

---

## 🗂️ Core Module Index

### API Layer (`apps/api/python/translator_api/`)

| File | Purpose | Last Change |
|------|---------|-------------|
| `routers_editor.py` | Main editor APIs for workspace | **Modified 2026-09-04** (pagination + N+1 fix) |
| `routers_admin.py` | Admin panel endpoints | Modified |
| `routers_providers.py` | Provider management APIs | **NEW** - Untracked |
| `main.py` | FastAPI application entry | Modified |
| `auth_dependency.py` | Authentication & authorization | Modified |
| `db.py` | Database connection & session | Modified |

### Worker Layer (`apps/worker/python/translator_worker/`)

| File | Purpose | Last Change |
|------|---------|-------------|
| `activities_phase3.py` | TTS & Translation activities | **Modified 2026-09-04** (normalize_chinese implemented) |
| `activities_phase4.py` | Audio mixing & export | Modified |
| `activities_voice_clone.py` | Voice cloning workflows | Modified |
| `activities_providers.py` | ASR, alignment, diarization | **Modified 2026-09-04** (alignment logging) |
| `activities_cache.py` | Redis cache with TTL policies | **Modified 2026-09-04** (per-artifact TTL) |
| `workflows_impl.py` | Main workflow orchestration | Modified |
| `main.py` | Temporal worker entry | Modified |

### Web Layer (`apps/web/`)

| File | Purpose | Last Change |
|------|---------|-------------|
| `app/projects/[id]/workspace/page.tsx` | Main workspace UI | Modified |
| `app/projects/[id]/quality-mode/page.tsx` | Quality control UI | Modified |
| `components/panels/AudioPanel.tsx` | Audio controls panel | Modified |
| `components/panels/RenderPanel.tsx` | Render settings panel | Modified |
| `components/panels/ProgressPanel.tsx` | Progress tracking UI | **NEW** - Untracked |
| `lib/useWorkflowStream.ts` | Workflow SSE streaming hook | Modified |
| `lib/useAudioMixer.ts` | Audio mixing utilities | **NEW** - Untracked |

### Providers (`apps/api/python/translator_api/providers/`)

| Module | Purpose | Status |
|--------|---------|--------|
| `tts/*.py` | TTS providers (Azure, Google, ElevenLabs, MeloTTS, VieNeu, VietVoice, CosyVoice, Qwen3) | Modified |
| `translate/*.py` | Translation providers (Claude, Gemini, OpenAI, LocalLLM, Passthrough) | Modified |
| `voice_clone/*.py` | Voice cloning (CosyVoice, VieNeu) | Modified |
| `ocr/*.py` | OCR providers (CRAFT, EasyOCR, Paddle) | Modified |
| `text_removal/*.py` | Text removal (LAMA, InpaintAnytime, OpenCV) | Modified |
| `asr/whisperx_provider.py` | Speech recognition | Modified |
| `diarize/pyannote_provider.py` | Speaker diarization | Modified |

### Database (`infra/migrations/versions/`)

| Migration | Purpose | Status |
|-----------|---------|--------|
| `003_add_indexes_fixed.py` | Index optimization | **NEW** - Untracked |
| `004_add_users_is_admin.py` | Admin flag migration | **NEW** - Untracked |
| `0005_phase5_voice_profile_columns.py` | Voice profile schema | Modified |

---

## 📊 Change Summary by Category

### Security & Auth
- ✅ `security/*.py` - CSRF, RBAC, session, identity, consent
- ✅ `auth_dependency.py` - Authentication flow

### Observability
- ✅ `observability/*.py` - Logging, metrics, tracing, error reporting

### Storage
- ✅ `storage_pkg/*.py` - S3, local, cache implementations

### Middleware
- ✅ `middleware/shedder.py` - Load shedding

---

## 🚀 Recent Changes Highlights

1. **Security hardening** - CSRF, RBAC, session management
2. **Voice cloning** - CosyVoice + VieNeu integration
3. **TTS providers** - Multiple provider support
4. **Workflow fixes** - See `WORKFLOW_FIX_SUMMARY.md`
5. **UI improvements** - Progress panel, audio mixer
6. **Database migrations** - Indexes + admin flag

---

## 📝 Untracked Files to Review

**Documentation (Ready to commit):**
- `PHASE_5_PLAN.md` - **NEW** - Phase 5 UX polish plan (322 lines)
- `PHASE_6_FUTURE_FEATURES.md` - **NEW** - Future features roadmap (458 lines)
- `NEXT_STEPS.md` - **NEW** - Developer onboarding guide (321 lines)
- `WORKFLOW_FIX_SUMMARY.md` - Workflow documentation
- `PHASE_4_COMPLETION_REPORT.md` - Phase 4 completion details (410 lines)

**Context System (Ready to commit):**
- `.cursor/rules/` - ContextForge rules
- `.cursor/context/` - Project memory system (PROJECT_STATE, TASK_PROGRESS, DECISIONS)

**Code (Ready to commit):**
- `apps/api/python/translator_api/routers_providers.py` - Provider routes
- `apps/api/python/translator_api/routers_workflow_cancel.py` - Workflow cancel endpoint
- `apps/web/components/panels/ProgressPanel.tsx` - Progress UI ✅
- `apps/web/components/ErrorBoundary.tsx` - Error handling ✅
- `apps/web/lib/useAudioMixer.ts` - Audio mixer hook ✅
- `apps/web/app/api/error-report/route.ts` - Error reporting ✅
- `apps/web/playwright.config.ts` - E2E test config ✅
- `apps/web/tests/` - E2E test suite (2 spec files) ✅

**Testing:**
- `test_provider_selection.md` - Provider test docs

**Local data (DO NOT COMMIT):**
- `.local-storage/projects/` - Local project storage (222 files)

---

## 🔗 L2 Detail Files

For detailed analysis of specific modules:
- `details/routers_editor.md` - Editor API details
- `details/activities_phase3.md` - TTS workflow details
- `details/workspace_page.md` - Workspace UI details
- *(Create more as needed)*

---

**Auto-updated by AI Agent**
**Rules:** `.cursor/rules/contextforge.md`
