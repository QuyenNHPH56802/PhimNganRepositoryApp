"""Local LLM translation provider (llama.cpp / Ollama).

Phase 3: lazy import; on missing SDK raise CapabilityUnsupported. The actual
inference is opt-in via env TRANSLATOR_LOCAL_LLM_BACKEND=ollama|llama_cpp.
"""

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


class LocalLlmProvider(Provider[TranslationInput, TranslationResponse]):
    id = "local_llm"
    capabilities = ProviderCapabilities(requires_gpu=False, is_local=True)

    def fingerprint(self, payload: TranslationInput) -> ArtifactSignature:
        cfg = payload.config
        return ArtifactSignature(
            input_hash=hashlib.sha256(repr(payload.segments).encode("utf-8")).hexdigest()[:32],
            model_id=cfg.model_id if cfg else "local_llm",
            model_version=cfg.model_id if cfg else "0.0.0",
            provider_build=self.id,
            config_hash=hashlib.sha256(repr(cfg).encode("utf-8")).hexdigest()[:32] if cfg else "pending",
            prompt_version=cfg.prompt_version if cfg else "v1",
        )

    async def run(self, payload: TranslationInput, *, ctx: ProviderContext) -> TranslationResponse:
        cfg = payload.config
        if cfg is None:
            raise CapabilityUnsupported("translate-missing-config", "Local LLM requires TranslationProviderConfig")

        system, user = build_translation_messages(payload)
        backend = os.environ.get("TRANSLATOR_LOCAL_LLM_BACKEND", "llama_cpp")
        # Use the configured base_url / model_id; fall back to env defaults so
        # users only have to pick `local_llm` in Settings without editing JSON.
        base_url = (cfg.base_url if cfg and cfg.base_url else None) or os.environ.get(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )
        model_id = (cfg.model_id if cfg and cfg.model_id else None) or os.environ.get(
            "TRANSLATOR_LOCAL_LLM_MODEL", "qwen2.5:7b"
        )
        if backend == "ollama":
            try:
                import httpx  # type: ignore[import-not-found]
            except Exception as exc:
                raise CapabilityUnsupported("translate-httpx-missing", str(exc)) from exc
            body = {"model": model_id, "prompt": f"{system['content']}\n\n{user['content']}", "stream": False}
            async with httpx.AsyncClient(timeout=cfg.timeout_s) as client:
                response = await client.post(f"{base_url.rstrip('/')}/api/generate", json=body)
            if response.status_code >= 400:
                raise RuntimeError(f"ollama-{response.status_code}: {response.text[:256]}")
            raw = response.json().get("response", "")
            return parse_translation_payload(raw, provider_id=self.id, model_id=model_id)

        if backend == "llama_cpp":
            try:
                from llama_cpp import Llama  # type: ignore[import-not-found]
            except Exception as exc:
                raise CapabilityUnsupported("llama-cpp-missing", str(exc)) from exc
            try:
                llm = Llama(model_path=model_id, n_ctx=8192)
            except Exception as exc:
                raise CapabilityUnsupported("llama-cpp-load-failed", str(exc)) from exc
            prompt = f"{system['content']}\n\n{user['content']}"
            output = llm(prompt, max_tokens=cfg.max_tokens, temperature=cfg.temperature, top_p=cfg.top_p)
            raw = output["choices"][0]["text"]
            return parse_translation_payload(raw, provider_id=self.id, model_id=model_id)

        raise CapabilityUnsupported("translate-local-llm-backend-unknown", f"unknown backend {backend}")
