# TTS Service

Independent FastAPI microservice that fronts Edge-TTS and Qwen3-TTS for the
Translator platform. Patterned after xdev-asia-labs/xTTS: a thin HTTP service
with chunked streaming and an LRU cache.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/healthz` | Liveness probe |
| `GET`  | `/readyz`  | Engine readiness + cache stats |
| `GET`  | `/voices?lang=vi` | List supported voices |
| `POST` | `/synthesize` | Synthesize speech |

### Request

```json
{
  "text": "Xin chào các bạn",
  "voice": "vi-VN-HoaiMyNeural",
  "rate": 1.0,
  "pitch": 0.0,
  "engine": "edge",
  "sample_rate": 24000
}
```

### Response

```json
{
  "audio_b64": "...",
  "mime": "audio/mpeg",
  "duration_ms": 1234,
  "voice": "vi-VN-HoaiMyNeural",
  "engine": "edge",
  "cache_hit": false,
  "chunk_count": 1
}
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3099` | HTTP port |
| `TTS_ENGINE` | `edge` | Default engine (`edge` or `qwen3`) |
| `TTS_MAX_CHUNK` | `500` | Max characters per chunk |
| `TTS_MAX_RETRIES` | `3` | Per-chunk retry budget |
| `TTS_MAX_TEXT_LENGTH` | `20000` | Hard limit on input text |
| `TTS_DEFAULT_VOICE` | `vi-VN-HoaiMyNeural` | Fallback voice |
| `TTS_CONCURRENCY` | `2` | Concurrent chunk requests |
| `TTS_CACHE_SIZE` | `100` | LRU size |

## Run locally

```bash
pip install -e .
python -m tts_service.main
# or
docker build -t translator-tts-service .
docker run --rm -p 3099:3099 translator-tts-service
```

## Tests

```bash
pytest -q apps/tts-service/tests
```
