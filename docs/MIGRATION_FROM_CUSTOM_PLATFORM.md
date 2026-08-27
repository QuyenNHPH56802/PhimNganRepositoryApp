# Migration: PhimNganRepositoryApp → pyVideoTrans

**From:** PhimNganRepositoryApp v1.3.0 (custom engine, FastAPI + Temporal + Next.js)
**To:** jianchang512/pyvideotrans v4.11 (community engine, CLI/GUI/WebUI)

This document maps every component of the current platform to its pyVideoTrans
equivalent (or documents the gap). No code is deleted at this stage.

---

## Migration Decision Matrix

### What to KEEP (transfer directly)

These components have direct equivalents in pyVideoTrans or represent knowledge
that transfers to the new setup:

| Current Component | Transfer To | Notes |
|-------------------|-------------|-------|
| **DeepSeek / OpenAI / Claude / Gemini API keys** | pyVideoTrans translation channels | Same API endpoints, same keys |
| **Edge-TTS Vietnamese voices** | pyVideoTrans `edge_tts` | Same Microsoft Edge service, same voice IDs |
| **FFmpeg rendering knowledge** | pyVideoTrans video output | Same CRF, codec, preset concepts |
| **pyannote diarization** | pyVideoTrans `pyannote-audio` | Same model, same HF token requirement |
| **Chinese → Vietnamese direction** | pyVideoTrans `--source_language_code zh-cn --target_language_code vi` | Supported natively |
| **Vietnamese voice roles** | pyVideoTrans `vi-VN-NamMinhNeural`, `vi-VN-HoaiMyNeural` | Same Edge-TTS voices |
| **Quality mode concepts** | pyVideoTrans model selection + CRF settings | Translate to faster-whisper model sizes + CRF |
| `.env.example` structure | Adapt to `videotrans/params.json` | Environment patterns remain valid |

### What becomes REFERENCE (legacy, not deleted)

These are preserved for historical reference, architecture education, and potential
future revival. They are NOT active in the new workflow:

| Reference | Location | Why Keep |
|-----------|----------|----------|
| Full FastAPI + Temporal architecture | `apps/api/`, `apps/worker/` | Architecture reference |
| All SQLAlchemy models + migrations | `apps/api/python/translator_api/models/`, `infra/migrations/` | Schema reference, ORM patterns |
| Temporal workflow definitions | `workflows_impl.py` | Workflow design reference |
| Custom provider implementations | `providers/tts/`, `providers/translate/` | Implementation reference for custom channels |
| Repository patterns | `apps/api/python/translator_api/repositories/` | Data access layer patterns |
| Observability (Prometheus/Grafana) | `infra/prometheus/`, `infra/grafana/` | Monitoring concepts |
| Kubernetes Helm charts | `infra/helm/translator/` | Deployment reference |
| TypeScript SDK | `apps/web/sdk/` | SDK design reference |
| All Web UI pages | `apps/web/app/` | UI/UX reference |
| OCR / text removal providers | `providers/ocr/`, `providers/text_removal/` | Future integration reference |
| All 34 scripts | `scripts/` | DevOps tooling reference |

### What gets REPLACED by pyVideoTrans

| Current | pyVideoTrans Replacement |
|---------|--------------------------|
| Custom ASR pipeline (`whisperx_faster_whisper`, `qwen3_asr`) | pyVideoTrans ASR (`faster-whisper`, `FunASR`, `Qwen-ASR`) |
| Custom TTS pipeline (10 providers) | pyVideoTrans TTS (34 providers, including Edge, Qwen3, F5-TTS, Confucius-TTS) |
| Custom workflow orchestration (Temporal) | pyVideoTrans CLI/GUI/WebUI (`vtv` task) |
| Custom project database (PostgreSQL + 30+ tables) | pyVideoTrans file-based workflow (`videotrans/params.json`, `output/`) |
| Custom Web UI (Next.js) | pyVideoTrans GUI (Qt6 `sp.py`) or WebUI (Gradio `webui.py`) |
| Custom provider registry | pyVideoTrans built-in provider system |
| Custom Temporal worker | pyVideoTrans built-in worker |
| Custom observability stack | pyVideoTrans logs + optional external monitoring |

### What needs NO changes

| Item | Action |
|------|--------|
| `.env.example` structure | Adapt variable names for pyVideoTrans params |
| Provider config patterns | Keep API key management approach |
| Chinese → Vietnamese language knowledge | Transfer to pyVideoTrans language codes |
| Vietnamese TTS voice knowledge | Transfer voice role IDs to pyVideoTrans |

### What CANNOT migrate (requires new work)

| Feature | Current State | pyVideoTrans Gap |
|---------|---------------|-----------------|
| Multi-project management | 30+ table relational DB | File-based, one video at a time |
| Team collaboration + RBAC | User/ProjectMember tables | No multi-user concept |
| Cloud deployment architecture | Docker/Kubernetes/Helm | Docker container exists but not cloud-native orchestration |
| SDK client library | `@translator/sdk` TypeScript | No SDK — CLI/GUI only |
| Historical translation memory | `TranslationVersion` + `TranslationSegment` tables | No TM database |
| Batch queue system | Temporal + PostgreSQL job queue | Manual batch via CLI loop |
| Character bible / glossary DB | `CharacterProfile`, `GlossaryTerm` tables | No glossary/TM system |
| Series/episode management | `Project` hierarchy | Single video per run |
| SSO / OAuth | Custom JWT auth | No auth built-in |
| Audit logging | `AuditLog` table | No audit trail |

---

## Component-by-Component Mapping

### ASR

| Current | pyVideoTrans |
|---------|--------------|
| `whisperx_faster_whisper` | `faster-whisper` (channel 0, same model) |
| `qwen3_asr` | `Qwen-ASR` (channel 3, Alibaba, **excellent for Chinese**) |

**Recommendation for Chinese → Vietnamese:** Use FunASR `paraformer-zh` or `SenseVoiceSmall`
as ASR channel. Both are built-in with no additional setup and excel at Chinese.

### Translation

| Current | pyVideoTrans |
|---------|--------------|
| `openai_compatible_http` | `ChatGPT / OpenAI` (same API key) |
| `gemini_compatible_http` | `Gemini` (same API key) |
| `claude_compatible_http` | `Claude` (same API key) |
| `local_llm` | `Ollama` or `OpenAI Compatible / Local Model` |
| (none) | **DeepSeek** (new — v3.74+, excellent quality + Deep Thinking) |
| (none) | **LiteLLM** (new — v4.11, unified interface) |

**Recommendation for Chinese → Vietnamese:** DeepSeek or OpenAI GPT-4o-mini for best
quality. Google Translate / Microsoft Translator as free fallback.

### TTS

| Current | pyVideoTrans | Notes |
|---------|--------------|-------|
| `edge_tts` | `Edge-TTS` | Same, identical voice roles |
| `dashscope_tts` | Not needed (Qwen3-TTS built-in) | |
| `qwen3_tts` (local) | `Qwen3-TTS` (built-in) | Better integration in pyVideoTrans |
| `vietvoice_tts` | **Confucius-TTS** (built-in v4.06) | Native Vietnamese, built-in |
| `vieneu_v3_turbo` | `CosyVoice3` (built-in) | Same quality, better integration |
| `cosyvoice_3` | `CosyVoice3` (built-in) | Same |
| `melotts_vi` | `Piper` or `Edge-TTS` | |
| `cloud_azure` | `Azure TTS` | Same |
| `cloud_google` | `Google Cloud TTS` | Same |
| `cloud_elevenlabs` | `ElevenLabs` | Same |
| (none) | **F5-TTS** (built-in v4.04) | Voice cloning, free |
| (none) | **OmniVoice** (built-in v4.05) | 600+ languages, voice cloning |
| (none) | **ChatTTS** (built-in) | High quality for Chinese |

**Recommendation for Chinese → Vietnamese:**
- Free: Edge-TTS (`vi-VN-HoaiMyNeural` / `vi-VN-NamMinhNeural`) or Confucius-TTS
- Quality: CosyVoice3 (3s voice cloning) or ElevenLabs

### Diarization

| Current | pyVideoTrans |
|---------|--------------|
| `pyannote_3_1` | `pyannote-audio` (same model, same HF token) |
| `nvidia_nemo` | Not available in pyVideoTrans |

**Recommendation:** Use pyannote-audio (channel 2 in Advanced Options), same HF token.

### Subtitle

| Current | pyVideoTrans |
|---------|--------------|
| `cps_wrapper` | Built-in (SRT/VTT/ASS, hard/soft burn-in) |

pyVideoTrans supports more subtitle options natively (ASS styling, bilingual subtitles).

### Render

| Current | pyVideoTrans |
|---------|--------------|
| `ffmpeg_render` | Built-in FFmpeg (`libx264`/`libx265`, CRF, presets) |

Identical — same FFmpeg engine.

### Voice Cloning

| Current | pyVideoTrans |
|---------|--------------|
| `vieneu_v3_turbo` (clone) | `CosyVoice3` (built-in, 3s clone) |
| `cosyvoice_3` (clone) | `CosyVoice3` (built-in, same) |

**Recommendation:** CosyVoice3 in pyVideoTrans (built-in, no separate service needed).

### OCR / Text Removal

| Current | pyVideoTrans |
|---------|--------------|
| `paddle_ocr` | Not built-in |
| `easy_ocr` | Not built-in |
| `craft` | Not built-in |
| All text removal providers | Not built-in |

**Status:** Gap. See `PYVIDEOTRANS_GAPS_FOR_CHINA_VIETNAM.md` (future work).

---

## pyVideoTrans Gaps for China-VNE

The following are NOT available in pyVideoTrans v4.11 and would require new work:

| Feature | Status | Priority |
|---------|--------|----------|
| Chinese OCR / text removal | Not available | High |
| Multi-project management | Not available | Medium |
| Translation memory / glossary | Not available | Medium |
| Team collaboration / RBAC | Not available | Low |
| Series / episode management | Not available | Medium |
| Audit logging | Not available | Low |
| SDK / API for programmatic access | Not available | Medium |
| Cloud-native deployment | Docker only, no k8s | Low |
| Character bible | Not available | Low |

These gaps do NOT block the migration. They are documented for future phases.

---

## Recommended China → Vietnam Configuration

Based on the component mapping above:

```bash
# ASR: FunASR paraformer-zh (best for Chinese, built-in)
# Translation: DeepSeek or OpenAI GPT-4o-mini
# TTS: Edge-TTS vi-VN-HoaiMyNeural (free) or CosyVoice3 (voice clone)
# Subtitle: Vietnamese SRT
# Output: libx265, CRF 20
```

See `PYVIDEOTRANS_ADOPTION_PLAN.md` for the full CLI command and all options.

---

## Migration Principles

1. **UPSTREAM-FIRST:** Always check if pyVideoTrans upstream has the feature before custom work
2. **REUSE > CONFIGURE > EXTEND > REWRITE:** Every custom change must be justified
3. **NO DEEP FORK:** Keep the fork as close to upstream as possible for easy upgrades
4. **TEST BEFORE CLAIM:** Every configuration must produce a real output video before documentation
5. **DOCUMENT WHAT EXISTS:** Write user guides against the actual UI, not assumptions

---

## Files in This Repository After Migration

After migration, the repository will contain:

```
PhimNganRepositoryApp/
├── docs/                          # All migration + user docs
│   ├── MIGRATION_FROM_CUSTOM_PLATFORM.md  # This file
│   ├── LEGACY_V1_3_0_STATUS.md   # Legacy platform inventory
│   ├── PYVIDEOTRANS_ADOPTION_PLAN.md       # pyVideoTrans audit
│   ├── HUONG-DAN-CHINA-VIETNAM-A-Z.md      # User guide (future)
│   ├── MODEL_SETUP_CHINA_VIETNAM.md         # Model setup (future)
│   ├── BENCHMARK_CHINA_VIETNAM.md          # Performance benchmarks (future)
│   ├── TROUBLESHOOTING.md                  # Troubleshooting guide (future)
│   └── PYVIDEOTRANS_GAPS_FOR_CHINA_VIETNAM.md  # Future work backlog
├── scripts/                       # Windows automation
│   ├── setup.bat
│   ├── start.bat
│   ├── doctor.bat
│   └── update.bat
├── pyvideotrans/                 # Source code (git submodule or cloned)
├── f5-tts/                       # Voice clone reference audio
├── output/                        # Translated videos
└── README.md                     # Point to pyVideoTrans + China-VNE docs
```

**What is NOT included:** No FastAPI, no Temporal, no PostgreSQL, no Next.js,
no Helm charts, no custom providers — unless specifically needed for a
configuration gap that pyVideoTrans cannot fill.
