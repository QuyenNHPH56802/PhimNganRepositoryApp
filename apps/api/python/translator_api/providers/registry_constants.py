"""Provider kind constants.

Centralized so that worker activities, API routers, and registry all
reference the same strings.
"""

from __future__ import annotations

ASR = "asr"
ALIGN = "align"
DIARIZE = "diarize"
TRANSLATE = "translate"
QA = "qa"
SUBTITLE = "subtitle"
TTS = "tts"
AUDIO_SEPARATION = "audio_separation"
MIX = "audio_mix"
DUBBING = "dubbing_align"
RENDER = "render"
EXPORT = "export"
CLEANUP = "cleanup"
OCR = "ocr"
TEXT_REMOVAL = "text_removal"
VOICE_CLONE = "voice_clone"
VOICE_EMBEDDING = "voice_embedding"

STORAGE = "storage"
