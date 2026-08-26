"""PaddleOCR provider."""

from __future__ import annotations

from translator_api.providers.base import CapabilityUnsupported
from translator_api.providers.ocr.base import OcrDetection, OcrInput, OcrProvider
from translator_api.providers.base import ProviderContext


class PaddleOcrProvider(OcrProvider):
    id = "paddleocr"

    def _run_inference(self, payload: OcrInput, ctx: ProviderContext) -> list[OcrDetection]:
        try:
            from paddleocr import PaddleOCR  # type: ignore[import-not-found]
        except Exception as exc:
            raise CapabilityUnsupported("paddleocr-not-installed", str(exc)) from exc
        _ = PaddleOCR
        return []