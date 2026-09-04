"""EasyOCR provider."""

from __future__ import annotations

from translator_api.providers.base import CapabilityUnsupported, ProviderContext
from translator_api.providers.ocr.base import OcrDetection, OcrInput, OcrProvider


class EasyOcrProvider(OcrProvider):
    id = "easyocr"

    def _run_inference(self, payload: OcrInput, ctx: ProviderContext) -> list[OcrDetection]:
        try:
            import easyocr  # type: ignore[import-not-found]
        except Exception as exc:
            raise CapabilityUnsupported("easyocr-not-installed", str(exc)) from exc
        _ = easyocr
        return []
