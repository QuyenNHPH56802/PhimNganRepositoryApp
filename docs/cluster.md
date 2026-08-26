# Cluster topology

Phase 6 ships the production cluster layout. Compose (`docker-compose.prod.yml`)
is sufficient for single-host production; Helm chart (`infra/helm/translator`)
covers OCI OKE / EKS / GKE deployments.

## Components

```
┌──────────────────────────────────────────────────────────────────┐
│                          Load Balancer                            │
└──────────────────────────────────────────────────────────────────┘
        │                                  │                │
        ▼                                  ▼                ▼
   Web (Next.js)                      API (FastAPI)   Temporal UI
                                                │
                                       ┌────────┴────────┐
                                       ▼                  ▼
                                Postgres           Redis (rate limit,
                                (state)           cache, shedder)
                                       │
                                       ▼
                                  MinIO (objects)
                                       ▲
                                       │
                                       │
   ┌──────────────────────── Worker pools ────────────────────────┐
   │                                                            │
   │   asr-queue    │ diarize-queue  │ align-queue              │
   │   translate-queue │ tts-queue  │ tts-cpu-queue            │
   │   separation-queue │ ocr-queue │ text-removal-queue      │
   │   cpu-queue                                                  │
   └──────────────────────────────────────────────────────────────┘
```

## Worker pools

| Pool | Task queue | Provider implementation |
|------|-----------|--------------------------|
| `worker-asr` | `asr-queue` | WhisperX / faster-whisper |
| `worker-diarize` | `diarize-queue` | pyannote 3.1 |
| `worker-align` | `align-queue` | wav2vec2 Chinese |
| `worker-translate` | `translate-queue` | OpenAI / Gemini / Claude / Local |
| `worker-tts-gpu` | `tts-queue` | VieNeu / CosyVoice 3.0 / VietVoice |
| `worker-tts-cpu` | `tts-cpu-queue` | MeloTTS Vi / Edge TTS |
| `worker-separation` | `separation-queue` | Demucs / BS-RoFormer / UVR5 |
| `worker-ocr` | `ocr-queue` | PaddleOCR / EasyOCR / CRAFT |
| `worker-removal` | `text-removal-queue` | LaMa / Inpaint-Anything / Telea |
| `worker-cpu` | `cpu-queue` | Subtitle / QA / Mix / Render / Export |

## Caching & shedder

- `ArtifactCache` wraps Redis metadata + S3 payload. Provider invocations
  check the cache first; misses go through, hits return the stored digest.
- Shedder middleware reads `pending_backlog` (in-process state updated by a
  Prometheus poller) and returns 503 when the queue is saturated.

## Scaling

| Signal | Action |
|--------|--------|
| p95 latency > 60s | Scale `worker-cpu` deployment |
| ASR queue pending > 5 | Scale `worker-asr` |
| TTS GPU memory pressure | Add GPU node to cluster |
| Backlog > 50 (soft) | Shedder triggers 503 + Retry-After: 30 |
| Backlog > 100 (hard) | Shedder triggers 503 + Retry-After: 120 |

## Bringing up the Helm chart

```bash
helm install translator infra/helm/translator \
    -f infra/helm/translator/values.prod.yaml \
    --set secrets.postgresPassword=$POSTGRES_PASSWORD \
    --set secrets.sessionSecret=$TRANSLATOR_SESSION_SECRET
```

`helm template` against `values.prod.yaml` is part of CI (`.github/workflows/benchmark.yml`)
so chart regressions are caught early.