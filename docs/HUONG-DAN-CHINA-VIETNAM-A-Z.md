# HUONG-DAN-CHINA-VIETNAM-A-Z.md

# Huong Dan Su Dung pyVideoTrans — China to Vietnamese

**Phien ban:** China-VNE Configuration for pyVideoTrans v4.11
**Cong cu:** pyVideoTrans (jianchang512/pyvideotrans)
**Muc tieu:** Dich video tieng Trung Quoc thanh tieng Viet

---

## Muc Luc

- [A - Cai Dat](#a---cai-dat)
- [B - Khoi Dong](#b---khoi-dong)
- [C - Cau Hinh API](#c---cau-hinh-api)
- [D - Dich Vu Dich Thuong Mai](#d---dich-vu-dich-thuong-mai)
- [E - Thu Nghiem Nhanh (Demo)](#e---thu-nghiem-nhanh-demo)
- [F - Chi Tiet Pipeline](#f---chi-tiet-pipeline)
- [G - GPU Setup](#g---gpu-setup)
- [H - Ho Tro Nguoi Dung](#h---ho-tro-nguoi-dung)
- [I - Xuat Video](#i---xuat-video)
- [J - Xu Ly Su Co](#j---xu-ly-su-co)
- [K - Cap Nhat](#k---cap-nhat)
- [L - Sao Luu](#l---sao-luu)
- [M - Model](#m---model)
- [N - Ngon Ngu](#n---ngon-ngu)
- [O - Tuy Chinh](#o---tuy-chinh)
- [P - Che Do Chat Luong](#p---che-do-chat-luong)
- [Q - Hoi Dap Thuong Gap](#q---hoi-dap-thuong-gap)
- [R - Dac Diem Ky Thuat](#r---dac-diem-ky-thuat)
- [S - Lenh CLI](#s---lenh-cli)
- [T - Thuat Ngu](#t---thuat-ngu)

---

## A - Cai Dat

### A1. Tai Xuong

**Phuong phap 1: Pre-packaged (khuyen nghi)**

1. Tai file `.7z` (~2.7 GB) tu mot trong cac nguon:
   - **Hugging Face:** https://huggingface.co/mortimerme/repocollect/resolve/main/win-pyvideotrans-v4.11.7z
   - **Baidu Netdisk:** https://pan.baidu.com/s/1GkL4pyAYxJRvRor0jfh2rg (mat khau: 1234)
   - **GitHub Releases:** https://github.com/jianchang512/pyvideotrans/releases

2. Giai nen ra mot thu muc (VD: `D:\ChinaVNE\pyvideotrans-win`)
   - **Quan trong:** Khong giai nen vao Desktop, Program Files, hoac thu muc co khoang trang/ky tu tieng Trung

3. Chay `sp.exe` de khoi dong

**Phuong phap 2: Source code (cho Linux/Mac/developer)**

```bash
# Cai dat uv
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Clone
git clone https://github.com/jianchang512/pyvideotrans.git
cd pyvideotrans

# Cai dat phu thuoc
uv sync

# Khoi dong
uv run sp.py
```

### A2. Thu Muc Cau Truc

```
pyvideotrans-win/
  sp.exe                    # File chay chinh (double-click)
  ffmpeg/                   # FFmpeg (duoc goi tu bundling)
  f5-tts/                   # File am thanh tham chieu cho voice cloning
  _internal/                # Python runtime + thu vien
  videotrans/               # Cau hinh (params.json o day)
  output/                   # Video da xu ly
  logs/                     # Log file
```

---

## B - Khoi Dong

### B1. Tu Dong Lenh

```batch
# Chay script khoi dong
scripts\china-vietnam\start.bat
```

### B2. Tu GUI

Double-click `sp.exe`

Giao dien chinh gom 5 tab:
1. **Nhap Video** — Chon video nguon
2. **STT** — Nhan dien tieng noi
3. **Dich** — Dich tieng noi
4. **Dubbing** — Dong am thanh
5. **Xuat** — Xuat video

---

## C - Cau Hinh API

### C1. Cau Hinh Key

Trong giao dien chinh, vao **Tools > Settings** (hoac nut cau hinh tuong ung):

| Dịch vụ | API Key | Ghi chu |
|----------|---------|---------|
| DeepSeek | `DEEPSEEK_API_KEY` | Khuyen nghi cho dich Trung -> Viet |
| ChatGPT | `OPENAI_API_KEY` | Phu hop |
| Claude | `ANTHROPIC_API_KEY` | Chatbot Claude |
| Gemini | `GEMINI_API_KEY` | Google |
| DeepL | `DEEPL_API_KEY` | Tra phi |
| Azure TTS | `AZURE_SPEECH_KEY` | Microsoft |
| ElevenLabs | `ELEVENLABS_API_KEY` | Voice cloning |

### C2. Khu vuc Cai Dat Chi Tiet

Vao **Tools > Advanced Options** de cau hinh:

- **CUDA compute type:** float16 (RTX 50-series) hoac int8 (VRAM thap hon)
- **CRF:** 18-23 (so nho hon = chat luong cao hon)
- **Codec:** libx265 (HEVC, nen nen) hoac libx264 (H.264, tuong thich hon)

---

## D - Dich Vu Dich Thuong Mai

### D1. Dich (Translation)

| Kenh | Chi so | Chi phi | Chat luong | Ghi chu |
|------|--------|---------|-----------|---------|
| **DeepSeek** | 5 | Tra phi | Rat tot | Khuyen nghi cho Trung -> Viet |
| **ChatGPT** | 4 | Tra phi | Tot | |
| **Google Translate** | 0 | Mien phi (gioi han) | Trung binh | |
| **Microsoft Translator** | 1 | Mien phi (gioi han) | Trung binh | |
| **Ollama (Local)** | 9 | Mien phi | Tuy model | Can cau hinh local |

**Khuuyen nghi cho China -> Vietnam:** DeepSeek (kenh 5) voi model `deepseek-chat` hoac `deepseek-v4-flash`

### D2. Nhan dien Tieng Noi (ASR)

| Kenh | Chi so | Chi phi | Ghi chu |
|------|--------|---------|---------|
| **FunASR** | 4 | Mien phi | **Tot nhat cho tieng Trung**, built-in |
| **Faster-Whisper** | 0 | Mien phi | Tot cho moi ngon ngu |
| **OpenAI Whisper** | 1 | Mien phi | Do chinh xac cao hon |
| **WhisperX** | 18 | Mien phi | Co timestamp + diarization |

**Khuuyen nghi:** FunASR (kenh 4) — built-in, mien phi, tot nhat cho tieng Trung Quoc

Model cho FunASR:
- `paraformer-zh` — Do chinh xac cao nhat
- `SenseVoiceSmall` — Nhe hon, nhanh hon

### D3. Text-to-Speech (TTS)

#### Mien phi — Edge-TTS (kenh 0)

**Khong can API key.** Gioi thieu tieng Viet.

```
vi-VN-HoaiMyNeural   # Nu
vi-VN-NamMinhNeural  # Nam
```

Cach su dung:
1. Tab 4 (TTS): Chon kenh = Edge-TTS
2. Voice role = `vi-VN-HoaiMyNeural`
3. Done

#### Built-in — Confucius-TTS (kenh 4)

Tu v4.06, built-in, ho tro tieng Viet, co voice cloning.

#### Built-in — F5-TTS (kenh 2)

Tu v4.04, built-in, ho tro voice cloning cho tieng Viet.

Cach su dung voice cloning:
1. Thu muc: `f5-tts/` trong thu muc pyVideoTrans
2. Dat file WAV tham chieu (3-10 giay, phat am rõ ràng, khong nhieu)
3. Trong GUI: Chon F5-TTS, voice role = `clone`

#### Built-in — OmniVoice (kenh 3)

Tu v4.05, 600+ ngon ngu, co voice cloning.

#### Tra phi — CosyVoice 3

Dang ky: https://github.com/FunAudioLLM/CosyVoice
- 3 giay tham chieu
- Chat luong cao
- Can GPU (16GB VRAM)

### D4. Speaker Diarization

Bat: **Tools > Advanced Options > Enable Diarization**
- Auto-detect: `--nums_diariz -1`
- Manual: Dat so luong nguoi noi

Cac backend:
- **Built-in** (mac dinh)
- **Ali CAM++** — Alibaba speaker verification
- **pyannote-audio** — Can HuggingFace token

---

## E - Thu Nghiem Nhanh (Demo)

### E1. Chi Dich Phu De (Khong Dong Am)

```bash
# Chi dich phu de, khong dong am thanh
uv run cli.py ^
  --task sts ^
  --name "video.srt" ^
  --target_language_code vi ^
  --translate_type 5
```

### E2. Video Translation Day Du

```bash
# FunASR + DeepSeek + Edge-TTS
uv run cli.py ^
  --task vtv ^
  --name "video_trung_quoc.mp4" ^
  --recogn_type 4 ^
  --translate_type 5 ^
  --tts_type 0 ^
  --source_language_code zh-cn ^
  --target_language_code vi ^
  --voice_role "vi-VN-HoaiMyNeural" ^
  --cuda
```

---

## F - Chi Tiet Pipeline

```
Video tieng Trung
      |
      v
[1. Chuan bi am thanh]
      | Demucs (tach nhac nen), denoise, VAD
      v
[2. Speech Recognition (ASR)]
      | FunASR paraformer-zh (kenh 4)
      | Dau ra: SRT tieng Trung + timestamps
      v
[3. Speaker Diarization] (neu bat)
      | Phat hien nguoi noi 1, nguoi noi 2...
      v
[4. Subtitle Translation]
      | DeepSeek (kenh 5)
      | Dau ra: SRT tieng Viet
      v
[5. Text-to-Speech]
      | Edge-TTS vi-VN-HoaiMyNeural (kenh 0)
      | Tach doan am thanh, dong am thanh tung cau
      v
[6. Video Synthesis]
      | FFmpeg, ghep am thanh Viet + nhac nen + video
      v
Video tieng Viet (output/)
```

---

## G - GPU Setup

### G1. Kiem Tra GPU

```cmd
nvidia-smi
```

Yeu cau:
- NVIDIA GPU
- CUDA 12.8
- cuDNN 9.11
- Driver nganh 570+ (cho RTX 50-series)

### G2. Cau Hinh CUDA

**Neu dung pre-packaged:** Da co san torch cu128, khong can cau hinh them.

**Neu cai dat source:**

```bash
# Go phiên ban CPU
uv remove torch torchaudio

# Cai phiên ban CUDA
uv add torch==2.7 torchaudio==2.7 --index-url https://download.pytorch.org/whl/cu128
uv add nvidia-cublas-cu12 nvidia-cudnn-cu12
```

### G3. RTX 50-Series (RTX 5090/5080)

**Quan trong:** RTX 50-series khong ho tro `int8` auto cuBLAS.

Vao **Tools > Advanced Options > CUDA compute type** = `float16`

### G4. VRAM Guide

| Model | VRAM |
|-------|------|
| FunASR paraformer-zh | 4GB+ (GPU recommended) |
| Faster-Whisper large-v3 | 8GB+ |
| CosyVoice 3 | 16GB+ |
| GPT-SoVITS | 16GB+ |

### G5. CPU Fallback

Neu khong co GPU, pyVideoTrans van hoat dong tren CPU.
- Chay cham hon (~3-5x)
- Tat ca cac kenh deu ho tro CPU

---

## H - Ho Tro Nguoi Dung

### H1. Tai Lieu Chinh Thuc

- **Website:** https://pyvideotrans.com
- **Forum:** https://bbs.pyvideotrans.com
- **GitHub:** https://github.com/jianchang512/pyvideotrans

### H2. Log File

Neu gap loi, xem log tai:
```
videotrans/logs/
```

Hoac trong thu muc lam viec.

---

## I - Xuat Video

### I1. Cai Dat Xuat

Trong tab **Output** (Tab 5):

| Tuy chon | Gia tri khuyen nghi |
|-----------|---------------------|
| **Codec** | `libx265` (HEVC) |
| **CRF** | `20` (18 = chat luong cao hon) |
| **Format** | `mp4` |
| **Frame rate** | CFR hoac VFR |
| **Hardware encode** | ON (neu co GPU) |

### I2. Loai Phu De

- **Soft subtitle:** The hien khi nguoi xem bat, khong mat chat luong
- **Hard subtitle:** Dot vao frame, mat chat luong nhung tuong thich moi player
- **Bilingual:** Ca goc + dich hien thi cung luc

### I3. Thu Muc Xuat

Mac dinh: `output/` trong thu muc pyVideoTrans

Doi thu muc xuat: Cau hinh trong **Tools > Settings > Output directory**

---

## J - Xu Ly Su Co

### J1. Lỗi "CUDA out of memory"

- Giam kich thuoc model (thay `large-v3` = `medium`)
- Tat diarization
- Tat denoise
- Tat VAD
- Giam batch size trong Advanced Options

### J2. Lỗi "FFmpeg not found"

Pre-packaged da co FFmpeg. Neu gap loi:
- Kiem tra thu muc `ffmpeg/` trong thu muc pyVideoTrans
- Copy `ffmpeg.exe` va `ffprobe.exe` vao thu muc chinh

### J3. Lỗi "Model download failed"

Kiem tra mang, thu lai. Hoac tai model thu cong:
- Hugging Face
- Modelscope

### J4. Lỗi "sp.exe not responding"

- Tat phan mem dien tuyen mang (VPN/proxy)
- Xoa thu muc `__pycache__` trong `_internal`
- Khoi dong lai

### J5. Lỗi "API key invalid"

Kiem tra:
- Key con han su dung
- Quyen truy cap (API permissions)
- Dia chi IP (mot so dich vu gioi han IP)

### J6. Chạy doctor

```batch
scripts\china-vietnam\doctor.bat
```

---

## K - Cap Nhat

### K1. Cap Nhat Len Phien Ban Moi

```batch
scripts\china-vietnam\update.bat
```

Script nay:
1. Sao luu `params.json` hien tai
2. Tai phien ban moi
3. Giai nen
4. Khoi phuc cau hinh

### K2. Kiem Tra Phien Ban

Trong pyVideoTrans: **Help > About**

Hoac doc file: `videotrans/__init__.py`

---

## L - Sao Luu

### L1. Nhung Gi Can Sao Luu

| File/Dir | Muc dich |
|-----------|----------|
| `videotrans/params.json` | Tat ca API keys + cau hinh |
| `f5-tts/*.wav` | File tham chieu voice cloning |
| `output/` | Video da xu ly |
| `logs/` | Log de debug |

### L2. Sao Luu Thủ Cong

Copy thu muc hoac dung script:

```batch
xcopy /E /Y "pyvideotrans-win\videotrans\params.json" "backup\"
xcopy /E /Y "pyvideotrans-win\f5-tts" "backup\f5-tts\"
```

---

## M - Model

### M1. Model ASR

| Model | Kenh | Kich thuoc | Ghi chu |
|-------|------|-----------|---------|
| `tiny` | 0-1 | 39 MB | Nhanh nhat |
| `base` | 0-1 | 74 MB | |
| `small` | 0-1 | 244 MB | |
| `medium` | 0-1 | 769 MB | |
| `large-v3` | 0-1 | 1.5 GB | Chat luong cao nhat |
| `paraformer-zh` | 4 | — | **Tot nhat cho Trung Quoc** |
| `SenseVoiceSmall` | 4 | — | Nhe hon, nhanh hon |

### M2. Model Dich (Neu dung local)

| Model | Kenh | Ghi chu |
|-------|------|---------|
| `qwen:latest` (Ollama) | 9 | Local, mien phi |
| `llama3.2:3b` (Ollama) | 9 | Local, nhe |

### M3. Vi Tri Model

Pre-packaged: Tu dong tai khi can

Source: `~/.cache/huggingface/`, `~/.cache/modelscope/`

---

## N - Ngon Ngu

### N1. Ma Ngon Ngu

| Ma | Ngon ngu |
|----|---------|
| `zh-cn` | Trung Quoc (Phồn thể) |
| `zh-tw` | Trung Quoc (Giản thể) |
| `vi` | Tieng Viet |
| `en` | Tieng Anh |
| `ja` | Tieng Nhat |
| `ko` | Tieng Han |
| `fr` | Tieng Phap |
| `de` | Tieng Duc |

### N2. Chi Tieu Ho tro Tieng Viet

| Tinh nang | Ho tro |
|-----------|--------|
| Nhan dien tieng Viet (ASR) | FunASR, WhisperX, Faster-Whisper |
| Dich sang tieng Viet | DeepSeek, ChatGPT, Gemini, Google, Microsoft |
| TTS tieng Viet | Edge-TTS, Confucius-TTS, F5-TTS, OmniVoice, ElevenLabs, Azure, CosyVoice |
| Phu de tieng Viet | SRT, VTT, ASS |
| Diacritics Viet (ă â ê ô ơ ư đ) | Ho tro day du |

---

## O - Tuy Chinh

### O1. Prompt Dich

Neu dung LLM channel (DeepSeek, ChatGPT, etc.):

Trong **Tools > Advanced Options**, co the dat:
- Prompt cho dich
- Yeu cau giữ ten riêng
- Yeu cau dich tu nhien
- Yeu cau giu cach xuong hô

### O2. Profile Chat Luong

| Che do | ASR | Model | Diarization | TTS |
|--------|-----|-------|------------|-----|
| **Nhanh (Fast)** | FunASR | SenseVoiceSmall | Tat | Edge-TTS |
| **Can bang (Balanced)** | FunASR | paraformer-zh | Bat | Edge-TTS |
| **Chat luong (High)** | FunASR | paraformer-zh | Bat | F5-TTS / CosyVoice |

### O3. Speed Control

- **Audio speed:** Toc do phat am thanh (mac dinh 1.0x)
- **Video speed:** Toc do video (mac dinh 1.0x)
- FFmpeg dieu chinh toc do bang atempo filter

---

## P - Che Do Chat Luong

### P1. Fast (Nhanh)

```
ASR: FunASR SenseVoiceSmall
Diarization: Tat
Translation: DeepSeek (nhanh)
TTS: Edge-TTS
CRF: 23
```

Phu hop: Video ngan, demo, thu nghiem

### P2. Balanced (Can Bang)

```
ASR: FunASR paraformer-zh
Diarization: Bat (2 nguoi noi)
Translation: DeepSeek
TTS: Edge-TTS + vi-VN-HoaiMyNeural
CRF: 20
```

Phu hop:大多数 trường hợp

### P3. High (Chat Luong Cao)

```
ASR: FunASR paraformer-zh (large model)
Diarization: Bat + pyannote
Translation: DeepSeek (model lon hon)
TTS: F5-TTS voice cloning hoac CosyVoice
CRF: 18
BGM: Giu lai
```

Phu hop: Phim, noi dung quan trong

---

## Q - Hoi Dap Thuong Gap

**Q: Tai sao video dau ra khong co am thanh?**
A: Kiem tra lai TTS da duoc cau hinh chua. Thu tab 4 (Dubbing) phai co TTS duoc chon.

**Q: Phu de tieng Viet bi loi font?**
A: Kiem tra ma hoa phu de trong output. Dung UTF-8. Kiem tra font trong ASS subtitle.

**Q: TTS am thanh khong dong bo voi video?**
A: Bat audio alignment trong Advanced Options. Hoac dieu chinh toc do audio speed.

**Q: Lam sao de giu nhac nen?**
A: Trong tab Audio, chon "Preserve BGM" hoac "Vocal separation" = Demucs.

**Q: Co the chay nhieu video cung luc?**
A: Co, trong chế độ batch. Hoặc dùng CLI với vòng lặp.

**Q: Lam sao thay đổi nguoi noi?**
A: Bat Diarization, sau đó trong tab 4, phan bo nguoi noi = nhan vat giong noi khac nhau.

---

## R - Dac Diem Ky Thuat

### R1. FFmpeg

Dùng FFmpeg bundled trong pre-packaged.

Chi tiết output:
- Codec: `libx264` (H.264) hoặc `libx265` (HEVC)
- Container: `mp4` hoặc `mkv`
- Audio: AAC 192kbps
- CRF: 0 (lossless) - 51 (lowest), mac dinh 23

### R2. Vocal Separation

Su dung **Demucs** de tach nhac nen:
- Nhạc nền được giữ lại
- Lời bị loại bỏ/thay thế
- Cách bật: Tab Audio > Vocal Separation > Demucs

### R3. VAD (Voice Activity Detection)

Su dung **ten-vad** built-in de phat hien khi co tieng noi.

### R4. Language Detection

ASR channel FunASR co the tu dong nhan dien tieng Trung.

---

## S - Lenh CLI

### S1. Lenh Co Ban

```bash
# Danh sach nha cung cap
uv run cli.py --list providers

# Danh sach ngon ngu
uv run cli.py --list languages

# Danh sach model Whisper
uv run cli.py --list models
```

### S2. Speech to Text

```bash
uv run cli.py --task stt ^
  --name "video.mp4" ^
  --recogn_type 4 ^
  --source_language_code zh-cn
```

### S3. Subtitle Translation

```bash
uv run cli.py --task sts ^
  --name "subtitle.srt" ^
  --target_language_code vi ^
  --translate_type 5
```

### S4. Text to Speech

```bash
uv run cli.py --task tts ^
  --name "subtitle.srt" ^
  --tts_type 0 ^
  --voice_role "vi-VN-HoaiMyNeural"
```

### S5. Video Translation (Day Du)

```bash
uv run cli.py --task vtv ^
  --name "video.mp4" ^
  --recogn_type 4 ^
  --translate_type 5 ^
  --tts_type 0 ^
  --source_language_code zh-cn ^
  --target_language_code vi ^
  --voice_role "vi-VN-HoaiMyNeural" ^
  --cuda
```

### S6. Video Translation with Diarization

```bash
uv run cli.py --task vtv ^
  --name "video.mp4" ^
  --recogn_type 4 ^
  --translate_type 5 ^
  --tts_type 0 ^
  --source_language_code zh-cn ^
  --target_language_code vi ^
  --voice_role "vi-VN-HoaiMyNeural" ^
  --enable_diariz ^
  --nums_diariz 2 ^
  --cuda
```

### S7. Video Translation with BGM

```bash
uv run cli.py --task vtv ^
  --name "video.mp4" ^
  --recogn_type 4 ^
  --translate_type 5 ^
  --tts_type 0 ^
  --source_language_code zh-cn ^
  --target_language_code vi ^
  --voice_role "vi-VN-NamMinhNeural" ^
  --cuda
  # Giu BGM trong tab Audio cua GUI
```

---

## T - Thuat Ngu

| Thuuat ngu | Giai thich |
|-----------|-----------|
| **ASR** | Automatic Speech Recognition — Nhận diện tiếng nói thành văn bản |
| **TTS** | Text-to-Speech — Tổng hợp văn bản thành giọng nói |
| **STT** | Speech-to-Text — Nhận diện giọng nói (cách gọi khác của ASR) |
| **STS** | Subtitle-to-Subtitle — Dịch phụ đề |
| **VTV** | Video Translate — Dịch video đầy đủ |
| **Diarization** | Phát hiện người nói (speaker 1, speaker 2...) |
| **CRF** | Constant Rate Factor — Thông số chất lượng video (thấp = tốt hơn) |
| **VAD** | Voice Activity Detection — Phát hiện có tiếng nói |
| **BGM** | Background Music — Nhạc nền |
| **VRAM** | Video RAM — Bộ nhớ GPU |
| **CUDA** | NVIDIA GPU compute platform |
| **FFmpeg** | Video/audio processing tool |
| **Soft subtitle** | Phụ đề dạng stream, có thể bật/tắt |
| **Hard subtitle** | Phụ đề đốt cố định vào frame |
| **Bilingual subtitle** | Phụ đề song ngữ |
| **Voice cloning** | Tạo giọng nói mới từ mẫu âm thanh |
| **CRF** | Constant Rate Factor — chất lượng video (0=lossless, 51=thấp nhất) |

---

## Thong Tin Them

- **Docs goc:** https://pyvideotrans.com
- **Forum:** https://bbs.pyvideotrans.com
- **GitHub:** https://github.com/jianchang512/pyvideotrans
- **China-VNE config:** docs/PYVIDEOTRANS_SOURCE_AUDIT.md
