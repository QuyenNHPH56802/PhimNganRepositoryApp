"""OCR provider base."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field
from translator_api.providers.base import Provider, ProviderCapabilities, ProviderContext
from translator_shared.providers import ArtifactSignature


@dataclass(frozen=True)
class OcrDetection:
    text: str
    bbox: list[dict[str, int]]
    frame_ts_ms: int
    confidence: float | None


@dataclass(frozen=True)
class OcrInput:
    asset_storage_key: str
    language_hint: str = "zh"
    detect_strategy: Literal["line", "word"] = "line"
    frame_ts_ms: int = 0


class OcrResponse(BaseModel):
    language: str
    model_id: str
    model_version: str
    detections: list[OcrDetection]
    signature: ArtifactSignature


class OcrProvider(Provider[OcrInput, OcrResponse]):
    id: str = ""
    capabilities = ProviderCapabilities(requires_gpu=True)

    def fingerprint(self, payload: OcrInput) -> ArtifactSignature:
        return ArtifactSignature(
            input_hash=hashlib.sha256(payload.asset_storage_key.encode("utf-8")).hexdigest()[:32],
            model_id=self.id,
            model_version="0.0.0",
            provider_build=self.id,
            config_hash="pending",
        )

    async def run(self, payload: OcrInput, *, ctx: ProviderContext) -> OcrResponse:
        detections = self._run_inference(payload, ctx)
        return OcrResponse(
            language=payload.language_hint,
            model_id=self.id,
            model_version="checkpoint",
            detections=detections,
            signature=self.fingerprint(payload),
        )

    def _run_inference(self, payload: OcrInput, ctx: ProviderContext) -> list[OcrDetection]:  # pragma: no cover - abstract
        raise NotImplementedError