"""VietVoice TTS provider (Apache-2.0).

Vietnamese TTS targeted at on-prem deployment. Phase 3 lazy-imports the
underlying SDK; on missing SDK raise CapabilityUnsupported. The provider
isn't expected to load checkpoints at import time.
"""

from __future__ import annotations

from translator_api.providers.base import CapabilityUnsupported
from translator_api.providers.tts.base import LocalTtsProvider, TtsInput


class VietVoiceTtsProvider(LocalTtsProvider):
    id = "vietvoice_tts"

    def _ensure_consent(self, payload: TtsInput) -> bool:
        return True

    def _ensure_loaded(self, config) -> None:
        try:
            import vietvoice_tts  # noqa: F401
        except Exception as exc:
            raise CapabilityUnsupported("vietvoice-not-installed", str(exc)) from exc
        self._loaded = True

    def _synthesize(self, payload: TtsInput) -> bytes:
        if not self._loaded:
            raise CapabilityUnsupported("vietvoice-not-loaded", "vietvoice SDK was not loaded")
        return b""
