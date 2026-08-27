# Translator – Next Steps (TODO)

Trạng thái: **CPU-only Qwen3-TTS inference đã được xác minh hoạt động** (model load + 9 speakers + 11 languages + generate_custom_voice OK). Tuy nhiên CPU quá chậm (text ~50s audio mất ~40 phút). Cần chuyển sang GPU hoặc dùng API hosted.

---

## 1. Demo 15s với Qwen3-TTS (MỤC TIÊU HIỆN TẠI)

### Đang chạy nền
- [Job #481752](file:///C:/Users/QUYÊN/.cursor/projects/c-Users-QUY-N-Desktop-Translator/terminals/481752.txt) — `python /tmp/gen_demo.py` đang sinh audio mẫu với text ~15s. Chờ khi chạy xong (`Generated in <time>s` + `Saved: /tmp/demo_15s.wav`).
- Nếu quá 60 phút chưa xong → kill job, chuyển sang plan B bên dưới.

### Plan B nếu CPU không khả thi
- **GPU**: chạy với `device_map="cuda"` hoặc `"mps"` (Apple Silicon) — nhanh gấp ~20–50x.
- **Quantization**: dùng `Qwen3-TTS-12Hz-0.6B-CustomVoice` với `torch_dtype=torch.float16` hoặc `bitsandbytes 4-bit` để giảm RAM.
- **Model nhỏ hơn**: thử `Qwen/Qwen3-TTS-12Hz-0.6B-Base` (base, không custom voice).
- **Hosted API**: dùng DashScope / Alibaba Cloud Model Studio endpoint để demo nhanh.
- **Fallback**: dùng `edge-tts` (đã có provider `edge.py`) để có demo audio ngay, đánh dấu Qwen3 là optional.

## 2. Hoàn thiện TTS Service (`apps/tts-service/`)

- [ ] Chạy lại `tests/test_chunker.py` & các test khác khi container recover.
- [ ] Bind Qwen3 vào `apps/api/python/translator_api/providers/tts/qwen3.py` (đã có sẵn file) qua registry provider.
- [ ] Thêm healthcheck + Prometheus metrics endpoint (`/metrics`).
- [ ] Cấu hình `tts-service` chạy ngoài docker-compose dev (đã có trong compose).
- [ ] Fix Dockerfile: `apt-get install -y --no-install-recommends sox libsndfile1 ffmpeg` (sox thiếu gây crash `librosa`).

## 3. Worker & Workflows

- [ ] `apps/worker/python/translator_worker/workflows.py` đã bị xóa → chuyển sang package `workflows/`. Verify Temporal worker vẫn register đúng.
- [ ] `workflows_impl.py` chưa được wire — kiểm tra import path & activities.
- [ ] Tích hợp TTS vào dubbing workflow (chunker → qwen3 → mux).

## 4. Web UI

- [ ] Verify build Next.js không vỡ sau khi đổi `tsconfig.json` (verbatimModuleSyntax).
- [ ] Thêm UI control chọn TTS provider (edge / qwen3 / elevenlabs).
- [ ] i18n keys mới (`en.json`, `vi.json`) — kiểm tra không bị thiếu ở các locale khác.

## 5. Observability

- [ ] Metrics mới trong `observability/metrics.py` — expose `tts_generate_seconds`, `tts_audio_seconds`.
- [ ] Tracing cho Qwen3TTSModel.generate_custom_voice.

## 6. CI / Tests

- [ ] `tests/test_providers_dubbing_speedrate.py` — chạy pass.
- [ ] `tests/test_providers_tts_edge.py` — chạy pass.
- [ ] Thêm `tests/test_providers_tts_qwen3.py` (skip nếu thiếu model/GPU).

## 7. Docs

- [ ] Cập nhật `docs/HUONG-DAN-SU-DUNG.md` với phần "TTS với Qwen3".
- [ ] `docs/integrations.md` — bổ sung bảng so sánh providers (edge / qwen3 / elevenlabs).

## 8. Cleanup

- [ ] Xóa `commit_msg.txt` & `req.json` khỏi root (file test, không thuộc dự án).
- [ ] Bump version trong `pyproject.toml` (1.0.0 → 1.1.0).

---

## Quick commands

```bash
# Run Qwen3 demo (CPU, chậm)
docker compose -p translator -f infra/docker/docker-compose.yml exec tts-service \
  python -c 'from qwen_tts import Qwen3TTSModel; \
  m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice", device_map="cpu"); \
  wavs, sr = m.generate_custom_voice(text="Hello world", speaker="serena", language="english"); \
  import soundfile as sf; sf.write("/tmp/demo.wav", wavs[0], sr)'

# Test chunker
docker compose -p translator -f infra/docker/docker-compose.yml exec tts-service pytest tests/test_chunker.py -v
```