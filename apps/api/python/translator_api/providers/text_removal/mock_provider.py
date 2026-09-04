"""Deterministic text-removal mock provider.

Returns a placeholder storage key so the data lifecycle (job → output asset)
can be exercised without GPU / model weights.
"""

from __future__ import annotations

import hashlib

from translator_api.providers.base import ProviderContext
from translator_api.providers.text_removal.base import (
    TextRemovalInput,
    TextRemovalProvider,
    TextRemovalResponse,
)


class MockTextRemovalProvider(TextRemovalProvider):
    id = "text_removal.mock"
    capabilities = None  # type: ignore[assignment]

    async def _run_inference(
        self, payload: TextRemovalInput, ctx: ProviderContext
    ) -> TextRemovalResponse:
        seed = int(hashlib.sha1(payload.asset_storage_key.encode()).hexdigest(), 16) % (10**6)
        output_key = (
            f"text_removal/{self.id}/{seed:08x}/{payload.strategy}/output.bin"
        )
        if ctx.storage is not None:
            ctx.storage.upload(output_key, b"\x00\x00\x00\x00", mime="application/octet-stream")

        sig = self.fingerprint(payload)
        sig.config_hash = f"mock-{seed}"
        return TextRemovalResponse(
            output_storage_key=output_key,
            method=payload.strategy,
            signature=sig,
        )
