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
            import cosyvoice  # noqa: F401
        except Exception as exc:
            raise CapabilityUnsupported("cosyvoice-not-installed", str(exc)) from exc
        self._loaded = True

    def _synthesize(self, payload: TtsInput) -> bytes:
        if not self._loaded:
            raise CapabilityUnsupported("cosyvoice-not-loaded", "cosyvoice SDK was not loaded")
        try:
            import cosyvoice
            import soundfile as sf
            import tempfile
            from pathlib import Path

            # Load cosyvoice model if not already loaded
            if not hasattr(self, '_model') or self._model is None:
                self._model = cosyvoice.CosyVoice('CozyVoice3/BionicSilicon/CosyVoice3-0.5B', 
                                                   load_cache=False, 
                                                   instruct_mode=True)

            # Generate speech
            result = self._model.inference(payload.text, prompt_text=payload.prompt_text, 
                                           prompt_audio=payload.reference_audio_key)
            
            # Convert to wav and return bytes
            output_path = Path(tempfile.mktemp(suffix='.wav'))
            sf.write(str(output_path), result['audio'].numpy(), result['sampling_rate'])
            audio_bytes = output_path.read_bytes()
            output_path.unlink()
            
            return audio_bytes
        except Exception as exc:
            raise CapabilityUnsupported("cosyvoice-synthesis-failed", f"CosyVoice synthesis failed: {exc}") from exc
