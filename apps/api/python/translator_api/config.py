"""Provider runtime configuration.

These settings are loaded from environment variables and from
ProviderConfig rows (DB). DB config takes precedence when present.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


import os


class AsrProviderConfig(BaseModel):
    provider_id: str = "whisperx_faster_whisper"
    model_id: str = Field(default_factory=lambda: os.getenv("WHISPER_MODEL", "base"))
    device: str = Field(default_factory=lambda: os.getenv("WHISPER_DEVICE", "cpu"))
    compute_type: str = Field(default_factory=lambda: os.getenv("WHISPER_COMPUTE_TYPE", "int8"))
    vad_filter: bool = True
    beam_size: int = 5
    hf_token: str | None = Field(default_factory=lambda: os.getenv("HF_TOKEN"))


class AlignmentProviderConfig(BaseModel):
    provider_id: str = "wav2vec2"
    model_id: str = "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"
    device: str = "cuda"


class DiarizationProviderConfig(BaseModel):
    provider_id: str = "pyannote_3_1"
    model_id: str = "pyannote/speaker-diarization-3.1"
    device: str = "cuda"
    hf_token: str | None = None
    min_speakers: int | None = None
    max_speakers: int | None = None


class ProviderRuntimeConfig(BaseModel):
    asr: AsrProviderConfig = Field(default_factory=AsrProviderConfig)
    align: AlignmentProviderConfig = Field(default_factory=AlignmentProviderConfig)
    diarize: DiarizationProviderConfig = Field(default_factory=DiarizationProviderConfig)