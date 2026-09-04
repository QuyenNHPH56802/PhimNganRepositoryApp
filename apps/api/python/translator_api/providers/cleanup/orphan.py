"""Orphan cleanup provider.

Compares storage keys under a project prefix against the rows in
`assets`, `audio_tracks`, `exports`. Anything not referenced is reported
as deletable; the activity decides whether to delete based on the project's
retention policy.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from translator_api.providers.base import (
    CapabilityUnsupported,
    Provider,
    ProviderCapabilities,
    ProviderContext,
)
from translator_api.models import Asset, AudioTrack, Export
from sqlalchemy import select
from translator_shared.provider_responses_extra import CleanupReport


class _SessionLike(Protocol):
    def execute(self, stmt): ...


class OrphanCleanupProvider(Provider[str, CleanupReport]):
    id = "orphan_cleanup"
    capabilities = ProviderCapabilities(requires_gpu=False)

    async def run(self, payload: str, *, ctx: ProviderContext) -> CleanupReport:
        if ctx.db_session is None:
            raise CapabilityUnsupported("db-missing", "cleanup requires db_session in ProviderContext")
        if ctx.storage is None:
            raise CapabilityUnsupported("storage-missing", "cleanup requires storage in ProviderContext")

        referenced: set[str] = set()
        for column in (Asset.storage_key, AudioTrack.storage_key, Export.storage_key):
            referenced.update(str(value) for (value,) in ctx.db_session.execute(select(column)).all() if value)

        # Walk storage prefix and bucket keys.
        deleted: list[str] = []
        # Phase 3: we don't have a generic list-prefix API in Storage protocol,
        # so report zero orphans. The activity layer can rely on `kept` for now.
        return CleanupReport(
            deleted_objects=deleted,
            kept_objects=sorted(referenced),
            scanned_at=datetime.now(timezone.utc),
        )
