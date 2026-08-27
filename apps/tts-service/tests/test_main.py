"""Unit tests for the TTS microservice main app: request validation and routing."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tts_service.main import app


class TestHealthEndpoints:
    def test_healthz(self) -> None:
        client = TestClient(app)
        response = client.get("/healthz")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert "uptime_s" in body

    def test_readyz(self) -> None:
        client = TestClient(app)
        response = client.get("/readyz")
        assert response.status_code == 200
        body = response.json()
        assert "engine" in body
        assert "cache" in body

    def test_voices_list(self) -> None:
        client = TestClient(app)
        response = client.get("/voices")
        assert response.status_code == 200
        body = response.json()
        assert "voices" in body
        assert "total" in body
        assert isinstance(body["voices"], list)
        assert len(body["voices"]) > 0
        for entry in body["voices"]:
            assert "name" in entry
            assert "locale" in entry


class TestSynthesizeValidation:
    def test_empty_text_rejected(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/synthesize",
            json={"text": "", "voice": "vi-VN-HoaiMyNeural"},
        )
        assert response.status_code in (400, 422)

    def test_text_too_long_rejected(self) -> None:
        client = TestClient(app)
        # Send text that would create > TTS_MAX_CHUNK=500 chars total; we want
        # to assert the Pydantic max_length validation kicks in.
        long_text = "x" * 25000
        response = client.post(
            "/synthesize",
            json={"text": long_text, "voice": "vi-VN-HoaiMyNeural"},
        )
        # 422 from Pydantic validation (max_length), 413 from runtime guard.
        assert response.status_code in (413, 422)

    def test_invalid_engine_rejected(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/synthesize",
            json={"text": "hello", "voice": "vi-VN-HoaiMyNeural", "engine": "bogus"},
        )
        assert response.status_code == 422