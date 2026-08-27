# Translator – Next Steps (TODO)

**Last reviewed:** 2026-08-27 18:30 UTC+7 (after pulling v1.3.0 + China-Vietnam branch)

**Trạng thái:** Hầu hết items trong TODO cũ đã được giải quyết bởi v1.1.0–v1.3.0 mới merge. Phần lớn còn lại thuộc về nhánh `feature/china-vietnam-setup` (phases 5–8 cần user + test videos + GUI).

---

## ✅ ĐÃ GIẢI QUYẾT (bởi code mới pull)

| Mục cũ | Giải quyết bởi |
|---|---|
| 1. Demo 15s Qwen3-TTS (CPU quá chậm) | ✅ **v1.2.0**: `DashScopeTtsProvider` (`cloud_qwen3.py`) — hosted, không cần GPU. + SSE streaming. |
| 1. Plan B: Hosted API / Edge fallback | ✅ `dashscope_tts` + `edge_tts` đều đã trong registry (xem `registry.py:97-99`). |
| 2. Bind Qwen3 vào registry | ✅ `Qwen3TtsProvider` đã register trong `registry.py:98`. |
| 2. /metrics Prometheus | ✅ `apps/tts-service/tts_service/main.py:139` + 4 histograms. |
| 2. Dockerfile fix sox/librosa | ✅ `apps/tts-service/Dockerfile:14-17` có sox + libsndfile1 + ffmpeg. |
| 3. Workflows.py → workflows/ package | ✅ `workflows/__init__.py` re-export từ `workflows_impl.py`. |
| 3. Workflows_impl wire activities | ✅ `workflows_impl.py` đầy đủ: ProjectWorkflow, SubtitleWorkflow, DubbingWorkflow, ChunkWorkflow. |
| 4. Web UI TTS provider selector | ✅ `app/settings/page.tsx` dropdown với 9 providers (Edge, Qwen3, VietVoice, VieNeu, CosyVoice 3, Azure, Google, ElevenLabs, MeloTTS). |
| 5. Observability metrics | ✅ `observability/metrics.py` có `tts_generate_seconds`, `tts_audio_seconds`, `tts_chunks_total`, `tts_requests_total`. |
| 6. Tests edge + dubbing | ✅ `test_providers_tts_edge.py`, `test_providers_dubbing_speedrate.py`, **mới** `test_providers_tts_dashscope.py`. |
| 8. Bump version 1.0.0 → 1.1.0 | ✅ Project hiện ở **v1.3.0** (theo CHANGELOG.md). |

---

## 🆕 Items MỚI từ code vừa pull (prioritized)

### A. Hoàn thiện `DashScopeTtsProvider` (MỨC CAO NHẤT)
- [ ] Test live với API key thật (cần `DASHSCOPE_API_KEY` từ user)
- [ ] Verify `_chunk_text` không cắt sai câu có dấu tiếng Việt (regex `[.!?\n]` không khớp `.` cuối câu VN)
- [ ] Thêm test cho Vietnamese language detection (hiện đang fallback về "Auto" — xem `test_vietnamese_falls_back_to_auto`)
- [ ] Kiểm tra fallback chain khi DashScope fail: `dashscope_tts → edge_tts → vietvoice_tts`
- [ ] Thêm healthcheck endpoint `/healthz/dashscope` để verify connectivity

### B. TTS Service microservice (ready nhưng chưa e2e test)
- [ ] End-to-end test: POST `/synthesize` với Qwen3 engine (cần `TTS_ENGINE=qwen3` + model download)
- [ ] Cache hit rate verification (`TTS_CHUNKS_TOTAL{cache="hit"}` vs `cache="miss"`)
- [ ] Concurrent load test (env `TTS_CONCURRENCY=2` — bump và benchmark)
- [ ] Wire tts-service vào docker-compose dev (đã có trong compose — verify)

### C. Worker Activities (theo v1.3.0 CHANGELOG)
- [ ] `translate_segments` activity: verify load `TranscriptVersion` qua `TranscriptRepository.latest_for_project()` không vỡ với project chưa có transcript
- [ ] `tts_synthesize` activity: verify fallback chain khi Qwen3 model chưa download
- [ ] `tts_synthesize` reads `tts_text` OR `display_text` — xử lý trường hợp cả hai null

### D. Web UI (CN-VN branch)
- [ ] `verbatimModuleSyntax` enabled in tsconfig — verify build không vỡ
- [ ] i18n keys `tts.providers` đã có cho 10 locales — check zh/th/pt/ko/ja/fr/de/es chưa có `tts.dashscope` key

---

## 🌏 China-Vietnam pipeline (`feature/china-vietnam-setup` đã merge)

Xem `docs/NEXT_STEPS_PLAN.md` để biết chi tiết. Tóm tắt:

### Phases 0–11 ✅ DONE
- Pre-packaged pyVideoTrans v4.11 (2.93 GB) + extracted (7.26 GB)
- GPU verified: RTX 4060 8GB / CUDA 13.2
- 4 Windows .bat scripts: `scripts/china-vietnam/{setup,start,doctor,update}.bat`

### Pending (cần user)
- **Phase 5**: Test Chinese ASR (FunASR) — cần test video Chinese + GUI
- **Phase 6**: Test DeepSeek translation — cần API key
- **Phase 7**: Test Vietnamese TTS Edge-TTS — cần GUI
- **Phase 8**: Test full pipeline end-to-end
- **Phase 12**: Regression tests
- **Phase 13**: Performance benchmarks → fill `BENCHMARK_CHINA_VIETNAM.md`

### Critical decisions pending
| Decision | Default |
|---|---|
| Translation provider | DeepSeek |
| TTS provider | Edge-TTS |
| Voice role | vi-VN-HoaiMyNeural |
| Video codec | libx265 (HEVC), CRF 20 |
| Pipeline mode | GUI for now |

---

## 🛠 Cleanup nhỏ còn lại

- [ ] Xóa `commit_msg.txt` & `req.json` ở root repo (file test cá nhân)
- [ ] `.gitignore`: đã có `pyvideotrans-win/` exclude (verify)
- [ ] Tag local: cần push tag `v1.2.0` & `legacy-v1.3.0` lên remote (đã fetch thấy nhưng chưa chắc đã push)

---

## Quick commands

```bash
# Pull latest
git pull origin main

# Test DashScope (cần API key)
DASHSCOPE_API_KEY=sk-xxx pytest apps/api/python/tests/test_providers_tts_dashscope.py -v

# Test TTS service chunker (không cần Docker)
cd apps/tts-service && pytest tests/test_chunker.py -v

# Push tags
git push origin v1.2.0 legacy-v1.3.0

# Cleanup root test artifacts
rm -f commit_msg.txt req.json
```

---

## ⚠️ Known blockers cho session hiện tại

- **Docker daemon không available** trong session → không thể chạy `docker compose` để test TTS service live
- **Không có GUI access** → không thể test `sp.exe` của pyVideoTrans
- **Chưa có DASHSCOPE_API_KEY** → chưa thể verify provider live (chỉ có thể chạy unit tests với mock)