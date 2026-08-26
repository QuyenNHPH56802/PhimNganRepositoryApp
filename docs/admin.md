# Admin Dashboard

Phase 8 ships an admin dashboard for OWNER users. The dashboard surfaces:

- Audit log viewer
- Voice profile lifecycle management
- Golden dataset CRUD with license guard
- Quality mode switch
- Live workflow progress + cancel button

All admin endpoints require `users.is_admin = true`. Project-level role
only gates `/projects/{id}/*`. An admin can grant themselves any new
project by using the OWNER role assertion at the route level.

## Routes

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/admin/audit-logs` | filterable list (`entity`, `action`, `actor`, limit, offset) |
| GET | `/admin/audit-logs/{id}` | single audit row |
| GET | `/admin/voice-profiles` | list profiles; filter by `project_id`, `speaker_id`, `consent_status` |
| POST | `/admin/voice-profiles` | create profile (consent_status=pending\|granted\|revoked; granted requires evidence_key) |
| PUT | `/admin/voice-profiles/{id}` | transition consent. State machine: pending→{granted, revoked}, granted→revoked, revoked→granted |
| GET | `/admin/datasets` | list golden sentences |
| GET | `/admin/datasets/provenance` | read `manifest.yaml` |
| POST | `/admin/datasets/sentences` | append golden sentence; license ∈ {CC-BY-SA-4.0, CC-BY-4.0, CC0} |

## Permission gates

### Project role

| Role | Audit/voice/dataset admin | Project page | Member manage |
|------|---------------------------|--------------|---------------|
| OWNER | yes | yes | yes |
| EDITOR | no | yes | no |
| VIEWER | no | read-only | no |

Admin endpoints check `users.is_admin`. The `users.is_admin` flag is set
manually in production by direct SQL — there is no UI to escalate to admin.
Local dev seeds an admin via `scripts/seed_admin.py`.

### Voice consent state machine

```
pending ─► granted   (requires evidence_key)
pending ─► revoked
granted ─► revoked
revoked ─► granted   (requires evidence_key)
```

Attempting any other transition returns `409 Conflict`. Setting
`granted` without `evidence_key` returns `422 Unprocessable Entity`.

## Audit log conventions

| Entity | Action | Trigger |
|--------|--------|---------|
| `user` | `created` | user signup |
| `user` | `role_changed` | admin role update |
| `project` | `created`, `deleted`, `quality_mode_set` | router mutations |
| `voice_profile` | `created`, `consent_granted`, `consent_revoked` | admin voice endpoints + voice-clone activities |
| `dataset` | `sentence_added` | admin datasets endpoint |
| `access_request` | `requested`, `approved`, `rejected` | Phase 4 access request flow |

`audit_logs.payload` is JSON; store small fields only. Do not log audio
content or full PII (consent evidence stays as storage key).

## Quality mode policy

`/projects/{id}/quality-mode` accepts:

```json
{ "mode": "fast" | "balanced" | "high" }
```

| Mode | ASR | Diarize | Alignment | Voice clone | Mixer | Subtitle CPS |
|------|-----|---------|-----------|-------------|-------|--------------|
| fast | faster-whisper | no | no | no | no | 18 |
| balanced | whisperx | yes | yes | no | yes | 16 |
| high | whisperx | yes | yes | yes | yes | 14 |

The policy is also persisted to `projects.quality_mode` so workflows
started after the call use the new policy.

## Progress streaming

`/workflows/{id}/ws` (WebSocket) and `/workflows/{id}/events` (SSE) both
subscribe to the in-process pubsub. Activities call `publish_step(...)`
to push updates; subscribers receive step rows with `name`, `status`,
`progress_pct`, and `progress_message`.

The cancel button posts to `/workflows/{id}/cancel` which uses Temporal
`WorkflowClient.cancel`.

## Local dev setup

```bash
# Seed an admin user
python scripts/seed_admin.py --email owner@team --password owner-pass

# Login and visit
http://localhost:3000/admin
```

## CI

`tests/e2e/admin.spec.ts` runs with `pnpm playwright test` after the API
seed script. CI env: `E2E_BASE_URL=http://localhost:3000`.

## Limitations

- Audit log viewer lacks CSV export; coming Phase 9.
- Dataset manager edits golden sentences JSONL in-place. No diff/preview.
- Live workflow cancel does not abort running activities mid-flight;
  Temporal schedules the cancellation after the current activity returns.