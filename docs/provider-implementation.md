# Provider Implementation Guide

Tài liệu này dành cho người muốn thêm một provider mới (ví dụ một TTS, một
translation backend, một aligner khác). Provider trong hệ thống là adapter
mỏng trên thư viện bên ngoài, tuân theo contract trong
`docs/provider-contracts.md`.

## Quy ước

- Mỗi provider thuộc một `kind` (`asr`, `align`, `diarize`, `translate`,
  `tts`, `audio_separation`, `ocr`, `text_removal`, `storage`).
- ID provider (`provider_id`) là chuỗi ổn định; Phase 2 dùng
  `whisperx_faster_whisper`, `wav2vec2`, `pyannote_3_1` (xem `docs/technology-selection.md`).
- Provider trả một trong:
  - **Pydantic response model** (success) — định nghĩa trong
    `packages/shared/python/translator_shared/provider_responses.py`.
  - `CapabilityUnsupported` — model chưa cài, không có GPU, ngôn ngữ không hỗ trợ.
  - `ConsentMissing` — provider gated yêu cầu accept user agreement (vd. pyannote).
  - `ProviderError` — lỗi khác; nên đặt `retryable=True` nếu có thể thử lại.
- Mọi phụ thuộc bên ngoài (model weights, SDK) đều **lazy-import** trong
  `run()` để môi trường không có model vẫn boot được. Nếu import fail,
  raise `CapabilityUnsupported("xxx-not-installed", str(exc))`.

## Bước thêm provider mới

1. **License audit**: thêm row vào `docs/licenses.md` (code license, model
   license, gated?, commercial verdict). Không bỏ qua bước này.
2. **Enum id**: mở `packages/shared/python/translator_shared/providers.py`,
   thêm enum value mới vào đúng enum (ví dụ `TranslationProviderId`).
3. **Pydantic response** (nếu cần): thêm model vào
   `packages/shared/python/translator_shared/provider_responses.py`.
4. **Provider class**: tạo file trong `apps/api/python/translator_api/providers/<kind>/<provider_id>.py`,
   kế thừa `Provider[InputT, OutputT]`, set `id` và `capabilities`.
5. **Config**: thêm Pydantic config vào `apps/api/python/translator_api/config.py`
   nếu provider có tunable.
6. **Registry**: mở `apps/api/python/translator_api/providers/registry.py`
   và `registry.register("<kind>", NewProvider())`.
7. **Activity wiring**: nếu provider thay thế activity stub, sửa
   `apps/worker/python/translator_worker/activities_providers.py` hoặc tạo
   activity mới. Đăng ký vào task queue đúng (`asr-queue`, `diarize-queue`,
   `tts-queue`, `cpu-queue`).
8. **Test**: thêm stub test ở `tests/unit/test_<provider>.py`. Phase 2 chưa
   cần GPU để pass test, chỉ cần xác nhận import boundary và fingerprint.
9. **Docs**: cập nhật `docs/technology-selection.md` (nếu thay đổi verdict)
   và `docs/runtime-topology.md` Tier 1 (nếu provider có GPU pool riêng).

## Mẫu skeleton

```python
from dataclasses import dataclass

from translator_api.providers.base import (
    CapabilityUnsupported,
    Provider,
    ProviderCapabilities,
    ProviderContext,
)
from translator_shared.providers import ArtifactSignature


@dataclass(frozen=True)
class MyInput:
    asset_storage_key: str


@dataclass(frozen=True)
class MyOutput:
    text: str


class MyProvider(Provider[MyInput, MyOutput]):
    id = "my_provider"
    capabilities = ProviderCapabilities(requires_gpu=True, supports_languages=("zh", "vi"))

    def fingerprint(self, payload: MyInput) -> ArtifactSignature:
        return ArtifactSignature(
            input_hash="...",
            model_id=self.id,
            model_version="0.0.0",
            provider_build="mybuild",
            config_hash="...",
        )

    async def run(self, payload: MyInput, *, ctx: ProviderContext) -> MyOutput:
        try:
            import my_sdk  # type: ignore[import-not-found]
        except Exception as exc:
            raise CapabilityUnsupported("my_sdk-not-installed", str(exc)) from exc
        ...
```

## Activity skeleton

```python
@activity.defn(name="my_provider_run")
async def my_provider_run(project_id: str, asset_id: str | None = None) -> dict:
    factory = build_factory()
    session = factory()
    try:
        asset_repo = AssetRepository(session)
        asset = asset_repo.get(UUID(asset_id)) if asset_id else asset_repo.list_for_project(UUID(project_id))[0]
        provider = MyProvider()
        ctx = ProviderContext(
            project_id=project_id,
            asset_id=str(asset.id),
            db_session=session,
            storage=build_storage(),
        )
        response = await provider.run(MyInput(asset.storage_key), ctx=ctx)
        return response.model_dump()
    finally:
        session.close()
```

## Cache key & retry

Mọi provider output phải đi kèm `ArtifactSignature.fingerprint()`. Caller
chịu trách nhiệm kiểm tra cache trước khi gọi provider (xem
`docs/provider-contracts.md` mục 13). Retry policy do activity đăng ký
trong `translator_worker/retry.py` (không provider tự retry).