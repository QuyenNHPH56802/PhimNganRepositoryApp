"""Google Cloud TTS provider."""

from __future__ import annotations

from translator_api.providers.tts.base import CloudTtsProvider, TtsInput


class GoogleCloudTtsProvider(CloudTtsProvider):
    id = "cloud_google"

    def __init__(self, base_url: str = "https://texttospeech.googleapis.com/v1", api_key_env: str = "GOOGLE_TTS_KEY") -> None:
        super().__init__(base_url=base_url, api_key_env=api_key_env)

    async def _call_http(self, payload: TtsInput, api_key: str, httpx) -> bytes:
        cfg = payload.config
        if cfg is None:
            return b""
        url = f"{self._base_url.rstrip('/')}/text:synthesize?key={api_key}"
        body = {
            "input": {"text": payload.text},
            "voice": {"languageCode": "vi-VN", "name": cfg.voice_id},
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": cfg.speed, "pitch": cfg.pitch},
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=body)
        if response.status_code >= 400:
            raise RuntimeError(f"google-tts-{response.status_code}")
        import base64

        return base64.b64decode(response.json()["audioContent"])