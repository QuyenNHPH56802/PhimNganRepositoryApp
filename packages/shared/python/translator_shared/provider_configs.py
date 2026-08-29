"""Shared Pydantic configs for Phase 3 providers."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TranslationProviderConfig(BaseModel):
    provider_id: str = "openai_compatible_http"
    model_id: str = "gpt-4o-mini"
    base_url: str = "https://api.openai.com/v1"
    api_key: str | None = None
    api_key_env: str = "TRANSLATION_OPENAI_API_KEY"
    temperature: float = 0.2
    top_p: float = 1.0
    max_tokens: int = 4096
    timeout_s: float = 60.0
    prompt_version: str = "v1"
    fallback_provider_ids: list[str] = Field(default_factory=list)


class QaProviderConfig(BaseModel):
    provider_id: str = "rule_based"
    length_ratio_min: float = 1.0
    length_ratio_max: float = 3.5
    max_chars_per_second: float = 17.0


class SubtitleProviderConfig(BaseModel):
    provider_id: str = "cps_wrapper"
    target_cps: float = 15.0
    max_chars_per_line: int = 42
    min_duration_ms: int = 1200
    max_duration_ms: int = 7000


class TtsProviderConfig(BaseModel):
    provider_id: str = "vietvoice_tts"
    model_id: str = "vietvoice-1"
    voice_id: str = "vietvoice-female-1"
    api_key: str | None = None
    default_accent: str | None = "northern"
    speed: float = 1.0
    pitch: float = 0.0
    sample_rate: int = 24000
    fallback_provider_ids: list[str] = Field(default_factory=list)
    reference_audio_key: str | None = None


class SeparationProviderConfig(BaseModel):
    provider_id: str = "uvr5_mdx"
    model_id: str = "MDX23K"
    device: str = "cuda"
    segment_size: int = 256


class MixProviderConfig(BaseModel):
    ffmpeg_path: str = "ffmpeg"
    voice_volume_db: float = 0.0
    background_volume_db: float = -6.0
    ducking: bool = True


class DubbingAlignProviderConfig(BaseModel):
    provider_id: str = "ffmpeg_atempo"
    ffmpeg_path: str = "ffmpeg"
    min_speed: float = 0.5
    max_speed: float = 2.0


class RenderProviderConfig(BaseModel):
    ffmpeg_path: str = "ffmpeg"
    crf: int = 20
    preset: str = "medium"
    hwaccel: str | None = None
    subtitle_mode: str = "soft"
    crf_map: dict[str, int] = Field(default_factory=lambda: {"mp4": 20, "mkv": 22, "webm": 28})


class ExportProviderConfig(BaseModel):
    formats: list[str] = Field(default_factory=lambda: ["mp4"])
    max_size_bytes: int = 8 * 1024 * 1024 * 1024