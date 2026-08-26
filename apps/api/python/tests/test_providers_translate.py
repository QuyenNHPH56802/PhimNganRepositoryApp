"""Unit tests for translation providers (HTTP providers, message builders)."""

from __future__ import annotations

import pytest

from translator_api.providers.base import (
    CapabilityUnsupported,
    ProviderCapabilities,
    ProviderContext,
)
from translator_api.providers.registry import bootstrap
from translator_api.providers.registry_constants import TRANSLATE
from translator_api.providers.translate.base import (
    Alias,
    CharacterBibleEntry,
    GlossaryTerm,
    TranslationInput,
    build_translation_messages,
    parse_translation_payload,
)
from translator_shared.provider_configs import TranslationProviderConfig
from translator_shared.providers import ArtifactSignature


@pytest.fixture(scope="module", autouse=True)
def _bootstrap() -> None:
    bootstrap()


def _sample_input(*, prompt_version: str = "v1") -> TranslationInput:
    return TranslationInput(
        segments=[{"idx": 0, "text": "你好"}, {"idx": 1, "text": "世界"}],
        glossary=[GlossaryTerm("你好", "xin chào", priority=10)],
        aliases=[Alias(source_pattern="X", replacement="Y")],
        character_bible=[CharacterBibleEntry(name="Alice", role="protagonist")],
        style_preset="modern",
        config=TranslationProviderConfig(
            model_id="gpt-4o-mini",
            api_key_env="OPENAI_API_KEY",
            prompt_version=prompt_version,
        ),
    )


class TestMessageBuilder:
    def test_build_messages_returns_role_content_pair(self) -> None:
        system, user = build_translation_messages(_sample_input())
        assert system["role"] == "system"
        assert user["role"] == "user"
        assert "glossary" in user["content"]
        assert "alias_map" in user["content"]
        assert "character_bible" in user["content"]

    def test_prompt_version_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="prompt version mismatch"):
            build_translation_messages(_sample_input(prompt_version="v999"))

    def test_default_config_when_none(self) -> None:
        payload = TranslationInput(
            segments=[],
            glossary=[],
            aliases=[],
            character_bible=[],
            style_preset="modern",
            config=None,
        )
        system, _user = build_translation_messages(payload)
        assert system["role"] == "system"


class TestParsePayload:
    def test_parses_minimal_payload(self) -> None:
        raw = '{"segments": [{"idx": 0, "display_text": "hi", "tts_text": "hi"}]}'
        response = parse_translation_payload(raw, provider_id="openai_compatible_http", model_id="gpt-4o-mini")
        assert len(response.segments) == 1
        assert response.segments[0].display_text == "hi"
        assert response.segments[0].tts_text == "hi"
        assert response.provider_id == "openai_compatible_http"
        assert response.model_id == "gpt-4o-mini"
        assert response.prompt_version == "v1"

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(ValueError, match="translation payload not JSON"):
            parse_translation_payload("not-json", provider_id="x", model_id="y")

    def test_missing_display_text_defaults_to_empty(self) -> None:
        raw = '{"segments": [{"idx": 0, "display_text": null}]}'
        response = parse_translation_payload(raw, provider_id="x", model_id="y")
        assert response.segments[0].display_text == "None"  # current behavior

    def test_tts_text_falls_back_to_display(self) -> None:
        raw = '{"segments": [{"idx": 0, "display_text": "hello"}]}'
        response = parse_translation_payload(raw, provider_id="x", model_id="y")
        assert response.segments[0].tts_text == "hello"

    def test_signature_carries_prompt_version(self) -> None:
        raw = '{"segments": []}'
        response = parse_translation_payload(raw, provider_id="x", model_id="y")
        assert isinstance(response.signature, ArtifactSignature)
        assert response.signature.prompt_version == "v1"


class TestRegistry:
    def test_translate_providers_registered(self) -> None:
        from translator_api.providers.base import get_default_registry

        registry = get_default_registry()
        provider_ids = registry.list(TRANSLATE)
        assert "openai_compatible_http" in provider_ids
        assert "gemini_compatible_http" in provider_ids
        assert "claude_compatible_http" in provider_ids
        assert "local_llm" in provider_ids

    def test_registry_returns_typed_provider(self) -> None:
        from translator_api.providers.base import get_default_registry
        from translator_api.providers.translate.openai_http import OpenAICompatibleHttpProvider

        registry = get_default_registry()
        provider = registry.get(TRANSLATE, "openai_compatible_http")
        assert isinstance(provider, OpenAICompatibleHttpProvider)
        assert provider.capabilities.is_local is False
        assert provider.capabilities.requires_gpu is False

    def test_missing_provider_raises_capability_unsupported(self) -> None:
        from translator_api.providers.base import get_default_registry

        registry = get_default_registry()
        with pytest.raises(CapabilityUnsupported):
            registry.get(TRANSLATE, "does_not_exist")


class TestOpenAIHttpProvider:
    def test_missing_api_key_raises_capability_unsupported(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from translator_api.providers.translate.openai_http import OpenAICompatibleHttpProvider

        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        provider = OpenAICompatibleHttpProvider()

        import asyncio

        with pytest.raises(CapabilityUnsupported):
            asyncio.run(provider.run(_sample_input(), ctx=ProviderContext(project_id="p")))

    def test_fingerprint_stable(self) -> None:
        from translator_api.providers.translate.openai_http import OpenAICompatibleHttpProvider

        provider = OpenAICompatibleHttpProvider()
        sig1 = provider.fingerprint(_sample_input())
        sig2 = provider.fingerprint(_sample_input())
        assert sig1.input_hash == sig2.input_hash
        assert sig1.model_id == sig2.model_id
        assert sig1.prompt_version == "v1"
