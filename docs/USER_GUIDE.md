# Hướng Dẫn Sử Dụng Translator Platform

**Phiên bản:** 1.3.0  
**Cập nhật:** 30/08/2026

---

## Mục Lục

1. [Giới thiệu](#giới-thiệu)
2. [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
3. [Cài đặt](#cài-đặt)
4. [Đăng nhập](#đăng-nhập)
5. [Tạo dự án mới](#tạo-dự-án-mới)
6. [Tải video lên](#tải-video-lên)
7. [Xem & Chỉnh sửa trong Workspace](#xem--chỉnh-sửa-trong-workspace)
8. [Khởi chạy Pipeline xử lý](#khởi-chạy-pipeline-xử-lý)
9. [Chế độ chất lượng](#chế-độ-chất-lượng)
10. [Quản lý giọng nói](#quản-lý-giọng-nói)
11. [Quản trị hệ thống](#quản-trị-hệ-thống)
12. [Xử lý sự cố](#xử-lý-sự-cố)

---

## Giới thiệu

**Translator Platform** là nền tảng video localization hỗ trợ dịch video từ **tiếng Trung (zh) → tiếng Việt (vi)**. Hệ thống tự động:

- Nhận dạng giọng nói (ASR) với WhisperX
- Dịch thuật tự động qua LLM (OpenAI/Gemini/Claude hoặc **Ollama local**)
- Tổng hợp giọng nói (TTS) với Edge-TTS
- Render video hoàn chỉnh với FFmpeg

---

## Yêu cầu hệ thống

### Docker (Khuyến nghị)

- Docker & Docker Compose
- RAM: 8GB minimum (16GB khuyến nghị)
- GPU: NVIDIA GPU với CUDA cho ASR/TTS nhanh hơn
- **Tùy chọn**: [Ollama](https://ollama.com) nếu muốn dịch local (không cần API key của OpenAI/Gemini/Claude) — xem mục [Dịch qua Ollama local](#dịch-qua-ollama-local-không-cần-api-key)

### Chạy Local (Development)

- Python 3.11+
- Node.js 18+
- PostgreSQL 16
- Temporal server

### Dịch qua Ollama local (không cần API key)

Thay vì dùng API key của OpenAI/Gemini/Claude, có thể chạy một model LLM local qua Ollama. Service `ollama` đã có sẵn trong `docker-compose.yml`.

```bash
# Khởi động service Ollama
docker compose -f infra/docker/docker-compose.yml up -d ollama

# Tải model ngôn ngữ (ví dụ qwen2.5:7b hỗ trợ tiếng Trung tốt)
docker compose -f infra/docker/docker-compose.yml exec ollama ollama pull qwen2.5:7b

# Verify service chạy
curl http://localhost:11434/api/tags
```

Sau khi Ollama đã sẵn sàng, set env cho api/worker (đã có default trong repo):

```env
TRANSLATOR_LOCAL_LLM_BACKEND=ollama
OLLAMA_BASE_URL=http://ollama:11434
TRANSLATOR_LOCAL_LLM_MODEL=qwen2.5:7b
```

Trong Settings UI (mục Provider config), chọn `local_llm` làm provider dịch. Provider `local_llm` đã được đăng ký sẵn trong `apps/api/python/translator_api/providers/translate/local_llm.py` — chỉ cần đổi backend sang `ollama` là chạy được, không cần API key bên ngoài.

> **Lưu ý GPU**: Ollama tự động dùng GPU NVIDIA nếu host có driver CUDA + Docker NVIDIA runtime. Nếu chạy CPU-only, đoạn `deploy.resources` trong compose có thể bị bỏ qua — Ollama vẫn chạy nhưng chậm hơn nhiều.

---

## Cài đặt

### 1. Clone và cấu hình

```bash
# Clone repository
git clone <repo-url>
cd Translator

# Copy file cấu hình môi trường
cp .env.example .env
```

### 2. Cấu hình biến môi trường (.env)

```env
# Database
DATABASE_URL=postgresql://translator:translator@localhost:5432/translator_db

# Temporal
TEMPORAL_ADDRESS=localhost:7233
TEMPORAL_NAMESPACE=default

# API Keys (bắt buộc cho translation)
OPENAI_API_KEY=sk-your-key-here
# hoặc
GEMINI_API_KEY=your-gemini-key
# hoặc
ANTHROPIC_API_KEY=your-claude-key

# TTS Service (nếu dùng TTS service riêng)
TTS_SERVICE_URL=http://tts-service:3099/synthesize

# Storage
TRANSLATOR_STORAGE_PROVIDER_ID=local
```

### 3. Khởi chạy với Docker

```bash
# Build và chạy tất cả services
docker-compose up -d

# Kiểm tra trạng thái
docker-compose ps
```

### 4. Truy cập ứng dụng

- **Web App:** http://localhost:3000
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## Đăng nhập

### Chế độ Demo

Nếu backend không khả dụng, hệ thống tự động chuyển sang **Demo Mode**:

1. Click nút **"Đăng nhập ngay"**
2. Nếu server không phản hồi → chọn **"Dùng thử Demo Mode"**
3. Token demo sẽ được lưu vào localStorage

### Chế độ Production

1. Nhập email admin
2. Click **"Đăng nhập ngay"**
3. Hệ thống sẽ kiểm tra credentials qua `/auth/login`

> **Lưu ý:** Token đăng nhập được lưu trong localStorage. Xóa token sẽ đăng xuất.

---

## Tạo dự án mới

### Cách thực hiện:

1. Từ Dashboard, click **"+ Dự án mới"** (góc phải header)
2. Điền thông tin:
   - **Tên dự án:** Tên video/dự án của bạn
   - **Chế độ chất lượng:** Fast / Balanced / High
   - **Ngôn ngữ nguồn:** zh (Trung Quốc)
   - **Ngôn ngữ đích:** vi (Việt Nam)
3. Click **"Tạo dự án"**

### Chế độ chất lượng

| Chế độ | Diarization | Voice Clone | TTS | Tốc độ |
|---------|-------------|-------------|-----|---------|
| **Fast** | Không | Không | Không | Nhanh nhất |
| **Balanced** | Có | Không | Có | Trung bình |
| **High** | Có | Có | Có | Chậm nhất |

---

## Tải video lên

### Các bước thực hiện:

1. Mở dự án → click tab **"Upload"**
2. **Kéo thả** file video vào vùng upload
3. Hoặc click **"Chọn file"** để duyệt
4. Đợi upload hoàn tất (progress bar hiển thị)

### Định dạng hỗ trợ

- **Video:** MP4, AVI, MOV, MKV
- **Audio:** MP3, WAV, M4A
- **Dung lượng tối đa:** 10GB

### Sau khi upload

- Video sẽ xuất hiện trong danh sách assets
- Click vào video để xem chi tiết
- Tiếp tục sang tab **"Workspace"** để chỉnh sửa

---

## Xem & Chỉnh sửa trong Workspace

Workspace là trung tâm chỉnh sửa chính của dự án.

### Giao diện Workspace

```
┌─────────────────────────────────────────────────────────────┐
│  [🎬 Video Player]           [🔊 Audio Controls]           │
├─────────────────────────────────────────────────────────────┤
│  [Transcript] [Translation] [Speaker] [Voice] [Subtitle]   │
│  [Audio] [Render]                                          │
├─────────────────────────────────────────────────────────────┤
│  Transcript Panel │ Translation Panel │ Inspector Panel    │
│  (Danh sách câu)  │ (Bản dịch VI)    │ (Chi tiết)        │
└─────────────────────────────────────────────────────────────┘
```

### Các Panel chính

#### 1. Transcript Panel
- Hiển thị danh sách câu thoại tiếng Trung
- Mỗi câu có timestamp (thời điểm bắt đầu → kết thúc)
- Click để chọn, double-click để split segment

#### 2. Translation Panel  
- Hiển thị bản dịch tiếng Việt tương ứng
- **Có thể chỉnh sửa trực tiếp** bản dịch
- Auto-save sau 1.5s không gõ (debounce)

#### 3. Speaker Panel
- Danh sách người nói được phát hiện
- Gán giọng nói (Voice Profile) cho từng speaker

#### 4. Voice Panel
- Quản lý Voice Profiles
- Tạo profile mới với reference audio
- Preview giọng nói trước khi sử dụng

#### 5. Subtitle Panel
- Tạo và chỉnh sửa phụ đề
- Split/merge segments
- Inspector để sửa chi tiết từng phụ đề

#### 6. Audio Panel
- Điều chỉnh âm lượng các track:
  - **Original:** Tiếng gốc Trung
  - **Voice VI:** Giọng lồng tiếng Việt
  - **Music:** Nhạc nền
  - **SFX:** Hiệu ứng âm thanh
- Preset: "Chỉ voice VI", "Giữ tất cả"

#### 7. Render Panel
- Xem tiến trình pipeline
- Cấu hình render:
  - **Độ phân giải:** 720p / 1080p / 4K
  - **Codec:** H.264 / H.265
  - **Chế độ âm thanh:** Dubbed / Sub-only / Dual Track
  - **Phụ đề:** Hardsub / Softsub

### Video Player

- **🎬 Video Gốc:** Xem video tiếng Trung gốc
- **✨ Video Đã Xử Lý:** Xem video đã lồng tiếng Việt
- Các nút điều khiển: Play/Pause, Volume, Fullscreen

### Phím tắt

| Phím | Chức năng |
|------|-----------|
| `Space` | Play/Pause |
| `←` / `→` | Tua 5 giây |
| `↑` / `↓` | Thay đổi âm lượng |
| `M` | Tắt tiếng |

---

## Khởi chạy Pipeline xử lý

### Pipeline Workflow

```
Video → ASR → Normalize → Translate → QA → Subtitle
                              ↓
                          TTS (nếu Balanced/High)
                              ↓
                    Audio Separation (nếu High)
                              ↓
                         Dubbing Align
                              ↓
                          Audio Mix
                              ↓
                        Render Video
                              ↓
                         Export MP4
```

### Cách khởi chạy

1. Trong **Render Panel**, chọn **"Bắt đầu Render"**
2. Chọn chế độ chất lượng (Fast/Balanced/High)
3. Click **"Khởi tạo"**
4. Theo dõi tiến trình trong **Pipeline Progress**

### Các bước Pipeline

| # | Bước | Mô tả |
|---|-------|-------|
| 1 | Chuẩn hóa tiếng Trung | Normalize Chinese text |
| 2 | Dịch thuật | Translate zh → vi |
| 3 | Kiểm định chất lượng | QA check |
| 4 | Tạo phụ đề | Subtitle segmentation |
| 5 | Tổng hợp giọng nói | TTS synthesis (Balanced/High) |
| 6 | Căn chỉnh lồng tiếng | Dubbing alignment |
| 7 | Trộn âm thanh | Audio mixing |
| 8 | Render video | FFmpeg render |

### Tải video hoàn chỉnh

Sau khi pipeline hoàn tất:

1. Nút **"📥 Tải Video MP4"** xuất hiện
2. Click để tải video đã xử lý
3. Có thể tải thêm **Phụ đề SRT/VTT**

---

## Quản lý giọng nói

### Tạo Voice Profile mới

1. Vào **Workspace** → tab **"Voice"**
2. Click **"Tạo Voice Profile mới"**
3. Điền thông tin:
   - **Tên:** Tên profile (VD: "Giọng Nam Việt")
   - **Provider:** Edge-TTS / VietVoice / ElevenLabs / ...
   - **Model:** vi-VN-NamMinhNeural / vi-VN-HoaiMyNeural / ...
4. Upload **Reference Audio** (tùy chọn, cho voice clone)
5. Click **"Lưu"**

### Gán Voice cho Speaker

1. Trong **Speaker Panel**, chọn speaker
2. Chọn Voice Profile từ dropdown
3. Profile được gán sẽ được dùng cho TTS

---

## Quản trị hệ thống

### Trang Admin (/admin)

- **Dashboard:** Tổng quan hệ thống
- **Voice:** Quản lý voice profiles toàn hệ thống
- **Dataset:** Quản lý dataset cho training
- **Audit Log:** Lịch sử các thao tác

### Trang Cài đặt (/settings)

- Cấu hình providers (Translation, TTS, ASR)
- API Keys management
- Default settings

### Cấu hình Providers

#### Translation Providers

| Provider | API Required | Giá |
|---------|--------------|-----|
| OpenAI-compatible | Yes | Theo usage |
| Gemini | Yes | Miễn phí tier |
| Claude | Yes | Theo usage |
| Local (Ollama) | No | Miễn phí |

#### TTS Providers

| Provider | Giá | Chất lượng |
|----------|------|------------|
| Edge-TTS | Miễn phí | Tốt |
| VietVoice | Miễn phí | Tốt |
| ElevenLabs | Trả phí | Xuất sắc |

---

## Xử lý sự cố

### Lỗi thường gặp

#### 1. "Failed to load resource: net::ERR_CONNECTION_REFUSED"

**Nguyên nhân:** Backend/API không chạy

**Giải pháp:**
```bash
# Kiểm tra containers đang chạy
docker-compose ps

# Restart services
docker-compose restart api worker
```

#### 2. "CORS policy blocked"

**Nguyên nhân:** Backend CORS chưa cấu hình đúng

**Giải pháp:** Đã được fix trong phiên bản 1.3.0. Đảm bảo:
- API chạy trên port 8000
- Web chạy trên port 3000
- Cấu hình CORS trong `apps/api/python/translator_api/main.py`

#### 3. Upload video thất bại

**Nguyên nhân:** Kích thước file vượt giới hạn hoặc storage lỗi

**Giải pháp:**
- Kiểm tra `MAX_UPLOAD_SIZE` trong config
- Kiểm tra volume storage docker

#### 4. Pipeline bị treo ở bước ASR

**Nguyên nhân:** Model download lỗi

**Giải pháp:**
```bash
# Xóa cache model
docker-compose exec worker rm -rf /root/.cache/huggingface

# Restart worker
docker-compose restart worker
```

#### 5. "Cannot read properties of undefined"

**Nguyên nhân:** Dữ liệu từ API chưa load xong

**Giải pháp:** Đợi trang load hoàn toàn, refresh lại trang

### Logs

```bash
# Xem logs API
docker-compose logs -f api

# Xem logs Worker
docker-compose logs -f worker

# Xem logs cụ thể
docker-compose logs --tail=100 api | grep ERROR
```

### Reset Database

```bash
# Stop services
docker-compose down

# Xóa volume database
docker-compose down -v

# Restart
docker-compose up -d
```

---

## Các thay đổi trong phiên bản 1.3.0

### Security Fixes
- **Đã xóa:** API keys hardcoded trong source code
- **Đã sửa:** Auth bypass vulnerability trong `_require_viewer`
- **Đã cập nhật:** CORS configuration an toàn hơn

### Bug Fixes
- **Đã sửa:** Duplicate `__init__` method trong WhisperX provider
- **Đã sửa:** State mutation during render trong SubtitlePanel
- **Đã sửa:** Memory leak trong polling và reconnect timer
- **Đã sửa:** Bare `[0]` access có thể gây crash
- **Đã sửa:** Deprecated `datetime.utcnow()` → `datetime.now(timezone.utc)`

### Improvements
- **Đã cải thiện:** API URL environment variable consistency
- **Đã triển khai:** CosyVoice TTS provider implementation
- **Đã tối ưu:** Auto-save debounce trong workspace

---

## Liên hệ & Hỗ trợ

- **Documentation:** http://localhost:3000/docs (nếu có)
- **API Reference:** http://localhost:8000/docs
- **Issues:** GitHub Issues

---

*Hướng dẫn này được cập nhật cho phiên bản 1.3.0 - 30/08/2026*
