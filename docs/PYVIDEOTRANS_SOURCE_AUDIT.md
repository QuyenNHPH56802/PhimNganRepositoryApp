# pyVideoTrans Source Code Audit

**Source:** [github.com/jianchang512/pyvideotrans](https://github.com/jianchang512/pyvideotrans)
**Cloned to:** `C:\Users\Administrator\Downloads\App\pyvideotrans-src\pyvideotrans`
**Version (package):** `4.05` (in `pyproject.toml`)
**Version (runtime):** `v4.11` (in `videotrans/__init__.py`)
**License:** GPL v3
**Python:** `>=3.10, <3.11` (pinned via `.python-version` = `3.10.19`)
**Package manager:** `uv`

---

## 1. Repository Layout (actual)

```
pyvideotrans/
├── cli.py                    # CLI entry point (26KB, argparse)
├── sp.py                     # GUI entry point (PySide6 / Qt6)
├── webui.py                  # WebUI entry point (Gradio)
├── pyproject.toml            # Project manifest (uv-managed)
├── uv.lock                   # Locked dependencies (665KB)
├── .python-version           # 3.10.19
├── Dockerfile                # WebUI Docker image
├── update_ffmpeg.bat         # Windows FFmpeg updater
├── ffmpeg/                   # Bundled FFmpeg binaries
├── f5-tts/                   # Reference audio for F5-TTS cloning
├── videotrans/               # Main package
│   ├── __init__.py           # VERSION = v4.11, ChannelProvider class
│   ├── recognition/          # 28 ASR provider modules
│   ├── translator/           # 33 translation modules + registry
│   ├── tts/                  # 40+ TTS modules
│   ├── configure/            # Settings (config.py, settings.py)
│   ├── component/            # Shared UI components
│   ├── confuciustts/         # Confucius4-TTS integration
│   ├── external/             # External API wrappers
│   ├── language/             # zh.json / en.json i18n + lang codes
│   ├── mainwin/              # Main window (Qt)
│   ├── mosstts/              # MOSS-TTS integration
│   ├── moss_transcribe_diarize/  # MOSS diarization
│   ├── process/              # Background processing
│   ├── prompts/              # Translation prompts
│   ├── styles/               # UI styles (QSS)
│   ├── task/                 # Background task runners
│   ├── ui/                   # UI widgets
│   ├── util/                 # Helpers (hello, helpers, mylist)
│   ├── voicejson/            # Voice role JSON registry
│   └── winform/              # Sub-windows (settings, source lang, etc.)
├── f5-tts/                   # Voice clone reference audio
└── docs/                     # architecture.md, cli.md, faq.md, webui.md, etc.
```

> **Note:** The audit found that `videotrans/api/` subdir (mentioned in Phase 0 doc) does **not** exist. Modules live directly in `videotrans/{recognition,translator,tts}/`.

---

## 2. Entry Points

### CLI (`cli.py`)

**Argparse groups:** `stt_group`, `tts_group`, `trans_group`, `common_group`

**Key arguments (from source):**

| Argument | Default | Purpose |
|----------|---------|---------|
| `--task` | (required) | `stt` (STT), `tts` (TTS), `sts` (Subtitle Trans), `vtv` (Video Trans) |
| `--name` | None | Absolute path to input file (mp4, wav, srt, etc.) |
| `--recogn_type` | `0` | ASR channel index |
| `--tts_type` | `0` | TTS channel index |
| `--translate_type` | `0` | Translation channel index |
| `--source_language_code` | None | e.g. `zh-cn` |
| `--target_language_code` | None | e.g. `vi` |
| `--model_name` | `tiny` | Whisper model: tiny, base, small, medium, large-v3 |
| `--cuda` | False | Enable GPU |
| `--enable_diariz` | False | Speaker diarization |
| `--nums_diariz` | `-1` | Speaker count (-1 = auto) |
| `--voice_role` | None | TTS voice role (e.g. `vi-VN-NamMinhNeural`) |
| `--output_dir` | `_video_out/` | Output directory |
| `--log-level` | WARNING | DEBUG/INFO/WARNING/ERROR |
| `--list` | None | List `providers`/`languages`/`models` |

**CLI Example for China → Vietnam:**
```bash
uv run cli.py --task vtv --name "./video.mp4" \
  --source_language_code zh-cn \
  --target_language_code vi \
  --recogn_type 4 \
  --translate_type 5 \
  --tts_type 0 \
  --voice_role "vi-VN-NamMinhNeural" \
  --enable_diariz \
  --nums_diariz -1 \
  --cuda
```

### GUI (`sp.py`)

- PySide6 (Qt6) desktop application
- Main window in `videotrans/mainwin/`
- StartWindow (splash screen) → MainWindow
- Supports tabbed workflow: 1) Source video, 2) STT, 3) Translate, 4) TTS, 5) Output

### WebUI (`webui.py`)

- Gradio-based, default port `7860`
- Optional install: `uv sync --extra webui`
- Has persistent volumes (`./data/output`, `./data/config`)

---

## 3. Channel Indices (from source)

### ASR Channels (`videotrans/recognition/__init__.py`)

| Index | Name | Type | Notes |
|-------|------|------|-------|
| `0` | `FASTER_WHISPER` | Built-in | Default, fast |
| `1` | `OPENAI_WHISPER` | Built-in | Higher accuracy |
| `4` | `FUNASR_CN` | Built-in | **Best for Chinese** (Alibaba DAMO) |
| `5` | `FIREREDASR` | Built-in | Chinese + dialects |
| `6` | `DOLPHIN` | Built-in | 40 Asian languages |
| `8` | `Omnilingual` | Built-in | 1,600+ languages |
| `10` | `OPENAI_API` | Cloud | OpenAI STT API |
| `11` | `QWENASR` | Built-in | Qwen-ASR local |
| `12` | `QWEN3ASR` | Cloud | Ali Qwen3-ASR (Alibaba Cloud) |
| `16` | `Whisper_CPP` | Local | Whisper.cpp |
| `18` | `WHISPERX_API` | LocalAPI | WhisperX (timestamps + diarization) |
| `22` | `MOSS_DIARIZE` | Built-in | MOSS Diarize |

**Allowed model changes:** `[0, 1, 4, 16, 11, 18, 22, ...]` (Faster-Whisper, OpenAI, FunASR, Qwen-ASR, Whisper.cpp, WhisperX, MOSS, Deepgram, HuggingFace)

### Translation Channels (`videotrans/translator/_constants.py`)

| Index | Constant | Type |
|-------|----------|------|
| `0` | `GOOGLE_INDEX` | MT (free) |
| `1` | `MICROSOFT_INDEX` | MT (free) |
| `2` | `M2M100_INDEX` | Local offline |
| `3` | `HYMT2_INDEX` | Local (Tencent Hunyuan) |
| `4` | `CHATGPT_INDEX` | AI LLM |
| `5` | `DEEPSEEK_INDEX` | AI LLM |
| `6` | `GEMINI_INDEX` | AI LLM |
| `7` | `ZHIPUAI_INDEX` | AI LLM |
| `8` | `AZUREGPT_INDEX` | AI LLM |
| `9` | `LOCALLLM_INDEX` | Local LLM (Ollama) |
| `10` | `OPENROUTER_INDEX` | AI LLM |
| `11` | `SILICONFLOW_INDEX` | AI LLM |
| `12` | `AI302_INDEX` | AI LLM |
| `13` | `QWENMT_INDEX` | Alibaba Qwen-MT |
| `14` | `ZIJIE_INDEX` | VolcEngine |
| `15` | `XIAOMI_INDEX` | Xiaomi |
| `16` | `MINIMAX_INDEX` | MiniMax M3 LLM |
| `17` | `CAMB_INDEX` | CAMB |
| `18` | `DEEPL_INDEX` | MT (paid) |
| `19` | `DEEPLX_INDEX` | DeepL relay |
| `20` | `BAIDU_INDEX` | MT (China-friendly) |
| `21` | `ALI_INDEX` | Alibaba MT (China-friendly) |
| `22` | `LIBRE_INDEX` | LibreTranslate |
| `23` | `TENCENT_INDEX` | MT (China-friendly) |
| `24` | `TRANSAPI_INDEX` | Custom API |
| `25` | `LITELLM_INDEX` | Unified LLM |

### TTS Channels (`videotrans/tts/__init__.py`)

| Index | Name | Type | Vietnamese Support |
|-------|------|------|------|
| `0` | `EDGE_TTS` | Free (Microsoft) | **Yes** (`vi-VN-HoaiMyNeural`, `vi-VN-NamMinhNeural`) |
| `2` | `F5_TTS` | Built-in (v4.04+) | Yes (zh, ja, it, en, de, fr, ru, hi, es, ar, tr, **vi**) |
| `3` | `OMNIVOICE_TTS` | Built-in | Yes (600+ languages) |
| `4` | `CONFUCIUS_TTS` | Built-in (v4.06+) | **Yes** (zh, en, ja, ko, de, fr, th, ...) |
| `8` | `CHATTERBOX_TTS` | Built-in | No |
| `13` | `GPTSOVITS_TTS` | LocalAPI | No (zh/en/ja/ko/yue) |
| `27` | `CHATTTS` | LocalAPI | No (zh/en) |

---

## 4. Configuration

**Config file:** `videotrans/params.json` (runtime-generated, user-editable)

**Settings categories:**
- API keys per provider
- Default ASR/Translation/TTS channels
- Default model names
- CUDA compute type (int8/float16/float32)
- Default source/target language codes
- Edge-TTS voice roles
- BGM / vocal separation settings
- CRF and video encoding presets
- Proxy URLs

---

## 5. Language Codes

**From `videotrans/language/en.json`:**

| Code | Language |
|------|----------|
| `zh` | Chinese |
| `zh-cn` | Simplified Chinese |
| `zh-tw` | Traditional Chinese |
| `vi` | Vietnamese |

Both `zh-cn` → `vi` translations are confirmed supported.

---

## 6. Dependencies (highlights from `pyproject.toml`)

**Core ML:**
- `torch==2.7.1`, `torchaudio==2.7.1` (CUDA 12.8 wheels for win/linux, CPU for macOS)
- `transformers==5.6.0` (overridden)
- `faster-whisper`, `openai-whisper>=20250625`
- `funasr==1.3.1`, `modelscope==1.34.0`
- `pyannote-audio`, `pyannote-audio`
- `qwen-asr-pvt`, `qwen-tts-pvt`
- `f5-tts==1.1.20`
- `omnivoice`, `chatterbox-tts==0.1.7`

**API:**
- `openai`, `elevenlabs`, `dashscope`, `deepl==1.18.0`
- `google-api-python-client==2.128.0`, `google-cloud-texttospeech==2.27.0`
- `azure-cognitiveservices-speech`
- `tencentcloud-sdk-python-tmt==3.0.1032`
- `litellm>=1.85.0,<2.0`
- `google-genai`

**UI:**
- `pyside6==6.9.2`, `qdarkstyle==3.2.3`
- `gradio>=6.8.0` (WebUI extra)

**Media:**
- `av==16.0.1` (PyAV), `ffmpeg-python==0.2.0`
- `imageio-ffmpeg==0.4.9`, `pydub==0.25.1`
- `librosa==0.11.0`, `soundfile==0.13.1`
- `demucs`

**Special Windows-only:**
- `pynini` from `pynini-windows-wheels` GitHub release
- `pythonnet ; sys_platform == 'win32'`

---

## 7. Source Directories Mapping to China-VNE Pipeline

| pyVideoTrans Module | Purpose | China → Vietnam Use |
|---------------------|---------|---------------------|
| `videotrans/recognition/_funasr.py` | FunASR (Alibaba Chinese) | Primary ASR for Chinese |
| `videotrans/recognition/_qwen3asr.py` | Qwen3-ASR (Alibaba Cloud) | Alternative Chinese ASR |
| `videotrans/recognition/_whisperx.py` | WhisperX (timestamps + diarization) | Speaker-aware transcription |
| `videotrans/translator/_deepseek.py` | DeepSeek translation | Primary translation |
| `videotrans/translator/_chatgpt.py` | ChatGPT/OpenAI | Alternative |
| `videotrans/translator/_gemini.py` | Google Gemini | Alternative |
| `videotrans/translator/_openaicompat.py` | OpenAI-compatible (Ollama, etc.) | Local LLM |
| `videotrans/tts/_edgetts.py` | Edge-TTS (Microsoft free) | Primary Vietnamese TTS |
| `videotrans/tts/_confuciustts.py` | Confucius4-TTS (built-in) | Vietnamese alternative |
| `videotrans/tts/_f5tts.py` | F5-TTS voice cloning | Optional voice clone |
| `videotrans/process/` | Background processing | Pipeline orchestration |

---

## 8. GPU Stack (verified from pyproject.toml)

- **CUDA:** 12.8 wheels via `https://download.pytorch.org/whl/cu128`
- **PyTorch:** 2.7.1 cu128 (Windows/Linux), CPU (macOS)
- **cuBLAS/cuDNN:** via `nvidia-cublas-cu12`, `nvidia-cudnn-cu12`
- **RTX 50-series:** Supported via cu128 (RTX 5090/5080 may need `float16` mode)

---

## 9. Recommended China → Vietnam Channel Selection

Based on channel indices and source code:

| Stage | Channel Index | Provider | Rationale |
|-------|---------------|----------|-----------|
| **ASR** | `4` (FUNASR_CN) | FunASR (Alibaba) | Built-in, **best for Chinese**, free, GPU-accelerated |
| **Translation** | `5` (DEEPSEEK_INDEX) | DeepSeek | Built-in since v3.74, OpenAI-compatible, "Deep Thinking" mode, great quality for Chinese → Vietnamese |
| **TTS** | `0` (EDGE_TTS) | Microsoft Edge-TTS | Free, native Vietnamese voices (`vi-VN-HoaiMyNeural`, `vi-VN-NamMinhNeural`), no setup |
| **Optional voice clone** | `2` (F5_TTS) | F5-TTS | Built-in v4.04, Vietnamese supported |
| **Optional quality upgrade** | `4` (CONFUCIUS_TTS) | Confucius4 | Built-in v4.06, Vietnamese native |
| **Diarization** | `--enable_diariz` | pyannote-audio (or built-in) | Speaker-aware output |

### Minimal CLI for China → Vietnam

```bash
uv run cli.py \
  --task vtv \
  --name "video_trung_quoc.mp4" \
  --recogn_type 4 \
  --translate_type 5 \
  --tts_type 0 \
  --source_language_code zh-cn \
  --target_language_code vi \
  --voice_role "vi-VN-HoaiMyNeural" \
  --cuda
```

### Quality Profile

```bash
# Larger ASR model + diarization + bilingual subtitle
uv run cli.py \
  --task vtv \
  --name "video.mp4" \
  --recogn_type 4 \
  --model_name large-v3 \
  --translate_type 5 \
  --tts_type 0 \
  --voice_role "vi-VN-HoaiMyNeural" \
  --enable_diariz \
  --nums_diariz 2 \
  --source_language_code zh-cn \
  --target_language_code vi \
  --cuda
```

---

## 10. Notes on `uv.lock`

- **Lockfile size:** 665KB (lockfile in repo)
- **Strategy:** `unsafe-best-match` (in `[tool.uv]` section)
- **Override-deps:** pins torch==2.7.1, transformers==5.6.0, f5-tts==1.1.20, chatterbox-tts==0.1.7, huggingface-hub==1.10.0
- **Platform markers:** torch/torchaudio get CUDA wheels on win32+linux, CPU wheels on darwin
- **URL wheels:** pynini from Windows wheels GitHub release; chatterbox-tts from master tarball

---

## 11. Setup Command (verbatim from README)

```bash
# 1. Install uv (Windows PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. Clone
git clone https://github.com/jianchang512/pyvideotrans.git
cd pyvideotrans

# 3. Sync
uv sync
# Optional extras:
uv sync --extra webui       # Gradio WebUI
uv sync --extra dotnet      # Whisper.NET (AMD GPU)
uv sync --all-extras        # All optional channels

# 4. Launch
uv run sp.py                # GUI
uv run cli.py --list providers  # CLI list
uv run webui.py             # WebUI (after --extra webui)
```

---

## 12. Conclusion

pyVideoTrans is a mature, full-featured video translation engine with:
- All required providers built-in
- Chinese → Vietnamese explicitly supported
- 3 entry points (GUI / CLI / WebUI)
- Windows-friendly via bundled FFmpeg and pre-packaged .exe (2.7GB)
- uv-based dependency management (matches the project requirements)

**Decision:** Adopt pyVideoTrans as-is. Configure channels for China → Vietnam via `params.json` (GUI/CLI) or `--recogn_type / --translate_type / --tts_type` (CLI). No source modifications needed for Phase 3+.

---

## 13. Documented Channel Mappings vs Actual Source

| Phase 0 Doc Claim | Actual Source |
|-------------------|---------------|
| `videotrans/api/_recognition/` | `videotrans/recognition/` (no `api/` prefix) |
| ASR channels listed at 0–8 | 22 channels indexed |
| FunASR channel ID | `4` (FUNASR_CN) |
| DeepSeek channel ID | `5` (DEEPSEEK_INDEX) |
| Edge-TTS channel ID | `0` (EDGE_TTS) |
| Confucius-TTS since v4.06 | Confirmed at index `4` |
| F5-TTS since v4.04 | Confirmed at index `2` |

The functional audit matches the Phase 0 adoption plan. Source path correction is required: use `videotrans/{recognition,translator,tts}/` instead of `videotrans/api/...`.
