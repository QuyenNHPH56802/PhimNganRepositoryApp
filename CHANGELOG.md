# Changelog

All notable changes to the Translator platform are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-08-27

### Added
- **TTS service `/metrics` endpoint** (`apps/tts-service/tts_service/main.py`):
  Exposes Prometheus metrics `tts_generate_seconds`, `tts_audio_seconds`,
  `tts_chunks_total`, and `tts_requests_total` labelled by engine.
- **Worker TTS metrics** (`apps/worker/python/translator_worker/metrics.py`):
  Adds `tts_generate_seconds` and `tts_audio_seconds` histograms plus an
  `observe_tts(...)` helper for activity-side instrumentation.
- **API TTS metrics** (`apps/api/python/translator_api/observability/metrics.py`):
  Mirrors the worker-side metrics so dashboards aggregate by provider
  regardless of where synthesis runs.
- **Qwen3-TTS provider instrumentation** (`apps/api/python/translator_api/providers/tts/qwen3.py`):
  Wraps synthesis calls in `observe_tts_call(...)` to track wall-clock
  time and audio length.
- **Web UI TTS provider selector** (`apps/web/app/settings/page.tsx`):
  A `<select>` dropdown replaces the static `vietvoice_tts` default and
  lets admins pick any of the 9 registered TTS providers (Edge, Qwen3,
  VietVoice, VieNeu, CosyVoice 3, Azure, Google, ElevenLabs, MeloTTS).
- **i18n `tts.providers` keys** for `zh`, `th`, `pt`, `ko`, `ja`, `fr`,
  `de`, `es` locales (matching the existing `en.json` / `vi.json` keys).
- **Qwen3-TTS user guide** (`docs/HUONG-DAN-SU-DUNG.md`, section 6.5):
  Step-by-step setup, hardware requirements, SDK install, checkpoint
  download, comparison table, and links to `docs/integrations.md`.

### Changed
- **TTS Dockerfile** (`apps/tts-service/Dockerfile`):
  Installs `sox`, `libsndfile1`, `ffmpeg` system packages so `librosa`
  no longer crashes when processing audio. Adds `soundfile`, `librosa`,
  and `prometheus-client` to the pip install step.
- **TTS service dependencies** (`apps/tts-service/pyproject.toml`):
  Adds `prometheus-client>=0.20` and `soundfile>=0.12`.
- **Worker `tts_synthesize` activity** (`apps/worker/python/translator_worker/activities_phase3.py`):
  Now resolves the provider from the default registry using the project's
  configured `provider_id` (so `edge_tts` / `qwen3_tts` / `vietvoice_tts`
  etc. all work) and records TTS timing via `observe_tts(...)`. Falls
  back to `VietVoiceTtsProvider` only when the registry has no matching
  provider.
- **Default TTS** in `apps/web/app/settings/page.tsx` switched from
  `vietvoice_tts` to `edge_tts` (no GPU required).
- **Bumped to 1.1.0** in `VERSION`, root `pyproject.toml`, `README.md`,
  and `docs/HUONG-DAN-SU-DUNG.md`.

### Known Limitations (carried over from 1.0.0)
- ~~**Qwen3-TTS on CPU is slow**~~: Resolved in 1.2.0 via the new
  `dashscope_tts` (hosted Qwen3) provider. No GPU or local model
  download required.

## [1.2.0] - 2026-08-27

### Added
- **DashScope Qwen3-TTS provider** (`apps/api/python/translator_api/providers/tts/cloud_qwen3.py`):
  New `dashscope_tts` provider that calls Alibaba Cloud Model Studio's
  hosted Qwen3-TTS endpoint. No GPU, no local model download — just set
  `DASHSCOPE_API_KEY` and synthesis runs on Alibaba's servers. Supports
  `qwen3-tts-flash` (default, fast) and `qwen3-tts-instruct-flash`
  (instruction-controlled). Auto-detects language from text Unicode
  ranges and chunks inputs to stay within the 512-token limit.
- **DashScope SSE streaming mode** (`apps/api/python/translator_api/providers/tts/cloud_qwen3.py`):
  Opt-in via `DASHSCOPE_STREAMING=1`. Streams Base64-encoded audio chunks
  via Server-Sent Events for ~0.5s time-to-first-byte vs ~2–5s for the
  default URL-based path. Trade-off: ~10–15% higher total latency
  because of Base64 decode overhead, but better suited for interactive
  previews and real-time feedback.
- **DashScope provider tests** (`apps/api/python/tests/test_providers_tts_dashscope.py`):
  Unit tests covering language detection (Chinese/Japanese/Korean/Russian/
  English/Auto), text chunker, fingerprint, missing API key, HTTP error
  responses, empty text, SSE chunk parsing, and streaming mode dispatch.
- **DashScope env vars** (`.env.example`): `DASHSCOPE_API_KEY`,
  `DASHSCOPE_BASE_URL`, and `DASHSCOPE_STREAMING`.

### Changed
- **Web UI TTS dropdown** (`apps/web/app/settings/page.tsx`):
  Added "DashScope Qwen3 (cloud)" option between Edge TTS and local Qwen3.
- **`docs/integrations.md`**: Added DashScope row to the TTS providers
  table and a step-by-step quick start section with curl example.
- **`docs/HUONG-DAN-SU-DUNG.md`**: Section 6.5 reorganized into 4 groups
  (free/hosted/local/commercial), added DashScope setup guide, and added
  DashScope column to the comparison table.
- **Bumped to 1.2.0** in `VERSION`, root `pyproject.toml`, `README.md`,
  and `docs/HUONG-DAN-SU-DUNG.md`.

## [1.0.0] - 2026-08-26

Initial public release of the Translator multimodal video localization
platform: ASR + translation + TTS + dubbing + render pipeline.
