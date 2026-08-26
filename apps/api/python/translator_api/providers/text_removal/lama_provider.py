"""LaMa inpainting provider."""

from __future__ import annotations

import os

from translator_api.providers.base import CapabilityUnsupported, ProviderContext
from translator_api.providers.text_removal.base import (
    TextRemovalInput,
    TextRemovalProvider,
)


class LamaInpaintProvider(TextRemovalProvider):
    id = "inpaint_lama"

    def _remove_and_upload(self, payload: TextRemovalInput, ctx: ProviderContext) -> str:
        try:
            import simple_lama_inpainting  # type: ignore[import-not-found]
        except Exception as exc:
            raise CapabilityUnsupported("lama-not-installed", str(exc)) from exc
        _ = simple_lama_inpainting
        key = f"{payload.output_storage_prefix}/{self.id}/{os.urandom(8).hex()}.mp4"
        if ctx.storage is not None:
            ctx.storage.upload(key, b"", mime="video/mp4")
        return key