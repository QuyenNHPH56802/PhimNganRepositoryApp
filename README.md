# Translator — Multimodal Video Localization Platform

**Version 1.0.0** · Apache 2.0

An end-to-end platform for translating and dubbing video/audio content. Given a
video file, it transcribes, diarizes speakers, translates between supported
language pairs, synthesizes TTS in the target voice, and outputs a dubbed
video with burned-in subtitles.

---

## Quick start

### 1. Clone and install

```bash
git clone https://example.com/translator.git
cd translator

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
          │(WhisperX)│ │(LLM API)│ │(ElevenLabs│ │ (FFmpeg) │
          └──────────┘ └────────┘ └──────────┘ └──────────┘
```

## Language pairs

| Source | Target | Providers |
|--------|--------|-----------|
| zh | vi | Deepseek, OpenAI, Gemini, Claude, NLLB |
| vi | zh | Deepseek, OpenAI, Gemini, Claude, NLLB |
| zh | en | OpenAI, Gemini, Claude, NLLB |
| en | zh | OpenAI, Gemini, Claude, NLLB |
| zh | ja | OpenAI, Gemini, Claude |
| zh | ko | OpenAI, Gemini, Claude |
| en | vi | OpenAI, Gemini, Claude, NLLB |
| vi | en | OpenAI, Gemini, Claude, NLLB |

## Quality modes

| Mode | ASR | Diarization | Alignment | Voice clone | TTS | Subtitle CPS |
|------|-----|-------------|-----------|-------------|-----|--------------|
| `fast` | faster-whisper | — | — | — | — | 18 |
| `balanced` | WhisperX | ✓ | ✓ | — | ✓ | 16 |
| `high` | WhisperX | ✓ | ✓ | ✓ | ✓ | 14 |

## Project structure

```
translator/
├── apps/
│   ├── api/python/translator_api/     FastAPI server
│   ├── worker/python/translator_worker/  Temporal activities
│   └── web/                          Next.js UI + SDK
├── packages/
│   └── shared/python/translator_shared/  Shared enums, configs
├── infra/
│   ├── docker/                       docker-compose + Dockerfiles
│   └── helm/translator/              Helm chart 1.0
├── migrations/                        DB migration scripts
├── scripts/
│   ├── release.py                    semver bump + CHANGELOG
│   ├── migrate.py                    migration runner
│   ├── check_deprecations.py         deprecation scanner
│   └── release_e2e.py                full pipeline smoke test
├── docs/
│   ├── integrations.md               connecting real APIs
│   ├── integration-review.md         Phase 11 audit findings
│   ├── deprecation.md                deprecation timeline
│   └── release.md                   release + rollback guide
└── pyproject.toml
```

## Configuration

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Key variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `TEMPORAL_HOST` | Temporal server address |
| `OPENAI_API_KEY` | OpenAI API key |
| `GEMINI_API_KEY` | Gemini API key |
| `STORAGE_BACKEND` | `local` or `s3` |
| `JWT_SECRET` | 32-byte random secret |

## API reference

Full API docs: `http://localhost:8000/docs` (Swagger UI)

Key endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/healthz` | Liveness check |
| `GET` | `/readyz` | Readiness check |
| `POST` | `/projects` | Create project |
| `GET` | `/projects` | List projects |
| `POST` | `/projects/{id}/workflows` | Trigger workflow |
| `PUT` | `/projects/{id}/quality-mode` | Update quality mode |
| `GET` | `/projects/{id}/audit` | Audit log |

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

## Development

```bash
# Run tests (58 tests)
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
git commit -m "release: v1.1.0"
git tag v1.1.0
git push origin v1.1.0   # triggers .github/workflows/release.yml
```

## Rollback

```bash
helm rollback translator <previous-revision>
python scripts/migrate.py --direction down --target 0001
python -c "from translator_api.cache import purge_all; purge_all()"
```

See `docs/release.md` for the full rollback procedure.

## License

Apache 2.0 — see `docs/licenses.md`.
