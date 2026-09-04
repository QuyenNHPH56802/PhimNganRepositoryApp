"""ElevenLabs TTS provider."""

from __future__ import annotations

from translator_api.providers.tts.base import CloudTtsProvider, TtsInput


class ElevenLabsTtsProvider(CloudTtsProvider):
    id = "cloud_elevenlabs"

    def __init__(self, base_url: str = "https://api.elevenlabs.io/v1", api_key_env: str = "ELEVENLABS_API_KEY") -> None:
        super().__init__(base_url=base_url, api_key_env=api_key_env)

    async def _call_http(self, payload: TtsInput, api_key: str, httpx) -> bytes:
        cfg = payload.config
        if cfg is None:
            return b""
        url = f"{self._base_url.rstrip('/')}/text-to-speech/{cfg.voice_id}"
        headers = {"xi-api-key": api_key, "Accept": "audio/mpeg", "Content-Type": "application/json"}
        body = {"text": payload.text, "model_id": cfg.model_id, "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=body, headers=headers)
        if response.status_code >= 400:
            raise RuntimeError(f"elevenlabs-tts-{response.status_code}")
        return response.content
