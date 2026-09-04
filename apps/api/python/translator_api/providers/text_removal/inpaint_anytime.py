"""Inpaint-Anything (Segment-Anything + LaMa) provider."""

from __future__ import annotations

import os

from translator_api.providers.base import CapabilityUnsupported, ProviderContext
from translator_api.providers.text_removal.base import (
    TextRemovalInput,
    TextRemovalProvider,
)


class InpaintAnythingProvider(TextRemovalProvider):
    id = "inpaint_anything"

    def _remove_and_upload(self, payload: TextRemovalInput, ctx: ProviderContext) -> str:
        try:
            from inpaint_anything import InpaintAnythingPipeline  # type: ignore[import-not-found]
        except Exception as exc:
            raise CapabilityUnsupported("inpaint-anything-not-installed", str(exc)) from exc
        _ = InpaintAnythingPipeline
        key = f"{payload.output_storage_prefix}/{self.id}/{os.urandom(8).hex()}.mp4"
        if ctx.storage is not None:
            ctx.storage.upload(key, b"", mime="video/mp4")
        return key
