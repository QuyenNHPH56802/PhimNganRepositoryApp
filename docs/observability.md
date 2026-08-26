# Observability

Phase 9 wires metrics, dashboards, alerts, SLOs, error tracking, dependency
scanning, synthetic probes, and an on-call runbook into a single operations
loop.

## Architecture

```
                    ┌──────────────────┐
                    │   Prometheus     │
                    └─────────┬────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
        Grafana        Alertmanager         SLO error budget
       (4 dashboards)   (9 alert rules)     (scripts/error_budget.py)
            ▲                 │                       ▲
            │                 ▼                       │
       dashboards.json    PagerDuty → on-call ─────────┘
                              │
                              ▼
                    Error reporter (Sentry-compatible)
                              ▲
                              │
              FastAPI middleware captures exceptions
```

## Metrics catalog

### API

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `translator_http_requests_total` | counter | method, endpoint, status | HTTP request count |
| `translator_http_request_duration_seconds` | histogram | method, endpoint | HTTP latency |
| `translator_provider_calls_total` | counter | kind, provider, status | Provider invocations |
| `translator_provider_call_duration_seconds` | histogram | kind, provider | Provider latency |
| `translator_active_projects` | gauge | — | In-flight projects |
| `translator_shedder_state` | gauge | — | 0=open, 1=soft, 2=hard |

### Worker

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `translator_activity_calls_total` | counter | name, status | Activity invocations |
| `translator_activity_duration_seconds` | histogram | name | Activity latency |
| `translator_queue_depth` | gauge | task_queue | Workflows pending in queue |
| `translator_cache_hit_total` | counter | kind | ArtifactCache hits |
| `translator_cache_miss_total` | counter | kind | ArtifactCache misses |
| `translator_gpu_memory_used_bytes` | gauge | gpu_index | GPU memory used |
| `translator_gpu_memory_total_bytes` | gauge | gpu_index | GPU memory total |
| `translator_gpu_utilization` | gauge | gpu_index | GPU utilization % |
| `translator_probe_success` | gauge | — | Synthetic probe result |

## SLOs

See `docs/slos.md` for the full table. The four SLOs are:

- **API availability**: 99.5% over 30d.
- **Workflow p95 latency**: < 300s.
- **Queue p99 depth**: < 50.
- **Golden bench regression**: ≤ 5% weekly.

Burn-rate alert triggers when error budget burns > 2x normal rate within
1 hour. Run `scripts/error_budget.py` to fetch the current state.

## Alert rules

See `infra/alerts/translator.rules.yml`. Nine rules cover latency,
errors, queue, GPU OOM, license expiry, backup fail, shedder, cache miss
ratio, and synthetic probe failures.

Severity routing:

| Severity | Channel |
|----------|---------|
| critical | PagerDuty primary |
| warning | Slack `#ops-translator` |
| info | Weekly digest email |

## Dashboards

`infra/grafana/dashboards/` ships four:

| Dashboard | Use case |
|-----------|----------|
| `api-overview.json` | request rate, p95 latency, error rate, shedder |
| `worker-pool.json` | queue depth, activity duration, cache hit ratio |
| `cluster.json` | node CPU, GPU memory + util, pod restarts |
| `cost.json` | provider calls/day, unit cost, daily spend |

Validate syntax: `promtool check rules` + `python -c "import json; json.load(open(f))"`.

## Error tracking

`translator_api/observability/error_reporter.py` ships a Sentry-compatible
payload. Sinks:

- `STDOUT` (default, dev/test).
- `HTTP_POST` (`TRANSLATOR_SINK_URL`).
- `NULL` (test, drops).

The reporter adds an HTTP breadcrumb per request, captures unhandled
exceptions, and never raises (a reporter that crashes the app is worse
than no reporter).

## Dependency scanning

`scripts/scan_dependencies.py`:

- Runs `pip-audit` against each `requirements*.txt`.
- Runs `npm audit --json`.
- Writes reports to `outputs/reports/dependencies/`.

`scripts/generate_sbom.py` produces CycloneDX SBOMs (`python_*.cdx.json`,
`node_*.cdx.json`).

Both run in `.github/workflows/observability.yml` weekly.

## Synthetic probe

`health_probe` workflow (Phase 9 `workflows/probe.py`) is a 4-step
end-to-end test:

1. `probe_create_project`
2. `probe_run_workflow`
3. `probe_publish_result`
4. Reports `translator_probe_success{result=ok|failed}`.

Cadence: every 5 minutes via Temporal cron. The CI workflow also runs the
probe once before merging changes to the worker modules.

## On-call

See `docs/on-call.md`. Rotation is weekly. Severity guide, escalation
matrix, communication templates, and handoff checklist are all there.

## CI

`.github/workflows/observability.yml` runs weekly and on every PR that
touches observability-related files. It:

1. Validates alert rules with `promtool check rules`.
2. Validates dashboard JSON.
3. Smoke-runs the error budget script.
4. Runs `pip-audit` + `npm audit`.

A failure blocks merge.

## Limitations

- No Sentry / GlitchTip backend integration (payload only).
- Synthetic probe uses stub activities; Phase 10 wires it to the real
  pipeline with a tiny audio fixture.
- Alertmanager routing receivers are configured in the Helm chart (Phase
  6) but not shipped as code here.
- Cluster dashboard relies on `kube_*` metrics; the bundle does not ship
  a Prometheus operator config.