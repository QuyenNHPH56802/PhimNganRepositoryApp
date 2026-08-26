"""MeloTTS Vietnamese preset voice provider."""

from __future__ import annotations

from translator_api.providers.base import CapabilityUnsupported
from translator_api.providers.tts.base import LocalTtsProvider, TtsInput


class MeloTtsViProvider(LocalTtsProvider):
    id = "melo_tts_vi"

    def _ensure_consent(self, payload: TtsInput) -> bool:
        return True

    def _ensure_loaded(self, config) -> None:
        try:
            import melo  # type: ignore[import-not-found]
        except Exception as exc:
            raise CapabilityUnsupported("melo-not-installed", str(exc)) from exc
        self._loaded = True

    def _synthesize(self, payload: TtsInput) -> bytes:
        if not self._loaded:
            raise CapabilityUnsupported("melo-not-loaded", "melo SDK was not loaded")
        return b""