"""Gemini-compatible HTTP translation provider."""

from __future__ import annotations

import hashlib
import os

from translator_api.providers.base import (
    CapabilityUnsupported,
    Provider,
    ProviderCapabilities,
    ProviderContext,
)
from translator_api.providers.translate.base import (
    TranslationInput,
    build_translation_messages,
    parse_translation_payload,
)
from translator_shared.providers import ArtifactSignature
from translator_shared.provider_responses_extra import TranslationResponse


class GeminiCompatibleHttpProvider(Provider[TranslationInput, TranslationResponse]):
    id = "gemini_compatible_http"
    capabilities = ProviderCapabilities(requires_gpu=False, is_local=False)

    def fingerprint(self, payload: TranslationInput) -> ArtifactSignature:
        cfg = payload.config
        return ArtifactSignature(
            input_hash=hashlib.sha256(repr(payload.segments).encode("utf-8")).hexdigest()[:32],
            model_id=cfg.model_id if cfg else "gemini_compatible_http",
            model_version=cfg.model_id if cfg else "0.0.0",
            provider_build=self.id,
            config_hash=hashlib.sha256(repr(cfg).encode("utf-8")).hexdigest()[:32] if cfg else "pending",
            prompt_version=cfg.prompt_version if cfg else "v1",
        )

    async def run(self, payload: TranslationInput, *, ctx: ProviderContext) -> TranslationResponse:
        cfg = payload.config
        if cfg is None:
            raise CapabilityUnsupported("translate-missing-config", "Gemini provider requires TranslationProviderConfig")
        api_key = os.environ.get(cfg.api_key_env)
        if not api_key:
            raise CapabilityUnsupported("translate-missing-api-key", f"env {cfg.api_key_env} not set")

        system, user = build_translation_messages(payload)
        body = {
            "contents": [{"role": "user", "parts": [{"text": f"{system['content']}\n\n{user['content']}"}]}],
            "generationConfig": {"temperature": cfg.temperature, "topP": cfg.top_p, "maxOutputTokens": cfg.max_tokens},
        }
        try:
            import httpx  # type: ignore[import-not-found]
        except Exception as exc:
            raise CapabilityUnsupported("translate-httpx-missing", str(exc)) from exc
        url = f"{cfg.base_url.rstrip('/')}/models/{cfg.model_id}:generateContent"
        async with httpx.AsyncClient(timeout=cfg.timeout_s) as client:
            response = await client.post(url, params={"key": api_key}, json=body)
        if response.status_code >= 400:
            raise RuntimeError(f"gemini-http-{response.status_code}: {response.text[:256]}")
        data = response.json()
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        return parse_translation_payload(raw, provider_id=self.id, model_id=cfg.model_id)
