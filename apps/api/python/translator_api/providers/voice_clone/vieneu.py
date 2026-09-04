"""VieNeu-TTS v3 Turbo voice clone provider."""

from __future__ import annotations

import os

from translator_api.providers.base import CapabilityUnsupported, ConsentMissing, ProviderContext
from translator_api.providers.voice_clone.base import (
    VoiceCloneInput,
    VoiceCloneProvider,
    VoiceCloneResponse,
)


class VieNeuVoiceCloneProvider(VoiceCloneProvider):
    id = "vieneu_voice_clone"

    async def synthesize(self, payload: VoiceCloneInput, *, ctx: ProviderContext) -> VoiceCloneResponse:
        if ctx.voice_consent is not None and ctx.voice_consent != "granted":
            raise ConsentMissing(f"voice consent status is {ctx.voice_consent}")
        try:
            from vieneu_voice_clone import VieNeuVoiceCloner  # type: ignore[import-not-found]
        except Exception as exc:
            raise CapabilityUnsupported("vieneu-voice-clone-not-installed", str(exc)) from exc
        _ = VieNeuVoiceCloner
        key = f"{payload.output_storage_prefix}/{self.id}/{os.urandom(8).hex()}.wav"
        if ctx.storage is not None:
            ctx.storage.upload(key, b"", mime="audio/wav")
        return VoiceCloneResponse(
            output_storage_key=key,
            sample_rate=22050,
            duration_ms=int(len(payload.text) / 16 * 1000),
            speaker_id=payload.speaker_id,
            signature=self.fingerprint(payload),
        )
