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
- **Qwen3-TTS on CPU is slow**: ~40 minutes for 50 seconds of audio
  (see `TODO_NEXT_STEPS.md`). Plan B options documented but not
  implemented: GPU (`device_map="cuda"`), quantization, or hosted
  DashScope endpoint.
- **`commit_msg.txt` and `req.json`**: not present in this repository
  snapshot; nothing to clean up.

## [1.0.0] - 2026-08-26

Initial public release of the Translator multimodal video localization
platform: ASR + translation + TTS + dubbing + render pipeline.
