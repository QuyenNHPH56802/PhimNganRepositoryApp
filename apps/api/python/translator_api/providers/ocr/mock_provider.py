"""Deterministic OCR mock provider for dev and tests.

Returns a fixed number of text regions per frame using the asset key as a
seed. The real providers (PaddleOCR, EasyOCR, CRAFT) live in
`apps/api/python/translator_api/providers/ocr/{paddle,easyocr,craft}_provider.py`.
"""

from __future__ import annotations

import hashlib

from translator_api.providers.ocr.base import (
    OcrDetection,
    OcrInput,
    OcrProvider,
)


class MockOcrProvider(OcrProvider):
    """A deterministic, model-free OCR provider."""

    id = "ocr.mock"
    capabilities = None  # type: ignore[assignment]

    def _run_inference(self, payload: OcrInput, ctx):
        # Use a seed derived from the asset key so repeated runs return
        # the same regions.
        seed = int(hashlib.sha1(payload.asset_storage_key.encode()).hexdigest(), 16) % (10**6)
        rng = (seed + payload.frame_ts_ms) % 7
        n = max(0, rng % 3)  # 0-2 regions
        samples = [
            ("字幕：欢迎来到", "Chào mừng bạn đến"),
            ("第一百章", "Chương một trăm"),
            ("出品：东方影业", "Hãng phim Phương Đông"),
            ("编剧：张三", "Biên kịch: Trương Tam"),
            ("导演：李四", "Đạo diễn: Lý Tứ"),
        ]
        detections: list[OcrDetection] = []
        for i in range(n):
            text_zh, text_vi = samples[(seed + i) % len(samples)]
            detections.append(
                OcrDetection(
                    text=text_zh,
                    bbox=[{"x": 10 + i * 20, "y": 50 + i * 30, "w": 200, "h": 30}],
                    frame_ts_ms=payload.frame_ts_ms,
                    confidence=0.9 - i * 0.05,
                )
            )
        return detections
