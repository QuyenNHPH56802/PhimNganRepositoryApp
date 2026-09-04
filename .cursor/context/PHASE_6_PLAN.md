# Phase 6: Quality & Integration Features

**Created:** 2026-09-04 10:25 AM
**Status:** 🟢 In Progress
**Priority:** P3 (Quality of life + extensibility)
**Estimated effort:** 60-85 hours (split across multiple sessions)

---

## 🎯 Scope

This phase implements three medium-effort, medium-impact features from
[`PHASE_6_FUTURE_FEATURES.md`](../PHASE_6_FUTURE_FEATURES.md) §6.4:

| Task | Why this one |
|------|--------------|
| **Glossary Management UI** | Powers users need consistent terminology; backend already accepts `glossary` dict in translation payloads. |
| **Quality Scoring Dashboard** | Helps editors triage which segments need re-translation without re-listening. |
| **Webhook Notifications** | Enables integration with Slack / Discord / internal dashboards without polling. |

**Out of scope** (deliberately deferred — see `PHASE_6_FUTURE_FEATURES.md`):
- Voice Cloning, Audio Separation, OCR, Text Removal — these need large model
  downloads and are out of scope for a web-only iteration.
- Mobile App, Multi-tenant — too large.

---

## Sprint plan

### Sprint 6.1: Glossary Management UI (this session)

**Backend already supports it:**
```python
# providers/translate/base.py already accepts glossary in payload.
```

**Frontend work:**
1. `apps/web/lib/glossary.ts` — type-safe CRUD against `/api/glossaries/*`
2. `apps/web/app/settings/glossary/page.tsx` — list + editor
3. `apps/web/components/GlossaryEditor.tsx` — table-style add/edit/delete
4. `apps/web/app/projects/[id]/workspace/page.tsx` — link "Glossary" project to project
5. `apps/api/python/translator_api/routers_glossary.py` — REST endpoints
6. Migration: `0006_glossaries_table.py` (if not present)

**Verification:**
- E2E: create glossary, add term, link to project, run translation, verify term is preserved

---

### Sprint 6.2: Quality Scoring Dashboard

**Score per translation segment:**
- CPS (characters per second) — too fast to read?
- Source/target length ratio — drift > 30% flagged
- Glossary adherence — % of glossary terms present in target
- Pinyin leakage — Chinese pinyin in VI target?
- Untranslated segment — still Chinese characters?

**Files:**
- `apps/api/python/translator_api/providers/qa/rule_based.py` — extend
- `apps/web/components/panels/TranslationPanel.tsx` — show per-row score
- `apps/web/app/projects/[id]/quality/page.tsx` — aggregate dashboard

---

### Sprint 6.3: Webhook Notifications

**Backend:**
- `webhooks` table — id, project_id?, event, url, secret, created_at
- `webhook_deliveries` — id, webhook_id, payload, status, attempt, last_error
- `apps/api/python/translator_api/routers_webhooks.py` — CRUD + test delivery
- Worker hooks into `workflow_completed` / `workflow_failed` events

**Frontend:**
- `apps/web/app/settings/webhooks/page.tsx` — list + add/edit
- Modal for "Send test event"

---

## Files affected (running tally)

```
NEW    apps/web/lib/glossary.ts
NEW    apps/web/app/settings/glossary/page.tsx
NEW    apps/web/components/GlossaryEditor.tsx
NEW    apps/api/python/translator_api/routers_glossary.py
NEW    apps/web/app/settings/webhooks/page.tsx
NEW    apps/web/app/projects/[id]/quality/page.tsx
NEW    apps/web/components/QualityScoreBadge.tsx
MOD    apps/web/app/projects/[id]/workspace/page.tsx
MOD    apps/web/components/panels/TranslationPanel.tsx
MOD    apps/api/python/translator_api/main.py   (router mount)
MOD    apps/api/python/translator_api/providers/qa/rule_based.py
```

---

**Maintained by:** AI Agent + Engineering
**Last updated:** 2026-09-04
