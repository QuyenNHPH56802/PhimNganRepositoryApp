# Security

Phase 4 ships the auth surface required to deploy Translator to a public
host. The default local flow uses an HS256 JWT signed with a dev secret;
production deployments must override `TRANSLATOR_SESSION_SECRET` with a
strong, rotated secret or switch to RS256 with a managed JWT issuer.

## RBAC

| Role | Description | Permissions |
|------|-------------|-------------|
| `owner` | Project owner (creator or first admin) | Full control: members, workflows, exports, deletions |
| `editor` | Operational staff | Run/cancel workflows, upload assets, edit translations |
| `viewer` | Read-only stakeholder | View projects, audit log, exports |

Membership is enforced via `require_project_role(minimum: Role)` on each
project-scoped route. The project owner always has the highest role.

```python
@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: UUID,
    identity: UserIdentity = Depends(_identity),
    db: Session = Depends(get_db),
):
    require_project_role(project_id, Role.OWNER, db=db, identity=identity)
    ...
```

## OIDC

`translator_api/security/oidc/` is the pluggable provider list. Phase 4 ships:

- `google.py` — Google OIDC (configured via `GOOGLE_OIDC_CLIENT_ID`/`SECRET`).
- `azure_ad.py` — Azure AD (via `AZURE_AD_TENANT`).
- `authentik.py` — Authentik (via `AUTHENTIK_ISSUER`).

In dev mode the `/auth/login/stub` endpoint issues a JWT for any email to
let engineers exercise the API.

## CSRF

Mutating routes require the `X-CSRF-Token` header to match the
`translator_csrf` cookie (`double-submit cookie`). The web client obtains a
token via `GET /auth/csrf`.

## Consent workflow

Voice cloning providers (`vieneu`, `vietvoice`, `cosyvoice`, `elevenlabs`)
must obtain consent before cloning. The lifecycle is:

```
draft -> requested -> granted | revoked
```

Every transition writes an `audit_logs` row:

```
entity_type: voice_profile
entity_id: <uuid>
action: consent_requested | consent_granted | consent_revoked
payload: { actor, evidence_key, reason }
```

Worker activities refuse to run a provider unless
`voice_profile.consent_status == "granted"`. Evidence keys point to signed
TOS documents stored in the object store.

## Rate limit + circuit breaker

`translator_api/util/throttle.py` ships:

- `TokenBucket` (in-process).
- `SlidingWindowRedis` (backed by Redis at `TRANSLATOR_REDIS_URL`).
- `CircuitBreaker` (closed → open → half-open after `recovery_seconds`).

All HTTP provider calls must wrap their invocation:

```python
breaker = CircuitBreaker(failure_threshold=5, recovery_seconds=30)
result = await run_with_breaker(breaker, lambda: client.acompletion(...))
```

When the breaker opens, the next call returns `ProviderError("circuit-open")`
and the worker schedules a back-off via Temporal retries.

## Secrets

| Variable | Purpose |
|----------|---------|
| `TRANSLATOR_SESSION_SECRET` | HMAC secret for HS256 JWTs |
| `TRANSLATOR_REDIS_URL` | Redis for sliding-window |
| `POSTGRES_PASSWORD` | Postgres admin |
| `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` | MinIO root |
| `GRAFANA_ADMIN_PASSWORD` | Grafana admin |
| `MON_USER`/`MON_PASSWORD` | Caddy basic auth for monitoring |

These must never be checked into git. Use OCI Vault in production.