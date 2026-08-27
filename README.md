# Translator — Multimodal Video Localization Platform

**Version 1.3.0** · Apache 2.0

An end-to-end platform for translating and dubbing video/audio content. Given a
video file, it transcribes, diarizes speakers, translates between supported
language pairs, synthesizes TTS in the target voice, and outputs a dubbed
video with burned-in subtitles.

---

## What's New in v1.3.0 (2026-08-27)

### Workflow TTS Integration
The dubbing pipeline is now fully wired end-to-end:

- **`translate_segments`** now loads source segments from the latest
  `TranscriptVersion` and persists the translation response as
  `TranslationVersion` + `TranslationSegment` DB records so downstream
  TTS can read them.
- **`tts_synthesize`** now reads `tts_text` from the persisted
  `TranslationSegment` records and passes a joined string to the TTS
  provider — previously it always called TTS with `text=""` and
  returned a stub.
- Added `TranscriptRepository.latest_for_project()` which was missing
  and required by the fixed `translate_segments` logic.

### README Fix
- Fixed the clone URL from the placeholder
  `https://example.com/translator.git` to the real repo URL.
- Fixed the `cd translator` step to `cd PhimNganRepositoryApp`.

For the full changelog from all versions, see `CHANGELOG.md`.

---

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/QuyenNHPH56802/PhimNganRepositoryApp.git
cd PhimNganRepositoryApp

# Python
python -m venv .venv && .venv/scripts/activate   # Windows
# python -m venv .venv && source .venv/bin/activate  # macOS/Linux
pip install -e ".[all,dev]"

# Node (for web UI and SDK)
npm install -g pnpm
cd apps/web && pnpm install && cd ../..
```

### 2. Start services

**Option A — Docker Compose (recommended)**

```bash
# Requires Docker Desktop running
docker compose -f infra/docker/docker-compose.yml up -d --build

# Verify
curl http://localhost:8000/healthz   # API
curl http://localhost:3000           # Web UI
# Temporal UI: http://localhost:8233
```

**Option B — Manual services (no Docker)**

```bash
# Terminal 1: PostgreSQL + Temporal (outside this repo)
# Then set DATABASE_URL and TEMPORAL_HOST in .env

# Terminal 2: API
uvicorn translator_api.main:app --reload --port 8000

# Terminal 3: Worker
python -m translator_worker
```

### 3. Create a project

```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Demo project",
    "quality_mode": "balanced",
    "source_language": "zh",
    "target_language": "vi"
  }'
```

### 4. Run a translation workflow

```bash
# Upload an asset, then trigger the workflow
curl -X POST http://localhost:8000/projects/<id>/workflows \
  -H "Content-Type: application/json" \
  -d '{"asset_id": "<asset-id>", "quality_mode": "balanced"}'
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Web  (Next.js)  ────►  API  (FastAPI)                │
│  SDK (@translator/sdk)      ├── routes                 │
│                              ├── provider registry       │
│                              └── Temporal client         │
└─────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                         ┌──────────────────┐
                         │  Temporal Worker  │
                         │  (activities)     │
                         └──────────────────┘
                         │  ┌──────────────┘
                         ▼  ▼
          ┌──────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐
          │   ASR    │ │Transl. │ │   TTS    │ │  Render  │
          │(WhisperX)│ │(LLM API)│ │(10 prov.)│ │ (FFmpeg) │
          └──────────┘ └────────┘ └──────────┘ └──────────┘
```

**Data flow (dubbing pipeline):**

```
Video → ASR → Align → Diarize → Normalize → Translate → QA → Subtitle → TTS → Mix → Render → Video
```

---

## Language pairs

| Source | Target | Providers |
|--------|--------|-----------|
| zh | vi | Deepseek, OpenAI, Gemini, Claude |
| vi | zh | Deepseek, OpenAI, Gemini, Claude |
| zh | en | OpenAI, Gemini, Claude |
| en | zh | OpenAI, Gemini, Claude |
| zh | ja | OpenAI, Gemini, Claude |
| zh | ko | OpenAI, Gemini, Claude |
| en | vi | OpenAI, Gemini, Claude |
| vi | en | OpenAI, Gemini, Claude |

---

## TTS providers (10 available)

| ID | Provider | Type | Cost | Notes |
|----|----------|------|------|-------|
| `edge_tts` | Microsoft Edge Neural | Cloud | Free | No API key required |
| `dashscope_tts` | Alibaba Qwen3 | Cloud | ~$0.004/min | `DASHSCOPE_API_KEY` |
| `qwen3_tts` | Qwen3-TTS | Local | Free | Requires GPU |
| `vietvoice_tts` | VietVoice | Local | Free | Vietnamese-only; GPU recommended |
| `vieneu_v3_turbo` | VieNeu | Local | Free | Voice-clone capable; GPU recommended |
| `cosyvoice_3` | CosyVoice 3 | Local | Free | Multilingual; voice-clone capable; GPU required |
| `melotts_vi` | MeloTTS | Local | Free | Lightweight Vietnamese |
| `cloud_azure` | Azure TTS | Cloud | Paid | `AZURE_TTS_KEY` |
| `cloud_google` | Google Cloud TTS | Cloud | Paid | `GOOGLE_TTS_KEY` |
| `cloud_elevenlabs` | ElevenLabs | Cloud | Paid | Voice cloning; `ELEVENLABS_API_KEY` |

**Free TTS options (no API key / no GPU):**

- `edge_tts` — best for quick demos, no setup
- `dashscope_tts` — best quality-to-effort ratio, only needs `DASHSCOPE_API_KEY`
- `melotts_vi` — lightweight Vietnamese, runs on CPU

## Quality modes

| Mode | ASR | Diarization | Alignment | Voice clone | TTS | Subtitle CPS |
|------|-----|-------------|-----------|-------------|-----|--------------|
| `fast` | faster-whisper | — | — | — | — | 18 |
| `balanced` | WhisperX | ✓ | ✓ | — | ✓ | 16 |
| `high` | WhisperX | ✓ | ✓ | ✓ | ✓ | 14 |

---

## Project structure

```
PhimNganRepositoryApp/
├── apps/
│   ├── api/python/translator_api/     FastAPI server
│   │   ├── providers/
│   │   │   ├── translate/             Translator providers (OpenAI, Gemini, Claude, LocalLLM)
│   │   │   ├── tts/                   TTS providers (10 providers: Edge, DashScope, Qwen3,
│   │   │   │                          VietVoice, VieNeu, CosyVoice, MeloTTS, Azure, Google, ElevenLabs)
│   │   │   ├── dubbing/               Dubbing align providers
│   │   │   ├── export/                Export providers
│   │   │   ├── mix/                   Audio mix providers
│   │   │   ├── render/                Render providers
│   │   │   ├── separation/            Audio separation (UVR5)
│   │   │   ├── subtitle/              Subtitle providers
│   │   │   └── cleanup/               Orphan cleanup
│   │   ├── routes/                    API endpoints
│   │   ├── models/                    SQLAlchemy models
│   │   ├── repositories/             Data access layer
│   │   └── observability/             Prometheus metrics
│   ├── worker/python/translator_worker/
│   │   ├── activities_phase3.py       Core pipeline activities (translate, TTS, QA, etc.)
│   │   ├── activities_voice_clone.py   Voice cloning activities
│   │   ├── activities_qa_multispeaker.py  Multi-speaker QA
│   │   ├── activities_providers.py    Provider-specific activities
│   │   ├── activities_phase4.py       Phase 4 activities
│   │   ├── activities_alignment.py    Alignment activities
│   │   ├── activities_cache.py        Cache management
│   │   ├── workflows_impl.py          Temporal workflow definitions
│   │   └── metrics.py                 Worker metrics
│   ├── tts-service/                   Standalone TTS service (optional)
│   └── web/                          Next.js UI + SDK
│       └── app/settings/page.tsx     TTS provider selector UI
├── packages/
│   └── shared/python/translator_shared/  Shared enums, configs, response types
├── infra/
│   ├── docker/                       docker-compose + Dockerfiles
│   └── helm/translator/              Helm chart 1.0
├── migrations/                        DB migration scripts
├── scripts/
│   ├── release.py                    semver bump + CHANGELOG
│   ├── migrate.py                    migration runner
│   ├── check_deprecations.py         deprecation scanner
│   └── release_e2e.py               full pipeline smoke test
├── docs/
│   ├── integrations.md               connecting real APIs
│   ├── integration-review.md         Phase 11 audit findings
│   ├── deprecation.md                deprecation timeline
│   ├── release.md                    release + rollback guide
│   └── HUONG-DAN-SU-DUNG.md          Vietnamese user guide
├── tests/                             Integration tests
├── CHANGELOG.md                       Full version history
├── pyproject.toml                     Python package config
├── VERSION                            Current version file
└── README.md
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Key variables:

| Variable | Description | Required for |
|----------|-------------|--------------|
| `DATABASE_URL` | PostgreSQL connection string | All modes |
| `TEMPORAL_HOST` | Temporal server address | All modes |
| `OPENAI_API_KEY` | OpenAI API key | OpenAI translator |
| `GEMINI_API_KEY` | Gemini API key | Gemini translator |
| `ANTHROPIC_API_KEY` | Anthropic API key | Claude translator |
| `DASHSCOPE_API_KEY` | Alibaba API key | DashScope TTS |
| `ELEVENLABS_API_KEY` | ElevenLabs API key | ElevenLabs TTS |
| `AZURE_TTS_KEY` | Azure TTS key | Azure TTS |
| `GOOGLE_TTS_KEY` | Google Cloud TTS key | Google TTS |
| `STORAGE_BACKEND` | `local` or `s3` | Storage |
| `JWT_SECRET` | 32-byte random secret | Auth |
| `TRANSLATOR_LOCAL_LLM_BACKEND` | `ollama` or `llama_cpp` | Local LLM translator |

---

## API reference

Full API docs: `http://localhost:8000/docs` (Swagger UI)

Key endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/healthz` | Liveness check |
| `GET` | `/readyz` | Readiness check |
| `POST` | `/projects` | Create project |
| `GET` | `/projects` | List projects |
| `GET` | `/projects/{id}` | Get project detail |
| `PUT` | `/projects/{id}/provider-configs` | Save provider config |
| `GET` | `/projects/{id}/provider-configs` | List provider configs |
| `POST` | `/projects/{id}/workflows` | Trigger workflow |
| `GET` | `/projects/{id}/workflows/{id}` | Get workflow status |
| `PUT` | `/projects/{id}/quality-mode` | Update quality mode |
| `GET` | `/projects/{id}/audit` | Audit log |

---

## SDK

Install the JS/TS client:

```bash
npm install @translator/sdk
# or: pnpm add @translator/sdk
```

```ts
import { TranslatorClient } from "@translator/sdk";

const client = new TranslatorClient({ baseUrl: "http://localhost:8000" });
const projects = await client.listProjects();
await client.triggerWorkflow(projectId, { quality_mode: "balanced" });
```

---

## Development

```bash
# Run tests
python -m pytest -q

# Type check Python
mypy apps packages

# Type check TypeScript SDK
cd apps/web/sdk && npm run typecheck

# Check deprecations
python scripts/check_deprecations.py

# Full release dry-run
python scripts/release_e2e.py

# Migration (PostgreSQL)
python scripts/migrate.py --dry-run
python scripts/migrate.py
```

---

## Release workflow

```bash
# 1. Check deprecations
python scripts/check_deprecations.py

# 2. Preview bump
python scripts/release.py --bump minor --dry-run

# 3. Execute bump
python scripts/release.py --bump minor

# 4. Review + commit
git add VERSION CHANGELOG.md releases/
git commit -m "release: v1.3.0"
git tag v1.3.0
git push origin v1.3.0   # triggers .github/workflows/release.yml
```

---

## Rollback

```bash
helm rollback translator <previous-revision>
python scripts/migrate.py --direction down --target 0001
python -c "from translator_api.cache import purge_all; purge_all()"
```

See `docs/release.md` for the full rollback procedure.

---

## Version history

See `CHANGELOG.md` for the complete release history. Summary:

| Version | Date | Highlights |
|---------|------|-----------|
| **1.3.0** | 2026-08-27 | Workflow TTS wiring (translate→TTS→DB chain), README fixes |
| **1.2.0** | 2026-08-27 | DashScope Qwen3-TTS provider + SSE streaming mode |
| **1.1.0** | 2026-08-27 | TTS metrics, Web UI selector, Dockerfile fix |
| **1.0.0** | 2026-08-26 | Initial release: ASR + translation + TTS + dubbing + render |

---

## License

Apache 2.0 — see `docs/licenses.md`.
