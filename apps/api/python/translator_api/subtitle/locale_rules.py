"""Locale-aware subtitle rules."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Mapping

from translator_shared.locale import DEFAULT_LOCALE, SUPPORTED_LOCALES


@dataclass(frozen=True)
class LocaleRule:
    code: str
    cps: float
    max_line_length: int
    punctuation_begin: tuple[str, ...]
    punctuation_end: tuple[str, ...]


_LOCALE_RULES: Mapping[str, LocaleRule] = {
    "vi": LocaleRule("vi", cps=16.0, max_line_length=40, punctuation_begin=(), punctuation_end=(".", ",", "!", "?", "…")),
    "en": LocaleRule("en", cps=17.0, max_line_length=42, punctuation_begin=(), punctuation_end=(".", ",", "!", "?", "…")),
    "zh": LocaleRule("zh", cps=16.0, max_line_length=22, punctuation_begin=("（", "「", "『"), punctuation_end=("）", "」", "』", "。", "！", "？")),
    "ja": LocaleRule("ja", cps=14.0, max_line_length=22, punctuation_begin=("（", "「", "『"), punctuation_end=("）", "」", "』", "。", "！", "？")),
    "ko": LocaleRule("ko", cps=14.0, max_line_length=22, punctuation_begin=(), punctuation_end=(".", "?", "!", "。")),
}


class SubtitleCueFactory:
    """Factory keyed by locale code."""

    def __init__(self, locale: str) -> None:
        if locale not in _LOCALE_RULES:
            if locale not in SUPPORTED_LOCALES:
                raise KeyError(f"unsupported locale {locale}")
        self._locale = locale if locale in _LOCALE_RULES else DEFAULT_LOCALE
        self._rule = _LOCALE_RULES[self._locale]

    @property
    def locale(self) -> str:
        return self._locale

    @property
    def rule(self) -> LocaleRule:
        return self._rule

    def normalize(self, text: str) -> str:
        return unicodedata.normalize("NFC", text).strip()

    def clamp(self, text: str, *, max_duration_ms: int) -> tuple[str, int]:
        """Trim text + set end_ms so CPS does not exceed the locale limit."""

        text = self.normalize(text)
        if max_duration_ms <= 0:
            return text, 0
        chars = max(1, len(text))
        max_chars = max(1, int(self._rule.cps * (max_duration_ms / 1000.0)))
        if chars > max_chars:
            text = text[:max_chars].rstrip()
        new_duration = max(max_duration_ms, int(len(text) / self._rule.cps * 1000))
        return text, new_duration


def locale_rule(locale: str) -> LocaleRule:
    if locale in _LOCALE_RULES:
        return _LOCALE_RULES[locale]
    return _LOCALE_RULES[DEFAULT_LOCALE]