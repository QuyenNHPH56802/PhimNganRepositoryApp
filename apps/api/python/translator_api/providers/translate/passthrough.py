"""Passthrough translation provider (development only).

Returns the source text as both `display_text` and `tts_text` so the rest of
the pipeline (subtitles, voices, render) can proceed even when no real LLM
backend (OpenAI/Anthropic/Ollama/...) is configured.

Configure via DB provider_configs:
  provider_kind = 'translate'
  provider_id   = 'passthrough'
  config        = {}
"""

from __future__ import annotations

import hashlib

from translator_api.providers.base import (
    Provider,
    ProviderCapabilities,
    ProviderContext,
)
from translator_api.providers.translate.base import TranslationInput
from translator_shared.providers import ArtifactSignature
from translator_shared.provider_responses_extra import TranslationResponse, TranslationSegment


class PassthroughTranslateProvider(Provider[TranslationInput, TranslationResponse]):
    id = "passthrough"
    capabilities = ProviderCapabilities(requires_gpu=False, is_local=True)

    def fingerprint(self, payload: TranslationInput) -> ArtifactSignature:
        cfg = payload.config
        model_id = cfg.model_id if cfg else "passthrough"
        return ArtifactSignature(
            input_hash=hashlib.sha256(repr(payload.segments).encode("utf-8")).hexdigest()[:32],
            model_id=model_id,
            model_version="0.0.0",
            provider_build=self.id,
            config_hash=hashlib.sha256(repr(cfg).encode("utf-8")).hexdigest()[:32] if cfg else "pending",
            prompt_version=cfg.prompt_version if cfg else "v1",
        )

    async def run(self, payload: TranslationInput, *, ctx: ProviderContext) -> TranslationResponse:
        out_segments = [
            TranslationSegment(
                idx=i,
                display_text=str(seg.get("display_text", "")),
                tts_text=str(seg.get("display_text", "")),
                applied_glossary_terms=[],
                applied_aliases=[],
                confidence=1.0,
            )
            for i, seg in enumerate(payload.segments)
        ]
        sig = self.fingerprint(payload)
        return TranslationResponse(
            provider_id=self.id,
            model_id=sig.model_id,
            prompt_version=sig.prompt_version,
            segments=out_segments,
            signature=sig,
        )
