"""Deterministic separation mock provider.

Real providers (Demucs, BS-RoFormer, UVR5) live alongside in
`providers/separation/*`. The mock returns empty placeholder storage keys for
each canonical track (vocals, background) so the data lifecycle
(CRUD + storage) can be exercised without GPU requirements.
"""

from __future__ import annotations

import hashlib

from translator_api.providers.base import ProviderContext
from translator_api.providers.separation.base import (
    LocalSeparationProvider,
    SeparationInput,
    upload_separation_output,
)
from translator_shared.provider_configs import SeparationProviderConfig
from translator_shared.provider_responses_extra import SeparationResponse


class MockSeparationProvider(LocalSeparationProvider):
    id = "separation.mock"
    capabilities = None  # type: ignore[assignment]

    async def _run_separation(self, payload: SeparationInput, ctx: ProviderContext) -> SeparationResponse:
        cfg = payload.config or SeparationProviderConfig()
        seed = int(hashlib.sha1(payload.asset_storage_key.encode()).hexdigest(), 16) % 1000
        vocals_key = upload_separation_output(ctx, payload.asset_storage_key, "vocals", self.id)
        background_key = upload_separation_output(ctx, payload.asset_storage_key, "background", self.id)
        sig = self.fingerprint(payload)
        sig.config_hash = f"mock-{seed}"
        return SeparationResponse(
            provider_id=self.id,
            model_id=self.id,
            model_version="mock-1",
            vocals_key=vocals_key,
            background_key=background_key,
            method=cfg.model_id,
            duration_ms=0,
            signature=sig,
        )
