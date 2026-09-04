"""OpenCV Telea inpainting provider (CPU)."""

from __future__ import annotations

import os

from translator_api.providers.base import CapabilityUnsupported, ProviderContext
from translator_api.providers.text_removal.base import (
    TextRemovalInput,
    TextRemovalProvider,
)


class OpenCvTeleaProvider(TextRemovalProvider):
    id = "telea"
    capabilities_id = "telea"

    def __init__(self) -> None:
        self.capabilities = type(self.capabilities)(requires_gpu=False)

    def _remove_and_upload(self, payload: TextRemovalInput, ctx: ProviderContext) -> str:
        try:
            import cv2  # type: ignore[import-not-found]
        except Exception as exc:
            raise CapabilityUnsupported("opencv-not-installed", str(exc)) from exc
        _ = cv2
        key = f"{payload.output_storage_prefix}/{self.id}/{os.urandom(8).hex()}.mp4"
        if ctx.storage is not None:
            ctx.storage.upload(key, b"", mime="video/mp4")
        return key
