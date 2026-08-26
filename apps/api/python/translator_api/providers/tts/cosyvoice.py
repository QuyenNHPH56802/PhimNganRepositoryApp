"""CosyVoice 3 TTS provider (multilingual)."""

from __future__ import annotations

from translator_api.providers.base import CapabilityUnsupported
from translator_api.providers.tts.base import LocalTtsProvider, TtsInput


class CosyVoice3Provider(LocalTtsProvider):
    id = "cosyvoice_3"

    def _ensure_consent(self, payload: TtsInput) -> bool:
        return True

    def _ensure_loaded(self, config) -> None:
        try:
            import cosyvoice  # type: ignore[import-not-found]
        except Exception as exc:
            raise CapabilityUnsupported("cosyvoice-not-installed", str(exc)) from exc
        self._loaded = True

    def _synthesize(self, payload: TtsInput) -> bytes:
        if not self._loaded:
            raise CapabilityUnsupported("cosyvoice-not-loaded", "cosyvoice SDK was not loaded")
        return b""