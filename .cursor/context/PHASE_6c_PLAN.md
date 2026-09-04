# Phase 6c: CI Hardening + AI Model Stubs

**Created:** 2026-09-04 10:40 AM
**Status:** 🟢 In Progress
**Priority:** P2 (Production readiness)

---

## 🎯 Scope

Three things in this phase:

| Task | Why |
|------|-----|
| **CI hardening** | Wire Playwright E2E + coverage into GitHub Actions so the Phase 5 Sprint 3 work actually runs in CI. |
| **OCR Integration API stub** | Front-load the API contract so backend / frontend teams can build in parallel; provider implementations land later. |
| **Audio Separation API stub** | Same pattern as OCR — interface + UI + route registration. |

Both OCR & Separation implementations are deferred behind a provider-stub layer:
- The interface + schema + UI ship now
- A `mock` provider returns deterministic placeholder data
- The real model integration is a follow-up that needs GPU + model weights

---

## Sprint plan

### Sprint 6.3.1: CI hardening

**New jobs in `.github/workflows/ci.yml`:**
- `web-lint`: runs `eslint` + `tsc --noEmit` on `apps/web`
- `web-e2e`: starts Postgres + Redis via service container, runs API + worker + web dev server, then `playwright test`
- `coverage`: merges coverage.xml from pytest, uploads to Codecov (optional)

**Files:**
- `.github/workflows/ci.yml` — extend with new jobs
- `apps/web/.eslintrc` — minimal config if missing

---

### Sprint 6.3.2: OCR Integration (API stub + UI)

**Backend:**
- New `routers_ocr.py` with endpoints:
  - `POST /projects/{id}/ocr/run` — kick off OCR scan on frames
  - `GET /projects/{id}/ocr/regions` — list detected text regions
  - `PATCH /projects/{id}/ocr/regions/{region_id}` — edit translation
- Tables (migration `0007_ocr_regions.py`):
  - `ocr_regions`: project_id, frame_index, bbox (x,y,w,h), source_text, translated_text, confidence, status
- Use the existing `providers/ocr/base.py` interface; ship a `mock` provider that
  returns 0-2 deterministic regions per frame.

**Frontend:**
- `apps/web/components/panels/OcrPanel.tsx` — list of regions with editable translations
- `lib/ocr.ts` — API client
- Add `ocr` to workspace tabs

---

### Sprint 6.3.3: Audio Separation (API stub + UI)

**Backend:**
- New `routers_separation.py`:
  - `POST /projects/{id}/separation/run` — kick off separation on audio
  - `GET /projects/{id}/separation/tracks` — list separated tracks (vocals / music / sfx)
- Mock provider returns three empty tracks keyed by the asset id.

**Frontend:**
- `apps/web/components/panels/SeparationPanel.tsx` — track list with download links
- `lib/separation.ts` — API client
- Add `separation` to workspace tabs

---

## Files affected (running tally)

```
NEW    .github/workflows/ci-web.yml
MOD    .github/workflows/ci.yml
NEW    apps/web/.eslintrc.json
NEW    infra/migrations/versions/0007_ocr_regions.py
NEW    apps/api/python/translator_api/models/ocr.py
NEW    apps/api/python/translator_api/models/separation.py
NEW    apps/api/python/translator_api/routers_ocr.py
NEW    apps/api/python/translator_api/routers_separation.py
NEW    apps/api/python/translator_api/providers/ocr/mock_provider.py
NEW    apps/api/python/translator_api/providers/separation/mock_provider.py
NEW    apps/web/components/panels/OcrPanel.tsx
NEW    apps/web/components/panels/SeparationPanel.tsx
NEW    apps/web/lib/ocr.ts
NEW    apps/web/lib/separation.ts
MOD    apps/web/app/projects/[id]/workspace/page.tsx
MOD    apps/web/lib/types.ts
MOD    apps/api/python/translator_api/main.py
MOD    apps/api/python/translator_api/models/__init__.py
```

---

**Maintained by:** AI Agent + Engineering
**Last updated:** 2026-09-04
