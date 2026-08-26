# On-call Runbook

Phase 9 ships an on-call runbook covering the alerts from
`infra/alerts/translator.rules.yml`. The expected rotation is weekly.

## Alert triage flowchart

```
ALERT  →  PagerDuty page
   │
   ▼
Acknowledge within 5 minutes
   │
   ▼
Grafana → dashboard
   │
   ▼
Runbook matches incident? ── yes ──► follow scenario
   │              │
   │              no
   ▼              ▼
Escalate       Debug via logs / metrics
```

## Severity guide

| Severity | Response time | Examples |
|----------|---------------|----------|
| critical | < 15 minutes | API 5xx > 2%, backup verify fail, synthetic probe fail |
| warning | < 1 hour | API p95 > 5s, queue backlog > 50, GPU OOM imminent |
| info | < 1 day | Cache miss ratio high |

## Common incidents

### 1. Workflow stuck

**Signal**: `translator_queue_depth{queue=...}` grows, activity duration
flatlines for >10 minutes.

**Steps**:

1. Open Temporal UI → namespace `default` → workflow list.
2. Identify stuck activity (look for retry exhaustion).
3. Click workflow → Terminate or Cancel.
4. If persistent: check provider error rate (`sum by (provider) (rate(translator_provider_calls_total{status="failed"}[5m]))`).
5. If provider is the issue: enable fallback (Policy from `policy_for(mode)`).
6. Post incident to `#ops-translator` with runbook link.

### 2. GPU OOM

**Signal**: `GPUOOMImminent` fires; worker logs `CUDA OOM`.

**Steps**:

1. Identify workload in `worker-tts-gpu` or `worker-asr`.
2. `kubectl describe pod` → check GPU index.
3. `kubectl logs` → identify large input.
4. Scale `worker-tts-gpu` deployment: `kubectl scale deploy worker-tts-gpu --replicas=N+1`.
5. If persistent: pin `max_input_seconds` in provider config.
6. Add postmortem to `docs/postmortems/`.

### 3. Queue saturation

**Signal**: `QueueBacklogHigh` for `task_queue=...`.

**Steps**:

1. Identify the queue in Prometheus.
2. Scale the matching worker pool (Phase 6 helm chart).
3. Confirm shedder not in HARD state — if so, requests are being rejected; back off new traffic.
4. Run `scripts/scale_test.py --projects 5` to reproduce.
5. If saturation persists > 30m, page secondary on-call.

### 4. License expiry

**Signal**: `LicenseExpiringSoon` fires.

**Steps**:

1. Check `translator_license_expiry_seconds` gauge (or run `scripts/license_audit.py`).
2. Identify provider (OpenAI / Gemini / Claude / Local model).
3. Renew API key, push to vault.
4. Restart API to reload env: `kubectl rollout restart deploy/api`.
5. Verify metric clears within 5 minutes.

### 5. Backup verify fail

**Signal**: `BackupVerifyFailed` for 30 minutes.

**Steps**:

1. SSH to backup runner.
2. Inspect S3 bucket `translator-backups` for missing shards.
3. Run `infra/scripts/backup_verify.sh BACKUP_TS=...`.
4. If checksum mismatch: trigger restore test from previous verified backup.
5. Page infra team if root cause unclear.

## Escalation matrix

| Role | Primary | Backup |
|------|---------|--------|
| API | @oncall-1 | @oncall-2 |
| Worker | @oncall-2 | @oncall-3 |
| Infra | @infra-lead | @sre-lead |
| Vendor (provider) | per provider runbook | provider support portal |

## Communication template

```text
[SEV-NAME] <one-line summary>
- Started: HH:MM UTC
- Impact: X% requests degraded
- Current status: <investigating|mitigated|resolved>
- Next update: in 15 minutes
```

Post in `#ops-translator` and update status page.

## Handoff checklist

When rotating on-call:

- [ ] Verify PagerDuty schedule
- [ ] Read last 24h incident notes
- [ ] Verify dashboards loaded
- [ ] Verify alertmanager receivers
- [ ] Run `scripts/error_budget.py` → confirm budget not exhausted
- [ ] Sync with outgoing on-call (5 min)