"""Language pair matrix + helpers."""

from __future__ import annotations

from typing import Iterable

SUPPORTED_LOCALES: tuple[str, ...] = ("vi", "en", "zh", "ja", "ko", "fr", "de", "es", "pt", "th")
DEFAULT_LOCALE = "vi"

# Phase 10: matrix of (source, target) -> supported providers.
LANGUAGE_PAIRS: dict[tuple[str, str], frozenset[str]] = {
    ("zh", "vi"): frozenset({"deepseek", "openai", "gemini", "claude", "local_nllb"}),
    ("vi", "zh"): frozenset({"deepseek", "openai", "gemini", "claude", "local_nllb"}),
    ("zh", "en"): frozenset({"openai", "gemini", "claude", "local_nllb"}),
    ("en", "zh"): frozenset({"openai", "gemini", "claude", "local_nllb"}),
    ("zh", "ja"): frozenset({"openai", "gemini", "claude"}),
    ("ja", "zh"): frozenset({"openai", "gemini", "claude"}),
    ("zh", "ko"): frozenset({"openai", "gemini", "claude"}),
    ("ko", "zh"): frozenset({"openai", "gemini", "claude"}),
    ("en", "vi"): frozenset({"openai", "gemini", "claude", "local_nllb"}),
    ("vi", "en"): frozenset({"openai", "gemini", "claude", "local_nllb"}),
}


def supported_pair(src: str, tgt: str) -> bool:
    return (src, tgt) in LANGUAGE_PAIRS


def providers_for_pair(src: str, tgt: str) -> frozenset[str]:
    return LANGUAGE_PAIRS.get((src, tgt), frozenset())


def list_pairs() -> Iterable[tuple[str, str]]:
    return LANGUAGE_PAIRS.keys()


def parse_accept_language(header: str) -> str:
    """Very small Accept-Language parser. Returns the highest-priority supported locale."""

    candidates: list[tuple[float, str]] = []
    for chunk in header.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split(";")
        tag = parts[0].strip().lower()
        q = 1.0
        for token in parts[1:]:
            token = token.strip()
            if token.startswith("q="):
                try:
                    q = float(token[2:])
                except ValueError:
                    q = 1.0
        if tag in SUPPORTED_LOCALES:
            candidates.append((q, tag))
    if not candidates:
        return DEFAULT_LOCALE
    candidates.sort(key=lambda c: c[0], reverse=True)
    return candidates[0][1]


def is_rtl(locale: str) -> bool:
    # Stub — no RTL locales in the current set.
    return False