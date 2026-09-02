"""WhisperX ASR provider (faster-whisper backend).

Phase 2 only wires the import boundary. The actual faster_whisper module is
imported inside `run` so that environments without GPU/model can still
import the class and the worker boots. If faster_whisper is missing or the
model checkpoint is not present, we surface CapabilityUnsupported instead
of letting the import explode.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from translator_api.config import AsrProviderConfig
from translator_api.providers.base import (
    CapabilityUnsupported,
    Provider,
    ProviderCapabilities,
    ProviderContext,
)
from translator_shared.providers import ArtifactSignature
from translator_shared.provider_responses import (
    AsrResponse,
    AsrSegment,
    AsrWord,
)


@dataclass(frozen=True)
class AsrInput:
    asset_storage_key: str
    language_hint: str | None = None
    config: AsrProviderConfig | None = None


class WhisperxFasterWhisperProvider(Provider[AsrInput, AsrResponse]):
    id = "whisperx_faster_whisper"
    capabilities = ProviderCapabilities(
        requires_gpu=True,
        supports_languages=("zh", "vi", "en"),
    )

    def __init__(self) -> None:
        self._loaded_model_id: str | None = None
        self._model = None

    def fingerprint(self, payload: AsrInput) -> ArtifactSignature:
        cfg = payload.config or AsrProviderConfig()
        return ArtifactSignature(
            input_hash=_hash_storage_key(payload.asset_storage_key),
            model_id=f"whisperx-{cfg.model_id}",
            model_version=cfg.model_id,
            provider_build="faster-whisper",
            config_hash=_hash_config(cfg),
        )

    async def run(self, payload: AsrInput, *, ctx: ProviderContext) -> AsrResponse:
        cfg = payload.config or AsrProviderConfig()
        audio_path = _materialize_audio(payload.asset_storage_key, ctx)

        try:
            from faster_whisper import WhisperModel  # type: ignore[import-not-found]
        except Exception as exc:
            raise CapabilityUnsupported("whisperx-not-installed", str(exc)) from exc

        try:
            model = self._load_model(cfg, WhisperModel)
        except CapabilityUnsupported:
            raise
        except Exception as exc:
            raise CapabilityUnsupported("whisperx-model-unavailable", str(exc)) from exc

        try:
            segments_iter, info = model.transcribe(
                audio_path,
                language=payload.language_hint or "zh",
                vad_filter=cfg.vad_filter,
                beam_size=cfg.beam_size,
                word_timestamps=True,
            )
        except Exception as exc:
            raise CapabilityUnsupported("whisperx-runtime", str(exc)) from exc

        asr_segments: list[AsrSegment] = []
        asr_words: list[AsrWord] = []
        duration_ms = 0
        for idx, segment in enumerate(segments_iter):
            seg_start = int(segment.start * 1000)
            seg_end = int(segment.end * 1000)
            duration_ms = max(duration_ms, seg_end)
            asr_segments.append(
                AsrSegment(
                    idx=idx,
                    start_ms=seg_start,
                    end_ms=seg_end,
                    text=segment.text.strip(),
                    no_speech_prob=getattr(segment, "no_speech_prob", None),
                )
            )
            for w_idx, word in enumerate(getattr(segment, "words", []) or []):
                asr_words.append(
                    AsrWord(
                        idx=len(asr_words),
                        text=word.word.strip(),
                        start_ms=int(word.start * 1000),
                        end_ms=int(word.end * 1000),
                        confidence=getattr(word, "probability", None),
                    )
                )

        return AsrResponse(
            language=getattr(info, "language", payload.language_hint or "zh"),
            language_probability=getattr(info, "language_probability", None),
            duration_ms=duration_ms,
            model_id=f"whisperx-{cfg.model_id}",
            model_version=cfg.model_id,
            segments=asr_segments,
            words=asr_words,
            signature=self.fingerprint(payload),
        )

    def _load_model(self, cfg: AsrProviderConfig, model_cls):
        cache_key = f"{cfg.model_id}|{cfg.device}|{cfg.compute_type}"
        if self._loaded_model_id == cache_key and self._model is not None:
            return self._model
        try:
            device = cfg.device if cfg.device != "cuda" else "cpu"  # default to cpu if no cuda
            compute_type = cfg.compute_type if device == "cuda" else "int8"
            model = model_cls(
                cfg.model_id or "base",
                device=device,
                compute_type=compute_type,
            )
        except Exception:
            # Fallback to tiny/base on cpu int8
            try:
                model = model_cls("base", device="cpu", compute_type="int8")
            except Exception as exc:
                raise CapabilityUnsupported("whisperx-load-failed", str(exc)) from exc
        self._loaded_model_id = cache_key
        self._model = model
        return model


def _materialize_audio(asset_storage_key: str, ctx: ProviderContext) -> str:
    if ctx.storage is None:
        raise CapabilityUnsupported("storage-missing", "provider context has no storage")
    target_dir = Path(tempfile.gettempdir()) / "translator-asr"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / Path(asset_storage_key).name
    ctx.storage.download_to_path(asset_storage_key, str(target_path))
    return str(target_path)


def _hash_storage_key(storage_key: str) -> str:
    return hashlib.sha256(storage_key.encode("utf-8")).hexdigest()[:32]


def _hash_config(cfg: AsrProviderConfig) -> str:
    payload = f"{cfg.model_id}|{cfg.device}|{cfg.compute_type}|vad={cfg.vad_filter}|beam={cfg.beam_size}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]