# SLO Definitions

Phase 9 defines four SLOs and tracks burn rate through the month. The
authoritative values live in `scripts/error_budget.py`.

| SLO | Indicator | Target | Window | Burn rate alert |
|-----|-----------|--------|--------|-----------------|
| API availability | `translator_http_requests_total{status!~"5.."}` / all | 99.5% | 30d rolling | burn > 2x trong 1h |
| Workflow p95 latency | workflow POST endpoint | < 300s | 30d rolling | p95 > 600s trong 5m |
| Queue p99 depth | `translator_queue_depth` | < 50 | 30d rolling | depth > 100 trong 5m |
| Golden bench regression | Phase 5 metric | ≤ 5% | weekly | bất kỳ metric regression > threshold |

## Error budget

Error budget = (1 - target) × window_in_minutes.

For availability 99.5% × 30 days:
- budget = 0.5% × 30d × 24h × 60m = 216 minutes.

When the budget is exhausted, the team must halt non-critical work and
ship fixes (see `docs/on-call.md` for the playbook).

## Tracking

`scripts/error_budget.py` queries Prometheus and writes
`reports/budget.json`. The CI observability job runs this script weekly
and fails if any SLO breaches (see `.github/workflows/benchmark.yml`).

## Adjusting SLOs

SLOs are code; change them via PR and review by at least one engineer
+ on-call lead. Update `SLO_QUERIES` in `scripts/error_budget.py` and the
documentation in this file together.