"""CPS-aware subtitle segmentation provider.

Splits long display_text into multiple SubtitleLine entries so that the
characters-per-second (CPS) budget is honored. Vietnamese target: 15 CPS,
max 42 chars per line, min 1.2s, max 7s.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from translator_api.providers.base import Provider, ProviderCapabilities, ProviderContext
from translator_shared.providers import ArtifactSignature
from translator_shared.provider_configs import SubtitleProviderConfig
from translator_shared.provider_responses_extra import (
    SubtitleLine,
    SubtitleResponse,
    TranslationSegment,
)


@dataclass(frozen=True)
class SubtitleInput:
    translations: list[TranslationSegment]
    original_segments: list[dict] = field(default_factory=list)
    config: SubtitleProviderConfig | None = None


class CpsWrapperSubtitleProvider(Provider[SubtitleInput, SubtitleResponse]):
    id = "cps_wrapper"
    capabilities = ProviderCapabilities(requires_gpu=False)

    def __init__(self, config: SubtitleProviderConfig | None = None) -> None:
        self._config = config or SubtitleProviderConfig()

    def fingerprint(self, payload: SubtitleInput) -> ArtifactSignature:
        return ArtifactSignature(
            input_hash=hashlib.sha256(repr(payload.translations).encode("utf-8")).hexdigest()[:32],
            model_id=self.id,
            model_version="0.0.0",
            provider_build=self.id,
            config_hash=hashlib.sha256(repr(self._config).encode("utf-8")).hexdigest()[:32],
        )

    async def run(self, payload: SubtitleInput, *, ctx: ProviderContext) -> SubtitleResponse:
        cfg = self._config
        lines: list[SubtitleLine] = []
        for seg in payload.translations:
            start_ms, end_ms = _resolve_timing(seg.idx, payload.original_segments)
            if end_ms <= start_ms:
                end_ms = start_ms + cfg.min_duration_ms
            chunks = _wrap_text(seg.display_text, max_chars=cfg.max_chars_per_line)
            duration = end_ms - start_ms
            cps = _cps(seg.display_text, duration)
            if cps > cfg.target_cps:
                sub_count = max(1, int((cps / cfg.target_cps) + 0.999))
                sub_duration = duration // sub_count
                for i, chunk in enumerate(chunks[:sub_count]):
                    lines.append(
                        SubtitleLine(
                            idx=len(lines),
                            start_ms=start_ms + i * sub_duration,
                            end_ms=start_ms + (i + 1) * sub_duration,
                            text=chunk,
                        )
                    )
            else:
                sub_duration = max(cfg.min_duration_ms, min(cfg.max_duration_ms, duration))
                if len(chunks) == 1:
                    lines.append(SubtitleLine(idx=len(lines), start_ms=start_ms, end_ms=end_ms, text=chunks[0]))
                else:
                    per = max(cfg.min_duration_ms, duration // max(1, len(chunks)))
                    for i, chunk in enumerate(chunks):
                        lines.append(
                            SubtitleLine(
                                idx=len(lines),
                                start_ms=start_ms + i * per,
                                end_ms=start_ms + (i + 1) * per,
                                text=chunk,
                            )
                        )
        return SubtitleResponse(track_id=None, segments=lines, signature=self.fingerprint(payload))


def _resolve_timing(idx: int, original_segments: list[dict]) -> tuple[int, int]:
    for seg in original_segments:
        if int(seg.get("idx", -1)) == idx:
            return int(seg.get("start_ms", 0)), int(seg.get("end_ms", 0))
    return 0, 0


def _wrap_text(text: str, *, max_chars: int) -> list[str]:
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
    words = text.split()
    chunks: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = word
    if current:
        chunks.append(current)
    return chunks


def _cps(text: str, duration_ms: int) -> float:
    if duration_ms <= 0:
        return float("inf")
    return len(text) / (duration_ms / 1000)