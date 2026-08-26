"""Quality mode (FAST / BALANCED / HIGH) — canonical source.

This module is the single owner of `QualityMode` + `QualityPolicy`. The
shared `translator_shared.workflows` re-exports the enum for cross-
package use so worker + API + web share the same values.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class QualityMode(str, Enum):
    FAST = "fast"
    BALANCED = "balanced"
    HIGH = "high"


@dataclass(frozen=True)
class QualityPolicy:
    asr_provider: str
    diarize: bool
    alignment: bool
    voice_clone: bool
    mixer: bool
    subtitle_target_cps: float


_POLICIES: dict[QualityMode, QualityPolicy] = {
    QualityMode.FAST: QualityPolicy(
        asr_provider="faster-whisper",
        diarize=False,
        alignment=False,
        voice_clone=False,
        mixer=False,
        subtitle_target_cps=18.0,
    ),
    QualityMode.BALANCED: QualityPolicy(
        asr_provider="whisperx",
        diarize=True,
        alignment=True,
        voice_clone=False,
        mixer=True,
        subtitle_target_cps=16.0,
    ),
    QualityMode.HIGH: QualityPolicy(
        asr_provider="whisperx",
        diarize=True,
        alignment=True,
        voice_clone=True,
        mixer=True,
        subtitle_target_cps=14.0,
    ),
}


def policy_for(mode: QualityMode) -> QualityPolicy:
    return _POLICIES[mode]


def modes() -> list[str]:
    return [m.value for m in QualityMode]
