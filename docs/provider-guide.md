# 🔌 Provider Implementation Guide

**Last Updated:** 2026-09-04
**Audience:** Engineers adding new translation, TTS, OCR, or voice-cloning backends.

This guide walks through adding a new provider to the platform. The pattern
applies uniformly to every kind (`translate`, `tts`, `ocr`, `voice_clone`,
`asr`, `align`, `diarize`, …).

> **Architecture overview:** see [`architecture-diagrams.md`](./architecture-diagrams.md) §3 (Provider Registry).
> **Reference providers:** see [`providers.md`](./providers.md) for the full catalog.

---

## 1. Concepts

| Concept | Meaning |
|---------|---------|
| **Provider** | A class that wraps one external service (e.g. `OpenAITranslator`). |
| **Provider ID** | Stable string used in DB / API to identify the implementation (e.g. `openai_compatible_http`). |
| **Kind** | Grouping: `translate`, `tts`, `ocr`, `voice_clone`, etc. |
| **Registry** | Singleton that maps `(kind, provider_id) → instance` and exposes lookup helpers. |
| **Bootstrap** | Registers the default providers at process start. |

The worker code never imports providers directly — it calls
`registry.get_translator("openai_compatible_http")` or
`registry.get_tts("cloud_azure")`. This indirection means new backends can be
added without touching worker code.

---

## 2. Directory layout

```
apps/api/python/translator_api/providers/
├── __init__.py
├── registry.py             ← singleton + bootstrap()
├── base.py                 ← abstract base classes (Translator, TTS, OCR, ...)
├── translate/
│   ├── __init__.py
│   ├── openai_compat.py
│   ├── gemini_compat.py
│   ├── claude_compat.py
│   ├── local_llm.py
│   └── passthrough.py
├── tts/
│   ├── __init__.py
│   ├── azure.py
│   ├── google.py
│   ├── elevenlabs.py
│   ├── edge.py
│   └── ... (one file per provider)
└── ocr/
    ├── __init__.py
    └── ...
```

Each `<kind>/` directory exports:

1. **Provider class** in `<kind>/<name>.py` (e.g. `tts/azure.py`).
2. **`register()`** function called by `bootstrap()` with provider id + class.

---

## 3. Step-by-step: adding a translation provider

We'll add a fictional `MyCloudTranslator` provider.

### 3.1 Define the provider class

Create `apps/api/python/translator_api/providers/translate/mycloud.py`:

```python
"""MyCloud translation provider."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from translator_api.providers.base import (
    Provider,
    ProviderCapabilities,
    ProviderContext,
    ProviderError,
)
from translator_shared.providers import ArtifactSignature

logger = logging.getLogger(__name__)


class MyCloudTranslator(Provider):
    """Translator backed by the MyCloud HTTP API.

    Required env: MYCLOUD_API_KEY
    Optional env: MYCLOUD_BASE_URL (defaults to https://api.mycloud.com)
                   MYCLOUD_MODEL (defaults to mycloud-translate-1)
    """

    id = "mycloud_translate"
    capabilities = ProviderCapabilities(
        is_local=False,
        supports_languages=("zh", "en", "vi", "ja", "ko"),
    )

    def __init__(self) -> None:
        self.api_key = os.environ["MYCLOUD_API_KEY"]
        self.base_url = os.environ.get("MYCLOUD_BASE_URL", "https://api.mycloud.com")
        self.model = os.environ.get("MYCLOUD_MODEL", "mycloud-translate-1")
        self._client: httpx.AsyncClient | None = None

    async def setup(self) -> None:
        """Lazy init — called by the registry before the first request."""
        self._client = httpx.AsyncClient(timeout=30.0)

    async def run(self, payload: dict[str, Any], *, ctx: ProviderContext) -> dict[str, Any]:
        if self._client is None:
            await self.setup()

        texts = payload["texts"]
        source = payload["source_lang"]
        target = payload["target_lang"]
        glossary = payload.get("glossary") or {}

        body = {
            "model": self.model,
            "source": source,
            "target": target,
            "inputs": list(texts),
            "glossary": glossary,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            assert self._client is not None
            r = await self._client.post(
                f"{self.base_url}/v1/translate",
                json=body,
                headers=headers,
            )
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ProviderError(
                code="mycloud_http_error",
                message=(
                    f"MyCloud dịch thất bại: HTTP {e.response.status_code} — "
                    f"{(e.response.text or '')[:200]}"
                ),
                retryable=e.response.status_code >= 500,
            ) from e
        except httpx.RequestError as e:
            raise ProviderError(
                code="mycloud_unreachable",
                message=f"MyCloud không phản hồi: {e}",
                retryable=True,
            ) from e

        data = r.json()
        outputs = data.get("translations")
        if not isinstance(outputs, list) or len(outputs) != len(texts):
            raise ProviderError(
                code="mycloud_malformed",
                message=f"MyCloud trả về response không hợp lệ: {data!r}",
                retryable=False,
            )

        return {"translations": [str(x) for x in outputs]}

    def fingerprint(self, payload: dict[str, Any]) -> ArtifactSignature:
        # Used for caching — same input + same config = same fingerprint.
        import hashlib, json
        h = hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        return ArtifactSignature(
            input_hash=h,
            model_id=self.id,
            model_version=self.model,
            provider_build="1.0.0",
            config_hash=h,
        )

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
```

### 3.2 Register it

Add a `register()` function in the same file:

```python
from translator_api.providers.registry import registry

def register() -> None:
    registry.register("translate", MyCloudTranslator())
```

Then add to the `__init__.py` of the `translate/` directory:

```python
# apps/api/python/translator_api/providers/translate/__init__.py
from . import openai_compat, gemini_compat, claude_compat, local_llm, passthrough, mycloud  # noqa: F401
```

### 3.3 Wire bootstrap

`registry.bootstrap()` runs at module import time. Add to
`apps/api/python/translator_api/providers/registry.py`:

```python
def bootstrap() -> None:
    # ... existing registrations ...

    from translator_api.providers.translate.mycloud import register as _mycloud
    _mycloud()
```

### 3.4 Add admin UI config

`apps/web/app/settings/page.tsx` reads provider list from `/api/providers`.
Ensure your provider shows up there. If it needs extra UI fields (API key
form), add a row to the `AVAILABLE_MODELS` list or use the `1-Click installer`
pattern documented in the settings page.

### 3.5 Smoke test

```bash
cd apps/api/python
python -c "
import asyncio
from translator_api.providers import registry
from translator_api.providers.base import ProviderContext
registry.bootstrap()
p = registry.get('translate', 'mycloud_translate')
asyncio.run(p.setup())
ctx = ProviderContext(project_id='00000000-0000-0000-0000-000000000000')
out = asyncio.run(p.run({'texts': ['你好'], 'source_lang': 'zh', 'target_lang': 'vi'}, ctx=ctx))
print(out)
"
```

### 3.6 Add docs entry

Add a row to [`docs/providers.md`](./providers.md):

```markdown
| 3 | translate | mycloud_translate | MyCloud Translate | MyCloud TOS | ⚠ caller's key |
```

---

## 4. Step-by-step: adding a TTS provider

Same flow but with `kind="tts"`:

```python
from translator_api.providers.base import (
    Provider,
    ProviderCapabilities,
    ProviderContext,
    ProviderError,
)

class MyCloudTTS(Provider):
    id = "mycloud_tts"
    capabilities = ProviderCapabilities(
        is_local=False,
        supports_languages=("vi",),
    )

    async def run(self, payload: dict, *, ctx: ProviderContext) -> dict:
        # Call MyCloud, write the resulting audio bytes to ctx.storage
        # at a path like f"tts/{ctx.project_id}/{uuid4()}.wav" and return
        # {"storage_key": "tts/<...>.wav", "duration_ms": 1234}
        ...

    async def list_voices(self) -> list[dict]:
        # Provider-specific extension; called from /api/providers/voices
        return [
            {"id": "vi-female-1", "name": "VI Female 1", "language": "vi"},
        ]
```

Then register with `registry.register("tts", MyCloudTTS())` and update `tts/__init__.py`.

---

## 5. Best practices

### 5.1 Use lazy initialization

Don't open network connections or load heavy models in `__init__`. Use
`async def setup()` that the registry calls once before the first use. This
keeps import time fast and avoids loading GPU models in the API process.

### 5.2 Friendly error messages

When you raise, write the message in plain Vietnamese/English so the UI's
`humanizeError()` can show it directly without translating HTTP status codes.
Include the provider id and the failing field if relevant.

### 5.3 Env-driven configuration

All API keys, base URLs, model ids must come from environment variables
**or** the admin UI database — never hard-code. Document required env vars
in a module-level docstring and in `.env.example`.

### 5.4 Tests

Add at least one integration test under
`tests/integration/translation/test_mycloud.py` that:

- Skips automatically if `MYCLOUD_API_KEY` env var is not set
- Mocks the HTTP response with `respx` or `aioresponses`
- Asserts the provider translates a known string and raises the expected
  error on 4xx/5xx responses

### 5.5 Streaming

For long-running translations (large batches), prefer streaming responses
(`response.aiter_lines()`) and yield chunks. The worker's `translate_segments`
activity is built around streaming.

---

## 6. Failure modes checklist

Before shipping, verify your provider:

- [ ] Handles missing env vars with a clear log + skip (not crash)
- [ ] Returns identical-length output as input (for batch translation)
- [ ] Times out after a configurable timeout (default 30s in httpx)
- [ ] Surfaces the original error message in the wrapped exception
- [ ] Closes network clients on `aclose()` (called by registry on shutdown)
- [ ] Does NOT log API keys, even at DEBUG level

---

## 7. Common gotchas

| Gotcha | Solution |
|--------|----------|
| Provider registered but worker says "Unknown provider" | Verify `bootstrap()` is called before the first workflow starts. Importing `translator_api.providers.registry` triggers it. |
| Glitches with Chinese input | Run `normalize_chinese` first (see `activities_phase3.py`). |
| TTS output is silent | Check the bitrate and sample rate match what the alignment activity expects (16kHz mono PCM). |
| Translation drops segments | Don't use `chunk_size` < 1 with batch APIs. The worker passes segments 1-by-1 by default. |

---

## 8. Reference providers to copy from

| Use case | Best example |
|----------|--------------|
| Simple HTTP + Bearer token | `tts/cloud_azure.py` |
| Streaming SSE | `translate/anthropic_compat.py` |
| On-prem / local model | `translate/local_llm.py` |
| Voice cloning | `voice_clone/cosyvoice_3.py` |
| OCR | `ocr/easyocr_provider.py` |

---

**Maintained by:** AI Agent + Engineering
