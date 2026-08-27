"""TTS providers."""

from translator_api.providers.tts.azure import AzureCloudTtsProvider
from translator_api.providers.tts.base import CloudTtsProvider, LocalTtsProvider, TtsInput
from translator_api.providers.tts.cosyvoice import CosyVoice3Provider
from translator_api.providers.tts.edge import (
    DEFAULT_VOICE,
    LRU_MAX_SIZE,
    MAX_CHUNK_CHARS,
    VOICE_MAP,
    EdgeTtsProvider,
    chunk_text,
    list_voices,
    resolve_voice,
)
from translator_api.providers.tts.elevenlabs import ElevenLabsTtsProvider
from translator_api.providers.tts.google import GoogleCloudTtsProvider
from translator_api.providers.tts.melotts import MeloTtsViProvider
from translator_api.providers.tts.qwen3 import Qwen3TtsProvider
from translator_api.providers.tts.vieneu import VieNeuProvider
from translator_api.providers.tts.vietvoice import VietVoiceTtsProvider

__all__ = [
    "AzureCloudTtsProvider",
    "CloudTtsProvider",
    "CosyVoice3Provider",
    "DEFAULT_VOICE",
    "EdgeTtsProvider",
    "ElevenLabsTtsProvider",
    "GoogleCloudTtsProvider",
    "LRU_MAX_SIZE",
    "LocalTtsProvider",
    "MAX_CHUNK_CHARS",
    "MeloTtsViProvider",
    "Qwen3TtsProvider",
    "TtsInput",
    "VOICE_MAP",
    "VieNeuProvider",
    "VietVoiceTtsProvider",
    "chunk_text",
    "list_voices",
    "resolve_voice",
]
