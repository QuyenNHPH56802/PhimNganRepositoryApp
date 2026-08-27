# MODEL_SETUP_CHINA_VIETNAM.md

# Model Setup for China -> Vietnamese Video Translation

**Phien ban:** 1.0
**Phan mem:** pyVideoTrans v4.11
**Muc dich:** Huong dan tai va cau hinh cac model AI can thiet de dich video Trung -> Viet

---

## Quy Tac Chung

> **Khong dua model vao Git repository.**

Model duoc luu tru:
- Trong cache cua pyVideoTrans
- Trong thu muc `models/` cua pyVideoTrans
- Trong HF cache (`~/.cache/huggingface/`)
- Trong ModelScope cache

Tai rieng theo co che pyVideoTrans.

---

## 1. Model ASR (Nhan dien tieng noi)

### 1.1 FunASR (Khuyen nghi cho tieng Trung)

**Kenh:** 4 (FUNASR_CN)
**Nguon:** Alibaba DAMO Academy
**Model file:** `paraformer-zh` (chat luong) hoac `SenseVoiceSmall` (nhe hon)

**Kich thuoc:**
- `paraformer-zh`: ~2 GB
- `SenseVoiceSmall`: ~300 MB

**Cach tai:**
- Tu dong: Su dung pyVideoTrans, lan dau su dung se tu tai
- Thu cong:
  ```bash
  # Tai tu ModelScope
  python -c "from modelscope import snapshot_download; snapshot_download('iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch', cache_dir='./models')"
  ```

**Yeu cau GPU:** 4GB+ VRAM (khuyen nghi), CPU fallback OK

### 1.2 Faster-Whisper

**Kenh:** 0 (FASTER_WHISPER)
**Nguon:** CTranslate2 port cua OpenAI Whisper
**Model:** `tiny`, `base`, `small`, `medium`, `large-v3`

**Kich thuoc:**
- `tiny`: 39 MB
- `base`: 74 MB
- `small`: 244 MB
- `medium`: 769 MB
- `large-v3`: 1.5 GB

**Cach tai:** Tu dong boi pyVideoTrans

**Yeu cau GPU:** 8GB+ VRAM cho `large-v3`

### 1.3 WhisperX (Co timestamp + diarization)

**Kenh:** 18 (WHISPERX_API)
**Yeu cau:** Deploy local WhisperX service rieng (port 8000)

---

## 2. Model Dich (Translation)

### 2.1 DeepSeek (Khuyen nghi)

**Kenh:** 5 (DEEPSEEK_INDEX)
**API:** OpenAI-compatible
**Model:** `deepseek-chat`, `deepseek-v4-flash`
**Dang ky:** https://platform.deepseek.com/

**Khong can tai model** (la dich vu cloud)

### 2.2 ChatGPT/OpenAI

**Kenh:** 4 (CHATGPT_INDEX)
**API:** OpenAI
**Model:** `gpt-4o-mini`, `gpt-4o`
**Dang ky:** https://platform.openai.com/

### 2.3 Ollama (Local LLM, mien phi)

**Kenh:** 9 (LOCALLLM_INDEX)
**Cai dat:**
```bash
# Tai Ollama
# Windows: https://ollama.com/download/windows
# Hoac:
curl -fsSL https://ollama.com/install.sh | sh

# Tai model (VD)
ollama pull qwen:latest
ollama pull llama3.2:3b
```

**Model khuyen nghi cho Trung -> Viet:**
- `qwen:latest` (4.7 GB) — Tot cho Trung, hop ly tieng Viet
- `llama3.2:3b` (2 GB) — Nhe, trung binh
- `gemma2:9b` (5.4 GB) — Chat luong cao

### 2.4 Google/Microsoft (Mien phi, MT)

**Kenh:** 0 (Google), 1 (Microsoft)
**Khong can API key** (co gioi han)

---

## 3. Model TTS (Text-to-Speech)

### 3.1 Edge-TTS (Mien phi, KHUYEN NGHI)

**Kenh:** 0 (EDGE_TTS)
**Nguon:** Microsoft Edge
**Giong tieng Viet:**
- `vi-VN-HoaiMyNeural` (Nu)
- `vi-VN-NamMinhNeural` (Nam)

**Khong can tai model** (dich vu cloud mien phi)
**Khong can API key**

### 3.2 F5-TTS (Voice cloning, built-in)

**Kenh:** 2 (F5_TTS)
**Model size:** ~1.5 GB
**Ngon ngu ho tro:** zh, en, ja, it, de, fr, ru, hi, es, ar, tr, **vi**

**Tham chieu am thanh:**
- Dat file `.wav` 3-10 giay vao `f5-tts/`
- Phat am ro rang, khong nhieu nen
- Cung noi dung van ban

**VD:**
```
pyvideotrans-win/f5-tts/
  my_vietnamese_voice.wav    # Tham chieu giong noi
```

**Cach su dung:**
- Trong GUI: Chon F5-TTS, voice role = `clone`
- pyVideoTrans se tu dong su dung tham chieu trong `f5-tts/`

### 3.3 Confucius4-TTS (Built-in, multi-language)

**Kenh:** 4 (CONFUCIUS_TTS)
**Model size:** ~2 GB
**Ngon ngu ho tro:** zh, en, ja, ko, de, fr, th, pt, ru, ms, **vi**

### 3.4 OmniVoice (Built-in, 600+ languages)

**Kenh:** 3 (OMNIVOICE_TTS)
**Model size:** ~3 GB
**Voice cloning:** Co

### 3.5 CosyVoice 3 (Chat luong cao, can deploy)

**Kenh:** 14 (COSYVOICE_TTS, local API)
**Deploy:** GitHub - FunAudioLLM/CosyVoice
**Port:** 8000
**Model:** 3s voice cloning
**VRAM:** 16GB+

---

## 4. Model Diarization (Speaker detection)

### 4.1 pyannote-audio

**Yeu cau:** HuggingFace token
**Lay token:** https://huggingface.co/settings/tokens
**Chap nhan EULA:** https://huggingface.co/pyannote/segmentation-3.0

**Thiet dat:**
1. Lay HF token
2. Dat vao bien moi truong:
   ```cmd
   set HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
   ```
3. Trong pyVideoTrans Advanced Options, nhap token

### 4.2 Ali CAM++

Built-in trong pyVideoTrans v4.11. Khong can tai them.

---

## 5. Cache va Restore

### 5.1 Vi tri Model Cache

**Windows:**
```
%USERPROFILE%\.cache\huggingface\
%USERPROFILE%\.cache\modelscope\
```

**pyVideoTrans:**
```
pyvideotrans-win/models/
pyvideotrans-win/_internal/models/
```

### 5.2 Xoa Cache

```cmd
# Xoa HF cache
rmdir /s /q %USERPROFILE%\.cache\huggingface

# Xoa ModelScope cache
rmdir /s /q %USERPROFILE%\.cache\modelscope
```

### 5.3 Sao Luu Model

Model thuong nang (>1 GB), nen luu o o cung rieng:

```cmd
xcopy /E /Y %USERPROFILE%\.cache\huggingface D:\backup\models\
```

---

## 6. Cai Dat GPU

### 6.1 CUDA 12.8

**Tai:** https://developer.nvidia.com/cuda-12-8-0-download-archive

### 6.2 cuDNN 9.11

**Tai:** https://developer.nvidia.com/cudnn

### 6.3 Kiem Tra

```cmd
nvidia-smi
```

Expected output:
```
+-------------------------------------------------------------------------+
| NVIDIA-SMI 5xx.xx       Driver Version: 5xx.xx    CUDA Version: 12.8   |
| GPU Name                  Memory  |    GPU-Util      |
| RTX 4080               16384 MiB  |    0%            |
+-------------------------------------------------------------------------+
```

### 6.4 Cai Dat PyTorch CUDA

```cmd
# Tao moi truong ao
uv sync

# Cai torch CUDA
uv remove torch torchaudio
uv add torch==2.7 torchaudio==2.7 --index-url https://download.pytorch.org/whl/cu128
uv add nvidia-cublas-cu12 nvidia-cudnn-cu12
```

### 6.5 RTX 50-Series

**Quan trong:** RTX 5090/5080 khong ho tro `int8` cuBLAS.

Vao pyVideoTrans **Tools > Advanced Options > CUDA compute type** = `float16`

---

## 7. Model Khuyen Nghi Theo Che Do

### Fast (Nhanh, demo)

```
ASR: FunASR SenseVoiceSmall (300 MB)
Translation: Google Translate (free) hoac DeepSeek
TTS: Edge-TTS vi-VN-HoaiMyNeural (free)
VRAM: 4GB (neu GPU)
```

### Balanced (Can bang, khuuyen nghi)

```
ASR: FunASR paraformer-zh (2 GB)
Translation: DeepSeek deepseek-chat
TTS: Edge-TTS vi-VN-HoaiMyNeural
Diarization: Built-in
VRAM: 8GB
```

### High (Chat luong cao, phim)

```
ASR: FunASR paraformer-zh (2 GB)
Translation: DeepSeek deepseek-chat voi prompt chi tiet
TTS: F5-TTS voice cloning hoac CosyVoice 3
Diarization: pyannote-audio
VRAM: 16GB+
```

---

## 8. Thu Tu Tai Model

Khi chay pyVideoTrans lan dau tien voi mot project China -> Vietnam:

1. **FunASR models** (auto, ~2 GB, vai phut)
2. **Edge-TTS voices** (auto, khong can tai)
3. **DeepSeek** (cloud, khong can tai)
4. **F5-TTS** (neu su dung voice clone, ~1.5 GB)
5. **pyannote** (neu su dung, can HF token)

**Tong cache cho balanced profile:** ~3.5 GB

---

## 9. Troubleshooting Model

### 9.1 "Model download failed"

- Kiem tra ket noi internet
- Dat proxy neu can:
  ```
  HF_ENDPOINT=https://hf-mirror.com
  ```
  Hoac:
  ```
  MODELSCOPE_CACHE=D:\models
  ```

### 9.2 "Out of memory" GPU

- Chuyen sang CPU mode (Advanced Options > cuda = off)
- Su dung model nho hon
- Dong cac GPU-intensive app khac

### 9.3 "Model not found"

- Kiem tra cache da ton tai
- Restart pyVideoTrans
- Xoa cache va tai lai

### 9.4 "HF token invalid"

- Token con han khong?
- Da chap nhan EULA cho model pyannote chua?
- Token co quyen doc (read)?

---

## 10. Lien Ket

- **pyVideoTrans:** https://github.com/jianchang512/pyvideotrans
- **DeepSeek:** https://platform.deepseek.com/
- **OpenAI:** https://platform.openai.com/
- **Ollama:** https://ollama.com/
- **HuggingFace:** https://huggingface.co/
- **ModelScope:** https://www.modelscope.cn/
- **FunASR:** https://github.com/modelscope/FunASR
- **F5-TTS:** https://github.com/SWivid/F5-TTS
- **CosyVoice:** https://github.com/FunAudioLLM/CosyVoice
- **pyannote:** https://github.com/pyannote/pyannote-audio
