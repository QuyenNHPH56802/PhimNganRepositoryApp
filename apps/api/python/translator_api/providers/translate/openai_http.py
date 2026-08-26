"""OpenAI-compatible HTTP translation provider."""

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


class OpenAICompatibleHttpProvider(Provider[TranslationInput, TranslationResponse]):
    id = "openai_compatible_http"
    capabilities = ProviderCapabilities(requires_gpu=False, is_local=False)

    def fingerprint(self, payload: TranslationInput) -> ArtifactSignature:
        cfg = payload.config
        return ArtifactSignature(
            input_hash=hashlib.sha256(repr(payload.segments).encode("utf-8")).hexdigest()[:32],
            model_id=cfg.model_id if cfg else "openai_compatible_http",
            model_version=cfg.model_id if cfg else "0.0.0",
            provider_build=self.id,
            config_hash=hashlib.sha256(repr(cfg).encode("utf-8")).hexdigest()[:32] if cfg else "pending",
            prompt_version=cfg.prompt_version if cfg else "v1",
        )

    async def run(self, payload: TranslationInput, *, ctx: ProviderContext) -> TranslationResponse:
        cfg = payload.config
        if cfg is None:
            raise CapabilityUnsupported("translate-missing-config", "OpenAI provider requires TranslationProviderConfig")
        api_key = os.environ.get(cfg.api_key_env)
        if not api_key:
            raise CapabilityUnsupported("translate-missing-api-key", f"env {cfg.api_key_env} not set")

        system, user = build_translation_messages(payload)
        body = {
            "model": cfg.model_id,
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
            "max_tokens": cfg.max_tokens,
            "messages": [system, user],
            "response_format": {"type": "json_object"},
        }
        try:
            import httpx  # type: ignore[import-not-found]
        except Exception as exc:
            raise CapabilityUnsupported("translate-httpx-missing", str(exc)) from exc
        headers = {"Authorization": f"Bearer {api_key}"}
        async with httpx.AsyncClient(timeout=cfg.timeout_s) as client:
            response = await client.post(f"{cfg.base_url.rstrip('/')}/chat/completions", json=body, headers=headers)
        if response.status_code >= 400:
            raise RuntimeError(f"openai-http-{response.status_code}: {response.text[:256]}")
        data = response.json()
        raw = data["choices"][0]["message"]["content"]
        return parse_translation_payload(raw, provider_id=self.id, model_id=cfg.model_id)