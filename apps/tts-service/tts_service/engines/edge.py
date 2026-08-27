"""Edge-TTS engine adapter for the TTS microservice."""

from __future__ import annotations

import io


class EdgeTtsEngine:
    """Thin async wrapper around the ``edge-tts`` package.

    ``synthesize_chunk`` returns MP3 bytes. The default voice is
    ``vi-VN-HoaiMyNeural`` (Vietnamese female); the engine maps friendly
    aliases (e.g. ``vi-male``) to the underlying ShortName.
    """

    VOICE_ALIASES: dict[str, str] = {
        "vi-VN-HoaiMyNeural": "vi-VN-HoaiMyNeural",
        "vi-VN-NamMinhNeural": "vi-VN-NamMinhNeural",
        "vi-female": "vi-VN-HoaiMyNeural",
        "vi-male": "vi-VN-NamMinhNeural",
        "en-US-JennyNeural": "en-US-JennyNeural",
        "en-US-GuyNeural": "en-US-GuyNeural",
        "zh-CN-XiaoxiaoNeural": "zh-CN-XiaoxiaoNeural",
        "ja-JP-NanamiNeural": "ja-JP-NanamiNeural",
        "ko-KR-SunHiNeural": "ko-KR-SunHiNeural",
    }
    DEFAULT_VOICE = "vi-VN-HoaiMyNeural"

    def resolve_voice(self, voice: str | None) -> str:
        if not voice:
            return self.DEFAULT_VOICE
        return self.VOICE_ALIASES.get(voice, voice)

    @staticmethod
    def format_rate(speed: float) -> str:
        pct = int(round((speed - 1.0) * 100))
        pct = max(-50, min(100, pct))
        return f"{'+' if pct >= 0 else ''}{pct}%"

    @staticmethod
    def format_pitch(hz: float) -> str:
        v = int(round(hz))
        v = max(-100, min(100, v))
        return f"{'+' if v >= 0 else ''}{v}Hz"

    async def synthesize_chunk(self, text: str, voice: str, rate: str, pitch: str) -> bytes:
        try:
            import edge_tts  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover - import branch
            raise RuntimeError(f"edge-tts-not-installed: {exc}")
        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
        buf = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio":
                buf.write(chunk["data"])
        data = buf.getvalue()
        if not data:
            raise RuntimeError(f"no audio returned for voice={voice}")
        return data
