# Technology Selection — Chinese → Vietnamese Video Localization

Phạm vi: Phase 0 (research + architecture). Workspace khởi đầu trống tại `c:\Users\QUYÊN\Desktop\Translator`; chưa có dependency nào được cài đặt.

Mọi quyết định dưới đây là mặc định production cho pipeline chuyên sâu Chinese → Vietnamese. Mỗi mục ghi rõ `Repository`, `Version / date checked`, `Stars / forks / activity`, `Code license`, `Model / dataset license`, `Strengths`, `Weaknesses`, `Mục đích sử dụng`, `Commercial compatibility`, và `Direct use / architecture-only`. Trước khi thay thế bất kỳ module nào, phải cập nhật file này với vấn đề, alternative, benchmark, license và migration impact.

> Disclaimer: Bảng license dưới đây tóm tắt các điều khoản chính mà nhóm có thể truy cập từ nguồn chính tại thời điểm khảo sát (26/08/2026). Trước khi commercial release phải đối chiếu lại file LICENSE và model card tại HEAD; license code, model, dataset và reference voice là các phép kiểm tra riêng biệt.

---

## 1. Application platform

| Component | Lựa chọn | Repository | Code license | Strengths | Weaknesses | Mục đích sử dụng | Commercial | Direct/arch-only |
|---|---|---|---|---|---|---|---|---|
| Web | Next.js (App Router, TypeScript) | https://github.com/vercel/next.js | MIT | SSR + RSC, streaming UI, hệ sinh thái lớn | Nặng bundle hơn Remix/Astro cho UI editor | Dashboard, simple/advanced mode, editor | Có | Direct |
| API | FastAPI + Pydantic v2 | https://github.com/fastapi/fastapi | MIT | Async, OpenAPI tự sinh, hợp Python ML stack | Phải tự thiết kế hàng đợi, auth, background job | Provider contract + job dispatch | Có | Direct |
| Worker runtime | Python 3.11/3.12 (chưa pin) | https://www.python.org | PSF | Hỗ trợ WhisperX 3.10–3.13, PyTorch, ONNX, FFmpeg bindings | Chưa phải 3.13 vì một số thư viện ML còn giới hạn trên | Worker media/ASR/TTS | Có | Direct |
| Workflow engine | Temporal | https://github.com/temporalio/temporal | MIT (server + SDK) | Durable execution, retry/cancel/heartbeat, child workflow, continue-as-new, deterministic replay | Phải tránh non-determinism trong workflow; persistence = PostgreSQL/MySQL riêng | DAG production | Có | Direct |
| Database | PostgreSQL | https://www.postgresql.org | PostgreSQL License (BSD-style) | JSONB, full-text, partitioning, mature | Phải tự quản trị backup/replication nếu self-host | Metadata, versioned content, audit log | Có | Direct |
| Object storage | S3 API contract (MinIO local adapter, managed S3 ở production) | https://github.com/minio/minio | AGPLv3 cho MinIO server (repo archived); S3 API không thuộc license | S3 API phổ biến, decouple với provider | MinIO AGPL + archived; chỉ dev adapter, prod phải chọn deployment hợp license | Asset binaries | MinIO local: không dùng cho production theo AGPL; managed S3 hoặc self-host có license phù hợp | Adapter thuần S3, MinIO là một implementation; không hard-bind |
| Media engine | FFmpeg | https://ffmpeg.org | LGPL/GPL tùy build | Đầy đủ filter concat/amix/sidechaincompressor/subtitles | GPL build kéo theo bắt buộc phát hành source nếu redistribute nhị phân | Probe, mix, encode | Có (LGPL hoặc GPL tùy distribution; cần chọn bản LGPL cho server nội bộ) | Direct |

## 2. ASR, VAD, forced alignment, speaker diarization

| Module | Lựa chọn | Repository | Code license | Model / dataset license | Strengths | Weaknesses | Mục đích sử dụng | Commercial | Direct/arch-only |
|---|---|---|---|---|---|---|---|---|---|
| ASR pipeline | WhisperX 3.8.x | https://github.com/m-bain/whisperX | BSD-2-Clause | OpenAI Whisper (MIT cho code + OpenAI Usage Policy cho model weights; không cấm dịch vụ dubbing/transcription) | Word-level alignment, batched inference, speaker diarization tích hợp | Overlap xử lý chưa tốt; từ ngoài từ điển alignment bị bỏ | Baseline ASR cho cả Mandarin/Vietnamese | Có | Direct |
| ASR backend | faster-whisper | https://github.com/SYSTRAN/faster-whisper | MIT | Cùng checkpoint Whisper | 4× nhanh, CTranslate2, int8/fp16, CUDA 12 + cuDNN 9 | Cần CUDA 12 + cuDNN 9 cho bản mới | Inference engine cho WhisperX | Có | Direct |
| Whisper model variant | `large-v3` mặc định; `turbo`/`distil-large-v3` cho throughput | https://github.com/openai/whisper; https://huggingface.co/distil-whisper/distil-large-v3 | MIT (code) | OpenAI terms cho weights; distil-large-v3 Apache-2.0 | large-v3 WER tốt nhất trên Mandarin; turbo/distil chấp nhận ~5% WER delta cho throughput | `large-v3` cần ~8 GB FP16, ~4.5 GB INT8; cần GPU >= 8 GB cho prod | Whisper checkpoint | Có | Direct |
| VAD | Silero VAD | https://github.com/snakers4/silero-vad | MIT | MIT | Nhẹ, chính xác, CPU/GPU | Một số bản phụ thuộc torch | Bộ VAD chính cho mọi tier | Có | Direct |
| VAD alt | pyannote.audio VAD | https://github.com/pyannote/pyannote-audio | MIT | Hugging Face model gated, MIT trong model card nhưng yêu cầu accept user agreement | Đồng nhất với diarization | Cần token HF và accept EULA | Provider fallback | Có (sau khi accept HF agreement) | Direct |
| Forced alignment | WhisperX `align` (zh → `jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn`; vi → `nguyenvulebinh/wav2vec2-base-vi-vlsp2020`) | https://github.com/m-bain/whisperX/blob/main/whisperx/alignment.py | BSD-2-Clause | wav2vec2 model từng repo; cần kiểm model card trước khi commercial | Tự chọn model theo language code | Ký tự ngoài dictionary (số, ký hiệu) bị bỏ | Word/character timing cho Chinese/Vietnamese | Có (sau khi audit model card) | Direct |
| Diarization | pyannote.audio 3.1 (`speaker-diarization-3.1`) | https://github.com/pyannote/pyannote-audio; https://huggingface.co/pyannote/speaker-diarization-3.1 | MIT | Model weights CC-BY-4.0 (ghi nhận 26/08/2026) — gated trên HF; yêu cầu accept user agreement; commercial OK + attribution | State-of-the-art DER benchmark; Mandarin | Cần HF token; overlap đôi khi gán nhầm; phải hiển thị pyannote attribution | Speaker timeline | Có (sau khi accept user agreement; hiển thị attribution) | Direct |
| ASR benchmark alt | Qwen3-ASR 0.6B/1.7B | https://github.com/QwenLM/Qwen3-ASR | Apache-2.0 | Apache-2.0 | Tốt cho code-switch và noise, mạnh Mandarin benchmark | Hệ sinh thái inference chưa trưởng thành bằng Whisper | Alternative cho benchmark Mandarin | Có | Direct (qua provider wrapper) |

## 3. Subtitle và media

| Module | Lựa chọn | Repository | Code license | Strengths | Weaknesses | Mục đích sử dụng | Commercial | Direct/arch-only |
|---|---|---|---|---|---|---|---|---|
| Subtitle parsing/export | Tự viết SRT/VTT/ASS bằng Python | n/a (in-repo) | Apache-2.0 (sẽ đề xuất) | Sạch, không phụ thuộc | Phải tự test edge case (multi-line, RTL) | Editor + export | Có | Direct |
| Burn-in subtitle | FFmpeg `subtitles`/`ass` filter | https://ffmpeg.org | LGPL/GPL tùy build | Ổn định, hỗ trợ styled ASS | Phải chuẩn hóa ASS để render đẹp | Render preview + final | Có | Direct |
| OCR burned subtitle | PaddleOCR (PP-OCRv4/v5) | https://github.com/PaddlePaddle/PaddleOCR | Apache-2.0 | Code Apache-2.0; từng checkpoint phải audit model card riêng | Đa ngôn ngữ, layout-aware; `ch_PP-OCRv4` là model Chinese/English | Cần PaddlePaddle framework (tách biệt PyTorch); benchmark tự báo cáo | OCR khi không có soft subtitle | Có (sau khi audit model card) | Direct |
| OCR fallback | EasyOCR | https://github.com/JaidedAI/EasyOCR | Apache-2.0 | Thuần PyTorch | Đơn giản, ít deps | Kém chính xác hơn PaddleOCR cho Chinese artistic fonts / low-res | Fallback cho deployment không muốn PaddlePaddle | Có | Direct qua provider wrapper |
| Subtitle region detector (custom) | YOLOv8 / Faster R-CNN (custom train) | https://github.com/ultralytics/ultralytics (AGPLv3 cho YOLOv8) | AGPLv3 cho YOLOv8 (vendor lock-in); custom weights cần license riêng | Tăng độ chính xác cho burned subtitle artistic trên Douyin/Bilibili | Phải tự train + collect dataset có quyền | Optional module (Tier 2+); không vào lõi nếu không có data | YOLOv8 AGPLv3 → cân nhắc YOLOv5 (GPLv3) hoặc RT-DETR (Apache-2.0) nếu không chấp nhận AGPL | Direct hoặc architecture-only tùy chọn license |
| Chinese text normalization (reference) | PaddleSpeech TextNormalize + pypinyin/g2pW | https://github.com/PaddlePaddle/PaddleSpeech; https://github.com/mozillazg/python-pinyin; https://github.com/AlexGidiotis/g2pW | Apache-2.0; MIT | Rule-based + dictionary; CTN là task-specific | Phải tự xây lớp riêng cho codebase | Reference; production tự viết | Có | Direct |
| Audio separation | UVR5/MDX-family, Demucs, BS-Roformer candidates | https://github.com/Anjok07/ultimatevocalremovergui (MIT); https://github.com/facebookresearch/demucs (MIT, repo archived); https://github.com/lucidrains/BS-Roformer | MIT cho code; từng checkpoint có license riêng | Nhiều model cho vocal/accompaniment | Khó đảm bảo license/checkpoint nhất quán; chất lượng SFX yếu | Tách vocals + music để giữ nhạc nền | Có nếu từng checkpoint MIT/Apache; nếu không thì chỉ experimental | Direct qua provider wrapper |

## 4. Translation

| Lựa chọn | Repository / doc | Code license | Model terms | Strengths | Weaknesses | Mục đích sử dụng | Commercial | Direct/arch-only |
|---|---|---|---|---|---|---|---|---|
| Translation provider contract (HTTP/OpenAI-compatible) | https://platform.openai.com/docs/api-reference/chat | n/a (HTTP) | Tuỳ provider | Không lock SDK; dễ swap model | Phải tự thiết kế structured output và retry | Lõi translation | Tuỳ provider | Direct |
| Self-host LLM (optional) | TBD — sẽ benchmark DeepSeek/GLM/Qwen khi Phase 0 hoàn tất | n/a (HTTP) | Tuỳ model | Không gửi data ra ngoài | Cần GPU | Provider optional | Tuỳ model license | Direct qua wrapper |
| Cloud Gemini/Claude-compatible (optional) | Tuỳ vendor | n/a (HTTP) | Vendor ToS | Chất lượng cao | Vendor lock-in, data residency | Provider optional | Vendor contract | Direct qua wrapper |

## 5. Vietnamese TTS

| Model | Repository | Code license | Model/license | Strengths | Weaknesses | Mục đích sử dụng | Commercial | Direct/arch-only |
|---|---|---|---|---|---|---|---|---|
| VieNeu-TTS v3-Turbo | https://github.com/pnnbao97/VieNeu-TTS | Apache-2.0 | Checkpoint v3 Turbo trên Hugging Face: `pnnbao-ump/VieNeu-TTS-v3-Turbo` — phải audit trước commercial enablement | Vietnamese-native, voice cloning, CPU/GPU, 48 kHz | Model/dataset license cần audit riêng từng revision | Local TTS chính | Tùy checkpoint; code Apache-2.0 | Direct qua provider wrapper |
| CosyVoice 3.0 | https://github.com/FunAudioLLM/CosyVoice | Apache-2.0 | Apache-2.0 cho code; checkpoint trên ModelScope/HF cần audit | Multilingual zero-shot, voice cloning | Chất lượng tiếng Việt phải benchmark trên gold set | Voice-system alternative/benchmark | Có nếu checkpoint Apache-2.0 (đã xác nhận repo Apache-2.0) | Direct qua provider wrapper |
| VietVoice-TTS | https://github.com/nguyenvulebinh/VietVoice-TTS | MIT | MIT (theo repo); voice pack/voice cloning cần audit | Vietnamese-native, có voice cloning | Cộng đồng nhỏ, ít benchmark public | Fallback local | Có nếu voice pack tuân MIT | Direct qua provider wrapper |
| MeloTTS Vietnamese | https://github.com/myshell-ai/MeloTTS (MIT) + https://github.com/manhcuong02/MeloTTS_Vietnamese (MIT) | MIT | MIT cho code; từng checkpoint/dataset phải audit | Nhẹ, CPU được | Chất lượng thấp hơn VieNeu/CosyVoice | Benchmark fallback | Có nếu checkpoint MIT | Direct qua provider wrapper |
| Cloud Vietnamese TTS (Azure/Google/AWS/ElevenLabs) | Vendor docs | n/a | Vendor ToS | Ổn định, accent đa dạng | Vendor lock, data retention, chi phí | Cloud fallback | Vendor contract | Direct qua provider wrapper |
| F5-TTS (excluded by default) | https://github.com/SWivid/F5-TTS | MIT | Pretrained weights CC-BY-NC-4.0 do Emilia dataset | Chất lượng cao | Pretrained weights không commercial; phải train lại từ đầu trên data có quyền | Loại khỏi commercial production core | Không với pretrained weights; chỉ dùng nếu tự train từ scratch | Architecture-only |
| ChatTTS (excluded by default) | https://github.com/2noise/ChatTTS | AGPLv3 (code) | Model CC-BY-NC-4.0 | Rất phổ biến cho daily dialogue | Copyleft mạnh + model NC = không commercial | Loại khỏi commercial production core | Không | Architecture-only (no code copy) |

## 6. Phụ trợ khác

| Module | Lựa chọn | License | Mục đích |
|---|---|---|---|
| Container runtime | Docker (chưa pin base image) | Apache-2.0 (Docker Engine) | Worker container |
| WebSocket/SSE | Built-in FastAPI + Next.js route handlers | MIT | Realtime progress events |
| Hash/checksum | hashlib (stdlib) | PSF | Artifact signature |
| Observability (placeholder) | TBD — OpenTelemetry-compatible stack | Apache-2.0 cho OTel SDK | Production observability |

---

## 7. Những lựa chọn bị loại (excluded by default) và lý do

- **F5-TTS pretrained weights**: CC-BY-NC-4.0 do Emilia dataset. Phải train lại từ scratch trên data thương mại được phép.
- **ChatTTS code**: AGPLv3 → bất kỳ service nào cung cấp qua mạng phải phát hành source. Model: CC-BY-NC-4.0. Không commercial.
- **XTTS-v2**: CPML non-commercial. Coqui shutdown, không có license thương mại.
- **Open-Unmix UMXL weights**: CC-BY-NC-SA 4.0. Không thương mại.
- **MinIO ở production**: repo archived, AGPLv3. Chỉ dùng S3-compatible managed storage hoặc self-host với license rõ ràng; MinIO local dev adapter vẫn được vì chỉ là implementation thuần S3.
- **pyVideoTrans core**: GPLv3, dùng làm đối chiếu kiến trúc, không sao chép code.
- **NLLB-200 / seamless-communication / M2M-100 (Meta)**: CC-BY-NC-4.0 + Meta AUP. Cấm commercial core.
- **YOLOv8**: AGPLv3. Nếu cần custom subtitle-region detector không chấp nhận AGPL, chọn YOLOv5 (GPLv3) hoặc RT-DETR (Apache-2.0) thay thế.

## 8. Quyết định cần benchmark nội bộ trước khi vào production

- Chất lượng TTS Việt trên gold set của VieNeu-TTS v3 Turbo, CosyVoice 3.0, VietVoice-TTS, MeloTTS Vietnamese. Đo pronunciation, naturalness, speaker consistency, timing, clipping.
- ASR Mandarin benchmark giữa WhisperX `large-v3` (Faster-Whisper backend) và Qwen3-ASR trên cùng gold set (Douyin, Bilibili, drama, anime, multi-speaker, code-switch).
- Audio separation: chất lượng vocals + music của UVR5 MDX/MDX23C so với BS-RoFormer trên video có nhạc nền lớn.
- ASR Vietnamese (nếu mở rộng sang locale khác) cần benchmark `nguyenvulebinh/wav2vec2-base-vi-vlsp2020` vs alternatives.

## 9. Đối chiếu yêu cầu gốc với baseline

- WhisperX, pyannote, Temporal, FFmpeg được giữ nguyên là lõi cốt lõi theo rule của project.
- Translation là provider contract, không hard-code SDK; default OpenAI-compatible HTTP, Gemini/Claude/local chỉ là adapter.
- TTS provider abstraction: thứ tự ưu tiên là VieNeu-TTS (sau audit) → CosyVoice 3.0 (voice-system alt) → cloud Vietnamese TTS. ChatTTS/F5-TTS weights không vào commercial core.
- Audio separation là `AudioSeparationProvider`; UVR/Demucs candidates, không mặc định một model duy nhất.
- Storage chỉ khóa ở S3-API contract; MinIO là adapter dev, production cần phê duyệt riêng.

## 10. Quy trình cập nhật

- Khi thay bất kỳ module nào: thêm entry mới vào bảng tương ứng, ghi rõ vấn đề, alternative, benchmark, license và migration impact. Không xóa entry cũ mà chỉ đánh `superseded`.
- Cập nhật `docs/licenses.md` đồng thời.
