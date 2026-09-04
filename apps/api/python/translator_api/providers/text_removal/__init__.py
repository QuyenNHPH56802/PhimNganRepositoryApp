"""Text removal providers."""

from __future__ import annotations

from translator_api.providers.text_removal.base import (
    TextRemovalInput,
    TextRemovalResponse,
)
from translator_api.providers.text_removal.inpaint_anytime import InpaintAnythingProvider
from translator_api.providers.text_removal.lama_provider import LamaInpaintProvider
from translator_api.providers.text_removal.opencv_telea import OpenCvTeleaProvider

__all__ = [
    "InpaintAnythingProvider",
    "LamaInpaintProvider",
    "OpenCvTeleaProvider",
    "TextRemovalInput",
    "TextRemovalResponse",
]
