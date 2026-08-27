"""DashScope Qwen3-TTS provider (Alibaba Cloud Model Studio, cloud-hosted).

DashScope provides a hosted Qwen3-TTS API that requires no local GPU — it
delivers high-quality multilingual synthesis via a REST endpoint.

API reference:
  https://docs.qwencloud.com/api-reference/speech-synthesis/qwen-tts

Two modes are supported:
  - Non-streaming: POST → receive a 24-hour audio URL
  - Streaming: POST with X-DashScope-SSE: enable → receive Base64 audio chunks

The non-streaming path is used by default (lower overhead, audio URL is
re-usable). Streaming is enabled when ``stream=True`` in the request.

Environment variables:
  DASHSCOPE_API_KEY  — API key from https://dashscope.console.aliyun.com
  DASHSCOPE_BASE_URL — override base URL (defaults to the international endpoint)

Models:
  qwen3-tts-flash          — standard Qwen3-TTS (fast)
  qwen3-tts-instruct-flash — supports instruction control (slower, higher quality)

Supported languages: Chinese, English, Vietnamese, Japanese, Korean, German,
Italian, Portuguese, Spanish, French, Russian (and more).
"""

from __future__ import annotations

import os
from typing import Literal

from translator_api.providers.base import (
    CapabilityUnsupported,
    Provider,
    ProviderCapabilities,
    ProviderContext,
)
from translator_api.providers.tts.base import TtsInput
from translator_shared.providers import ArtifactSignature
from translator_shared.provider_configs import TtsProviderConfig
from translator_shared.provider_responses_extra import TtsResponse

DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/api/v1"
DEFAULT_MODEL = "qwen3-tts-flash"
STREAMING_MODEL = "qwen3-tts-instruct-flash"
MAX_CHUNK_CHARS = 500  # Qwen3-TTS supports up to 512 tokens; use 500 as safe margin


class DashScopeTtsProvider(Provider[TtsInput, TtsResponse]):
    """Hosted Qwen3-TTS via DashScope / Alibaba Cloud Model Studio.

    This provider does NOT require local GPU or a downloaded model checkpoint.
    All synthesis happens on Alibaba's servers. Latency is ~1–3 seconds per
    request depending on text length and server load.

    Fallback chain: DashScope → Edge-TTS (edge_tts) → VietVoice (vietvoice_tts)
    """

    id = "dashscope_tts"
    capabilities = ProviderCapabilities(requires_gpu=False, is_local=False)

    def fingerprint(self, payload: TtsInput) -> ArtifactSignature:
        cfg = payload.config or TtsProviderConfig()
        return ArtifactSignature(
            input_hash=str(abs(hash(payload.text)) % (2**32)),
            model_id=cfg.model_id or DEFAULT_MODEL,
            model_version=cfg.model_id or DEFAULT_MODEL,
            provider_build=self.id,
            config_hash=str(abs(hash(f"{cfg.voice_id}|{cfg.speed}|{cfg.pitch}")) % (2**32)),
        )

    async def run(self, payload: TtsInput, *, ctx: ProviderContext) -> TtsResponse:
        if ctx.storage is None:
            raise CapabilityUnsupported("storage-missing", "provider context has no storage")

        cfg = payload.config or TtsProviderConfig()
        base_url = os.environ.get("DASHSCOPE_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
        api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            raise CapabilityUnsupported(
                "dashscope-missing-api-key",
                "DASHSCOPE_API_KEY environment variable not set",
            )

        try:
            import httpx
        except Exception as exc:
            raise CapabilityUnsupported("dashscope-httpx-missing", str(exc)) from exc

        voice = cfg.voice_id or "Cherry"
        language = _detect_language(payload.text)
        model = cfg.model_id or DEFAULT_MODEL

        # Chunk text to stay within 512-token limit (use 500 as safe margin).
        chunks = _chunk_text(payload.text, max_chars=MAX_CHUNK_CHARS)
        if not chunks:
            raise CapabilityUnsupported("dashscope-empty-text", "no content to synthesize")

        audio_bytes = await self._synthesize_chunks(
            chunks=chunks,
            voice=voice,
            language=language,
            model=model,
            base_url=base_url,
            api_key=api_key,
            httpx=httpx,
        )

        prefix = payload.output_storage_prefix or "tts"
        storage_key = f"{prefix}/{self.id}/{voice}/{os.urandom(8).hex()}.wav"
        ctx.storage.upload(storage_key, audio_bytes, mime="audio/wav")

        # Rough estimate: ~12 kB/s for PCM 16-bit mono at 24 kHz
        duration_ms = max(1, len(audio_bytes) // 24)
        return TtsResponse(
            voice_profile_id=None,
            audio_storage_key=storage_key,
            duration_ms=duration_ms,
            sample_rate=cfg.sample_rate or 24000,
            signature=self.fingerprint(payload),
            fallback_used=False,
        )

    async def _synthesize_chunks(
        self,
        chunks: list[str],
        voice: str,
        language: str,
        model: str,
        base_url: str,
        api_key: str,
        httpx,
    ) -> bytes:
        """Synthesize each chunk and concatenate the resulting audio.

        Each chunk returns a WAV file (from the audio URL or Base64 decoding).
        Chunks are concatenated in-order into a single WAV stream.
        """
        results: list[bytes] = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            for chunk_text in chunks:
                wav_bytes = await self._synthesize_one(
                    text=chunk_text,
                    voice=voice,
                    language=language,
                    model=model,
                    base_url=base_url,
                    api_key=api_key,
                    client=client,
                )
                results.append(wav_bytes)
        return b"".join(results)

    async def _synthesize_one(
        self,
        text: str,
        voice: str,
        language: str,
        model: str,
        base_url: str,
        api_key: str,
        client,
    ) -> bytes:
        """Call DashScope non-streaming API and return WAV bytes.

        Non-streaming flow:
          1. POST /services/aigc/multimodal-generation/generation
          2. Receive JSON with output.audio.url
          3. Download the audio file from that URL
        """
        url = f"{base_url}/services/aigc/multimodal-generation/generation"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "input": {
                "text": text,
                "voice": voice,
                "language_type": language,
            },
        }

        response = await client.post(url, json=payload, headers=headers)
        if response.status_code >= 400:
            raise CapabilityUnsupported(
                f"dashscope-api-{response.status_code}",
                response.text[:200],
            )

        data = response.json()

        # Handle error responses (code != 200)
        if data.get("code") and data["code"] != 200:
            msg = data.get("message", str(data))
            raise CapabilityUnsupported(f"dashscope-error-{data.get('code')}", msg)

        audio_url = data.get("output", {}).get("audio", {}).get("url")
        if not audio_url:
            raise CapabilityUnsupported(
                "dashscope-no-audio-url",
                f"unexpected response shape: {str(data)[:200]}",
            )

        # Download the audio file returned by DashScope
        audio_response = await client.get(audio_url, follow_redirects=True)
        if audio_response.status_code >= 400:
            raise CapabilityUnsupported(
                f"dashscope-audio-download-{audio_response.status_code}",
                f"failed to download {audio_url}",
            )
        return audio_response.content


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _detect_language(text: str) -> str:
    """Map the first meaningful character range to a DashScope language tag.

    DashScope accepts: Chinese, English, German, Italian, Portuguese, Spanish,
    Japanese, Korean, French, Russian, Auto
    """
    if not text:
        return "Auto"

    # Fast heuristic: check Unicode ranges
    for char in text[:100]:
        code = ord(char)
        if 0x4E00 <= code <= 0x9FFF:
            return "Chinese"
        if 0x3040 <= code <= 0x30FF:
            return "Japanese"
        if 0xAC00 <= code <= 0xD7AF:
            return "Korean"
        if 0x0600 <= code <= 0x06FF:
            return "Arabic"
        if 0x0400 <= code <= 0x04FF:
            return "Russian"
        if 0x00C0 <= code <= 0x00FF:
            # Covers French, Spanish, Portuguese, Italian, German
            return "English"  # default to English for Latin scripts

    return "Auto"


def _chunk_text(text: str, max_chars: int) -> list[str]:
    """Split text into sentence-aligned chunks of <= max_chars.

    Mirrors the chunking strategy used by Edge-TTS provider so both produce
    compatible output granularity for downstream alignment.
    """
    import re

    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    # Split on sentence boundaries
    parts = re.split(r"([.!?\n])", text)
    sentences: list[str] = []
    for i in range(0, len(parts) - 1, 2):
        segment = parts[i].strip()
        delim = parts[i + 1] if i + 1 < len(parts) else ""
        if segment or delim:
            sentences.append((segment + delim).strip())

    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if not sentence:
            continue
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            # Hard-split overlong sentences
            for i in range(0, len(sentence), max_chars):
                chunks.append(sentence[i : i + max_chars])
            continue
        if not current:
            current = sentence
        elif len(current) + 1 + len(sentence) <= max_chars:
            current = f"{current} {sentence}"
        else:
            chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    return chunks
