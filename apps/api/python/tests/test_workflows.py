"""Unit tests for workflow contracts (QualityMode, WorkflowStatus enums)."""

from __future__ import annotations

import pytest


class TestWorkflowStatus:
    def test_all_states_present(self) -> None:
        from translator_shared.workflows import WorkflowStatus

        expected = {"draft", "processing", "awaiting_review", "ready", "archived", "failed"}
        actual = {state.value for state in WorkflowStatus}
        assert expected.issubset(actual)

    def test_serialization_round_trip(self) -> None:
        from translator_shared.workflows import WorkflowStatus

        for state in WorkflowStatus:
            assert WorkflowStatus(state.value) is state

    def test_unknown_state_raises(self) -> None:
        from translator_shared.workflows import WorkflowStatus

        with pytest.raises(ValueError):
            WorkflowStatus("nonsense")


class TestQualityPolicy:
    def test_fast_policy_no_diarization(self) -> None:
        from translator_api.quality_mode import QualityMode, policy_for

        policy = policy_for(QualityMode.FAST)
        assert policy.diarize is False
        assert policy.voice_clone is False
        assert policy.alignment is False

    def test_balanced_policy_has_alignment(self) -> None:
        from translator_api.quality_mode import QualityMode, policy_for

        policy = policy_for(QualityMode.BALANCED)
        assert policy.alignment is True
        assert policy.voice_clone is False

    def test_high_policy_full(self) -> None:
        from translator_api.quality_mode import QualityMode, policy_for

        policy = policy_for(QualityMode.HIGH)
        assert policy.voice_clone is True
        assert policy.diarize is True
        assert policy.alignment is True

    def test_cps_decreases_with_quality(self) -> None:
        from translator_api.quality_mode import QualityMode, policy_for

        fast = policy_for(QualityMode.FAST).subtitle_target_cps
        balanced = policy_for(QualityMode.BALANCED).subtitle_target_cps
        high = policy_for(QualityMode.HIGH).subtitle_target_cps
        assert fast > balanced > high

    def test_modes_returns_strings(self) -> None:
        from translator_api.quality_mode import QualityMode, modes

        values = modes()
        assert "fast" in values
        assert "balanced" in values
        assert "high" in values
        assert all(isinstance(v, str) for v in values)
        assert values == [m.value for m in QualityMode]


class TestWorkflowInputSchema:
    def test_translation_input_serializes(self) -> None:
        from translator_api.providers.translate.base import (
            Alias,
            CharacterBibleEntry,
            GlossaryTerm,
            TranslationInput,
        )

        payload = TranslationInput(
            segments=[{"idx": 0, "text": "hi"}],
            glossary=[GlossaryTerm("a", "b")],
            aliases=[Alias("c", "d")],
            character_bible=[CharacterBibleEntry(name="x", role="y")],
            style_preset="modern",
        )
        d = payload.__dict__
        assert d["style_preset"] == "modern"
        assert d["glossary"][0].vietnamese == "b"

    def test_glossary_priority_default_zero(self) -> None:
        from translator_api.providers.translate.base import GlossaryTerm

        term = GlossaryTerm("a", "b")
        assert term.priority == 0
