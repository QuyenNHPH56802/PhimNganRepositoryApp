# Phase 6d: Voice Cloning + Text Removal

**Created:** 2026-09-04 12:01 PM
**Status:** 🟢 In Progress
**Priority:** P2 (Feature completeness)

---

## 🎯 Scope

Final two features from `PHASE_6_FUTURE_FEATURES.md` §6.3:

| Task | Why |
|------|-----|
| **Voice Cloning** | Reuse a sample voice to generate a personalized TTS voice profile. Bridges voice profile management to AI synthesis. |
| **Text Removal** | Already has providers (`opencv_telea`, `lama`, `inpaint_anytime`); wire them into a router + UI so OCR regions → cleaned frames pipeline works. |

Both ship with `mock` providers for dev/test; real model integration deferred to GPU environment.

---

## Sprint plan

### Sprint 6.4.1: Voice Cloning

**Backend:**
- New provider stack under `providers/voice/`
  - `base.py` — provider interface (`VoiceCloneInput`, `VoiceCloneResponse`)
  - `mock_provider.py` — derives a deterministic embedding from sample key
  - `xtts_provider.py` — stub (raises `CapabilityUnsupported` since model is heavy)
- New model `VoiceCloneSample` in `models/voice.py`:
  - `id`, `project_id`, `sample_storage_key`, `provider_id`, `embedding_key`,
    `quality_score`, `duration_ms`, `status`, `created_at`
- New router `routers_voice_clone.py`:
  - POST /projects/{id}/voice-clone/samples — upload sample
  - GET /projects/{id}/voice-clone/samples — list
  - POST /projects/{id}/voice-clone/samples/{sid}/run — start cloning
  - DELETE /projects/{id}/voice-clone/samples/{sid}

**Frontend:**
- `lib/voiceClone.ts`
- `components/panels/VoiceClonePanel.tsx`
- Add tab to workspace

---

### Sprint 6.4.2: Text Removal

**Backend:**
- Reuse existing `providers/text_removal/*`
- New router `routers_text_removal.py`:
  - POST /projects/{id}/text-removal/jobs — kick off removal using selected OCR regions
  - GET /projects/{id}/text-removal/jobs — list jobs
  - GET /projects/{id}/text-removal/jobs/{jid} — status
  - DELETE /projects/{id}/text-removal/jobs/{jid}
- Reuse `TextRemovalJob` model already defined in `models/ocr.py`
- Use `MockTextRemovalProvider` if no real provider configured (so dev works)

**Frontend:**
- `lib/textRemoval.ts`
- `components/panels/TextRemovalPanel.tsx` — picks OCR regions, runs job, shows before/after
- Add tab to workspace

---

## Files affected (running tally)

```
NEW    apps/api/python/translator_api/providers/voice/__init__.py
NEW    apps/api/python/translator_api/providers/voice/base.py
NEW    apps/api/python/translator_api/providers/voice/mock_provider.py
NEW    apps/api/python/translator_api/providers/voice/xtts_provider.py
NEW    apps/api/python/translator_api/providers/text_removal/mock_provider.py
NEW    apps/api/python/translator_api/routers_voice_clone.py
NEW    apps/api/python/translator_api/routers_text_removal.py
NEW    apps/web/lib/voiceClone.ts
NEW    apps/web/lib/textRemoval.ts
NEW    apps/web/components/panels/VoiceClonePanel.tsx
NEW    apps/web/components/panels/TextRemovalPanel.tsx
MOD    apps/api/python/translator_api/main.py
MOD    apps/api/python/translator_api/models/__init__.py
MOD    apps/api/python/translator_api/models/voice.py
MOD    apps/web/app/projects/[id]/workspace/page.tsx
MOD    apps/web/lib/types.ts
```

---

**Maintained by:** AI Agent + Engineering
**Last updated:** 2026-09-04
