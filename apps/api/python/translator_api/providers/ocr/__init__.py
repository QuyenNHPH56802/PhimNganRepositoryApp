"""OCR providers."""

from __future__ import annotations

from translator_api.providers.ocr.base import OcrInput, OcrDetection, OcrResponse
from translator_api.providers.ocr.craft_provider import CraftTextDetectorProvider
from translator_api.providers.ocr.easyocr_provider import EasyOcrProvider
from translator_api.providers.ocr.paddle_provider import PaddleOcrProvider

__all__ = [
    "CraftTextDetectorProvider",
    "EasyOcrProvider",
    "OcrDetection",
    "OcrInput",
    "OcrResponse",
    "PaddleOcrProvider",
]