# TROUBLESHOOTING.md

# Troubleshooting pyVideoTrans China -> Vietnam

**Phien ban:** 1.0
**Ap dung cho:** pyVideoTrans v4.11 + China-VNE configuration

---

## 1. Loi Cai Dat

### 1.1 Setup.bat that bai

**Trieu chung:** "Download failed" hoac "Extraction failed"

**Nguyen nhan:**
- Mat mang
- Khong co 7-Zip
- Duong dan co khoang trang hoac ky tu Trung
- File da bi hong

**Giai phap:**

1. Tai thu cong: https://huggingface.co/mortimerme/repocollect/resolve/main/win-pyvideotrans-v4.11.7z
2. Giai nen bang 7-Zip (khong phai Windows built-in):
   - Tai: https://www.7-zip.org/
   - Hoac Bandizip: https://www.bandisoft.com/bandizip/
3. Giai nen vao thu muc KHONG chua ky tu tieng Viet/khoang trang
4. Dam bao `sp.exe` nam trong thu muc giai nen

### 1.2 sp.exe khong khoi dong

**Trieu chung:** Double-click khong co gi xay ra

**Kiem tra:**
- File co bi chan boi antivirus khong?
- Co quyen admin khong?
- Thu muc co can ghi khong?

**Giai phap:**
- Add exception trong antivirus
- Chay voi quyen admin (Run as Administrator)
- Chuyen den thu muc khac (khong phai Program Files)

---

## 2. Loi FFmpeg

### 2.1 "FFmpeg not found"

**Kiem tra:**
```cmd
ffmpeg -version
```

**Neu loi:** Pre-packaged version phai co `ffmpeg.exe` trong thu muc `ffmpeg/` hoac `_internal/`.

**Giai phap:**

1. Kiem tra thu muc:
   ```
   pyvideotrans-win/
     ffmpeg/ffmpeg.exe
     ffmpeg/ffprobe.exe
   ```

2. Neu khong co, copy tu `_internal/`:
   ```cmd
   copy _internal\ffmpeg.exe ffmpeg\ffmpeg.exe
   copy _internal\ffprobe.exe ffmpeg\ffprobe.exe
   ```

3. Hoac tai FFmpeg va PATH:
   - Tai: https://www.gyan.dev/ffmpeg/builds/
   - Giai nen, them vao PATH

### 2.2 "FFmpeg codec not supported"

**Trieu chung:** Loi khi xuat video, codec libx264 hoac libx265 khong co

**Giai phap:**
- Su dung pre-packaged version (da co san codec)
- Cap nhat FFmpeg len phien ban moi nhat

---

## 3. Loi GPU / CUDA

### 3.1 "CUDA out of memory"

**Trieu chung:** Loi khi nhan dien hoac TTS, GPU memory het

**Giai phap:**

1. Su dung model nho hon:
   - Fast-Whisper: `large-v3` → `medium` → `small`
   - FunASR: `paraformer-zh` → `SenseVoiceSmall`

2. Dong cac ung dung GPU khac (Chrome, Photoshop, game)

3. Giam batch size trong Advanced Options

4. Tat diarization (tiet kiem VRAM)

5. CPU fallback (Advanced Options > cuda = off)

### 3.2 "CUDA error: no kernel image is available"

**Nguyen nhan:** GPU khong tuong thich PyTorch

**Giai phap:**
- RTX 50-series: Dat `CUDA compute type` = `float16`
- GPU cu: Su dung pre-packaged version (co torch 2.7 cu128)
- CPU fallback

### 3.3 "NVIDIA driver is too old"

**Trieu chung:** Loi "cudaErrorInsufficientDriver" hoac tuong tu

**Giai phap:**
- Cap nhat driver NVIDIA: https://www.nvidia.com/drivers
- RTX 50-series can driver 570+
- RTX 40-series can driver 525+

### 3.4 Khong co GPU NVIDIA

**Khong phai loi.** pyVideoTrans van hoat dong tren CPU, chi cham hon.

**Benchmark so sanh CPU vs GPU:**
- FunASR large: GPU ~10x nhanh hon CPU
- Edge-TTS: cloud, khong phu thuoc GPU
- DeepSeek: cloud, khong phu thuoc GPU

---

## 4. Loi ASR (Nhan dien tieng noi)

### 4.1 "Recognition failed"

**Kiem tra:**
- File am thanh co ton tai khong?
- Co API key khong (neu su dung cloud)?
- Model da tai chua?

**Giai phap:**
- Chay `setup_done.txt` de xac nhan model da tai
- Thu chuyen sang FunASR (kenh 4) neu khac dang su dung
- Kiem tra log: `videotrans/logs/` de xem chi tiet

### 4.2 Nhan dien sai tieng Viet (khi nguon la Trung)

**Nguyen nhan:** Source language set sai

**Giai phap:** Set `source_language_code = zh-cn`

### 4.3 Nhan dien khong co timestamp

**Kiem tra:** Co su dung faster-whisper hoac FunASR

**Giai phap:**
- WhisperX (kenh 18) cung cap timestamp chi tiet nhat
- FunASR co timestamp san
- faster-whisper cung co

---

## 5. Loi Dich (Translation)

### 5.1 "Invalid API key"

**Kiem tra:**
- Key con han su dung?
- Quyen truy cap (permission)?
- Dia chi IP (mot so dich vu gioi han IP)?

**Giai phap:**
- Test API key truc tiep:
  ```bash
  curl https://api.deepseek.com/v1/chat/completions ^
    -H "Authorization: Bearer YOUR_KEY" ^
    -H "Content-Type: application/json" ^
    -d "{\"model\":\"deepseek-chat\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}],\"max_tokens\":5}"
  ```

### 5.2 "Rate limit exceeded"

**Nguyen nhan:** Qua nhieu request trong thoi gian ngan

**Giai phap:**
- Doi va thu lai
- Su dung dich vu khac (Google, Microsoft mien phi)
- Mua goi tra phi de co rate limit cao hon

### 5.3 Dich sai nghia / Literal translation

**Nguyen nhan:** Prompt dich khong tot

**Giai phap:**

Trong **Tools > Advanced Options > Translation prompt**, dat prompt tot hon:

```
Ban la mot dich gia chuyen nghiep dich phim Trung Quoc sang tieng Viet.

Nguyen tac:
1. Dich tu nhien, giu y nghia goc
2. Giu ten rieng nhat quan (khong dich ten)
3. Giu cach xung ho theo quan he nhan vat
4. Khong tu them noi dung
5. Khong dich literal neu lam cau Viet mat tu nhien

Dau vao: %SRT_TEXT%
```

### 5.4 Ten nhan vat khac nhau giua cac doan

**Nguyen nhan:** Dich theo tung doan doc lap, khong co memory

**Giai phap:**
- Su dung prompt de chi dinh ten nhan vat
- Sua SRT thu cong sau khi dich
- Hoac accept inconsistency

---

## 6. Loi TTS (Text-to-Speech)

### 6.1 "TTS failed"

**Kiem tra:**
- Voice role co ton tai cho ngon ngu vi khong?
- API key (neu can)?
- Ket noi mang (neu su dung cloud)?

**Giai phap:**
- Edge-TTS giong mac dinh:
  - `vi-VN-HoaiMyNeural` (Nu)
  - `vi-VN-NamMinhNeural` (Nam)
- Kiem tra voice role list trong GUI

### 6.2 TTS am thanh khong dong bo

**Trieu chung:** Doan am thanh khong khop voi phu de

**Giai phap:**

1. Bat **Audio Alignment** trong Advanced Options:
   - Su dung atempo filter (FFmpeg)
   - Dieu chinh toc do audio cho khop duration

2. Hoac sua toc do TTS:
   - `voice rate` (1.0x = normal)
   - Tang neu TTS qua nhanh

3. Kiem tra duration cua subtitle khong qua ngan

### 6.3 Giong noi khong ro rang / khong tu nhien

**Nguyen nhan:** Model TTS chat luong thap

**Giai phap:**

| Model | Chat luong | Chi phi | Khuyen nghi |
|-------|-----------|---------|------------|
| Edge-TTS | Tot | Mien phi | Chat luong trung binh-cao |
| Confucius-TTS | Rat tot | Mien phi | Chat luong tot |
| F5-TTS voice clone | Xuất sac | Mien phi | Can 3-10s tham chieu |
| CosyVoice 3 | Xuat sac | Mien phi | Can 16GB+ VRAM |
| ElevenLabs | Xuat sac | Tra phi | $5-$22/thang |
| Azure TTS | Xuat sac | Tra phi | API key Microsoft |

### 6.4 Voice clone khong hoat dong

**Trieu chung:** Giong noi clone khong giong ban goc

**Nguyen nhan:**
- File tham chieu qua ngan (<3s)
- File tham chieu co nhieu
- File tham chieu sai noi dung

**Giai phap:**

- File WAV: 3-10 giay
- Phat am ro, khong nhieu
- Cung noi dung van ban
- Vi tri: `pyvideotrans-win/f5-tts/your_voice.wav`

---

## 7. Loi Phu De (Subtitle)

### 7.1 Phu de tieng Viet bi loi font

**Trieu chung:** Hien thi ? hoac o vuong cho cac ky tu dac biet

**Kiem tra:**
- Ma hoa: UTF-8
- Font: Arial, Tahoma, hoac font Viet Nam

**Giai phap:**
- Trong Advanced Options, dat font mac dinh
- Dung SRT thay vi ASS neu gap loi font

### 7.2 Ky tu tieng Viet (ă â ê ô ơ ư đ) khong hien thi

**Nguyen nhan:** Font khong ho tro Vietnamese

**Giai phap:**
- Font khuyen nghi:
  - Arial Unicode MS
  - DejaVu Sans
  - Noto Sans
  - Be Vietnam Pro

### 7.3 Subtitle timing sai

**Trieu chung:** Subtitle xuat hien qua som hoac qua muon

**Giai phap:**
- Bat **Subtitle alignment**
- Kiem tra duration cua segment am thanh
- Sua SRT thu cong

### 7.4 CPS (Characters per second) qua cao

**Trieu chung:** Subtitle qua nhieu ky tu, kho doc

**Giai phap:**
- Set CPS limit trong Advanced Options (14-18)
- pyVideoTrans se tu chia nho subtitle

---

## 8. Loi Video Output

### 8.1 Video xuat bi lag / mat frame

**Giai phap:**
- Dung codec `libx264` thay vi `libx265` (nhanh hon)
- Giam CRF (23 → 20 → 18)
- Tang preset (medium → fast → ultrafast)
- Su dung hardware encoding (Advanced Options)

### 8.2 Video khong co am thanh

**Kiem tra:**
- TTS co chay thanh cong khong?
- Tuy chon "Embed audio" co bat khong?

**Giai phap:**
- Tab Output > Audio Settings > Embed audio = ON
- Kiem tra tab Dubbing co chon TTS khong

### 8.3 Video xuat rat lon (>1 GB)

**Giai phap:**
- CRF cao hon: 20 → 23
- Codec `libx264` thay vi `libx265`
- Giam resolution (neu can)
- Hardware encoding

### 8.4 Video xuat rat nho (chat luong kem)

**Nguyen nhan:** CRF qua cao

**Giai phap:**
- CRF thap: 18-20 cho chat luong tot
- Bitrate: tu dong theo CRF
- Dung `libx265` cho compression tot hon

---

## 9. Loi Bo Sung

### 9.1 Loi khi chay CLI

**Trieu chung:** "uv not found" hoac "python not found"

**Giai phap:**
- Source deployment can Python 3.10 + uv
- Pre-packaged version khong can Python
- Neu dung source:
  ```bash
  python --version
  uv --version
  ```

### 9.2 Loi mat thoi gian / Crash

**Kiem tra log:** `pyvideotrans-win/logs/` hoac `%TEMP%`

**Giai phap:**
- Restart pyVideoTrans
- Kiem tra disk space
- Tang RAM cho GPU (Advanced Options)
- Xoa `__pycache__`

### 9.3 Loi proxy / Internet

**Trieu chung:** Edge-TTS, DeepSeek, ChatGPT khong truy cap duoc

**Giai phap:**

Trong Advanced Options > Proxy:
```
http://127.0.0.1:7890
```

Hoac su dung cac dich vu trong nuoc:
- Thay Edge-TTS bang Azure TTS (can key)
- Thay DeepSeek bang... DeepSeek (server Trung Quoc, OK)

### 9.4 Loi khi cap nhat (update.bat)

**Trieu chung:** "Backup failed" hoac "Restore failed"

**Giai phap:**
- Chay update.bat voi quyen admin
- Kiem tra quyen ghi thu muc
- Restore thu cong tu backup

---

## 10. Loi cu the voi China -> Vietnamese

### 10.1 Phim co BGM nhieu, ASR nham lan

**Trieu chung:** Nhan dien sai, lang nghe ca phan nhac

**Giai phap:**
- Bat **Vocal separation** (Demucs)
- Tab Audio > Vocal Separation = Demucs
- BGM se bi tach rieng, ASR nhan dien giong noi ro hon

### 10.2 Phim co nhieu nguoi noi

**Trieu chung:** Subtitle thay doi voice role khong nhat quan

**Giai phap:**
- Bat **Diarization**
- Tab STT > Enable Diarization = ON
- Sau do gan voice role cho moi speaker trong Tab TTS

### 10.3 Nhan vat noi gioi / nhan vat noi nho

**Trieu chung:** Doan nho qua, ASR bo qua

**Giai phap:**
- Dam bao VAD (Voice Activity Detection) bat
- Tang sensitivity cua VAD trong Advanced Options
- Sua SRT thu cong

---

## 11. Lien Ket Huu Ich

- **Forum chinh thuc:** https://bbs.pyvideotrans.com
- **Docs:** https://pyvideotrans.com
- **GitHub Issues:** https://github.com/jianchang512/pyvideotrans/issues

Khi bao loi:
- Cung cap pyVideoTrans version
- Cung cap file log
- Mo ta steps reproduce
- Cung cap thong tin he thong (OS, GPU, RAM)
