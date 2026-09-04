"""Deterministic voice cloning mock provider.

For development and tests: produces an embedding and a (placeholder) preview
key derived from the sample key. Real provider implementation (XTTS) lives in
`xtts_provider.py` and raises CapabilityUnsupported.
"""

from __future__ import annotations

import hashlib

from translator_api.providers.base import ProviderContext
from translator_api.providers.voice.base import (
    VoiceCloneInput,
    VoiceCloneProvider,
    VoiceCloneResponse,
    upload_voice_clone_embedding,
)


class MockVoiceCloneProvider(VoiceCloneProvider):
    id = "voice.mock"
    capabilities = None  # type: ignore[assignment]

    async def _run_cloning(self, payload: VoiceCloneInput, ctx: ProviderContext) -> VoiceCloneResponse:
        seed = int(hashlib.sha1(payload.sample_storage_key.encode()).hexdigest(), 16) % (10**6)
        embedding_key = upload_voice_clone_embedding(ctx, payload.sample_storage_key, self.id)

        preview_key: str | None = None
        if payload.text_preview:
            key = f"voice_clone/{self.id}/{seed:08x}/preview.bin"
            if ctx.storage is not None:
                ctx.storage.upload(key, b"\x00\x00\x00\x00", mime="audio/wav")
            preview_key = key

        # Quality score is seeded so it's reproducible per sample.
        score = 0.6 + ((seed % 40) / 100.0)

        sig = self.fingerprint(payload)
        sig.config_hash = f"mock-{seed}"

        return VoiceCloneResponse(
            embedding_storage_key=embedding_key,
            preview_storage_key=preview_key,
            duration_ms=0,
            quality_score=score,
            provider_id=self.id,
            method=payload.strategy,
            signature=sig,
        )
