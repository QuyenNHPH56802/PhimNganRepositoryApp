# Translator — Hướng Dẫn Sử Dụng Từ A đến Z

> **Dành cho:** Người dùng không biết lập trình, người mới bắt đầu
> **Phiên bản:** 1.2.0

---

## Mục lục

1. [Translator là gì?](#1-translator-là-gì)
2. [Yêu cầu trước khi cài đặt](#2-yêu-cầu-trước-khi-cài-đặt)
3. [Cài đặt Docker Desktop](#3-cài-đặt-docker-desktop)
4. [Cài đặt dự án](#4-cài-đặt-dự-án)
5. [Khởi động ứng dụng](#5-khởi-động-ứng-dụng)
6. [Cách sử dụng](#6-cách-sử-dụng)
   - 6.5: [TTS với Qwen3 và các tùy chọn khác](#65-tts-với-qwen3-và-các-tùy-chọn-khác)
7. [Các chế độ chất lượng](#7-các-chế-độ-chất-lượng)
8. [Các ngôn ngữ được hỗ trợ](#8-các-ngôn-ngữ-được-hỗ-trợ)
9. [Xem tiến trình xử lý](#9-xem-tiến-trình-xử-lý)
10. [Xử lý lỗi thường gặp](#10-xử-lý-lỗi-thường-gặp)
11. [Gỡ cài đặt](#11-gỡ-cài-đặt)

---

## 1. Translator là gì?

**Translator** là một phần mềm giúp bạn **dịch và lồng tiếng video** từ ngôn ngữ này sang ngôn ngữ khác một cách tự động.

**Bạn có thể làm được gì?**

- Upload một video tiếng Trung → nhận video đã lồng tiếng Việt
- Tự động nhận diện người nói trong video
- Dịch phụ đề với độ chính xác cao
- Chọn 3 mức chất lượng: Nhanh, Cân bằng, Chất lượng cao

---

## 2. Yêu cầu trước khi cài đặt

### Phần cứng

| Thành phần | Yêu cầu tối thiểu | Yêu cầu khuyến nghị |
|------------|--------------------|-----------------------|
| RAM | 8 GB | 16 GB |
| Ổ cứng trống | 20 GB | 50 GB |
| CPU | 4 nhân | 8 nhân |
| GPU (card đồ họa) | Không bắt buộc | NVIDIA có CUDA |

### Phần mềm

- **Windows 10/11** hoặc **macOS** hoặc **Ubuntu Linux**
- **Docker Desktop** (phần mềm chạy container)

---

## 3. Cài đặt Docker Desktop

Docker là phần mềm giúp chạy Translator. Làm theo các bước sau:

### Windows

**Bước 3.1:** Tải Docker Desktop

Truy cập: **https://www.docker.com/products/docker-desktop/**
Nhấn nút **"Download for Windows"**

**Bước 3.2:** Cài đặt

1. Mở file vừa tải (ví dụ: `DockerDesktopInstaller.exe`)
2. Nhấn **"I accept the terms"** → **Install**
3. Đợi 5-10 phút để cài đặt xong
4. Nhấn **"Close and restart"**

**Bước 3.3:** Khởi động Docker Desktop

1. Tìm **Docker Desktop** trong menu Start
2. Mở Docker Desktop
3. Đợi biểu tượng cá voi 🐳 xuất hiện trên thanh taskbar (phía dưới màn hình)
4. Khi thấy chữ **"Docker Desktop is running"** là xong

> **Lưu ý:** Lần đầu khởi động có thể mất 2-3 phút. Nếu thấy lỗi WSL2, xem mục [Xử lý lỗi](#10-xử-lý-lỗi-thường-gặp)

### macOS

1. Tải Docker Desktop từ https://www.docker.com/products/docker-desktop/
2. Mở file `.dmg`, kéo biểu tượng Docker vào thư mục Applications
3. Mở Docker từ Applications

### Kiểm tra đã cài đúng

Mở **PowerShell** (Windows) hoặc **Terminal** (macOS/Linux), gõ:

```
docker --version
```

Nếu thấy dòng chữ version (ví dụ: `Docker version 20.10...`) là thành công.

---

## 4. Cài đặt dự án

### Bước 4.1: Tải mã nguồn về máy

Mở PowerShell, chạy lệnh:

```
cd $HOME\Desktop
git clone https://github.com/QuyenNHPH56802/PhimNganRepositoryApp.git
cd PhimNganRepositoryApp
```

### Bước 4.2: Tạo file cấu hình

Sao chép file mẫu:

```
cp .env.example .env
```

### Bước 4.3: Điền API Key (nếu có)

API Key là "chìa khóa" để Translator kết nối dịch vụ dịch thuật. Bạn có thể bỏ trống bước này nếu muốn dùng thử.

**Hướng dẫn lấy API Key OpenAI:**

1. Truy cập https://platform.openai.com/api-keys
2. Đăng nhập hoặc tạo tài khoản mới
3. Nhấn **"Create new secret key"**
4. Đặt tên (ví dụ: "translator-key")
5. Nhấn **"Create"**
6. **Copy API Key** (bắt đầu bằng `sk-...`)

Mở file `.env` bằng Notepad, sửa dòng:

```
OPENAI_API_KEY=sk-your-key-here
```

---

## 5. Khởi động ứng dụng

### Bước 5.1: Đảm bảo Docker đang chạy

Kiểm tra biểu tượng Docker 🐳 trên thanh taskbar.

### Bước 5.2: Khởi động stack

Mở PowerShell trong thư mục dự án, chạy:

```
.\scripts\up.ps1 up
```

**Hoặc nếu bạn dùng Terminal (macOS/Linux):**

```
make up
```

### Bước 5.3: Đợi khởi động (3-5 phút lần đầu)

Bạn sẽ thấy các dòng log xuất hiện. Đợi cho đến khi thấy dòng tương tự:

```
✔ Container translator-db-1       Started
✔ Container translator-api-1     Started
✔ Container translator-web-1      Started
✔ Container translator-temporal-1 Started
```

### Bước 5.4: Mở giao diện

Sau khi khởi động xong, mở trình duyệt web (Chrome, Edge, Firefox):

| Dịch vụ | Địa chỉ |
|---------|----------|
| **Giao diện chính** | http://localhost:3000 |
| **Tài liệu API** | http://localhost:8000/docs |
| **Temporal (xem tiến trình)** | http://localhost:8233 |

---

## 6. Cách sử dụng

### 6.1: Tạo dự án mới

1. Mở http://localhost:3000
2. Nhấn nút **"New Project"** (hoặc **"Tạo dự án mới"**)
3. Điền **Tiêu đề** (ví dụ: "Video Trung Quốc")
4. Chọn **Chế độ chất lượng** (xem mục 7)
5. Nhấn **"Tạo"**

### 6.2: Upload video

1. Trong trang dự án, nhấn **"Upload Video"**
2. Chọn file video từ máy tính (định dạng: .mp4, .mkv, .avi)
3. Đợi upload xong (thanh tiến trình 100%)
4. Video sẽ xuất hiện trong danh sách

### 6.3: Bắt đầu dịch

1. Nhấn nút **"Dịch"** hoặc **"Translate"** bên cạnh video
2. Chọn **ngôn ngữ nguồn** (video gốc)
3. Chọn **ngôn ngữ đích** (video cần dịch sang)
4. Chọn **giọng lồng tiếng** (xem chi tiết mục [6.5 — TTS providers](#65-tts-với-qwen3-và-các-tùy-chọn-khác)):
   - **Edge TTS (miễn phí)** — khuyến nghị cho người mới, không cần API key, không cần GPU
   - **DashScope Qwen3 (cloud)** — chất lượng cao, không cần GPU, cần API key
   - **Qwen3 TTS (local GPU)** — cần cài thêm model + GPU
   - **VietVoice / VieNeu / CosyVoice** — cần GPU
   - **Azure / Google / ElevenLabs** — cần API key thương mại
5. Nhấn **"Bắt đầu"**

### 6.4: Xem kết quả

1. Quay lại trang dự án
2. Nhấn vào video đang xử lý
3. Xem tiến trình từng bước:
   - ✅ Đang nhận diện giọng nói
   - ✅ Đang dịch nội dung
   - ✅ Đang tạo phụ đề
   - ✅ Đang lồng tiếng
   - ✅ Đang render video

Khi hoàn tất, nhấn **"Tải xuống"** để lưu video đã dịch.

---

### 6.5: TTS với Qwen3 và các tùy chọn khác

Phần này hướng dẫn chi tiết cách chọn và cấu hình **giọng lồng tiếng (TTS provider)**. Translator hỗ trợ 10 provider khác nhau, chia thành 4 nhóm:

#### Nhóm 1 — Miễn phí, không cần GPU (khuyến nghị cho người mới)

| Provider | Engine | Ưu điểm | Hạn chế |
|----------|--------|---------|---------|
| **Edge TTS** | `edge_tts` | Microsoft Edge neural voices, không cần API key | Chỉ truy cập được khi có internet |
| **MeloTTS (VI)** | `melotts_vi` | Model Việt nhẹ, chạy CPU | Chỉ tiếng Việt, chất lượng vừa |

#### Nhóm 2 — Cloud hosted, không cần GPU, chất lượng cao

| Provider | Engine | Ưu điểm | Hạn chế | Chi phí |
|----------|--------|---------|---------|---------|
| **DashScope Qwen3** | `dashscope_tts` | Đa ngôn ngữ, không cần GPU, chất lượng rất cao | Cần internet + API key | ~$0.004/phút |

#### Nhóm 3 — Chất lượng cao (cần GPU)

| Provider | Engine | Ưu điểm | Hạn chế |
|----------|--------|---------|---------|
| **Qwen3 TTS** | `qwen3_tts` | Đa ngôn ngữ (zh/en/vi/ja/ko), chất lượng rất cao | Cần GPU (CUDA) và ~6GB VRAM |
| **VietVoice** | `vietvoice_tts` | Giọng Việt tự nhiên | Chỉ tiếng Việt |
| **VieNeu** | `vieneu_v3_turbo` | Hỗ trợ voice clone | Cần GPU |
| **CosyVoice 3** | `cosyvoice_3` | Đa ngôn ngữ + voice clone | Cần GPU mạnh (~12GB VRAM) |

#### Nhóm 4 — Thương mại (cần API key)

| Provider | Engine | Biến môi trường |
|----------|--------|-----------------|
| **Azure TTS** | `cloud_azure` | `AZURE_TTS_KEY` |
| **Google Cloud TTS** | `cloud_google` | `GOOGLE_TTS_KEY` |
| **ElevenLabs** | `cloud_elevenlabs` | `ELEVENLABS_API_KEY` |

#### Hướng dẫn cụ thể cho DashScope Qwen3 (không cần GPU)

**Khuyến nghị: Đây là cách nhanh nhất để dùng Qwen3 mà không cần GPU.**

**Bước 1 — Lấy API key:**
1. Truy cập https://dashscope.console.aliyun.com
2. Đăng nhập tài khoản Alibaba Cloud (có thể dùng tài khoản Alipay/taobao)
3. Tạo API key mới (DashScope → Create API Key)

**Bước 2 — Thêm vào .env:**
```bash
DASHSCOPE_API_KEY=sk-your-key-here
```

**Bước 3 — Chọn provider trong giao diện:**
1. Mở http://localhost:3000/settings
2. Tại mục **TTS**, chọn **DashScope Qwen3 (cloud)** trong dropdown
3. Nhấn **"Update"** để lưu

**Bước 4 — Chạy dịch thử:**
- Quay lại dự án → nhấn **"Dịch"**

---

#### Hướng dẫn cụ thể cho Qwen3 TTS (local GPU)

**Yêu cầu phần cứng:**
- GPU NVIDIA với CUDA (khuyến nghị ≥ 8 GB VRAM)
- Ổ cứng trống ≥ 6 GB (để chứa checkpoint)
- RAM hệ thống ≥ 16 GB

**Bước 1 — Cài đặt SDK:**
```bash
pip install qwen-tts
```

**Bước 2 — Tải checkpoint (chỉ cần làm 1 lần):**
```bash
python -c "from qwen_tts import Qwen3TTS; Qwen3TTS(model_id='qwen3-tts')"
```
Lệnh này sẽ tải checkpoint về `~/.cache/qwen-tts/` (~5–6 GB).

**Bước 3 — Đổi TTS provider trong giao diện:**
1. Mở http://localhost:3000/settings
2. Tại mục **TTS**, chọn **Qwen3 TTS (high quality)** trong dropdown
3. Nhấn **"Update"** để lưu

**Bước 4 — Chạy dịch thử:**
- Quay lại dự án → nhấn **"Dịch"**
- Kiểm tra log Temporal (http://localhost:8233) để xác nhận `tts_synthesize` chạy trên `tts-queue`

**Lưu ý:** Nếu không có GPU, Qwen3 vẫn chạy được trên CPU nhưng rất chậm (1 câu ~10 giây audio mất ~3 phút). Khuyến nghị dùng Edge TTS cho máy không có GPU.

#### So sánh nhanh

| Tiêu chí | Edge | DashScope | Qwen3 | VietVoice | ElevenLabs |
|----------|------|-----------|-------|-----------|------------|
| Chất lượng | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Tốc độ (CPU) | ⚡⚡⚡ | ⚡⚡⚡ | ⚡ | ⚡⚡ | ⚡⚡⚡ |
| Tốc độ (GPU) | ⚡⚡⚡ | ⚡⚡⚡ | ⚡⚡⚡ | ⚡⚡⚡ | ⚡⚡⚡ |
| Chi phí | Miễn phí | ~$0.004/phút | Miễn phí | Miễn phí | ~$5/tháng |
| Yêu cầu GPU | Không | Không | Có (CPU chậm) | Có | Không |
| Số ngôn ngữ | 100+ | 11+ | 11 | 1 (VI) | 29 |

Xem thêm chi tiết tại `docs/integrations.md` mục 8.

---

## 7. Các chế độ chất lượng

| Chế độ | Tốc độ | Chất lượng | Phù hợp khi |
|--------|--------|------------|-------------|
| **Fast (Nhanh)** | ⚡⚡⚡ | ⭐⭐ | Cần kết quả nhanh, chấp nhận chất lượng vừa |
| **Balanced (Cân bằng)** | ⚡⚡ | ⭐⭐⭐ | Sử dụng thường ngày |
| **High (Chất lượng cao)** | ⚡ | ⭐⭐⭐⭐⭐ | Cần kết quả tốt nhất |

**Chi tiết từng chế độ:**

### Fast (Nhanh)
- Không có phân tách người nói
- Không có lồng tiếng
- Phụ đề cơ bản
- Thời gian xử lý: ~10-30 phút cho video 1 giờ

### Balanced (Cân bằng)
- Phân tách người nói ✓
- Có lồng tiếng ✓
- Phụ đề chính xác hơn
- Thời gian xử lý: ~30-60 phút cho video 1 giờ

### High (Chất lượng cao)
- Tất cả tính năng của Balanced
- Thêm voice clone (giọng nói gốc) ✓
- Tối ưu thời gian phụ đề
- Thời gian xử lý: ~1-2 giờ cho video 1 giờ

---

## 8. Các ngôn ngữ được hỗ trợ

| Ngôn ngữ nguồn | Ngôn ngữ đích |
|----------------|--------------|
| Tiếng Trung (zh) | Tiếng Việt (vi) ✓ |
| Tiếng Việt (vi) | Tiếng Trung (zh) ✓ |
| Tiếng Trung (zh) | Tiếng Anh (en) ✓ |
| Tiếng Anh (en) | Tiếng Trung (zh) ✓ |
| Tiếng Trung (zh) | Tiếng Nhật (ja) ✓ |
| Tiếng Trung (zh) | Tiếng Hàn (ko) ✓ |
| Tiếng Anh (en) | Tiếng Việt (vi) ✓ |
| Tiếng Việt (vi) | Tiếng Anh (en) ✓ |

---

## 9. Xem tiến trình xử lý

### Cách 1: Giao diện chính

Mở http://localhost:3000 → nhấn vào dự án đang xử lý

### Cách 2: Temporal UI (nâng cao)

Mở http://localhost:8233

Đây là công cụ xem chi tiết từng bước xử lý. Phù hợp khi cần debug.

### Trạng thái dự án

| Trạng thái | Ý nghĩa |
|------------|---------|
| `draft` | Mới tạo, chưa xử lý |
| `processing` | Đang xử lý |
| `awaiting_review` | Chờ kiểm tra |
| `ready` | Hoàn thành |
| `failed` | Có lỗi |
| `archived` | Đã lưu trữ |

---

## 10. Xử lý lỗi thường gặp

### Lỗi: "Docker Desktop is not running"

**Dấu hiệu:** Màn hình đen hoặc lỗi kết nối

**Cách khắc phục:**
1. Mở Docker Desktop từ menu Start
2. Đợi 1-2 phút cho đến khi thấy biểu tượng 🐳 xanh
3. Thử chạy lại `.\scripts\up.ps1 up`

---

### Lỗi: "Port is already allocated"

**Dấu hiệu:** Báo port 3000, 8000, hoặc 5432 đang bị chiếm

**Cách khắc phục:**
1. Đóng các ứng dụng khác đang dùng port đó (ví dụ: Skype, nginx)
2. Hoặc chạy lệnh:
```
docker compose -f infra/docker/docker-compose.yml down
```
3. Sau đó khởi động lại

---

### Lỗi: "OPENAI_API_KEY is not set"

**Dấu hiệu:** Video không dịch được, báo lỗi API key

**Cách khắc phục:**
1. Mở file `.env` bằng Notepad
2. Sửa dòng `OPENAI_API_KEY=` thành `OPENAI_API_KEY=sk-your-key`
3. Lưu file
4. Chạy lại:
```
docker compose -f infra/docker/docker-compose.yml restart api
```

---

### Lỗi: Không thể truy cập localhost

**Dấu hiệu:** Trình duyệt báo "This site can't be reached"

**Cách khắc phục:**
1. Đảm bảo Docker đang chạy
2. Kiểm tra địa chỉ đúng:
   - Giao diện: http://localhost:3000 (không phải https)
   - API: http://localhost:8000/docs
3. Thử tải lại trang (nhấn F5)

---

### Lỗi: Video upload chậm hoặc thất bại

**Dấu hiệu:** Thanh upload không nhích hoặc bị lỗi

**Cách khắc phục:**
1. Kiểm tra file video không lớn hơn 2GB
2. Dùng trình duyệt Chrome hoặc Edge
3. Kiểm tra kết nối internet
4. Thử upload lại

---

## 11. Gỡ cài đặt

### Dừng ứng dụng

Mở PowerShell, chạy:

```
.\scripts\up.ps1 down
```

### Gỡ Docker Desktop

**Windows:**
1. Mở **Settings** → **Apps**
2. Tìm **Docker Desktop**
3. Nhấn **Uninstall**

**macOS:**
1. Kéo biểu tượng Docker ra khỏi Applications

---

## Liên hệ hỗ trợ

Nếu gặp lỗi không có trong danh sách trên:

1. Chụp ảnh màn hình lỗi
2. Mở PowerShell, chạy:
```
docker compose -f infra/docker/docker-compose.yml logs > logs.txt
```
3. Gửi file `logs.txt` cùng ảnh chụp cho người phát triển

---

**Chúc bạn sử dụng Translator hiệu quả! 🎬**
