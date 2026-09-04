"""Provider metadata endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from translator_api.providers.base import get_default_registry
from translator_api.providers.registry_constants import TRANSLATE, TTS

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/{kind}/metadata")
def get_provider_metadata(kind: str) -> dict:
    """Return metadata about available providers for a given kind (tts, translate, etc.)."""
    registry = get_default_registry()
    providers = registry.list_providers(kind)
    
    result = []
    for provider in providers:
        # Determine if provider requires API key
        requires_api_key = False
        requires_gpu = False
        is_local = getattr(provider.capabilities, "is_local", False)
        requires_consent = False
        
        # Check for cloud providers that need API keys
        if kind == TTS:
            if provider.id in ["cloud_azure", "cloud_google", "cloud_elevenlabs", "dashscope_tts"]:
                requires_api_key = True
            if provider.id in ["vietvoice_tts", "vieneu_tts", "cosyvoice3_tts", "melo_tts_vi", "qwen3_tts"]:
                requires_gpu = True
                
        elif kind == TRANSLATE:
            if provider.id in ["openai_compatible_http", "gemini_compatible_http", "claude_compatible_http"]:
                requires_api_key = True
            if provider.id == "local_llm":
                requires_gpu = True
        
        result.append({
            "id": provider.id,
            "requires_api_key": requires_api_key,
            "requires_gpu": requires_gpu,
            "is_local": is_local,
            "requires_consent": requires_consent,
        })
    
    return {"providers": result}
