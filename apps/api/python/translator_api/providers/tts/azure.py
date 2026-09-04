"""Azure cloud TTS provider."""

from __future__ import annotations

from translator_api.providers.tts.base import CloudTtsProvider, TtsInput

DEFAULT_BASE_URL = "https://eastasia.tts.speech.microsoft.com"


class AzureCloudTtsProvider(CloudTtsProvider):
    id = "cloud_azure"

    def __init__(self, base_url: str = DEFAULT_BASE_URL, api_key_env: str = "AZURE_TTS_KEY") -> None:
        super().__init__(base_url=base_url, api_key_env=api_key_env)

    async def _call_http(self, payload: TtsInput, api_key: str, httpx) -> bytes:
        cfg = payload.config
        if cfg is None:
            return b""
        url = f"{self._base_url.rstrip('/')}/cognitiveservices/v1"
        ssml = (
            "<speak version='1.0' xml:lang='vi-VN'>"
            f"<voice name='{cfg.voice_id}'><prosody rate='{cfg.speed}' pitch='{cfg.pitch:+}%'>{payload.text}</prosody></voice>"
            "</speak>"
        )
        headers = {"Ocp-Apim-Subscription-Key": api_key, "Content-Type": "application/ssml+xml", "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, content=ssml, headers=headers)
        if response.status_code >= 400:
            raise RuntimeError(f"azure-tts-{response.status_code}")
        return response.content
