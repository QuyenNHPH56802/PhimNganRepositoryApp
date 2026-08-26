# Real-world Integrations

Phase 1–10 deliver a working stub for every external dependency. To run
against real services, follow the checklist below.

## 1. Translation providers

| Provider | Env vars | Notes |
|----------|----------|-------|
| OpenAI | `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL` | The provider reads `cfg.api_key_env` from the per-project `ProviderConfig`; set `api_key_env=OPENAI_API_KEY` in the DB. |
| Gemini | `GEMINI_API_KEY`, `GEMINI_BASE_URL`, `GEMINI_MODEL` | Same shape. |
| Anthropic | `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`, `ANTHROPIC_MODEL` | Same shape. |
| Local NLLB | none | Set `provider_id=local_nllm` and load model weights once. |

Smoke test (no DB required):

```bash
export OPENAI_API_KEY=sk-...
pytest apps/api/python/tests/test_providers_translate.py::TestOpenAIHttpProvider -v
```

## 2. Object storage (S3 / R2 / MinIO)

1. Create a bucket (`translator-prod`).
2. Issue an IAM access key with `s3:GetObject`, `s3:PutObject`,
   `s3:ListBucket` scoped to that bucket.
3. Fill `.env`:
   ```
   STORAGE_BACKEND=s3
   S3_BUCKET=translator-prod
   S3_REGION=ap-southeast-1
   S3_ACCESS_KEY=...
   S3_SECRET_KEY=...
   ```
4. For Cloudflare R2 / MinIO, also set `S3_ENDPOINT=https://...`.

Verify:

```python
from translator_api.storage_pkg import S3CompatibleStorage
S3CompatibleStorage().presign_put("asset/sample.mp4", ttl=3600)
```

## 3. Kubernetes (worker scheduling)

Phase 6 wires the worker to call `kube_batch.schedule(...)` for GPU
jobs. To enable:

```bash
export KUBE_CONFIG=$HOME/.kube/config
export KUBE_NAMESPACE=translator
export KUBE_GPU_NODE_LABEL=nvidia.com/gpu.present
```

The Helm chart (`infra/helm/translator`) installs with:

```bash
helm upgrade --install translator infra/helm/translator \
  --values values-prod.yaml \
  --set worker.gpus=1
```

## 4. Auth (JWT)

Set `JWT_SECRET` to a 32-byte random string. The API validates
`Authorization: Bearer <token>` against HS256 by default. To rotate:

```bash
python scripts/jwt_rotate.py --new-secret $(openssl rand -hex 32)
```

## 5. Observability

- **Prometheus**: scrape the API's `/metrics` endpoint. Set
  `PROMETHEUS_URL` for SLO/error-budget scripts.
- **OpenTelemetry**: set `OTEL_EXPORTER_OTLP_ENDPOINT` to ship traces.
- **Sentry**: set `SENTRY_DSN` to capture unhandled exceptions.

## 6. Voice cloning consent

`apps/api/python/translator_api/consent/` records speaker consent
per-project. Production deploys must:

1. Capture consent text per locale (`apps/web/messages/{locale}.json`
   already has the strings).
2. Persist `ConsentRecord` rows with `speaker_id`, `asset_id`,
   `signed_at`, `expires_at`.
3. Enforce expiry in `provider.consent_required` activities.

## 7. Production checklist

Before tagging `vX.Y.Z`:

- [ ] `make test` is green (58 tests).
- [ ] `make typecheck` passes.
- [ ] `python scripts/check_deprecations.py` passes.
- [ ] `python scripts/release_dryrun.py` passes.
- [ ] Helm chart `infra/helm/translator` renders without errors.
- [ ] On-call rotation has reviewed `releases/vX.Y.Z.md`.
- [ ] Smoke test from a fresh VM in staging region.