"""Sentence-aligned text chunker for the TTS service.

Mirrors ``translator_api.providers.tts.edge.chunk_text`` so both the in-process
provider and the microservice share identical chunking semantics.
"""

from __future__ import annotations

import re

_SENTENCE_END = re.compile(r"([.!?\n])")

DEFAULT_MAX_CHARS = 500


def chunk_text(text: str, max_chars: int = DEFAULT_MAX_CHARS) -> list[str]:
    """Split ``text`` into sentence-aligned chunks of <= ``max_chars`` chars."""
    cleaned = (text or "").strip()
    if not cleaned:
        return []
    if len(cleaned) <= max_chars:
        return [cleaned]

    sentences: list[str] = []
    parts = _SENTENCE_END.split(cleaned)
    i = 0
    while i < len(parts):
        segment = parts[i].strip()
        delim = parts[i + 1] if i + 1 < len(parts) else ""
        i += 2
        if not segment and not delim:
            continue
        sentences.append((segment + delim).strip())

    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if not sentence:
            continue
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            for j in range(0, len(sentence), max_chars):
                chunks.append(sentence[j : j + max_chars])
            continue
        if not current:
            current = sentence
        elif len(current) + 1 + len(sentence) <= max_chars:
            current = f"{current} {sentence}"
        else:
            chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    return chunks
