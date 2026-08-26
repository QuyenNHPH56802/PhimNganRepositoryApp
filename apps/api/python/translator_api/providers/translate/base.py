"""Common types + helpers for translation providers."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from translator_api.prompts.translate_prompt import (
    PROMPT_VERSION,
    build_system_message,
    build_user_message,
)
from translator_shared.provider_configs import TranslationProviderConfig
from translator_shared.provider_responses_extra import TranslationResponse, TranslationSegment


@dataclass(frozen=True)
class GlossaryTerm:
    chinese: str
    vietnamese: str
    priority: int = 0


@dataclass(frozen=True)
class Alias:
    source_pattern: str
    replacement: str


@dataclass(frozen=True)
class CharacterBibleEntry:
    name: str
    role: str
    preferred_pronouns: dict[str, str] = field(default_factory=dict)
    preferred_honorifics: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TranslationInput:
    segments: list[dict[str, Any]]
    glossary: list[GlossaryTerm]
    aliases: list[Alias]
    character_bible: list[CharacterBibleEntry]
    style_preset: str
    config: TranslationProviderConfig | None = None


def build_translation_messages(payload: TranslationInput) -> tuple[dict[str, str], dict[str, str]]:
    cfg = payload.config or TranslationProviderConfig()
    if cfg.prompt_version != PROMPT_VERSION:
        raise ValueError(f"prompt version mismatch: provider={cfg.prompt_version} expected={PROMPT_VERSION}")
    system = build_system_message(cfg.prompt_version)
    user = build_user_message(
        style_preset=payload.style_preset,
        glossary=[{"chinese": t.chinese, "vietnamese": t.vietnamese, "priority": t.priority} for t in payload.glossary],
        aliases=[{"source_pattern": a.source_pattern, "replacement": a.replacement} for a in payload.aliases],
        character_bible=[e.__dict__ for e in payload.character_bible],
        source_segments=payload.segments,
    )
    return system, user


def parse_translation_payload(raw: str, *, provider_id: str, model_id: str) -> TranslationResponse:
    try:
        body = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"translation payload not JSON: {exc}") from exc
    segments_data = body.get("segments", [])
    parsed = [
        TranslationSegment(
            idx=int(s.get("idx", idx)),
            display_text=str(s.get("display_text", "")),
            tts_text=str(s.get("tts_text", s.get("display_text", ""))),
            applied_glossary_terms=list(s.get("applied_glossary_terms", []) or []),
            applied_aliases=list(s.get("applied_aliases", []) or []),
            confidence=s.get("confidence"),
        )
        for idx, s in enumerate(segments_data)
    ]
    from translator_shared.providers import ArtifactSignature

    signature = ArtifactSignature(
        input_hash="pending",
        model_id=model_id,
        model_version=model_id,
        provider_build=provider_id,
        config_hash="pending",
        prompt_version=PROMPT_VERSION,
    )
    return TranslationResponse(
        provider_id=provider_id,
        model_id=model_id,
        prompt_version=PROMPT_VERSION,
        segments=parsed,
        signature=signature,
    )