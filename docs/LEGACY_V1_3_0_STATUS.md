# PhimNganRepositoryApp — Legacy v1.3.0 Status

**Version:** 1.3.0
**Git Commit:** `4180631` ("release: v1.3.0 — workflow TTS wiring, README rewrite", 2026-08-27)
**Tags:** `v1.1.0`, `v1.2.0`, `legacy-v1.3.0`
**Branch:** `main`
**Remote:** `origin` → `https://github.com/QuyenNHPH56802/PhimNganRepositoryApp.git`
**Working tree:** Clean

---

## Architecture Overview

The platform is a multimodal video localization orchestrator built with:

- **Frontend:** Next.js 14 (TypeScript)
- **API:** FastAPI (Python)
- **Workflow engine:** Temporal
- **Database:** PostgreSQL (SQLAlchemy, Alembic migrations)
- **Storage:** Local or S3
- **GPU support:** NVIDIA CUDA via Docker compose
- **Orchestration:** Docker Compose (dev/prod/cluster/gpu variants), Helm 3

```
Next.js (Port 3000)
    ↓ HTTP
FastAPI (Port 8000)
    ↓ Temporal client
Temporal Worker (Activities)
    ↓
ASR / Translation / TTS / Render providers
```

---

## Components Inventory

### ASR (Speech Recognition)

| Provider ID | Type | Class | File |
|------------|------|-------|------|
| `whisperx_faster_whisper` | Local | `WhisperxFasterWhisperProvider` | `providers/asr/whisperx_provider.py` |
| `qwen3_asr` | Local | `Qwen3AsrProvider` | (referenced in registry) |

### Translation

| Provider ID | Type | Class | File |
|------------|------|-------|------|
| `openai_compatible_http` | Cloud | `OpenAICompatibleHttpProvider` | `providers/translate/openai_http.py` |
| `gemini_compatible_http` | Cloud | `GeminiCompatibleHttpProvider` | `providers/translate/gemini_http.py` |
| `claude_compatible_http` | Cloud | `ClaudeCompatibleHttpProvider` | `providers/translate/claude_http.py` |
| `local_llm` | Local | `LocalLlmProvider` | `providers/translate/local_llm.py` |

### TTS (Text-to-Speech) — 10 Providers

| # | Provider ID | Name | Type | Class | File |
|---|-------------|------|------|-------|------|
| 1 | `edge_tts` | Microsoft Edge Neural | Cloud (free) | `EdgeTtsProvider` | `providers/tts/edge.py` |
| 2 | `dashscope_tts` | Alibaba Qwen3 (cloud) | Cloud (paid) | `DashScopeTtsProvider` | `providers/tts/cloud_qwen3.py` |
| 3 | `qwen3_tts` | Qwen3-TTS (local) | Local (GPU) | `Qwen3TtsProvider` | `providers/tts/qwen3.py` |
| 4 | `vietvoice_tts` | VietVoice | Local | `VietVoiceTtsProvider` | `providers/tts/vietvoice.py` |
| 5 | `vieneu_v3_turbo` | VieNeu V3 Turbo | Local (voice-clone) | `VieNeuProvider` | `providers/tts/vieneu.py` |
| 6 | `cosyvoice_3` | CosyVoice 3 | Local (GPU, voice-clone) | `CosyVoice3Provider` | `providers/tts/cosyvoice.py` |
| 7 | `melotts_vi` | MeloTTS Vietnamese | Local (lightweight) | `MeloTtsViProvider` | `providers/tts/melotts.py` |
| 8 | `cloud_azure` | Azure TTS | Cloud (paid) | `AzureCloudTtsProvider` | `providers/tts/azure.py` |
| 9 | `cloud_google` | Google Cloud TTS | Cloud (paid) | `GoogleCloudTtsProvider` | `providers/tts/google.py` |
| 10 | `cloud_elevenlabs` | ElevenLabs | Cloud (paid, voice-clone) | `ElevenLabsTtsProvider` | `providers/tts/elevenlabs.py` |

### Diarization

| Provider ID | Name | Class | File |
|------------|------|-------|------|
| `pyannote_3_1` | pyannote 3.1 | `PyannoteDiarizationProvider` | `providers/diarize/pyannote_provider.py` |
| `nvidia_nemo` | NVIDIA NeMo | (referenced in registry) | — |

### Alignment

| Provider ID | Name | Class | File |
|------------|------|-------|------|
| `whisperx_align` | WhisperX alignment | `WhisperxAlignmentProvider` | (in `providers/align/`) |
| `wav2vec2` | Wav2Vec2 | `Wav2vec2AlignmentProvider` | `providers/align/wav2vec2_provider.py` |

### Subtitle

| Provider ID | Name | Class | File |
|------------|------|-------|------|
| `cps_wrapper` | CPS wrapper | `CpsWrapperSubtitleProvider` | `providers/subtitle/cps_wrapper.py` |

Subtitle formats: SRT, VTT, ASS
Alignment: `subtitle/aligner.py`, locale rules: `subtitle/locale_rules.py`

### Audio Separation

| Provider ID | Name | Class |
|------------|------|-------|
| `uvr5_mdx` | UVR5 MDX | `Uvr5MdxProvider` |
| `demucs` | Demucs | `DemucsProvider` |
| `bs_roformer` | BS Roformer | `BsRoformerProvider` |

### Dubbing / Voice Alignment

| Provider | Name | Class | File |
|----------|------|-------|------|
| `ffmpeg_atempo` | FFmpeg atempo | `FfmpegAtempoAlignProvider` | `providers/dubbing/align.py` |

### Render

| Provider | Name | Class | File |
|----------|------|-------|------|
| `ffmpeg_render` | FFmpeg render | `FfmpegRenderProvider` | `providers/render/ffmpeg_render.py` |

### Voice Cloning

| Provider ID | Name | Class | File |
|------------|------|-------|------|
| `vieneu_v3_turbo` | VieNeu voice clone | `VieNeuVoiceCloneProvider` | `providers/voice_clone/vieneu.py` |
| `cosyvoice_3` | CosyVoice 3 voice clone | `CosyVoice3VoiceCloneProvider` | `providers/voice_clone/cosyvoice.py` |

### OCR

| Provider ID | Name | Class | File |
|------------|------|-------|------|
| `paddle_ocr` | PaddleOCR | `PaddleOcrProvider` | `providers/ocr/paddle_provider.py` |
| `easy_ocr` | EasyOCR | `EasyOcrProvider` | `providers/ocr/easyocr_provider.py` |
| `craft` | CRAFT text detector | `CraftTextDetectorProvider` | `providers/ocr/craft_provider.py` |

### Text Removal

| Provider ID | Name | Class |
|------------|------|-------|
| `inpaint` | Inpaint Anything | `InpaintAnythingProvider` |
| `cover` | Cover/blur | `CoverProvider` |
| `blur` | OpenCV blur | `OpenCvTeleaProvider` |
| `lama` | LaMa inpainting | `LamaInpaintProvider` |

### QA

| Provider ID | Name | Class | File |
|------------|------|-------|------|
| `rule_based` | Rule-based QA | `RuleBasedQaProvider` | `providers/qa/rule_based.py` |

---

## Database — SQLAlchemy Models (Alembic Migrations)

**Migrations:** `infra/migrations/versions/0001`–`0004`

**30+ tables:**

| Model | Table | Purpose |
|-------|-------|---------|
| `User` | `users` | User accounts |
| `Project` | `projects` | Translation projects |
| `ProjectMember` | `project_members` | Project membership / RBAC |
| `ProjectSettings` | `project_settings` | Per-project settings |
| `Asset` | `assets` | Uploaded video/audio assets |
| `Transcript` | `transcripts` | ASR transcript |
| `TranscriptSegment` | `transcript_segments` | Transcript segments |
| `TranscriptWord` | `transcript_words` | Word-level timestamps |
| `Speaker` | `speakers` | Speaker profiles |
| `SpeakerSegment` | `speaker_segments` | Speaker-to-segment mapping |
| `CharacterProfile` | `character_profiles` | Character bible |
| `CharacterAlias` | `character_aliases` | Character name aliases |
| `Glossary` | `glossaries` | Translation glossary |
| `GlossaryTerm` | `glossary_terms` | Glossary entries |
| `TranslationVersion` | `translation_versions` | Translation version |
| `TranslationSegment` | `translation_segments` | Translated segments |
| `VoiceProfile` | `voice_profiles` | TTS voice profiles |
| `TtsSegment` | `tts_segments` | TTS segment data |
| `AudioTrack` | `audio_tracks` | Audio tracks |
| `AudioSegment` | `audio_segments` | Audio segments |
| `SubtitleTrack` | `subtitle_tracks` | Subtitle track |
| `SubtitleSegment` | `subtitle_segments` | Subtitle segments |
| `Workflow` | `workflows` | Workflow runs |
| `WorkflowStep` | `workflow_steps` | Individual workflow steps |
| `RenderJob` | `render_jobs` | Render jobs |
| `Export` | `exports` | Export records |
| `OcrDetection` | `ocr_detections` | OCR results |
| `TextRemovalJob` | `text_removal_jobs` | Text removal jobs |
| `ProviderConfig` | `provider_configs` | Per-project provider configs |
| `AuditLog` | `audit_logs` | Audit trail |

---

## Temporal Workflows

**File:** `apps/worker/python/translator_worker/workflows_impl.py`

| Workflow | Task Queue | Description |
|----------|------------|-------------|
| `ProjectWorkflow` | `project-queue` | Root workflow — validates, runs Subtitle or Dubbing workflow |
| `SubtitleWorkflow` | `project-queue` | fast mode: ASR → align → diarize → normalize → translate → QA → subtitle |
| `DubbingWorkflow` | `project-queue` | balanced/high mode: full pipeline + TTS + mix + render |
| `ChunkWorkflow` | `project-queue` | per-chunk: ASR → translate → TTS |

**Task queues:** `asr-queue`, `diarize-queue`, `tts-queue`, `cpu-queue`

**Activities:** `activities.py`, `activities_phase3.py`, `activities_phase4.py`, `activities_alignment.py`, `activities_voice_clone.py`, `activities_qa_multispeaker.py`, `activities_providers.py`, `activities_cache.py`

---

## Web UI — Next.js 14

**Routes (14 pages):**

| Route | File |
|-------|------|
| `/` | `app/page.tsx` (Dashboard, server component) |
| `/login` | `app/login/page.tsx` |
| `/projects/new` | `app/projects/new/page.tsx` |
| `/projects/[id]` | `app/projects/[id]/page.tsx` (server) + `ProjectDetailClient.tsx` (client, 5s polling) |
| `/projects/[id]/upload` | `app/projects/[id]/upload/page.tsx` |
| `/projects/[id]/audit` | `app/projects/[id]/audit/page.tsx` |
| `/projects/[id]/quality-mode` | `app/projects/[id]/quality-mode/page.tsx` |
| `/settings` | `app/settings/page.tsx` (TTS provider selector, 10 providers) |
| `/voice` | `app/voice/page.tsx` |
| `/workflows/[id]` | `app/workflows/[id]/page.tsx` |
| `/admin` | `app/admin/page.tsx` |
| `/admin/audit` | `app/admin/audit/page.tsx` |
| `/admin/dataset` | `app/admin/dataset/page.tsx` |
| `/admin/voice` | `app/admin/voice/page.tsx` |

**i18n (11 languages):** `de`, `en`, `es`, `fr`, `ja`, `ko`, `pt`, `th`, `vi`, `zh`, and one more

**Components:** `LocaleSwitcher`, `Providers`, `RequireOwner`, `ThemeProvider`, `ReferenceUpload`

**Auth:** JWT-based via `lib/auth.ts`

---

## SDK

**Package:** `@translator/sdk` at `apps/web/sdk/`
- `client.ts` — `TranslatorClient` class
- `index.ts` — package exports
- Package manager: pnpm

---

## Infrastructure

**Docker compose variants:** `docker-compose.yml`, `docker-compose.prod.yml`, `docker-compose.cluster.yml`, `docker-compose.gpu.yml`, `infra/docker/docker-compose.yml`

**Dockerfiles:** `api.Dockerfile`, `web.Dockerfile`, `worker.Dockerfile`, plus variants in `infra/docker/`

**Helm chart:** `infra/helm/translator/` (v1.0)
- Templates: api/web/worker (CPU + GPU pools), PostgreSQL, MinIO, Redis, Temporal, Ingress, ServiceAccount

**Reverse proxy:** `infra/Caddyfile`

**Observability stack:**
- Prometheus + Alertmanager + Grafana dashboards (api, cluster, cost, worker-pool)
- Promtail + Loki
- OpenTelemetry collector

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/release.py` | Semver bump + CHANGELOG |
| `scripts/migrate.py` | DB migration runner |
| `scripts/check_deprecations.py` | Deprecation scanner |
| `scripts/release_e2e.py` | E2E smoke test |
| `scripts/benchmark.py` | Performance benchmark |
| `scripts/scale_test.py` | Scale testing |
| `scripts/generate_sbom.py` | SBOM generation |
| `scripts/seed_admin.py` | Admin seeding |
| `scripts/up.ps1` | PowerShell startup |

---

## Documentation

| File | Description |
|------|-------------|
| `docs/architecture.md` | Architecture overview |
| `docs/ERD.md` | Entity-relationship diagram |
| `docs/providers.md` | Provider documentation |
| `docs/provider-contracts.md` | Provider contract specs |
| `docs/provider-implementation.md` | Implementation guide |
| `docs/integrations.md` | API integration guide |
| `docs/integration-review.md` | Phase 11 audit |
| `docs/pipeline-quality.md` | Quality pipeline |
| `docs/workflow.md` | Workflow documentation |
| `docs/deprecation.md` | Deprecation timeline |
| `docs/cluster.md` | Cluster setup |
| `docs/multi-region.md` | Multi-region deployment |
| `docs/runtime-topology.md` | Runtime topology |
| `docs/deploy.md` | Deployment guide |
| `docs/setup-docker.md` | Docker setup |
| `docs/dev-setup.md` | Dev environment setup |
| `docs/security.md` | Security documentation |
| `docs/observability.md` | Observability guide |
| `docs/slos.md` | SLO definitions |
| `docs/benchmark.md` | Benchmark guide |
| `docs/golden-dataset.md` | Golden dataset |
| `docs/admin.md` | Admin guide |
| `docs/on-call.md` | On-call runbooks |
| `docs/runbooks.md` | Operational runbooks |
| `docs/release.md` | Release + rollback guide |
| `docs/licenses.md` | License registry |
| `docs/HUONG-DAN-SU-DUNG.md` | Vietnamese user guide |

---

## Version History

| Version | Date | Commit | Highlights |
|---------|------|--------|-----------|
| **1.3.0** | 2026-08-27 | `4180631` | Workflow TTS wiring (translate→TTS→DB chain), README rewrite |
| **1.2.0** | 2026-08-27 | `66fa29b` | DashScope Qwen3-TTS provider + SSE streaming mode |
| **1.1.0** | 2026-08-27 | `6c79bb1` | TTS metrics, Web UI selector, Dockerfile fix |
| **1.0.0** | 2026-08-26 | `5d781ea` | Initial release: ASR + translation + TTS + dubbing + render |

---

## Tag Strategy

This codebase is frozen as `legacy-v1.3.0` (tag `legacy-v1.3.0`).

The codebase is kept as-is for reference. Future development continues in a new
pyVideoTrans-based distribution.
