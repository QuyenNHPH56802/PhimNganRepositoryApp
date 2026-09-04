"""Translation prompt templates.

The contract mirrors docs/provider-contracts.md section 5. Every translation
provider MUST build the same pair of messages (system + user) using this
helper so that prompt version increments stay in lock-step across providers.
"""

from __future__ import annotations

from typing import Any

PROMPT_VERSION = "v1"

SYSTEM_TEMPLATE = (
    "You are a professional Chinese→Vietnamese translator for localizing video. "
    "Preserve names (rendered via the alias table), follow the glossary exactly, "
    "match the style preset, never invent facts, never insert romanized pinyin. "
    "Return strictly JSON: {\"segments\": [{\"idx\": int, \"display_text\": str, \"tts_text\": str}]}"
)

USER_TEMPLATE = (
    "style_preset: {style_preset}\n"
    "glossary (zh -> vi): {glossary}\n"
    "alias_map: {aliases}\n"
    "character_bible: {character_bible}\n"
    "source_segments:\n{source_segments}\n"
)


def build_system_message(prompt_version: str = PROMPT_VERSION) -> dict[str, str]:
    if prompt_version != PROMPT_VERSION:
        raise ValueError(f"unknown prompt version {prompt_version}")
    return {"role": "system", "content": SYSTEM_TEMPLATE}


def build_user_message(
    *,
    style_preset: str,
    glossary: list[dict[str, str]],
    aliases: list[dict[str, str]],
    character_bible: list[dict[str, Any]],
    source_segments: list[dict[str, Any]],
) -> dict[str, str]:
    return {
        "role": "user",
        "content": USER_TEMPLATE.format(
            style_preset=style_preset,
            glossary=glossary,
            aliases=aliases,
            character_bible=character_bible,
            source_segments=source_segments,
        ),
    }
