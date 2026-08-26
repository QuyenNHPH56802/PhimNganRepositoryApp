# Multi-region advisory

Phase 6 ships single-region Temporal + Postgres + MinIO. This document
captures the design notes for going multi-region **later** without
rewriting the application code.

## Goals

- **Read latency < 200ms p95** for users in the second region.
- **RPO 15 minutes**, **RTO 60 minutes** per region.
- Zero-downtime upgrades (rolling).

## Topology

```
                     ┌─────────────────────────────┐
                     │      Global Load Balancer   │
                     └────────────┬────────────────┘
                                  │
                ┌─────────────────┼──────────────────┐
                ▼                                    ▼
    ┌────────────────────────┐         ┌────────────────────────┐
    │   Region A (primary)   │         │   Region B (replica)   │
    │  Postgres primary      │◀───────▶│  Postgres read replica │
    │  MinIO primary         │         │  MinIO CRR bucket      │
    │  Temporal namespace A  │         │  Temporal namespace B  │
    └────────────────────────┘         └────────────────────────┘
```

## Postgres

- Region A primary (write).
- Region B read replica (lag < 5s).
- Promote when Region A down; client apps reconnect via RDS Proxy.

## Object storage

- MinIO (or OCI Object Storage) in Region A: `translator`.
- Cross-region replication (CRR) bucket `translator-crr` in Region B.
- Workers in Region B read CRR; if Region A down, fall back to Region B.

## Temporal

- Region A namespace `primary` (write workflows).
- Region B namespace `replica` (start workflows that can survive A outage).
- Workflows are routed by `TRANSLATOR_NAMESPACE` env on the API side.
- Cross-region replication not supported by Temporal OSS; cloud customers
  should use Temporal Cloud global namespaces.

## Cache (Redis)

- Region A primary; Region B secondary with sentinel failover.
- `ArtifactCache` keys are deterministic by fingerprint, so failover does
  not corrupt cache; it just re-computes for the missing window.

## Latency budget

| Tier | p50 | p95 |
|------|-----|-----|
| API | 80ms | 250ms |
| Worker (CPU) | 1s | 5s |
| Worker (GPU) | 5s | 30s |
| Object GET | 50ms | 200ms |

## Failure modes

| Scenario | Behavior |
|----------|----------|
| Region A DB outage | Promote Region B. Read replica accepts writes for the duration of recovery. |
| Region A object loss | Region B CRR bucket holds the latest artifact. Workers auto-resolve. |
| Region A Temporal loss | Workflows must be replayed via Region B namespace. New workflows land in B; running workflows may need manual continuation. |
| Region A cache loss | Cold start; workers re-run providers. Cache rebuilds from new requests. |

## What is NOT shipped

- No actual CRR bucket — Phase 6 stays single-region.
- No Temporal multi-cluster replication — Phase 6 uses a single namespace.
- No read-replica logic in the API — `DATABASE_URL` points to a single host.

These are documented here so the next phase can pick them up without
re-designing the provider contracts.