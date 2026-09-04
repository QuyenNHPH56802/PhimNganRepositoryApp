"""Voice cloning providers."""

from __future__ import annotations

from translator_api.providers.voice_clone.base import (
    VoiceCloneInput,
    VoiceCloneResponse,
    VoiceEmbeddingInput,
    VoiceEmbeddingResponse,
    VoiceCloneProvider,
    VoiceEmbeddingProvider,
)
from translator_api.providers.voice_clone.vieneu import VieNeuVoiceCloneProvider
from translator_api.providers.voice_clone.cosyvoice import CosyVoice3VoiceCloneProvider

__all__ = [
    "CosyVoice3VoiceCloneProvider",
    "VieNeuVoiceCloneProvider",
    "VoiceCloneInput",
    "VoiceCloneProvider",
    "VoiceCloneResponse",
    "VoiceEmbeddingInput",
    "VoiceEmbeddingProvider",
    "VoiceEmbeddingResponse",
]
