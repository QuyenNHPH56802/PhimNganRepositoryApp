# pyVideoTrans Adoption Plan

**Source:** [jianchang512/pyvideotrans](https://github.com/jianchang512/pyvideotrans)
**GitHub:** 18,813 stars · GPL v3
**Latest Release:** v4.11 (2026-08-23)
**Source version:** 4.05 (in-progress, `pyproject.toml`)

---

## Source Repository Audit

### Basic Info

| Item | Value |
|------|-------|
| Python | `>=3.10, <3.11` (recommended: 3.10) |
| Package manager | `uv` (recommended), also `pip` |
| License | GPL v3 |
| Pre-packaged Windows | `.exe` / `.7z` bundle (~2.7 GB, no Python needed) |
| Download mirrors | Baidu Netdisk, Hugging Face |

### Entry Points

pyVideoTrans has three interfaces:

| Interface | Command | Port | Notes |
|-----------|---------|------|-------|
| **GUI** (Desktop) | `uv run sp.py` or double-click `sp.exe` | N/A | Qt6-based, full featured |
| **CLI** | `uv run cli.py [args]` | N/A | Automatable, batch-friendly |
| **WebUI** (Browser) | `uv sync --extra webui && uv run webui.py` | `7860` | Gradio-based, remote access |
| **Docker** | `docker build / docker run` | `7860` | GPU-enabled container |

### CLI Tasks

```bash
uv run cli.py --task <task> [options]
```

| Task | Description |
|------|-------------|
| `vtv` | **Video Translate** — full pipeline (ASR → translate → TTS → merge) |
| `stt` | **Speech To Text** — audio/video → subtitle |
| `sts` | **Subtitle Translate** — existing SRT → translated SRT |
| `tts` | **Text To Speech** — subtitle → dubbed audio |

List utilities:
```bash
uv run cli.py --list languages   # View all language codes
uv run cli.py --list providers   # View all service channels
uv run cli.py --list models      # View faster-whisper models
```

---

## ASR (Speech Recognition) — 9+ Providers

**Location:** `videotrans/api/_recognition/`

| # | Channel | Type | GPU | Notes |
|---|---------|------|-----|-------|
| 0 | **faster-whisper** | Built-in (local) | Yes | Default, fast + accurate |
| 1 | **openai-whisper** | Built-in (local) | Yes | Higher accuracy, slower |
| 2 | **FunASR** | Built-in (local) | Yes | Alibaba DAMO Academy — **excellent for Chinese** |
| 3 | **Qwen-ASR** | Built-in (local) | Yes | Alibaba open-source, excellent for Chinese |
| 4 | Whisper.cpp | Win built-in, manual on macOS/Linux | Yes | Native binary |
| 5 | Firered Chinese | Built-in | No | Chinese + 20 dialects |
| 6 | Dolphin | Built-in | No | 40+ Asian languages |
| 7 | Omnilingual ASR | Built-in | No | 1,600+ languages |
| 8 | parakeet Japanese | Built-in | No | Japanese only |
| — | WhisperX | LocalAPI (manual) | Yes | Timestamp + diarization |
| — | Parakeet | LocalAPI (manual) | Yes | Timestamp + diarization |
| — | STT (Custom) | LocalAPI / Custom | — | Your own STT endpoint |
| — | Huggingface_ASR | Built-in | — | HF Hub models |

**Best for Chinese:** FunASR `paraformer-zh` (recommended), FunASR `SenseVoiceSmall` (lightweight)

**Faster-Whisper model sizes:** `tiny`, `base`, `small`, `medium`, `large-v3`

### ASR CLI Example

```bash
uv run cli.py --task stt --name "video.mp4" --model_name large-v3 --cuda
```

---

## Translation — 10+ Channels

**Location:** `videotrans/api/_translate/`

### AI LLM Translation (context-aware, natural)

| Channel | Notes |
|---------|-------|
| **DeepSeek** | Standalone since v3.74, OpenAI-compatible, supports "Deep Thinking" |
| **ChatGPT / OpenAI** | Full OpenAI model support, relay/third-party OK |
| **Claude** | Anthropic Claude models |
| **Gemini** | Google Gemini |
| **MiniMax AI** | MiniMax M3 LLM, OpenAI-compatible |
| **OpenAI Compatible / Local Model** | Any OpenAI-API-compatible (Ollama, LM Studio, Moonshot, etc.) |
| **LiteLLM** | Unified LLM interface, added in v4.11 |
| **Custom Translation API** | Your own endpoint |

### Traditional Machine Translation

| Channel | Free? | Notes |
|---------|-------|-------|
| **Google Translate** | Yes (free tier) | Needs proxy in mainland China |
| **Microsoft Translator** | Yes (free tier) | No proxy needed, rate-limited |
| **DeepL** | Paid | DeepLX also supported |
| **Baidu Translate** | Paid | No proxy needed (China) |
| **Tencent Translate** | Paid | No proxy needed (China) |
| **Alibaba MT** | Paid | Alibaba Machine Translation |
| **302.AI** | Paid | Third-party relay aggregator |

### Local Offline Translation

| Channel | Notes |
|---------|-------|
| **Ollama** | Local LLM, e.g. `qwen:latest`, `llama3.2:3b` |
| **M2M100** | Built-in, fully offline neural MT |
| **Hy-MT2** | Built-in, Tencent Hunyuan local model |
| **Alibaba Bailian** | Alibaba Qwen models via Bailian API |

---

## TTS (Text-to-Speech) — 34 Providers

**Location:** `videotrans/api/tts/`

### Free / Built-in

| Channel | Languages | Clone | GPU | Notes |
|---------|-----------|-------|-----|-------|
| **Edge-TTS** | All | No | N/A | Microsoft free API, **default recommended** |
| **gTTS** | Many | No | N/A | Google TTS, basic quality |
| **Qwen3-TTS** | zh, en, ja, ko, de, fr, ru, pt, es, it | Yes | Yes | Alibaba open-source |
| **F5-TTS** | zh, en, ja, fr, de, ru, it, es, hi, ar | Yes | Yes | Built-in since v4.04, voice cloning |
| **OmniVoice-TTS** | 600+ | Yes | Yes | Built-in since v4.05 |
| **Confucius-TTS** | zh, en, ja, ko, de, fr, es, id, it, th, pt, ru, ms, **vi** | Yes | Yes | Built-in since v4.06, **Vietnamese included** |
| **ChatterBox** | 20+ | Yes | Yes | Resemble AI |
| **MOSS-TTS-Nano** | Multi | Yes | Yes | Fudan MOSS project |
| **Piper** | Multi | No | No | Lightweight local |
| **VITS** | Chinese | No | No | Built-in |
| **SuperionTTS** | Multi | Yes | Yes | Built-in |
| **ChatTTS** | zh, en | No | Yes | High-quality open-source |

### Deployable Voice Cloning Services

| Channel | Languages | Clone | API Port | Notes |
|---------|-----------|-------|----------|-------|
| **GPT-SoVITS** | zh, en, ja, ko, yue | Yes | 9880 | Separate deployment |
| **CosyVoice3** | zh, en, ja, ko, yue | Yes | 8000 | Alibaba Tongyi, 3s cloning |
| **F5-TTS** (ext) | zh, en | Yes | 5010 | Extended language models |
| **Index-TTS** | zh, en | Yes | — | |
| **VoxCPM-TTS** | 27+ incl. vi | Yes | — | |
| **Spark-TTS** | zh, en | Yes | — | ByteDance |

### Paid Online API

| Channel | Notes |
|---------|-------|
| **OpenAI TTS** | 9 voice styles |
| **Azure TTS** | More voices than Edge, better quality |
| **ElevenLabs** | High-quality voice cloning API |
| **Deepgram** | Speech synthesis API |
| **Google Cloud TTS** | GCP text-to-speech |
| **MiniMax TTS** | MiniMax voice synthesis |
| **302.AI** | Third-party relay (works in China) |

### Vietnamese TTS Options

For Chinese → Vietnamese, the following work natively for Vietnamese:

| Rank | Option | Cost | Quality | Setup |
|------|--------|------|---------|-------|
| 1 | **Edge-TTS** (`vi-VN-HoaiMyNeural`, `vi-VN-NamMinhNeural`) | Free | Good | No setup |
| 2 | **Confucius-TTS** (built-in, v4.06+) | Free | Good | Built-in |
| 3 | **ElevenLabs** | Paid | Excellent | `ELEVENLABS_API_KEY` |
| 4 | **Azure TTS** | Paid | Excellent | `AZURE_TTS_KEY` |
| 5 | **CosyVoice3** (local) | Free | Excellent | 16GB VRAM |

---

## Speaker Diarization

**Location:** `videotrans/api/prepare_audio.py`

Supported backends:

| Backend | Type | Notes |
|---------|------|-------|
| **Built-in** | Local model | Default |
| **Ali CAM++** | Local model | Alibaba speaker verification |
| **pyannote-audio** | Local model | Requires HuggingFace token |
| **reverb** | Simple | Basic reverb-based |

CLI flags:
```bash
--enable_diariz              # Enable diarization
--nums_diariz -1             # Auto-detect speaker count
--enable_diariz --nums_diariz 2  # Force 2 speakers
```

---

## Voice Cloning

Multiple integration paths:

| Method | Cloning Time | How |
|--------|-------------|-----|
| **F5-TTS** (built-in v4.04) | 3–10s reference | Place WAV in `f5-tts/` folder, use `clone` voice role |
| **CosyVoice3** | 3s reference | Supports "clone character" (auto-clone from original video) |
| **GPT-SoVITS** | Separate deploy | Deploy api_v2.py on port 9880, use `clone` voice role |
| **OmniVoice** | Built-in | 600+ languages |
| **Confucius-TTS** | Built-in | Vietnamese included |
| **Qwen3-TTS** | Built-in | Chinese + multilingual |

Reference audio requirements:
- Format: WAV (recommended), MP3 acceptable
- Duration: 3–10 seconds ideal
- Content: Clear pronunciation, no background noise
- Location: `f5-tts/` folder under pyVideoTrans root

---

## Subtitle Formats

| Format | Read | Write | Edit | Notes |
|--------|------|-------|------|-------|
| **SRT** | Yes | Yes | Yes | Primary format |
| **VTT** | Yes | Yes | Yes | WebVTT for web |
| **ASS** | Yes | Yes | Yes | Full style control |

Subtitle embedding types:
- **No Subtitles** — audio only
- **Hard Subtitles** — burned into video (re-encoding)
- **Soft Subtitles** — subtitle stream, toggleable (lossless possible)
- **Bilingual Hard Subtitles** — original + translated burned in
- **Bilingual Soft Subtitles** — dual-language track, toggleable

---

## Audio / Video Processing

**Input formats:** `mp4`, `mov`, `avi`, `mkv`, `webm`, `mpeg`, `ogg`, `mts`, `ts`
**Audio input:** `wav`, `mp3`, `m4a`, `flac`, `ogg`

Audio processing features:
- Vocal separation (Demucs-based, preserves BGM)
- Denoise / noise reduction
- Punctuation restoration
- Audio speed-up (up to 100x)
- Video slowdown (up to 10x)
- VAD (Voice Activity Detection) via `ten-vad`
- BGM mixing with dubbed audio
- Batch audio extraction

Video output:
- Codecs: `libx264` (H.264, compatibility) or `libx265` (HEVC, compression)
- Formats: `mp4`, `mkv`
- CRF: 0 (lossless) to 51 (lowest), default 23, recommended 18-20
- Presets: `ultrafast` → `veryslow`
- Hardware encoding preferred, CUDA video decode
- Custom FFmpeg arguments supported

---

## GPU Support

| GPU Type | Support | Requirements |
|----------|---------|--------------|
| **NVIDIA GPU (CUDA)** | Full | CUDA 12.8 + cuDNN 9.11, NVIDIA driver, PyTorch cu128 |
| **NVIDIA RTX 50-series** | Full | CUDA 12.8, driver 570-open (open kernel), PyTorch 2.7+ |
| **AMD GPU** | Limited | Whisper.NET supports AMD |
| **Apple Silicon (MPS)** | Partial | PyTorch macOS CPU wheel |
| **CPU only** | Fallback | Works without GPU, slower |

VRAM recommendations:
- faster-whisper `large-v3`: 8GB+
- FunASR models: 4GB+ (GPU recommended)
- CosyVoice / GPT-SoVITS: 16GB+ recommended

RTX 50-series note: RTX 5090/5080 do not support `int8` auto cuBLAS — set `CUDA compute type` to `float16` in Menu → Tools → Advanced Options.

---

## Chinese → Vietnamese Direction

**Fully supported.** Source `zh-cn` (Simplified Chinese) → target `vi` (Vietnamese).

### CLI Full Pipeline Example

```bash
uv run cli.py \
  --task vtv \
  --name "video.mp4" \
  --source_language_code zh-cn \
  --target_language_code vi \
  --voice_role "vi-VN-NamMinhNeural" \
  --cuda
```

Vietnamese Edge-TTS voice roles:
- `vi-VN-NamMinhNeural` (Male)
- `vi-VN-HoaiMyNeural` (Female)

### CLI Subtitle Translation Only

```bash
uv run cli.py \
  --task sts \
  --name "video.srt" \
  --target_language_code vi
```

---

## Configuration Mechanism

**Config file:** `videotrans/params.json` (shared by GUI, WebUI, CLI)

Key configurable areas:

| Category | Options |
|----------|---------|
| **Translation** | Channel, language codes, AI thinking mode, send full SRT for context |
| **ASR** | Channel (0–8+), model, language detection, GPU, denoise, diarization |
| **Dubbing** | TTS channel, voice role, clone role, audio speed, video speed |
| **Video output** | CRF (0–51), preset, codec (264/265), format, CFR/VFR, HW encoding |
| **Advanced** | Compute type (int8/float16/float32), beam size, proxy URL, prompts |

---

## Key Dependencies

**AI/ML:** `torch==2.7.1`, `torchaudio==2.7.1`, `faster-whisper`, `funasr==1.3.1`, `modelscope==1.34.0`, `transformers>=5.3.0`, `pyannote-audio`, `ten-vad>=1.0.6.8`, `edge-tts`, `chatterbox-tts>=0.1.7`, `f5-tts`, `qwen-tts-pvt`, `qwen-asr-pvt`, `omnivoice`, `litellm>=1.85.0,<2.0`

**Video/Audio:** `ffmpeg-python==0.2.0`, `imageio-ffmpeg==0.4.9`, `av==16.0.1`, `pydub==0.25.1`, `librosa==0.11.0`, `soundfile==0.13.1`, `demucs`

**UI:** `pyside6==6.9.2`, `qdarkstyle==3.2.3`, `gradio>=6.8.0`

**Translation APIs:** `deepl==1.18.0`, `dashscope`, `google-api-python-client==2.128.0`, `openai`, `elevenlabs`, `tencentcloud-sdk-python-tmt==3.0.1032`

**Subtitles:** `srt==3.5.2`, `WeTextProcessing`, `pytsmod>=0.3.8`, `pyrubberband>=0.4.0`

---

## Source Directories

```
videotrans/
├── api/
│   ├── _recognition/       # ASR implementations (9+ channels)
│   ├── _translate/         # Translation implementations (10+ channels)
│   ├── tts/                # TTS implementations (34 channels)
│   ├── dubbing/            # Dubbing orchestration
│   ├── prepare_audio.py    # Vocal separation, denoise, VAD, diarization
│   ├── converter/          # Format conversion
│   └── video_edit/         # Video compositing, subtitle embedding
├── sp.py                   # GUI entry point
├── cli.py                  # CLI entry point
├── webui.py               # WebUI entry point
└── params.json             # Shared configuration
```

---

## Windows Pre-packaged Distribution

pyVideoTrans offers a pre-packaged Windows `.exe` / `.7z` bundle (~2.7 GB) that includes:
- Python runtime
- All dependencies
- FFmpeg
- Pre-downloaded models
- No manual Python/dependency installation required

This is the recommended path for non-technical Windows users.

---

## Decision: Source vs Fork

For the China-VNE distribution, the recommended approach is:

> **Use pyVideoTrans as-is (upstream), configure for China → Vietnam, add Windows automation scripts.**

Do NOT create a deep fork unless a customization cannot be achieved through configuration. See `MIGRATION_FROM_CUSTOM_PLATFORM.md` for the full analysis.
