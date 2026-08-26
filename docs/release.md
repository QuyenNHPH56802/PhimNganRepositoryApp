# Release & Rollback

Phase 10 introduces a release manager (`scripts/release.py`), migration
runner (`scripts/migrate.py`), and a per-version rollback plan.

## Release flow

```
git tag vX.Y.Z
    │
    ▼
.github/workflows/release.yml
    │
    ├── python -m build  ──► dist/translator-X.Y.Z-py3-none-any.whl
    ├── pnpm build        ──► apps/web/sdk/dist/index.js
    ├── docker buildx     ──► translator-{api,worker,web}:X.Y.Z
    └── helm template      ──► infra/helm/translator/...
```

Manual steps before tagging:

1. `python scripts/check_deprecations.py` — must pass.
2. `python scripts/release.py --bump patch --dry-run` — preview.
3. `python scripts/release.py --bump patch` — bump VERSION + CHANGELOG.
4. `python scripts/migrate.py --dry-run` — verify migrations.
5. `git add VERSION CHANGELOG.md releases/ && git commit -m "release: X.Y.Z"`.
6. `git tag vX.Y.Z`.
7. `git push origin vX.Y.Z` — triggers CI.

## Rollback per version

### v1.0.0 (chart 1.0.0)

```bash
# Rollback to previous chart release
helm history translator
helm rollback translator <previous-revision>

# DB rollback (migrations are forward-only)
python scripts/migrate.py --direction down --target 0001

# Cache purge
kubectl exec -it deploy/api -- python -c \
    "from translator_api.cache import purge_all; purge_all()"

# Queue drain — cancel queued workflows
python scripts/drain_queue.py --task-queue translator-default
```

### v0.x (pre-release)

Rollback = `helm uninstall translator && helm install translator ...`
plus DB drop. Acceptable for alpha/beta only.

## Dry-run

```bash
python scripts/release.py --bump minor --dry-run
python scripts/migrate.py --dry-run
python scripts/release_dryrun.py    # full simulated release
```

`scripts/release_dryrun.py` chạy toàn bộ các bước của release.yml nhưng
không upload artifact. Exit code 1 nếu bất kỳ bước nào fail.

## Communication

- Release notes file: `releases/vX.Y.Z.md` (auto-gen từ git log).
- Slack `#ops-translator` announcement.
- Update status page sau khi smoke test 30 phút.

## Release branch protection

- `main` requires 2 reviews + CI green + on-call lead approval.
- Tag pushes cannot be retried; remove tag locally + delete remote tag.
- Hotfix flow: branch `hotfix/vX.Y.Z+1` off the previous tag.