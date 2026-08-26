"""Text-removal provider base."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel
from translator_api.providers.base import Provider, ProviderCapabilities, ProviderContext
from translator_api.providers.ocr.base import OcrDetection
from translator_shared.providers import ArtifactSignature


@dataclass(frozen=True)
class TextRemovalInput:
    asset_storage_key: str
    detections: list[OcrDetection]
    strategy: Literal["inpaint_lama", "inpaint_anything", "telea"]
    output_storage_prefix: str = "text_removal"


class TextRemovalResponse(BaseModel):
    output_storage_key: str
    method: str
    signature: ArtifactSignature


class TextRemovalProvider(Provider[TextRemovalInput, TextRemovalResponse]):
    id: str = ""
    capabilities = ProviderCapabilities(requires_gpu=True)

    def fingerprint(self, payload: TextRemovalInput) -> ArtifactSignature:
        return ArtifactSignature(
            input_hash=hashlib.sha256(payload.asset_storage_key.encode("utf-8")).hexdigest()[:32],
            model_id=self.id,
            model_version="0.0.0",
            provider_build=self.id,
            config_hash="pending",
        )

    async def run(self, payload: TextRemovalInput, *, ctx: ProviderContext) -> TextRemovalResponse:
        output_key = self._remove_and_upload(payload, ctx)
        return TextRemovalResponse(output_storage_key=output_key, method=self.id, signature=self.fingerprint(payload))

    def _remove_and_upload(self, payload: TextRemovalInput, ctx: ProviderContext) -> str:  # pragma: no cover - abstract
        raise NotImplementedError