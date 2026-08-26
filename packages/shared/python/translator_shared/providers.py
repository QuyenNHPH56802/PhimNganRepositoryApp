"""Provider id enums and shared provider primitives.

These ids are referenced by docs/provider-contracts.md. Adding new providers
requires extending the enums and updating docs/technology-selection.md.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class AsrProviderId(str, Enum):
    WHISPERX_FASTER_WHISPER = "whisperx_faster_whisper"
    QWEN3_ASR = "qwen3_asr"


class AlignmentProviderId(str, Enum):
    WHISPERX_ALIGN = "whisperx_align"
    WAV2VEC2 = "wav2vec2"


class DiarizationProviderId(str, Enum):
    PYANNOTE_3_1 = "pyannote_3_1"
    NVIDIA_NEMO = "nvidia_nemo"


class TranslationProviderId(str, Enum):
    OPENAI_COMPATIBLE_HTTP = "openai_compatible_http"
    GEMINI_COMPATIBLE_HTTP = "gemini_compatible_http"
    CLAUDE_COMPATIBLE_HTTP = "claude_compatible_http"
    LOCAL_LLM = "local_llm"


class TtsProviderId(str, Enum):
    VIENEU_V3_TURBO = "vieneu_v3_turbo"
    COSYVOICE_3 = "cosyvoice_3"
    VIETVOICE_TTS = "vietvoice_tts"
    MELO_TTS_VI = "melo_tts_vi"
    CLOUD_AZURE = "cloud_azure"
    CLOUD_GOOGLE = "cloud_google"
    CLOUD_ELEVENLABS = "cloud_elevenlabs"


class AudioSeparationProviderId(str, Enum):
    UVR5_MDX = "uvr5_mdx"
    DEMUCS = "demucs"
    BS_ROFORMER = "bs_roformer"


class OcrProviderId(str, Enum):
    PADDLE_OCR = "paddle_ocr"
    EASY_OCR = "easy_ocr"


class TextRemovalProviderId(str, Enum):
    INPAINT = "inpaint"
    COVER = "cover"
    BLUR = "blur"


class StorageProviderId(str, Enum):
    S3_COMPATIBLE = "s3_compatible"
    LOCAL_FS = "local_fs"


class FallbackPolicy(str, Enum):
    NONE = "none"
    PREFER_ALT = "prefer_alt"
    HUMAN_REVIEW = "human_review"


class ArtifactSignature(BaseModel):
    input_hash: str
    model_id: str
    model_version: str
    provider_build: str
    config_hash: str
    prompt_version: str | None = None
    glossary_snapshot_id: str | None = None
    character_bible_snapshot_id: str | None = None
    language_profile_version: str | None = None
    extra: dict[str, str] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        parts = [
            self.input_hash,
            self.model_id,
            self.model_version,
            self.provider_build,
            self.config_hash,
            self.prompt_version or "",
            self.glossary_snapshot_id or "",
            self.character_bible_snapshot_id or "",
            self.language_profile_version or "",
        ]
        for k in sorted(self.extra):
            parts.append(f"{k}={self.extra[k]}")
        return "|".join(parts)


class ProviderError(BaseModel):
    code: str
    message: str
    retryable: bool = False
    details: dict[str, str] = Field(default_factory=dict)