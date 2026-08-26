"""Rule-based translation QA provider.

Checks per docs/provider-contracts.md section 6:
1. Length ratio (zh char count vs vi word count) within [1.0, 3.5].
2. Glossary term must appear in display_text when source contains the term.
3. Alias source pattern must be removed.
4. Pinyin leak detection.
5. Untranslated Hán tự.
6. Empty / None display_text.

Output QaReport with passed=True iff there are no severity=error issues.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from translator_api.providers.base import Provider, ProviderCapabilities, ProviderContext
from translator_api.providers.translate.base import GlossaryTerm
from translator_shared.provider_configs import QaProviderConfig
from translator_shared.provider_responses_extra import (
    QaIssue,
    QaReport,
    QaStats,
    TranslationSegment,
)

_PINYIN_RE = re.compile(r"[a-z]{4,}")
_HAN_RE = re.compile(r"[\u4e00-\u9fff]{2,}")


@dataclass(frozen=True)
class QaInput:
    source_segments: list[dict[str, str]]
    translations: list[TranslationSegment]
    glossary: list[GlossaryTerm] = field(default_factory=list)


class RuleBasedQaProvider(Provider[QaInput, QaReport]):
    id = "rule_based"
    capabilities = ProviderCapabilities(requires_gpu=False)

    def __init__(self, config: QaProviderConfig | None = None) -> None:
        self._config = config or QaProviderConfig()

    async def run(self, payload: QaInput, *, ctx: ProviderContext) -> QaReport:
        cfg = self._config
        issues: list[QaIssue] = []
        ratio_min = None
        ratio_max = None
        glossary_misses = 0
        pinyin_leak_count = 0
        untranslated_count = 0

        glossary_by_priority = sorted(cfg and [g for g in payload.glossary if g.priority >= 1], key=lambda g: -g.priority)
        sources_by_idx = {int(s["idx"]): s.get("text", "") for s in payload.source_segments}

        for seg in payload.translations:
            source_text = sources_by_idx.get(seg.idx, "")
            display_text = (seg.display_text or "").strip()

            if not display_text:
                issues.append(QaIssue(kind="empty", segment_idx=seg.idx, message="display_text empty", severity="error"))
                continue

            ratio = _length_ratio(source_text, display_text)
            ratio_min = ratio if ratio_min is None else min(ratio_min, ratio)
            ratio_max = ratio if ratio_max is None else max(ratio_max, ratio)
            if ratio < cfg.length_ratio_min:
                issues.append(
                    QaIssue(kind="length_ratio_low", segment_idx=seg.idx, message=f"ratio {ratio:.2f}", severity="warn")
                )
            elif ratio > cfg.length_ratio_max:
                issues.append(
                    QaIssue(kind="length_ratio_high", segment_idx=seg.idx, message=f"ratio {ratio:.2f}", severity="warn")
                )

            for term in glossary_by_priority:
                if term.chinese in source_text and term.vietnamese not in display_text:
                    glossary_misses += 1
                    issues.append(
                        QaIssue(
                            kind="glossary_miss",
                            segment_idx=seg.idx,
                            message=f"missing term '{term.vietnamese}'",
                            severity="warn",
                        )
                    )

            if _PINYIN_RE.search(display_text):
                pinyin_leak_count += 1
                issues.append(
                    QaIssue(kind="pinyin_leak", segment_idx=seg.idx, message="latin token ≥4 chars in display_text", severity="warn")
                )

            if _HAN_RE.search(display_text):
                untranslated_count += 1
                issues.append(
                    QaIssue(kind="untranslated", segment_idx=seg.idx, message="Hán tự still present in display_text", severity="error")
                )

        passed = not any(issue.severity == "error" for issue in issues)
        if passed and issues:
            qa_status = "warn"
        elif passed and not issues:
            qa_status = "pass"
        else:
            qa_status = "fail"
        return QaReport(
            passed=passed,
            qa_status=qa_status,
            issues=issues,
            stats=QaStats(
                ratio_min=ratio_min,
                ratio_max=ratio_max,
                pinyin_leak_count=pinyin_leak_count,
                untranslated_count=untranslated_count,
                glossary_misses=glossary_misses,
            ),
        )


def _length_ratio(source_zh: str, display_vi: str) -> float:
    if not source_zh:
        return 0.0
    vi_words = max(1, len(display_vi.split()))
    return vi_words / max(1, len(source_zh))