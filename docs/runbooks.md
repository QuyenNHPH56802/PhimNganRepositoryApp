# Runbooks

## Provider circuit breaker tripped

**Symptom**: `translator_provider_calls_total{status="failed"}` spikes,
provider returns `circuit-open`.

**Steps**:

1. Check provider status page (OpenAI/Gemini/Claude/ElevenLabs/Azure).
2. Inspect worker logs filtered by `provider_id`.
3. Reduce traffic by stopping the worker pool.
4. Once the provider recovers, breaker auto-recovers after
   `recovery_seconds`.
5. If still open after 1h, force-close by restarting the worker.

## Worker queue backlog

**Symptom**: `workflow_step_status_total{status="pending"}` stays above 5.

**Steps**:

1. Open Temporal UI → Workflows → filter by `status="running"`.
2. Identify the activity (`asr`, `tts`, `separation`, ...).
3. Scale the matching worker pool: add replicas via `docker compose up --scale worker-gpu=N`.
4. If GPU pool, check VRAM via `nvidia-smi`.

## Postgres connection exhausted

**Symptom**: `psycopg.OperationalError: connection pool exhausted`.

**Steps**:

1. Check `SELECT count(*) FROM pg_stat_activity`.
2. Identify long-running sessions (`state='idle in transaction'`).
3. Terminate with `SELECT pg_terminate_backend(pid)`.
4. Increase `max_connections` in Postgres if persistent.

## Disk full on MinIO

**Symptom**: `s3.UploadPart` returns `InternalError`.

1. `df -h` on the MinIO volume.
2. Run `infra/scripts/backup.sh` and prune old artifacts via the
   `OrphanCleanupProvider` (scheduled via Temporal cron).

## Backup restore

```bash
BACKUP_TS=20240101T000000Z ./scripts/restore.sh
```

Confirm:

1. `psql -c '\dt'` shows expected tables.
2. Replay last few workflows via Temporal UI.

## Audit + compliance

All consent transitions appear in `audit_logs`. Use Grafana → Loki →
filter `entity_type=voice_profile` for a full trail. Export to JSON via
`pg_dump --table=audit_logs`.

## Disaster recovery (full outage)

**Targets**: RPO 15 minutes, RTO 60 minutes.

1. Provision fresh OCI instance / OKE cluster.
2. Pull images (`docker compose pull`).
3. Run `infra/scripts/restore.sh BACKUP_TS=20240101T000000Z` with the most
   recent verified backup. `infra/scripts/backup_verify.sh` runs daily and
   refuses to mark a backup as healthy if any SHA256 mismatch is detected;
   the runbook treats the latest verified backup as the recovery point.
4. Update DNS / ingress to point at the new host (or keep TTL low).
5. Validate end-to-end with the smoke test below.

### Verification schedule

```cron
*/15 * * * * /opt/translator/scripts/backup.sh        # every 15 minutes
30 1 * * *   /opt/translator/scripts/backup_verify.sh  # 01:30 daily
```

`backup_verify.sh` exits non-zero on SHA mismatch and emits a Prometheus
metric `translator_backup_verify_status{result="ok|failed"}=1`. Alert rule:

```yaml
- alert: BackupVerifyFailed
  expr: translator_backup_verify_status{result="failed"} == 1
  for: 30m
```

### Cluster bring-up after restore

```bash
helm install translator infra/helm/translator \
    -f infra/helm/translator/values.prod.yaml
kubectl rollout status deployment/api --timeout=300s
kubectl rollout status deployment/worker-cpu --timeout=300s
```

### Smoke test

```bash
curl -fsS https://$PUBLIC_DOMAIN/api/healthz
curl -fsS https://$PUBLIC_DOMAIN/api/projects -H "Authorization: Bearer $JWT"
```

If both succeed, the cluster is live.