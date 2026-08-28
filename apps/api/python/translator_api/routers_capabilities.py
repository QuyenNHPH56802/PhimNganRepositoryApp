"""Capabilities endpoint — tells the frontend which features are real.

The frontend uses this to disable UI affordances for stub providers instead of
pretending they work. Values are derived from the live provider registry.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
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


def _stub_provider_ids() -> set[str]:
    """Hard-coded list of provider IDs that are documented as stubs.

    Kept here (rather than added to the registry) to avoid coupling the
    runtime to a single feature flag. Update both this list and the audit
    report when a stub provider becomes real.
    """
    return {
        # TTS local providers (stubs until GPU runtime available)
        "vietvoice_tts",
        "vieneu_v3_turbo",
        "cosyvoice_3",
        "melo_tts_vi",
        "qwen3_tts",
        # Voice clone (stubs)
        "vieneu_voice_clone",
        "cosyvoice3_voice_clone",
        # OCR (stubs)
        "paddleocr",
        "easyocr",
        "craft",
        # Audio separation (stubs)
        "uvr5_mdx",
        "demucs",
        "bs_roformer",
    }


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
