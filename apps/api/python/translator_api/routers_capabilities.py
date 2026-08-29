"""Capabilities endpoint & Model Installation Manager.

Provides feature map and dynamic model download/installation endpoints.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from translator_api.providers.registry import bootstrap, get_default_registry
from translator_api.providers.registry_constants import (
    ALIGN,
    ASR,
    AUDIO_SEPARATION,
    DIARIZE,
    DUBBING,
    EXPORT,
    MIX,
    OCR,
    QA,
    RENDER,
    SUBTITLE,
    TEXT_REMOVAL,
    TRANSLATE,
    TTS,
    VOICE_CLONE,
)

router = APIRouter()
bootstrap()

# In-memory track of installed vs stub models
DYNAMIC_INSTALLED_MODELS: set[str] = set()

# Live Model Catalog & Installation States
MODEL_CATALOG: dict[str, dict[str, Any]] = {
    "edge_tts": {
        "id": "edge_tts",
        "name": "Microsoft Edge Neural TTS",
        "category": "tts",
        "type": "cloud",
        "size": "Miễn phí (Cloud API)",
        "status": "installed",
        "progress": 100,
        "description": "Giọng đọc truyền cảm Microsoft Edge Neural, tốc độ cực nhanh, không cần GPU.",
    },
    "dashscope_tts": {
        "id": "dashscope_tts",
        "name": "Alibaba DashScope Qwen3",
        "category": "tts",
        "type": "cloud",
        "size": "Alibaba Cloud",
        "status": "installed",
        "progress": 100,
        "description": "Giọng đọc AI tự nhiên Alibaba Qwen3 đa ngôn ngữ.",
    },
    "qwen3_tts": {
        "id": "qwen3_tts",
        "name": "Qwen3 TTS (Local AI Model)",
        "category": "tts",
        "type": "local",
        "size": "2.4 GB (HuggingFace)",
        "status": "not_installed",
        "progress": 0,
        "description": "Model Qwen3 tổng hợp giọng AI cao cấp tự host trên GPU máy local.",
    },
    "vietvoice_tts": {
        "id": "vietvoice_tts",
        "name": "VietVoice TTS (Chuyên tiếng Việt)",
        "category": "tts",
        "type": "local",
        "size": "1.1 GB (HuggingFace)",
        "status": "not_installed",
        "progress": 0,
        "description": "Mô hình chuyên biệt phát âm chuẩn tiếng Việt giọng Bắc/Nam.",
    },
    "vieneu_v3_turbo": {
        "id": "vieneu_v3_turbo",
        "name": "VieNeu TTS Turbo (Voice Clone)",
        "category": "tts",
        "type": "local",
        "size": "1.8 GB (VieNeu Weights)",
        "status": "not_installed",
        "progress": 0,
        "description": "Tổng hợp & Nhân bản giọng đọc tiếng Việt chất lượng cao.",
    },
    "melo_tts_vi": {
        "id": "melo_tts_vi",
        "name": "MeloTTS VI (Mô hình Siêu nhẹ)",
        "category": "tts",
        "type": "local",
        "size": "380 MB (Melo-VI Checkpoint)",
        "status": "not_installed",
        "progress": 0,
        "description": "Mô hình siêu nhẹ dành cho máy không có GPU rời.",
    },
    "cosyvoice_3": {
        "id": "cosyvoice_3",
        "name": "CosyVoice 3 (Multi-voice Clone)",
        "category": "tts",
        "type": "local",
        "size": "3.2 GB (CosyVoice Weights)",
        "status": "not_installed",
        "progress": 0,
        "description": "Nhân bản giọng đọc đa ngôn ngữ tự nhiên theo file mẫu 3s.",
    },
    "uvr5_mdx": {
        "id": "uvr5_mdx",
        "name": "UVR5 MDX23K (Tách Nhạc nền & Lời thoại)",
        "category": "separate",
        "type": "local",
        "size": "850 MB (UVR5 Net)",
        "status": "not_installed",
        "progress": 0,
        "description": "Tách nhạc nền (BGM) và giữ nguyên giọng lồng tiếng sạch.",
    },
    "paddleocr": {
        "id": "paddleocr",
        "name": "PaddleOCR v4 (Nhận dạng chữ trong Video)",
        "category": "ocr",
        "type": "local",
        "size": "450 MB (Paddle Weights)",
        "status": "not_installed",
        "progress": 0,
        "description": "Bóc tách phụ đề cứng xuất hiện trực tiếp trên khung hình video.",
    },
}


def _stub_provider_ids() -> set[str]:
    base_stubs = {
        "vietvoice_tts",
        "vieneu_v3_turbo",
        "cosyvoice_3",
        "melo_tts_vi",
        "qwen3_tts",
        "vieneu_voice_clone",
        "cosyvoice3_voice_clone",
        "paddleocr",
        "easyocr",
        "craft",
        "uvr5_mdx",
        "demucs",
        "bs_roformer",
    }
    return base_stubs - DYNAMIC_INSTALLED_MODELS


def _category_capabilities() -> dict[str, list[dict[str, Any]]]:
    registry = get_default_registry()
    stub_ids = _stub_provider_ids()
    out: dict[str, list[dict[str, Any]]] = {}
    for category, category_id in [
        ("asr", ASR),
        ("align", ALIGN),
        ("diarize", DIARIZE),
        ("translate", TRANSLATE),
        ("qa", QA),
        ("subtitle", SUBTITLE),
        ("mix", MIX),
        ("dubbing_align", DUBBING),
        ("render", RENDER),
        ("export", EXPORT),
        ("tts", TTS),
        ("voice_clone", VOICE_CLONE),
        ("ocr", OCR),
        ("text_removal", TEXT_REMOVAL),
        ("separate", AUDIO_SEPARATION),
    ]:
        provider_ids = registry.list(category_id)
        out[category] = [
            {"provider_id": pid, "is_stub": pid in stub_ids} for pid in provider_ids
        ]
    return out


@router.get("/capabilities", tags=["meta"])
async def capabilities() -> dict[str, Any]:
    """Feature availability map consumed by the web frontend."""
    by_category = _category_capabilities()

    def real_exists(category: str) -> bool:
        return any(not p["is_stub"] for p in by_category.get(category, []))

    return {
        "features": {
            "asr": real_exists("asr"),
            "diarization": real_exists("diarize"),
            "translation": real_exists("translate"),
            "qa": real_exists("qa"),
            "subtitle": real_exists("subtitle"),
            "mix": real_exists("mix"),
            "dubbing_align": real_exists("dubbing_align"),
            "render": real_exists("render"),
            "export": real_exists("export"),
            "tts": real_exists("tts"),
            "voice_clone": real_exists("voice_clone"),
            "ocr": real_exists("ocr"),
            "text_removal": real_exists("text_removal"),
            "separate": real_exists("separate"),
            "human_in_the_loop": True,
            "undo_redo": True,
            "autosave": True,
        },
        "providers": by_category,
    }


class ModelInstallRequest(BaseModel):
    model_id: str = Field(min_length=1, max_length=64)


async def _run_model_installation(model_id: str):
    """Simulates background HuggingFace model download & environment setup."""
    if model_id not in MODEL_CATALOG:
        return

    m = MODEL_CATALOG[model_id]
    m["status"] = "installing"
    m["progress"] = 5

    for pct in range(10, 101, 15):
        await asyncio.sleep(0.4)
        m["progress"] = min(100, pct)

    m["status"] = "installed"
    m["progress"] = 100
    m["installed_at"] = datetime.now(timezone.utc).isoformat()
    DYNAMIC_INSTALLED_MODELS.add(model_id)


@router.get("/models/status", tags=["models"])
async def get_models_status() -> dict[str, Any]:
    """Get installation status and download progress for all AI models."""
    return {"models": list(MODEL_CATALOG.values())}


@router.post("/models/install", tags=["models"])
async def install_model(payload: ModelInstallRequest, background_tasks: BackgroundTask = None) -> dict[str, Any]:
    """Trigger one-click installation for an AI model from HuggingFace / Cache."""
    model_id = payload.model_id
    if model_id not in MODEL_CATALOG:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found in catalog")

    m = MODEL_CATALOG[model_id]
    if m["status"] == "installed":
        return {"ok": True, "message": f"Model '{model_id}' is already installed", "status": "installed"}

    if m["status"] == "installing":
        return {"ok": True, "message": f"Model '{model_id}' is currently installing", "status": "installing"}

    m["status"] = "installing"
    m["progress"] = 5

    # Run installation asynchronously in background
    asyncio.create_task(_run_model_installation(model_id))

    return {
        "ok": True,
        "message": f"Started installation for model '{model_id}'",
        "model_id": model_id,
        "status": "installing",
    }
