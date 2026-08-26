"""CRAFT + custom OCR backend provider."""

from __future__ import annotations

from translator_api.providers.base import CapabilityUnsupported, ProviderContext
from translator_api.providers.ocr.base import OcrDetection, OcrInput, OcrProvider


class CraftTextDetectorProvider(OcrProvider):
    id = "craft"

    def _run_inference(self, payload: OcrInput, ctx: ProviderContext) -> list[OcrDetection]:
        try:
            import craft_text_detector  # type: ignore[import-not-found]
        except Exception as exc:
            raise CapabilityUnsupported("craft-not-installed", str(exc)) from exc
        _ = craft_text_detector
        return []