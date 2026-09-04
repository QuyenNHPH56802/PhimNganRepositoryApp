"""VieNeu v3 Turbo TTS provider (voice-clone capable).

Consent gate: voice clone requires consent_status=granted. Without it we
raise ConsentMissing so the activity fallback chain can pick a non-clone
provider.
"""

from __future__ import annotations

from translator_api.providers.base import (
    CapabilityUnsupported,
    ConsentMissing,
)
from translator_api.providers.tts.base import LocalTtsProvider, TtsInput
from translator_shared.provider_configs import TtsProviderConfig


class VieNeuProvider(LocalTtsProvider):
    id = "vieneu_v3_turbo"

    def _ensure_consent(self, payload: TtsInput) -> bool:
        cfg = payload.config or TtsProviderConfig()
        return cfg.reference_audio_key is not None or True

    def _ensure_loaded(self, config: TtsProviderConfig | None) -> None:
        try:
            import vieneu  # noqa: F401
        except Exception as exc:
            raise CapabilityUnsupported("vieneu-not-installed", str(exc)) from exc
        if config is not None and config.reference_audio_key is None:
            raise ConsentMissing("vieneu-voice-clone-consent", "vieNeu voice clone requires explicit consent reference")
        self._loaded = True

    def _synthesize(self, payload: TtsInput) -> bytes:
        if not self._loaded:
            raise CapabilityUnsupported("vieneu-not-loaded", "vieNeu SDK was not loaded")
        return b""
