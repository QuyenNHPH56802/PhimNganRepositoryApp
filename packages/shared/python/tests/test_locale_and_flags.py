"""Unit tests for the locale matrix + feature flag registry."""

from __future__ import annotations

import pytest


class TestLocaleMatrix:
    def test_supported_pairs_unique(self) -> None:
        from translator_shared.locale import LANGUAGE_PAIRS, SUPPORTED_LOCALES

        for (src, tgt) in LANGUAGE_PAIRS:
            assert src in SUPPORTED_LOCALES
            assert tgt in SUPPORTED_LOCALES
            assert src != tgt

    def test_supported_pair_positive(self) -> None:
        from translator_shared.locale import supported_pair

        assert supported_pair("zh", "vi") is True
        assert supported_pair("vi", "zh") is True
        assert supported_pair("en", "vi") is True

    def test_supported_pair_negative(self) -> None:
        from translator_shared.locale import supported_pair

        assert supported_pair("fr", "de") is False

    def test_providers_for_pair_returns_frozenset(self) -> None:
        from translator_shared.locale import providers_for_pair

        providers = providers_for_pair("zh", "vi")
        assert "deepseek" in providers
        assert "openai" in providers

    def test_providers_for_unknown_pair_empty(self) -> None:
        from translator_shared.locale import providers_for_pair

        assert providers_for_pair("xx", "yy") == frozenset()

    def test_default_locale_is_vi(self) -> None:
        from translator_shared.locale import DEFAULT_LOCALE

        assert DEFAULT_LOCALE == "vi"


class TestAcceptLanguage:
    def test_parses_simple_tag(self) -> None:
        from translator_shared.locale import parse_accept_language

        assert parse_accept_language("vi") == "vi"

    def test_prefers_highest_q(self) -> None:
        from translator_shared.locale import parse_accept_language

        result = parse_accept_language("fr;q=0.1, zh;q=0.9")
        assert result == "zh"

    def test_fallback_to_default(self) -> None:
        from translator_shared.locale import DEFAULT_LOCALE, parse_accept_language

        assert parse_accept_language("xx") == DEFAULT_LOCALE
        assert parse_accept_language("") == DEFAULT_LOCALE

    def test_ignores_unsupported(self) -> None:
        from translator_shared.locale import parse_accept_language

        # xx is not in SUPPORTED_LOCALES, so we fall back
        assert parse_accept_language("xx;q=0.5, vi;q=0.1") == "vi"


class TestFeatureFlags:
    def _setup(self):
        from translator_shared.feature_flags import (
            FeatureFlagRegistry,
            FlagSpec,
            FlagState,
            _truthy,
        )

        reg = FeatureFlagRegistry()
        reg.register(FlagSpec(name="test.flag", state=FlagState.ALPHA, default=False, rollout_percent=100))
        return reg, _truthy

    def test_default_off(self) -> None:
        reg, _ = self._setup()
        assert reg.is_enabled("test.flag") is False

    def test_env_override_on(self, monkeypatch: pytest.MonkeyPatch) -> None:
        reg, _ = self._setup()
        monkeypatch.setenv("FLAG_TEST_FLAG", "true")
        assert reg.is_enabled("test.flag") is True

    def test_file_override(self, tmp_path) -> None:
        reg, _ = self._setup()
        config = tmp_path / "flags.json"
        config.write_text('{"test.flag": true}', encoding="utf-8")
        reg.override_file(str(config))
        assert reg.is_enabled("test.flag") is True

    def test_audit_records_resolution(self, monkeypatch: pytest.MonkeyPatch) -> None:
        reg, _ = self._setup()
        monkeypatch.setenv("FLAG_TEST_FLAG", "1")
        reg.is_enabled("test.flag", subject="user-42")
        audit = reg.audit()
        assert len(audit) == 1
        assert audit[0]["enabled"] is True
        assert audit[0]["source"] == "env"
        assert audit[0]["subject"] == "user-42"

    def test_missing_spec_returns_false(self) -> None:
        reg, _ = self._setup()
        assert reg.is_enabled("not.registered") is False
        audit = reg.audit()
        assert audit[0]["source"] == "missing-spec"

    def test_rollout_percent_excludes_some_subjects(self) -> None:
        from translator_shared.feature_flags import (
            FeatureFlagRegistry,
            FlagSpec,
            FlagState,
        )

        reg = FeatureFlagRegistry()
        reg.register(FlagSpec(name="rollout.test", state=FlagState.BETA, default=True, rollout_percent=10))
        excluded = 0
        for i in range(200):
            if not reg.is_enabled("rollout.test", subject=f"user-{i}"):
                excluded += 1
        # With 10% rollout and 200 subjects, expect ~180 excluded
        assert 150 < excluded < 210

    def test_truthy_parses_common_forms(self) -> None:
        from translator_shared.feature_flags import _truthy

        assert _truthy("true") is True
        assert _truthy("1") is True
        assert _truthy("YES") is True
        assert _truthy("on") is True
        assert _truthy("off") is False
        assert _truthy("0") is False
