# Phase 6b: Productivity Features

**Created:** 2026-09-04 10:19 AM
**Status:** 🟢 In Progress
**Priority:** P3 (User productivity)
**Estimated effort:** 50-70 hours

---

## 🎯 Scope

Three medium-effort features from [`PHASE_6_FUTURE_FEATURES.md`](../PHASE_6_FUTURE_FEATURES.md) §6.3:

| Task | Why this one |
|------|--------------|
| **Multi-Language Subtitles** | Expand from zh→vi single-target to multiple target languages (en, ja, ko). High market reach impact. |
| **Batch Processing** | Upload + process multiple videos in parallel. Big productivity win for agencies. |
| **Project Templates** | Save and reuse project configs (providers, quality mode, glossary). Fast setup for similar projects. |

**Out of scope:**
- OCR, Voice Cloning, Audio Separation — need large AI models
- Mobile App, Multi-tenant — too large for this session

---

## Sprint plan

### Sprint 6.2.1: Multi-Language Subtitles

**Backend changes:**
- `models/subtitle.py` — add `language_code` column to subtitles table (migration 0007)
- `routers_subtitle.py` — extend to accept `target_languages: list[str]` on generate
- Worker: call translation + TTS for each language, generate separate SRT files
- Store each language's subtitle as separate rows

**Frontend changes:**
- `SubtitlePanel.tsx` — add language selector (checkboxes for en/ja/ko)
- `apps/web/app/projects/[id]/subtitles/page.tsx` — multi-language view
- API client: update to pass `target_languages`

**Effort:** 15-20h

---

### Sprint 6.2.2: Batch Processing

**Backend changes:**
- `routers_batch.py` — POST /batch with list of project configs
- Worker: run multiple workflows in parallel (or queue)
- Response: map of `{ project_id: workflow_id }` per item

**Frontend changes:**
- `apps/web/app/batch/page.tsx` — drag-drop multi-upload UI
- Progress tracker per project in the batch
- `BatchProgress` component in dashboard

**Effort:** 20-30h

---

### Sprint 6.2.3: Project Templates

**Backend changes:**
- `models/template.py` — `project_templates` table
- `routers_templates.py` — CRUD for templates (owner-scoped)
- Apply template → create new project with template's settings

**Frontend changes:**
- `apps/web/app/settings/templates/page.tsx` — list + create + delete
- Template editor: pick providers, quality mode, glossary
- "New project from template" flow

**Effort:** 15-20h

---

## Files affected (running tally)

```
NEW    apps/api/python/translator_api/models/template.py
NEW    apps/api/python/translator_api/routers_templates.py
NEW    apps/api/python/translator_api/routers_batch.py
NEW    infra/migrations/versions/0007_multi_lang_subtitles.py
MOD    apps/api/python/translator_api/models/subtitle.py
MOD    apps/api/python/translator_api/routers_subtitle.py
MOD    apps/api/python/translator_api/main.py
NEW    apps/web/app/settings/templates/page.tsx
NEW    apps/web/app/batch/page.tsx
NEW    apps/web/components/BatchUploader.tsx
NEW    apps/web/components/TemplateEditor.tsx
MOD    apps/web/components/panels/SubtitlePanel.tsx
MOD    apps/web/lib/api.ts
```

---

**Maintained by:** AI Agent + Engineering
**Last updated:** 2026-09-04
