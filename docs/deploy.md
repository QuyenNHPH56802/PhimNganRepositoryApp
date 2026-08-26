# Deployment

Phase 4 brings up the production stack on OCI using
`docker-compose.prod.yml`. The compose file expects a `.env.prod` with:

```
PUBLIC_DOMAIN=translator.example.com
POSTGRES_PASSWORD=...
MINIO_ROOT_USER=...
MINIO_ROOT_PASSWORD=...
TRANSLATOR_STORAGE_BUCKET=translator
TRANSLATOR_SESSION_SECRET=...
GRAFANA_ADMIN_PASSWORD=...
MON_USER=ops
MON_PASSWORD=...
TRANSLATOR_OTEL_EXPORTER_OTLP_ENDPOINT=
```

## Bring-up

```bash
docker compose -f infra/docker-compose.prod.yml --env-file .env.prod pull
docker compose -f infra/docker-compose.prod.yml --env-file .env.prod up -d
docker compose -f infra/docker-compose.prod.yml exec api \
    alembic -c /app/alembic.ini upgrade head
```

Caddy auto-issues Let's Encrypt certificates when `PUBLIC_DOMAIN` resolves
to the host. The default `Caddyfile` ships with `tls internal` for safe
local runs.

## Topology

```
   ┌──────────────┐
   │   Browser    │
   └──────┬───────┘
          │ :443
   ┌──────▼─────────┐
   │     Caddy      │  TLS + routing
   └──┬─────┬─────┬─┘
      │     │     │
      ▼     ▼     ▼
    API  Web  Temporal UI
    │
    ▼
  Worker (GPU / CPU pools)
```

Storage: Postgres + MinIO. Replace MinIO with OCI Object Storage by
unsetting `TRANSLATOR_STORAGE_ENDPOINT` and providing `s3_*` credentials.

## Backups

`infra/scripts/backup.sh` runs `pg_dump` + uploads the artifact to S3.
Wire it to cron:

```cron
0 * * * * /opt/translator/scripts/backup.sh
```

Retention is governed by `BACKUP_KEEP_DAYS` (default 30). Restore with
`infra/scripts/restore.sh BACKUP_TS=20240101T000000Z`.

## Health checks

- `GET /api/healthz` — API readiness.
- `GET /temporal` (UI) — Temporal UI.
- `GET /prometheus/-/healthy` — Prometheus.
- `GET /grafana/api/health` — Grafana.

## Resource sizing (OCI shapes)

| Service | vCPU | RAM |
|---------|------|-----|
| api | 2 | 4G |
| worker | 4 | 8G |
| web | 1 | 1G |
| postgres | 2 | 8G |
| minio | 1 | 2G |
| prometheus | 1 | 2G |

Adjust `deploy.resources.limits` in compose before going live.

## Smoke test

```bash
curl -fsS https://$PUBLIC_DOMAIN/api/healthz
curl -fsS https://$PUBLIC_DOMAIN/api/projects -H "Authorization: Bearer $JWT"
```

If both succeed, the stack is live.

## OCI OKE (Kubernetes) deployment

For production at scale, deploy via the bundled Helm chart on OCI OKE.

```bash
# 1. Create OKE cluster
oci ce cluster create --name translator-prod --kubernetes-version v1.30 \
    --node-pool-shape VM.Standard.A1.Flex --node-shape-config '{"ocpus":4,"memoryInGBs":24}'

# 2. Add a GPU node pool (A100 shape)
oci ce node-pool create --cluster-id $CLUSTER_ID --name gpu-pool \
    --node-shape VM.Standard.A100.1 --node-config-details '{"size":2}'

# 3. Install helm chart
helm install translator infra/helm/translator \
    -f infra/helm/values.prod.yaml \
    --set secrets.postgresPassword=$POSTGRES_PASSWORD \
    --set secrets.sessionSecret=$TRANSLATOR_SESSION_SECRET \
    --set secrets.minioRootUser=$MINIO_ROOT_USER \
    --set secrets.minioRootPassword=$MINIO_ROOT_PASSWORD

# 4. Validate
kubectl rollout status deployment/api --timeout=300s
kubectl rollout status deployment/worker-cpu --timeout=300s
```

GPU nodes require the NVIDIA device plugin DaemonSet. The bundled worker
deployments have `nodeSelector` and `resources.limits.nvidia.com/gpu` set
so they only schedule on A100 nodes.

For OCI Object Storage instead of MinIO:

```bash
helm upgrade translator infra/helm/translator \
    --reuse-values \
    --set config.storageBackend=s3 \
    --set config.s3Endpoint=https://objectstorage.us-ashburn-1.oraclecloud.com
```