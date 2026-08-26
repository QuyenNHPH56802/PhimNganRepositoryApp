"""TTS providers."""

from translator_api.providers.tts.azure import AzureCloudTtsProvider
from translator_api.providers.tts.base import CloudTtsProvider, LocalTtsProvider, TtsInput
from translator_api.providers.tts.cosyvoice import CosyVoice3Provider
from translator_api.providers.tts.elevenlabs import ElevenLabsTtsProvider
from translator_api.providers.tts.google import GoogleCloudTtsProvider
from translator_api.providers.tts.melotts import MeloTtsViProvider
from translator_api.providers.tts.vieneu import VieNeuProvider
from translator_api.providers.tts.vietvoice import VietVoiceTtsProvider

__all__ = [
    "AzureCloudTtsProvider",
    "CloudTtsProvider",
    "CosyVoice3Provider",
    "ElevenLabsTtsProvider",
    "GoogleCloudTtsProvider",
    "LocalTtsProvider",
    "MeloTtsViProvider",
    "TtsInput",
    "VieNeuProvider",
    "VietVoiceTtsProvider",
]