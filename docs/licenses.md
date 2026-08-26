# License Audit — Chinese → Vietnamese Video Localization

Ngày khảo sát: 26/08/2026. Bảng này là hợp nhất license cho code, model, dataset, reference voice và deployment. Trước khi commercial release phải đối chiếu lại từng file `LICENSE` và model card tại HEAD.

Phân loại:
- `allowed core` — đưa vào production core mặc định.
- `provider optional` — chỉ chạy khi người dùng chọn provider này và đã ký hợp đồng/audit phù hợp.
- `research only` — chỉ dùng nội bộ benchmark; không phân phối.
- `excluded by default` — cấm trong commercial production core.

| # | Component | Type | Source | Code license | Model / dataset / data terms | Commercial verdict | Ghi chú |
|---|---|---|---|---|---|---|---|
| 1 | WhisperX | Code | https://github.com/m-bain/whisperX | BSD-2-Clause | OpenAI Whisper code MIT + Whisper model weights theo OpenAI terms; từng checkpoint Whisper lớn có thể đi kèm OpenAI Usage Policy | allowed core | File LICENSE upstream đã verify; cần pin phiên bản |
| 2 | faster-whisper (CTranslate2) | Code | https://github.com/SYSTRAN/faster-whisper | MIT | Dùng cùng checkpoint Whisper (model card nói rõ model weights do OpenAI phát hành, không có ràng buộc cho dubbing/transcription) | allowed core | Inference engine; CUDA 12 + cuDNN 9 cho GPU mới nhất |
| 3 | Silero VAD | Code + model | https://github.com/snakers4/silero-vad | MIT | MIT cho model, không telemetry, không key | allowed core | Verify checkpoint khi update |
| 4 | pyannote.audio 3.1 | Code + model | https://github.com/pyannote/pyannote-audio; https://huggingface.co/pyannote/speaker-diarization-3.1 | MIT (code) | Model weights CC-BY-4.0 (không phải CC-BY-NC) — ghi nhận mới sau audit 26/08/2026; gated trên HF, yêu cầu accept user agreement + cung cấp contact | allowed core (sau khi accept HF user agreement; commercial OK + attribution) | Cần HF token; phải hiển thị "pyannote" attribution trong product UI/docs |
| 5 | wav2vec2 Chinese alignment (`jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn`) | Model | https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn | Apache-2.0 (model card) | Cùng Apache-2.0 cho weight | allowed core | Cần verify model card trước khi ship |
| 6 | wav2vec2 Vietnamese alignment (`nguyenvulebinh/wav2vec2-base-vi-vlsp2020`) | Model | https://huggingface.co/nguyenvulebinh/wav2vec2-base-vi-vlsp2020 | Apache-2.0 (model card) | Cùng Apache-2.0 | allowed core | Dùng khi mở rộng sang tiếng Việt ASR |
| 7 | Qwen3-ASR | Code + model | https://github.com/QwenLM/Qwen3-ASR | Apache-2.0 | Apache-2.0 cho code và model 0.6B/1.7B | allowed core (alt benchmark) | Pin version trước khi đưa vào provider |
| 8 | PaddleOCR | Code + model | https://github.com/PaddlePaddle/PaddleOCR | Apache-2.0 | Code Apache-2.0; từng PP-OCRv5 checkpoint cần audit license model card | allowed core (sau khi audit model card) | Dùng cho burned subtitle |
| 9 | UVR5 / MDX-family | Code + model | https://github.com/Anjok07/ultimatevocalremovergui | MIT (code) | Từng checkpoint MDX/MDX23C/VR-Arch có license riêng; một số weights NC | provider optional (từng checkpoint) | Phải audit từng model hash |
| 10 | Demucs | Code + model | https://github.com/facebookresearch/demucs | MIT | Model weights MIT; TensorRT compiled engines chỉ research/personal theo Meta | provider optional (chỉ plain PyTorch weights) | Repo archived; chỉ benchmark/backup |
| 11 | BS-RoFormer (lucdrains) | Code | https://github.com/lucidrains/BS-Roformer | MIT | Checkpoint weights license riêng (cần audit) | provider optional (từng checkpoint) | Reference architecture |
| 12 | VieNeu-TTS v3 Turbo | Code + model | https://github.com/pnnbao97/VieNeu-TTS | Apache-2.0 (code) | Checkpoint v3 Turbo và dataset VieNeu-TTS-1000h cần audit trên Hugging Face; một số component (MOSS-Audio-Tokenizer-Nano, sea-g2p) Apache-2.0 | provider optional (sau khi audit checkpoint/dataset) | Sẽ vào lõi local TTS sau audit |
| 13 | CosyVoice 3.0 | Code + model | https://github.com/FunAudioLLM/CosyVoice | Apache-2.0 | Checkpoint `Fun-CosyVoice3-0.5B-2512` cần audit model card | provider optional (sau khi audit checkpoint) | Voice-system alt |
| 14 | VietVoice-TTS | Code + model | https://github.com/nguyenvulebinh/VietVoice-TTS | MIT (code) | Voice pack/voice cloning cần audit | provider optional (sau khi audit voice pack) | Fallback local |
| 15 | MeloTTS Vietnamese | Code + model | https://github.com/myshell-ai/MeloTTS (MIT) + https://github.com/manhcuong02/MeloTTS_Vietnamese (MIT) | MIT | Checkpoint weights license riêng; dataset `doof-ferb/infore1_25hours` cần audit | provider optional (sau khi audit checkpoint/dataset) | CPU fallback |
| 16 | F5-TTS (pretrained) | Code + model | https://github.com/SWivid/F5-TTS | MIT (code) | Pretrained weights CC-BY-NC-4.0 do Emilia dataset; weights remain NC kể cả khi fine-tune | excluded by default | Chỉ dùng nếu tự train từ scratch với data thương mại được phép |
| 17 | ChatTTS | Code + model | https://github.com/2noise/ChatTTS | AGPLv3 (code) | Model CC-BY-NC-4.0 | excluded by default | Copyleft + NC = double blocker |
| 18 | XTTS-v2 (Coqui) | Code + model | https://github.com/coqui-ai/TTS | MPL-2.0 / Apache cho code, CPML cho weights | Weights CPML non-commercial; Coqui shutdown 2024 → không có license thương mại | excluded by default | |
| 19 | Open-Unmix UMXL weights | Model | https://github.com/sigsep/open-unmix-pytorch | MIT (code) | Weights UMXL CC-BY-NC-SA-4.0 | excluded by default | Dùng plain UMX thay thế |
| 20 | FFmpeg | Binary | https://ffmpeg.org | LGPL 2.1+ (build `--enable-gpl --enable-nonfree`) hoặc GPL (build mặc định có GPL components) | Phụ thuộc build flag | allowed core nếu build LGPL; nếu build GPL, server nội bộ vẫn OK nhưng không redistribute nhị phân kèm closed source | Pin build config |
| 21 | MinIO (server) | Binary | https://github.com/minio/minio | AGPLv3 | Repo archived; community edition không có binary prebuilt | excluded ở production; allowed ở local dev | Chỉ dùng S3-compatible managed storage hoặc self-host có license rõ ràng |
| 22 | PostgreSQL | Database | https://www.postgresql.org | PostgreSQL License (BSD-like) | n/a | allowed core | |
| 23 | Temporal | Code + server | https://github.com/temporalio/temporal | MIT (server + SDK) | n/a | allowed core | Self-host free; cloud là vendor ToS |
| 24 | Next.js | Framework | https://github.com/vercel/next.js | MIT | n/a | allowed core | |
| 25 | FastAPI + Pydantic v2 | Framework | https://github.com/fastapi/fastapi (MIT), https://github.com/pydantic/pydantic (MIT) | MIT | n/a | allowed core | |
| 26 | pyVideoTrans | Reference | https://github.com/jianchang512/pyvideotrans | GPLv3 | n/a | architecture-only (no code copy) | Dùng để đối chiếu kiến trúc |
| 27 | NLLB-200 (Meta) | Model | https://huggingface.co/facebook/nllb-200-distilled-600M | CC-BY-NC-4.0 | Cấm commercial production core | excluded by default | Benchmark nội bộ chỉ khi không phân phối |
| 28 | seamless-communication (Meta) | Model | https://huggingface.co/facebook/seamless-m4t-v2-large | CC-BY-NC-4.0 + Meta AUP | Cấm commercial production core | excluded by default | |
| 29 | M2M-100 (Meta) | Model | https://huggingface.co/facebook/m2m100-1.2B | CC-BY-NC-4.0 | Cấm commercial production core | excluded by default | |
| 30 | PaddleSpeech TextNormalize | Code | https://github.com/PaddlePaddle/PaddleSpeech | Apache-2.0 | Reference Chinese text normalization | allowed core | Dùng làm tham chiếu rule; production sẽ tự viết lớp riêng |
| 31 | g2pW, pypinyin | Code | https://github.com/AlexGidiotis/g2pW, https://github.com/mozillazg/python-pinyin | MIT | Reference cho pronunciation | allowed core | |
| 32 | EasyOCR | Code + model | https://github.com/JaidedAI/EasyOCR | Apache-2.0 | Code Apache-2.0; một số pretrained model downloader tự động gọi các weights bên thứ ba (Craft, Latin) cần audit từng checkpoint | allowed core (sau khi audit checkpoint) | OCR alt; CPU friendly |
| 33 | CRAFT text detector | Code | https://github.com/clovaai/CRAFT-pytorch | MIT | Pretrained model từ clovaai repo MIT | allowed core | Detector-only; không OCR recognition |
| 34 | LaMa inpainting | Code + model | https://github.com/advimman/lama | MIT | LaMa weights `big-lama.pt` Apache-2.0; inpaint-anything wrapper Apache-2.0 | allowed core | Dùng cho burn-subtitle removal |
| 35 | Inpaint-Anything | Code | https://github.com/geekyutao/Inpaint-Anything | Apache-2.0 | Yêu cầu SAM (Apache-2.0) + LaMa (Apache-2.0) đi kèm | allowed core | Phụ thuộc SAM/LaMa; verify khi update |
| 36 | OpenCV inpaint (Telea / NS) | Code | https://github.com/opencv/opencv | Apache-2.0 | n/a | allowed core | CPU fallback; chất lượng thấp nhưng không cần GPU |
| 37 | Craft-Text-Detector (packaging) | Code | https://github.com/fcakyon/craft-text-detector | MIT | Đóng gói CRAFT + checkpoints | allowed core | |
| 38 | simple-lama-inpainting (packaging) | Code | https://github.com/ENOT-AutoDL/simple-lama-inpainting | Apache-2.0 | Wrapper cho LaMa | allowed core | |
| 39 | Open-Unmix UMX (plain, không phải UMXL) | Code + model | https://github.com/sigsep/open-unmix-pytorch | MIT (code + UMX weights) | Plain UMX MIT | allowed core (chỉ plain UMX) | Thay thế UMXL weights đã exclude |
| 40 | redis-py | Code | https://github.com/redis/redis-py | MIT | n/a | allowed core | Dùng cho sliding-window rate limit |
| 41 | caddy | Binary | https://github.com/caddyserver/caddy | Apache-2.0 | n/a | allowed core | Reverse proxy + TLS |
| 42 | prometheus / alertmanager | Binary | https://github.com/prometheus/prometheus (Apache-2.0), https://github.com/prometheus/alertmanager (Apache-2.0) | Apache-2.0 | n/a | allowed core | |
| 43 | Grafana / Loki / Promtail | Binary | https://github.com/grafana/grafana (AGPLv3), https://github.com/grafana/loki (AGPLv3), https://github.com/grafana/promtail (AGPLv3) | AGPLv3 | Grafana Cloud là vendor ToS; self-host AGPL OK nếu mở source cùng distribution | allowed core (self-host only); nếu phân phối SaaS closed-source cần commercial license | Dùng OSS edition self-host; commercial hosting phải mua license Grafana Enterprise |
| 44 | OpenTelemetry Collector | Binary | https://github.com/open-telemetry/opentelemetry-collector-contrib | Apache-2.0 | n/a | allowed core | |
| 45 | python-jose / PyJWT | Code | https://github.com/mpdavis/python-jose (MIT), https://github.com/jpadb/python-jose (MIT), https://github.com/jpadb/jose (MIT) | MIT | n/a | allowed core | JWT verify trong security/oidc |
| 46 | httpx | Code | https://github.com/encode/httpx | BSD-3-Clause | n/a | allowed core | HTTP client cho OIDC + cloud provider |
| 47 | boto3 / botocore | Code | https://github.com/boto/boto3 | Apache-2.0 | n/a | allowed core | S3 + SDK |

## Phụ thuộc gián tiếp cần audit trong Phase 1

- ffmpeg-python (LGPL/GPL tùy binding), bất kỳ binding FFmpeg nào dùng cho Python.
- onnxruntime (MIT) và backend CPU/GPU (license theo vendor).
- PyTorch (BSD-3-Clause).
- hydra / pydantic-settings / SQLAlchemy / alembic: đều MIT; chỉ cần pin version.
- Redis (BSD-3-Clause) nếu dùng cho ephemeral state; cần license review nếu enterprise có Redis Enterprise ToS.

## Phụ thuộc gián tiếp Phase 4 (production hardening)

- prometheus_client (Apache-2.0): `/metrics` FastAPI endpoint.
- opentelemetry-api/sdk (Apache-2.0): tracing.
- structlog (Apache-2.0) — tuỳ chọn thay cho logging stdlib khi cần typed logger.
- python-jose (MIT): JWT verify OIDC.
- redis (BSD-3-Clause): rate limit.
- bcrypt / passlib (BSD): nếu đổi từ stub sang password-based login (chưa dùng Phase 4).
- MinIO AGPLv3: Phase 4 ghi chú ở mục 21 là `excluded ở production; allowed ở local dev`. Production sẽ chuyển sang OCI Object Storage / Cloudflare R2 / bất kỳ S3-compatible commercial.

## Reference voice & dataset bắt buộc khai báo

- Mọi voice profile (voice clone) phải lưu: source audio path/hash, người sở hữu/quyền sử dụng, scope sử dụng (commercial Y/N), ngày accept, và reference tới file đồng ý.
- Không tự động clone voice người nổi tiếng/nhân vật nếu không có quyền sử dụng thương mại.
- Golden fixtures chỉ dùng audio tổng hợp hoặc audio do người dùng sở hữu/được cấp phép; cấm dùng video YouTube/Bilibili/Douyin không có quyền.

## Các quyết định license quyết định Phase 1

- Lõi TTS local tạm thời đặt `provider optional` cho VieNeu-TTS v3 Turbo cho đến khi hoàn tất audit checkpoint/dataset (mục 12). Không đặt thành `allowed core` mặc định.
- CosyVoice 3.0, VietVoice-TTS, MeloTTS Vietnamese: chỉ vào `provider optional` sau khi audit từng checkpoint/dataset.
- Storage production: viết `docs/architecture.md` và provider contract với MinIO chỉ là dev adapter; production cần quyết định deployment S3-compatible riêng trước khi lên Tier 2+.
- FFmpeg build phải chốt LGPL-only để không kéo theo GPL khi redistribute; nếu cần codec nonfree, đặt thành `provider optional` và document GPL/nonfree notice.
- pyannote.audio 3.1 model weights dùng CC-BY-4.0 (không phải CC-BY-NC). vẫn gated và yêu cầu accept user agreement. Attribution cho pyannote phải xuất hiện trong product UI/docs; không được ẩn.
- Model Meta (NLLB/seamless/M2M-100) đã thêm vào `excluded by default` (mục 27–29); cấm dùng cho commercial core kể cả khi tự host vì license NC không có ngoại lệ thương mại.

## Ngày tái kiểm

- Mỗi checkpoint model ASR/VAD/diarization/TTS phải được tái audit khi có phiên bản mới; không assume license của model cũ đúng cho model mới.
- Tái kiểm toàn bộ bảng này mỗi quý hoặc khi thêm component mới.
- Phase 4 audit pass 26/08/2026: thêm mục 32–47 (OCR/text-removal/monitoring stack).
