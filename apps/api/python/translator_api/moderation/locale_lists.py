"""Locale-aware banned-phrase lists.

Phase 10 expands moderation to per-locale lists. Lists are loaded from
JSON files under `apps/api/python/translator_api/moderation/locales/`.
Falls back to an empty list if a locale is missing so missing data
degrades open (review flag instead of hard block).
"""

from __future__ import annotations

import json
import pathlib
from collections.abc import Iterable


def _data_dir() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent / "locales"


def banned_phrases(locale: str) -> list[str]:
    path = _data_dir() / f"{locale}.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("banned_phrases", [])
    except (OSError, json.JSONDecodeError):
        return []


def any_match(text: str, locale: str) -> list[str]:
    phrases = banned_phrases(locale)
    lowered = text.lower()
    return [phrase for phrase in phrases if phrase.lower() in lowered]


def supported_locales() -> Iterable[str]:
    return sorted(path.stem for path in _data_dir().glob("*.json"))