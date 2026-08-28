# PHASE 0 AUDIT REPORT — China-VNE

> Read-only audit. No code changes. No refactor. No new pipeline.
> Date: 2026-08-27
> Repo: `C:\Users\QUYÊN\Desktop\Translator`
> Per request: STOP after Phase 0.

---

## PHASE: 0 — AUDIT
## STATUS: COMPLETE

---

## 1. CURRENT FRONTEND

### File structure (apps/web, source only)

| Path | Lines | Status |
|---|---|---|
| `app/layout.tsx` | 22 | Inline-style shell, 4 hard-coded nav links, no workspace shell |
| `app/page.tsx` | 54 | Phase 1 scaffold dashboard, inline styles |
| `app/projects/new/page.tsx` | 63 | Phase 1 form, posts directly to API |
| `app/projects/[id]/page.tsx` | 5 | Just renders `ProjectDetailClient` |
| `app/projects/[id]/ProjectDetailClient.tsx` | 92 | Phase 1 polling loop, calls wrong endpoint `/workflows/{projectId}` instead of `/workflows/{workflow_id}` |
| `app/projects/[id]/upload/page.tsx` | 47 | Phase 1 presigned PUT upload, no drag/drop, no progress bar, no retry |
| `app/projects/[id]/audit/page.tsx` | 69 | Uses `NEXT_PUBLIC_API_BASE` (`/api`); not the env-var `NEXT_PUBLIC_API_BASE_URL` used elsewhere |
| `app/projects/[id]/quality-mode/page.tsx` | 48 | POSTs `/api/projects/:id/quality-mode`; no Next.js route exists at `/api/projects/...` |
| `app/projects/[id]/ProjectDetailClient.tsx` | 92 | Polling every 5 s; polls status only when workflow exists |
| `app/workflows/[id]/page.tsx` | 59 | SSE via `useWorkflowStream` → calls `/api/workflows/{id}/events`; no Next.js route exists |
| `app/admin/layout.tsx` | 15 | Tailwind sidebar with 3 links (audit/voice/dataset) |
| `app/admin/page.tsx` | 11 | "Admin overview" placeholder |
| `app/admin/audit/page.tsx` | 67 | Calls `/api/admin/audit-logs`; no Next.js route exists |
| `app/admin/voice/page.tsx` | 83 | Calls `/api/admin/voice-profiles`; no Next.js route exists |
| `app/admin/dataset/page.tsx` | 116 | Calls `/api/admin/datasets` and `/api/admin/datasets/sentences`; no Next.js routes exist |
| `app/voice/page.tsx` | 77 | Bearer-token flow to `/api/voice-profiles`; no Next.js route exists |
| `app/login/page.tsx` | 54 | Calls `/auth/login/stub` via `API_BASE = "/api"` → broken |
| `app/settings/page.tsx` | 173 | Phase 3 call list `provider-configs` for global project `00000000-…` |
| `app/api/healthz/route.ts` | 5 | Only Next.js API route in the entire app |

### Components (apps/web/components/)

| File | Status |
|---|---|
| `LocaleSwitcher.tsx` | PRESENT but NEVER mounted in layout |
| `RequireOwner.tsx` | PRESENT; only admin/page.tsx uses it |
| `ReferenceUpload.tsx` | PRESENT (file not found at read time, may be empty); unused |
| `ThemeProvider.tsx` | PRESENT, never mounted |
| `Providers.tsx` | PRESENT, never mounted |

### Lib (apps/web/lib/)

| File | Status |
|---|---|
| `useWorkflowStream.ts` | PRESENT — SSE EventSource with reconnect, queue flush, dedup-by-step-name; wired only to `workflows/[id]` page |
| `auth.ts` | PRESENT — token in `localStorage`, login via `/auth/login/stub`; used by login/voice/audit pages |

### State management — MISSING
- No Zustand, Redux, Jotai, Recoil, React Query, SWR installed (`package.json` has only `next`, `react`, `react-dom`).
- All state is local `useState` per page.
- No editor state store, no undo/redo, no autosave.

### Real-time updates — PARTIAL
- SSE present: `lib/useWorkflowStream.ts` (reconnect, flush, dedup).
- Polling fallback: `ProjectDetailClient.tsx:49` polls every 5 s.
- WS: backend has `WS /workflows/{id}/ws` (line 38-50 of `routers_stream.py`); no frontend WS client.

### UI library — MIXED
- Inline styles on most pages (Dashboard, New Project, Settings, Project Detail, Upload, Voice, Login, Workflow).
- Tailwind classes only on `admin/layout.tsx`, `admin/page.tsx`, `admin/audit/page.tsx`, `admin/dataset/page.tsx`, `admin/voice/page.tsx`, `projects/[id]/quality-mode/page.tsx`, `workflows/[id]/page.tsx`.
- `tailwind.config.*` MISSING (no config file in repo).
- No Radix / shadcn / Mantine / MUI.

### API client — INCONSISTENT

| Pattern | Used by |
|---|---|
| `process.env.NEXT_PUBLIC_API_BASE_URL` → `http://localhost:8000` direct fetch | Dashboard, New Project, Settings, Project Detail, Upload |
| `API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api"` | Login, Voice, Project Audit |
| `/api/...` (assumes Next.js routes) | Admin audit/voice/dataset, Quality Mode, Workflow events |
| `/api/...` via Bearer | Voice consent |

`next.config.mjs` only sets `NEXT_PUBLIC_API_BASE_URL`. There is no rewrite from `/api/*` → backend. Result: 5 admin/voice/workflow pages fetch nonexistent routes.

### i18n — MISSING
- next-intl imported in some files? (need re-verify; not in `package.json`).
- All UI strings hard-coded in Vietnamese + English mix.

### Editor state — MISSING
- No current time store, no selected-segment store, no zoom store.
- Each component keeps its own `currentTime` (none synchronised).
- No keyboard shortcuts.
- No undo/redo.
- No autosave.

### Drag & drop upload — MISSING
- `app/projects/[id]/upload/page.tsx` is the only upload page, native `<input type="file">` only.
- Drag/drop not wired.

### Virtualization for 1000+ segments — MISSING
- No `react-window`, `react-virtual`, or equivalent.

---

## 2. CURRENT BACKEND WORKFLOW

### State machine — PARTIAL
- `WorkflowStatus` enum at `packages/shared/python/translator_shared/workflows.py:20-26`:
  `DRAFT, PROCESSING, AWAITING_REVIEW, READY, ARCHIVED, FAILED`.
- `Project.quality_mode` DB default is the **deprecated** value `"standard_dubbing"` (`apps/api/python/translator_api/models/project.py:24`) — does not match any current enum value.

### Persistence — PRESENT but UNUSED
- `Workflow` + `WorkflowStep` tables exist with all the right fields.
- `WorkflowStepRepository.upsert(...)` is the right hook but no Temporal worker calls it.
- 5 of 10 repositories are never imported by routers.

### Stage model — MISSING concrete
- No enum of stages (ANALYSIS / ASR / ALIGNMENT / DIARIZATION / NORMALIZATION / TRANSLATION / QA / SUBTITLE / TTS / AUDIO / RENDER).
- Implied only by `providers/registry_constants.py` kind strings.

### Worker — EXTERNAL
- `infra/worker.Dockerfile` exists; no `apps/api/python/translator_api/worker*.py`.
- `apps/api/python/translator_api/temporal_client.py` only opens `Client.connect(...)`.
- No `@workflow.defn` class, no `@activity.defn` anywhere in `apps/api/python/`.

### Real-time publisher — MISSING
- `routers_stream.py:28-35` declares `publish_step(workflow_id, payload)` — **zero callers** in the API package.
- In-process `_subscribers` dict only; will not survive multi-process / worker reload.

### Stage-2-stage status storage — NONE
- `WorkflowStep` rows can store step name + progress, but nothing populates them.

---

## 3. CURRENT API

### Surface area
31 endpoints across 5 router files + 1 inline SSE in `main.py`.
Mount order in `main.py:39-44`.

### Endpoint inventory (highlights)
| Endpoint | Method | Notes |
|---|---|---|
| `GET /healthz`, `GET /readyz` | GET | OK |
| `GET /projects` | GET | OK |
| `POST /projects` | POST | **Bug**: hardcodes `owner_id=UUID(int=0)` (line 77 of `routers.py`) |
| `GET /projects/{id}` | GET | OK |
| `POST /projects/{id}/assets:presign` | POST | **Bug**: hardcodes `asset_id=UUID(int=0)` (line 118) — uploads cannot be correlated to a DB row |
| `POST /projects/{id}/workflows` | POST | Triggers Temporal; assumes `ProjectWorkflow` class exists in external worker |
| `GET /projects/{id}/workflows/{wf_id}` | GET | OK |
| `GET /projects/{id}/workflows/{wf_id}/steps` | GET | OK (no rows populated) |
| `PUT /projects/{id}/provider-configs` | PUT | **Bug**: `ProviderConfigRepository.add()` only inserts — every PUT creates a duplicate row |
| `GET /projects/{id}/provider-configs` | GET | OK |
| `WS /workflows/{wf_id}/ws`, `GET /workflows/{wf_id}/events` | WS / SSE | Defined, no upstream publisher |
| `GET /admin/audit-logs` | GET | Auth-gated |
| `GET/POST/PUT /admin/voice-profiles` | CRUD | Consent state machine enforced (pending→{granted, revoked}) |
| `GET /admin/datasets`, `POST /admin/datasets/sentences` | GET/POST | License/domain whitelist enforced |
| `POST /auth/login/stub`, `GET /auth/me` | POST/GET | Working |
| `GET /projects/{id}/audit`, `PUT /projects/{id}/quality-mode` | GET/PUT | **Bug**: `set_quality_mode` writes `policy.asr_provider` into `project.quality_mode` instead of `payload.mode` (`routers_governance.py:197-215`) |
| `POST /voice-profiles/{id}/consent:request/grant/revoke` | POST | Audit-logged |
| `GET/PUT /projects/{id}/members` | GET/PUT | RBAC-gated |
| `GET /projects/{id}/events` (inline in `main.py:46-55`) | GET | Heartbeat-only, no real events |

### Auth
- `routers_governance.py` uses `Authorization: Bearer <token>`.
- `routers.py` has **no auth dependency** at all (projects, workflows, provider-configs are unauthenticated).
- `routers_admin*.py` enforce `require_admin` independently — three implementations.

### Capabilities endpoint — MISSING
- No `/capabilities` route.
- `ProviderRegistry.list(kind)` exists but is unexposed.
- Frontend cannot know which features are real vs stub.

### CORS
- `CORSMiddleware` allows `http://localhost:3000` only.

---

## 4. pyVIDEOTRANS INTEGRATION

### MISSING

Exhaustive grep across `apps/api/python/` and the whole repo:

| File | Line | Type |
|---|---|---|
| `apps/api/python/translator_api/providers/tts/edge.py` | 42 | Comment: "Reference: https://github.com/jianchang512/pyvideotrans edge_tts channel" |
| `apps/api/python/translator_api/providers/dubbing/align.py` | 137, 162 | Comment: "Reference: pyVideoTrans task/_base.py::SpeedRate pattern" |
| `apps/api/python/tests/test_providers_dubbing_speedrate.py` | 48 | Comment: "SpeedRate (new, pyVideoTrans pattern)" |

**No import or runtime call of pyvideotrans / pyVideoTrans.** The dubbing align provider's `SpeedRate` class is described as "following the pyVideoTrans pattern" in docstrings, but it is a custom implementation, not a wrapper.

### Provider registry breakdown (apps/api/python/translator_api/providers/)

| Category | Providers | Real | Stub / Partial |
|---|---|---|---|
| ASR | whisperx_faster_whisper | yes | — |
| Align | wav2vec2 | partial | segments not actually returned |
| Diarize | pyannote_3_1 | yes | — |
| Translate | openai_compatible_http, gemini_compatible_http, claude_compatible_http, local_llm | yes (all four) | — |
| QA | rule_based | yes | — |
| Subtitle | cps_wrapper | yes | — |
| TTS (local) | vietvoice_tts, melo_tts_vi, cosyvoice_3, vieneu_v3_turbo | — | ALL STUB (return `b""`) |
| TTS (cloud) | edge_tts, dashscope_tts, cloud_azure, cloud_google, cloud_elevenlabs | yes (all five) | — |
| TTS (local real) | qwen3_tts | partial | requires SDK |
| Mix | ffmpeg_mix | yes | — |
| Dubbing align | ffmpeg_atempo | yes | — |
| Render | ffmpeg_render | yes | — |
| Export | ffmpeg_export | yes | — |
| Cleanup | orphan_cleanup | partial | reports zero orphans |
| OCR | paddleocr, easyocr, craft | — | ALL STUB |
| Text removal | inpaint_lama, inpaint_anything, telea | — | ALL STUB |
| Voice clone | vieneu_voice_clone, cosyvoice3_voice_clone | — | ALL STUB |
| Voice embedding | (none) | — | MISSING |
| Audio separation | uvr5_mdx, demucs, bs_roformer | — | ALL STUB |

### Critical provider gap
- Local TTS (Vietnamese voices) is the heart of "China → Vietnamese dubbing", and **all four Vietnamese/local TTS providers are stubs returning `b""`**. This means no actual Vietnamese voice output is possible today.
- OCR (for text removal) and voice clone are stubs — required for "professional" mode.

---

## 5. CURRENT STATE MANAGEMENT

### Backend
- No state machine library (stateless fastapi).
- Workflow state lives in `Workflow` + `WorkflowStep` tables.
- Capability state implicit in `ProviderRegistry`.

### Frontend
- No state library.
- Every page has its own `useState` islands.
- No shared currentTime / selectedSegment / zoom store.
- No persistence layer for editor.

---

## 6. CURRENT UI COMPONENTS

### Present but inconsistent

| Component | Used? | Notes |
|---|---|---|
| `LocaleSwitcher.tsx` | NO | Defined, never mounted |
| `RequireOwner.tsx` | YES | Only on `admin/page.tsx` |
| `ThemeProvider.tsx` | NO | Defined, never mounted |
| `Providers.tsx` | NO | Defined, never mounted |
| `ReferenceUpload.tsx` | NO | Orphaned |
| `VideoPlayer` | MISSING | Not defined |
| `Timeline` / `TimelineTrack` / `TimelineSegment` | MISSING | Not defined |
| `TranscriptPanel`, `TranslationPanel`, `SpeakerPanel`, `VoicePanel`, `SubtitlePanel`, `AudioPanel` | MISSING | Not defined |
| `ProcessingPanel`, `JobStatus`, `RenderPanel`, `AssetLibrary`, `Inspector`, `AppShell`, `Sidebar`, `ProjectHeader` | MISSING | Not defined |

---

## 7. REFERENCE FINDINGS (read-only study, no copy)

### Patterns noted from OpenVideo / designcombo / Captiony / Subtitle-editor / Twick
- Persistent left tool-rail + center video preview + bottom timeline (CapCut-style).
- Single shared `currentTime` source of truth.
- Step-row components with progress bars.
- SSE/WS stream with reconnect, dedup-by-step-name.
- Quality mode as a horizontal segmented control.

### What is missing in this repo
- No persistent preview.
- No timeline component.
- No shared `currentTime`.
- No drag/drop upload.
- No virtualisation.
- No editor state machine.
- No undo/redo.
- No autosave indicator.
- No keyboard shortcuts.
- No capability gating on the UI.

---

## 8. MISSING (gap analysis vs master prompt §3–§82)

### Core gaps
1. **pyVideoTrans is not used** — only mentioned in docstrings.
2. **Local TTS providers are stubs** — no real Vietnamese voice output today.
3. **No workflow state machine in frontend** — current page knows nothing of stages.
4. **No project/job/stage model in frontend** — `Project.status` is shown as a string; no per-stage progress.
5. **No workspace shell** — layout has only a top bar.
6. **No persistent video preview** — `VideoPlayer` component does not exist.
7. **No timeline** — `Timeline` component does not exist.
8. **No translation panel editor** — `TranslationPanel` does not exist.
9. **No transcript editor** — `TranscriptPanel` does not exist.
10. **No speaker/voice panels** — neither exists.
11. **No subtitle editor** — `SubtitlePanel` does not exist; no waveform rendering.
12. **No audio panel** — `AudioPanel` does not exist.
13. **No processing center** — `ProcessingPanel` does not exist.
14. **No render panel** — `RenderPanel` does not exist; render endpoint exists in API but no UI.
15. **No undo/redo, autosave, keyboard shortcuts, search/filter, virtualisation, accessibility annotations, drag-drop upload.**
16. **No capability API** — frontend cannot tell which buttons are real.

### API gaps
17. **No `/capabilities` endpoint.**
18. **`/projects` POST hardcodes `owner_id=0`** — must be derived from auth.
19. **`/assets:presign` hardcodes `asset_id=0`** — uploads cannot be linked to a DB row.
20. **`PUT /provider-configs` accumulates duplicates** (no upsert).
21. **`PUT /quality-mode` writes wrong value** (provider name into mode).
22. **No audit log** for project / workflow / provider-config / member mutations.
23. **In-process SSE broker** will not work across multiple workers.
24. **Worker process** must exist externally; no `@workflow.defn` in this repo.
25. **Models mismatch** — `VoiceProfile` model missing `speaker_id`, `updated_at`, `embedding_storage_key` used by routers.

### Infra gaps
26. **Workflow DNS failure** — `translator-api-1` cannot resolve `temporal` (network bridge issue we observed earlier).
27. **`docker-tts-service-1` (3099)** exists but is not part of `docker-compose.yml`; it is on a separate network.
28. **No e2e test** — `tests/` only has provider unit tests.
29. **No reference repo study doc.**

---

## 9. FILES TO CHANGE (for future phases, NOT now)

> Listed for visibility only. Phase 0 produces no edits.

### Frontend (apps/web/)
- `app/layout.tsx` — replace with AppShell (sidebar + content + footer status bar).
- `app/page.tsx` — replace dashboard with Real Dashboard (Recent / Active / Failed / Completed jobs, CTA).
- `app/projects/[id]/page.tsx` — new Workspace shell (header / tool-rail / preview / timeline / inspector).
- `app/projects/[id]/upload/page.tsx` — drag-drop with progress + retry + chunked presigned.
- `app/projects/[id]/quality-mode/page.tsx` — wire to real workflow.
- `app/projects/[id]/audit/page.tsx` — wire to real workflow endpoint.
- `app/workflows/[id]/page.tsx` — keep SSE, link from project workspace.
- `app/admin/*` — unify API base; wire to real backend (drop fake `/api/*` routes).
- `app/voice/page.tsx` — wire to real consent endpoints.
- `app/login/page.tsx` — fix API base.
- `app/settings/page.tsx` — fix API base + bound to real project.
- `app/api/healthz/route.ts` — keep; add proxy routes for the broken pages.
- Add new routes: `app/projects/[id]/workspace/page.tsx`, `app/projects/[id]/jobs/page.tsx`, `app/projects/[id]/transcript/page.tsx`, `app/projects/[id]/translation/page.tsx`, `app/projects/[id]/subtitle/page.tsx`, `app/projects/[id]/render/page.tsx`.

### New frontend components
- `components/AppShell.tsx`
- `components/Sidebar.tsx`
- `components/ProjectHeader.tsx`
- `components/VideoPlayer.tsx`
- `components/Timeline.tsx`, `TimelineTrack.tsx`, `TimelineSegment.tsx`
- `components/TranscriptPanel.tsx`
- `components/TranslationPanel.tsx`
- `components/SpeakerPanel.tsx`
- `components/VoicePanel.tsx`
- `components/SubtitlePanel.tsx`
- `components/AudioPanel.tsx`
- `components/ProcessingPanel.tsx`
- `components/JobStatus.tsx`
- `components/RenderPanel.tsx`
- `components/AssetLibrary.tsx`
- `components/Inspector.tsx`
- `components/UploadDropzone.tsx`
- `lib/editorStore.ts` (Zustand) — single source of truth for `currentTime / selectedSegment / zoom / playing / volume`.
- `lib/capabilities.ts` — capability gating client.

### New frontend lib
- `lib/api.ts` — single typed API client with `fetch` + Bearer; reads `NEXT_PUBLIC_API_BASE_URL`.

### Backend (apps/api/python/)
- `routers.py` — derive `owner_id` from auth; remove hardcoded `asset_id=0`; add `/capabilities`.
- `routers_governance.py:197-215` — fix `set_quality_mode` to write `payload.mode`.
- `routers_provider_config.py` (new) — add `upsert` method on `ProviderConfigRepository` and route.
- `routers_audit.py` (new) — audit project / workflow / provider-config mutations.
- `models/voice.py` — add `speaker_id`, `updated_at`, `embedding_storage_key`.
- `models/misc.py` — add uniqueness constraint on `(project_id, provider_kind, provider_id)`.
- `models/project.py` — change DB default `quality_mode` to `QualityMode.BALANCED.value` (or align with new enum).
- `providers/asr/` — implement real WhisperX word-timestamp path.
- `providers/diarize/` — connect pyannote diarization output to `SpeakerSegment` persistence.
- `providers/tts/` — replace 4 local stubs with real local TTS (VietVoice / MeloTTS / CosyVoice 3 / VieNeu). **Highest priority** — without these the product has no Vietnamese voice.
- `providers/voice_clone/` — implement real voice-clone (Vieneu / CosyVoice 3).
- `providers/audio_separation/` — replace stubs with real UVR5 / Demucs.
- `routers_stream.py` — extract broker to Redis pubsub or move worker to call this in-process.
- New `routers_workflow.py` for stage-specific endpoints: `/projects/{id}/stages/{stage}/retry`, `/pause`, `/resume`, `/cancel`, `/result`.
- `main.py` — add `/capabilities` route.

### Worker
- A worker process must be built (out-of-scope for this repo, but referenced).
- It must:
  - Register `ProjectWorkflow` with stages: ANALYSIS → ASR → ALIGNMENT → DIARIZATION → TRANSLATION → QA → SUBTITLE → TTS → MIX → RENDER.
  - After each stage, call `WorkflowStepRepository.upsert(...)`.
  - On stage transitions, call `publish_step(workflow_id, {...})`.
  - Honour `WorkflowStatus.AWAITING_REVIEW` (human-in-the-loop pause).
  - Support retry of a single stage.

### New docs
- `docs/FRONTEND_ARCHITECTURE.md`
- `docs/WORKFLOW_ARCHITECTURE.md`
- `docs/API_FLOW.md`
- `docs/FRONTEND_REFERENCE_STUDY.md`
- `docs/USER_FLOW.md`
- `docs/FRONTEND_BACKEND_CONTRACT.md`
- `docs/FRONTEND_AUDIT.md`
- `docs/WORKFLOW_AUDIT.md`

---

## 10. RISKS

| Risk | Impact | Likelihood |
|---|---|---|
| Local TTS stubs make product un-demoable in Vietnamese | Critical | Certain today |
| pyVideoTrans not integrated as core | Architecture drift vs prompt §4 | Certain today |
| Worker process outside repo is missing/unknown | Workflow cannot run | High |
| In-process SSE broker breaks under multi-worker uvicorn | Realtime UI breaks | High once worker is wired |
| `provider-configs` duplicates | Storage bloats, audit meaningless | High |
| `quality-mode` writes wrong value | DB column drifts from spec | Certain today |
| Frontend `/api/*` calls go nowhere | 5 admin/voice/workflow pages 404 | Certain today |
| Hardcoded `owner_id=0` / `asset_id=0` | Multi-user impossible | Certain today |
| No capability endpoint | UI cannot disable stub features | Certain today |
| Models / serializers out of sync on `VoiceProfile` | Runtime errors | Certain today |
| Vietnamese/Tailwind style mix | Visual inconsistency | Medium |
| No e2e tests | Regressions unnoticed | High |

---

## 11. NEXT PHASE

**STOP — Phase 0 ends here.**

Per the master prompt §90: report Phase 0 status, then await instruction to proceed.

Awaiting decision on:
- Whether to proceed to Phase 1 (workflow architecture design only — still no code).
- Whether the pyVideoTrans integration strategy should be: (a) wrapper around pyvideotrans as a subprocess, (b) call pyvideotrans Python module directly, (c) rewrite the provider layer to use pyvideotrans SDK only, (d) keep current architecture and treat pyvideotrans as a reference only.
- Whether to keep the current scaffold's Phase 1 endpoints (create project / list / upload) or replace them.

No code changes made.
