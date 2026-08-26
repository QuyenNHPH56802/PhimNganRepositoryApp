"""Provider registry bootstrap.

Import this module to populate the default registry with every built-in
provider. APIs and workers should call `get_default_registry()` rather
than constructing their own registry so that registration is consistent.
"""

from __future__ import annotations

from translator_api.providers.align import Wav2vec2AlignmentProvider
from translator_api.providers.asr import WhisperxFasterWhisperProvider
from translator_api.providers.base import get_default_registry
from translator_api.providers.cleanup import OrphanCleanupProvider
from translator_api.providers.diarize import PyannoteDiarizationProvider
from translator_api.providers.dubbing import FfmpegAtempoAlignProvider
from translator_api.providers.export import FfmpegExportProvider
from translator_api.providers.mix import FfmpegMixProvider
from translator_api.providers.qa import RuleBasedQaProvider
from translator_api.providers.ocr import (
    CraftTextDetectorProvider,
    EasyOcrProvider,
    PaddleOcrProvider,
)
from translator_api.providers.registry_constants import (
    ALIGN,
    ASR,
    AUDIO_SEPARATION,
    CLEANUP,
    DIARIZE,
    DUBBING,
    EXPORT,
    MIX,
    OCR,
    QA,
    RENDER,
    SUBTITLE,
    TEXT_REMOVAL,
    TRANSLATE,
    TTS,
    VOICE_CLONE,
    VOICE_EMBEDDING,
)
from translator_api.providers.render import FfmpegRenderProvider
from translator_api.providers.separation import (
    BsRoformerProvider,
    DemucsProvider,
    Uvr5MdxProvider,
)
from translator_api.providers.subtitle import CpsWrapperSubtitleProvider
from translator_api.providers.text_removal import (
    InpaintAnythingProvider,
    LamaInpaintProvider,
    OpenCvTeleaProvider,
)
from translator_api.providers.voice_clone import (
    CosyVoice3VoiceCloneProvider,
    VieNeuVoiceCloneProvider,
)
from translator_api.providers.translate import (
    ClaudeCompatibleHttpProvider,
    GeminiCompatibleHttpProvider,
    LocalLlmProvider,
    OpenAICompatibleHttpProvider,
)
from translator_api.providers.tts import (
    AzureCloudTtsProvider,
    CosyVoice3Provider,
    ElevenLabsTtsProvider,
    GoogleCloudTtsProvider,
    MeloTtsViProvider,
    VieNeuProvider,
    VietVoiceTtsProvider,
)


def bootstrap():
    registry = get_default_registry()
    registry.register(ASR, WhisperxFasterWhisperProvider())
    registry.register(ALIGN, Wav2vec2AlignmentProvider())
    registry.register(DIARIZE, PyannoteDiarizationProvider())

    registry.register(TRANSLATE, OpenAICompatibleHttpProvider())
    registry.register(TRANSLATE, GeminiCompatibleHttpProvider())
    registry.register(TRANSLATE, ClaudeCompatibleHttpProvider())
    registry.register(TRANSLATE, LocalLlmProvider())

    registry.register(QA, RuleBasedQaProvider())
    registry.register(SUBTITLE, CpsWrapperSubtitleProvider())

    registry.register(TTS, VietVoiceTtsProvider())
    registry.register(TTS, VieNeuProvider())
    registry.register(TTS, CosyVoice3Provider())
    registry.register(TTS, MeloTtsViProvider())
    registry.register(TTS, AzureCloudTtsProvider())
    registry.register(TTS, GoogleCloudTtsProvider())
    registry.register(TTS, ElevenLabsTtsProvider())

    registry.register(AUDIO_SEPARATION, Uvr5MdxProvider())
    registry.register(AUDIO_SEPARATION, DemucsProvider())
    registry.register(AUDIO_SEPARATION, BsRoformerProvider())

    registry.register(MIX, FfmpegMixProvider())
    registry.register(DUBBING, FfmpegAtempoAlignProvider())
    registry.register(RENDER, FfmpegRenderProvider())
    registry.register(EXPORT, FfmpegExportProvider())
    registry.register(CLEANUP, OrphanCleanupProvider())

    registry.register(OCR, PaddleOcrProvider())
    registry.register(OCR, EasyOcrProvider())
    registry.register(OCR, CraftTextDetectorProvider())

    registry.register(TEXT_REMOVAL, LamaInpaintProvider())
    registry.register(TEXT_REMOVAL, InpaintAnythingProvider())
    registry.register(TEXT_REMOVAL, OpenCvTeleaProvider())

    registry.register(VOICE_CLONE, VieNeuVoiceCloneProvider())
    registry.register(VOICE_CLONE, CosyVoice3VoiceCloneProvider())

    return registry


bootstrap()