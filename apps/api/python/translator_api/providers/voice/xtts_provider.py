"""XTTS voice cloning provider (skeleton).

Real XTTS model lives behind `transformers` + heavy torch + Coqui model
weights. This module raises `CapabilityUnsupported` until those are wired in,
giving clients a clear error to fall back to the mock provider.
"""

from __future__ import annotations

from translator_api.providers.base import (
    CapabilityUnsupported,
    ProviderContext,
)
from translator_api.providers.voice.base import (
    VoiceCloneInput,
    VoiceCloneProvider,
    VoiceCloneResponse,
)


class XttsVoiceCloneProvider(VoiceCloneProvider):
    id = "voice.xtts"

    async def _run_cloning(self, payload: VoiceCloneInput, ctx: ProviderContext) -> VoiceCloneResponse:
        try:
            import torch  # type: ignore[import-not-found]
            import TTS  # type: ignore[import-not-found]  # Coqui TTS package
        except Exception as exc:
            raise CapabilityUnsupported(
                f"{self.id}-missing-deps",
                f"Install torch + TTS to enable XTTS: {exc}",
            ) from exc
        raise CapabilityUnsupported(
            f"{self.id}-not-implemented",
            "XTTS integration pending model weights and GPU target.",
        )
