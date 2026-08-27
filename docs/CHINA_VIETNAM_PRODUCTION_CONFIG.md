# China -> Vietnam Production Configuration

**Date:** 2026-08-27
**pyVideoTrans version:** v4.11
**Purpose:** Document the optimal production configuration for Chinese -> Vietnamese video translation

---

## Decision Summary

After auditing pyVideoTrans source code and channel capabilities, the recommended
production configuration for Chinese -> Vietnamese video translation is:

| Stage | Channel | Provider | Reason |
|-------|---------|----------|--------|
| **ASR** | 4 (FUNASR_CN) | FunASR (Alibaba) | Built-in, free, best for Chinese |
| **Translation** | 5 (DEEPSEEK_INDEX) | DeepSeek | Built-in, excellent quality, "Deep Thinking" mode, OpenAI-compatible |
| **TTS** | 0 (EDGE_TTS) | Microsoft Edge-TTS | Free, native Vietnamese voices, no setup |
| **Voice role** | `vi-VN-HoaiMyNeural` | Female Vietnamese | Natural-sounding female Vietnamese voice |
| **Voice role (alt)** | `vi-VN-NamMinhNeural` | Male Vietnamese | Natural-sounding male Vietnamese voice |
| **Diarization** | `--enable_diariz` | Built-in (auto) | Multi-speaker support |
| **Vocal separation** | Demucs | Built-in | Preserve BGM, remove source voice |
| **Video codec** | libx265 | HEVC | Better compression |
| **CRF** | 20 | — | High quality |
| **Format** | mp4 | — | Universal compatibility |

---

## Why These Choices?

### ASR: FunASR (channel 4)

**Why not faster-whisper (channel 0)?**
- FunASR is specifically optimized for Chinese by Alibaba DAMO Academy
- Better Mandarin accuracy than Whisper for Chinese content
- Hotword support (can recognize domain terms)

**Why not WhisperX (channel 18)?**
- WhisperX requires local API deployment (extra setup)
- FunASR has built-in timestamp alignment
- Diarization can be added separately if needed

**Model choice: paraformer-zh vs SenseVoiceSmall**
- `paraformer-zh` — Higher accuracy, recommended
- `SenseVoiceSmall` — Faster, smaller, slightly lower accuracy
- Default: `paraformer-zh`

### Translation: DeepSeek (channel 5)

**Why not Google/Microsoft (channels 0/1)?**
- Machine translation tends to be literal for Chinese -> Vietnamese
- Less natural Vietnamese output

**Why not ChatGPT (channel 4)?**
- Both DeepSeek and ChatGPT are good
- DeepSeek has "Deep Thinking" mode for better context
- DeepSeek is significantly cheaper for large volumes

**Why not Ollama/local LLM (channel 9)?**
- Local LLMs require significant GPU resources
- Quality is generally lower than DeepSeek for Chinese -> Vietnamese
- Latency is higher

### TTS: Edge-TTS (channel 0)

**Why not Confucius-TTS (channel 4)?**
- Both are free
- Edge-TTS requires no setup, no model download
- Edge-TTS Vietnamese voices sound natural

**Why not F5-TTS (channel 2)?**
- F5-TTS requires reference audio + setup
- Edge-TTS is "good enough" for most use cases
- F5-TTS recommended only when voice cloning is needed

**Why not paid (CosyVoice, ElevenLabs, Azure)?**
- Edge-TTS is free and quality is good
- Upgrade to paid only when specific voice needed

### Voice role: vi-VN-HoaiMyNeural

**Why HoaiMy vs NamMinh?**
- HoaiMy (female) is more commonly used for narration
- NamMinh (male) for male character voices
- Both are natural-sounding Microsoft voices

**For multi-speaker videos:**
- Use diarization
- Map speaker 1 -> HoaiMy (female)
- Map speaker 2 -> NamMinh (male)
- Or reverse based on actual content

---

## Production Configurations

### Configuration A: Fast (Demo, low-resource)

```bash
uv run cli.py --task vtv \
  --name "video.mp4" \
  --recogn_type 4 \
  --model_name SenseVoiceSmall \
  --translate_type 5 \
  --tts_type 0 \
  --source_language_code zh-cn \
  --target_language_code vi \
  --voice_role "vi-VN-HoaiMyNeural"
```

**Expected performance:**
- 1-minute video: ~30-60 seconds processing
- 5-minute video: ~3-5 minutes processing
- 10-minute video: ~6-10 minutes processing

**Use case:**
- Demo
- Quick verification
- Low-end hardware

### Configuration B: Balanced (Recommended)

```bash
uv run cli.py --task vtv \
  --name "video.mp4" \
  --recogn_type 4 \
  --model_name paraformer-zh \
  --translate_type 5 \
  --tts_type 0 \
  --source_language_code zh-cn \
  --target_language_code vi \
  --voice_role "vi-VN-HoaiMyNeural" \
  --enable_diariz \
  --nums_diariz 2 \
  --cuda
```

**Expected performance (GPU):**
- 1-minute video: ~60-120 seconds processing
- 5-minute video: ~5-10 minutes processing
- 10-minute video: ~10-20 minutes processing

**Use case:**
- Most videos
- Chinese dramas
- YouTube content
- General Vietnamese audience

### Configuration C: High Quality (Production)

```bash
uv run cli.py --task vtv \
  --name "video.mp4" \
  --recogn_type 4 \
  --model_name paraformer-zh \
  --translate_type 5 \
  --tts_type 2 \
  --source_language_code zh-cn \
  --target_language_code vi \
  --voice_role "clone" \
  --enable_diariz \
  --nums_diariz -1 \
  --cuda
```

Requires:
- F5-TTS reference audio in `f5-tts/`
- 8GB+ VRAM for FunASR + F5-TTS
- HF token for pyannote (diarization)

**Expected performance (GPU):**
- 1-minute video: ~2-5 minutes processing
- 5-minute video: ~10-25 minutes processing
- 10-minute video: ~20-50 minutes processing

**Use case:**
- Professional dubbing
- Film industry
- Premium content

---

## Translation Prompt (Advanced)

For higher quality Vietnamese output, configure a translation prompt in
**Tools > Advanced Options**:

```
Ban la mot dich gia phim chuyen nghiep, dich thoai tu tieng Trung sang tieng Viet.

Nguyen tac bat buoc:
1. Dich tu nhien, nhu nguoi Viet ban xem phim
2. Giu ten rieng nhat quan xuyen suot phim
3. Giu cach xung ho theo quan he nhan vat
4. Khong tu them noi dung hoac sua loi cua nhan vat
5. Khi gap cau Trung kho dich tu nhien sang Viet, uu tien y nghia hon cau truc

Dau vao: %SRT_TEXT%
Dau ra: chi tra ve phan dich, khong giai thich
```

---

## Quality Profiles

### For Chinese Dramas (古装剧, 古装仙侠)

**Configuration:**
- ASR: FunASR paraformer-zh
- Translation: DeepSeek with historical/period prompt
- TTS: F5-TTS (voice clone of original actors if possible) or Edge-TTS
- Subtitle: Hardcoded (burn-in) for compatibility

**Prompt variation:**
```
Phim co trang Trung Quoc, xung ho theo phe phai (ta thanh, hoang thuong, cong chua, ...)
```

### For Modern Drama (现代剧)

**Configuration:**
- Same as balanced
- No special prompt needed

### For Short Video (短视频, TikTok)

**Configuration:**
- ASR: FunASR SenseVoiceSmall (fast)
- Translation: DeepSeek
- TTS: Edge-TTS
- Subtitle: Vertical format if needed

### For Wuxia/Xianxia (武侠, 仙侠)

**Configuration:**
- ASR: FunASR paraformer-zh
- Translation: DeepSeek with wuxia-specific prompt
- TTS: F5-TTS voice clone
- Use historical Chinese terminology

---

## Subtitle Recommendations

For Vietnamese subtitles:

**SRT format:**
- Encoding: UTF-8
- CPS (characters per second): 14-18
- Maximum line length: 35-40 characters
- Hard line breaks: at sentence boundaries

**Font:**
- Be Vietnam Pro (modern)
- Arial Unicode MS (universal)
- Noto Sans (cross-platform)

**Style:**
- Bottom-center placement
- Outline: 2px black
- Background: semi-transparent black

---

## Audio Recommendations

**For videos with BGM:**
- Enable Demucs vocal separation
- Original voice: remove
- BGM: preserve
- TTS: layer over BGM

**For videos without BGM:**
- Disable vocal separation (faster)
- Just replace original voice with TTS

**Audio settings:**
- Output sample rate: 44100 Hz
- Output bit depth: 16-bit
- Codec: AAC 192 kbps

---

## Default Settings Summary

| Setting | Value |
|---------|-------|
| Source language | `zh-cn` |
| Target language | `vi` |
| ASR channel | `4` (FunASR) |
| ASR model | `paraformer-zh` |
| Translation channel | `5` (DeepSeek) |
| Translation model | `deepseek-chat` |
| TTS channel | `0` (Edge-TTS) |
| Voice role | `vi-VN-HoaiMyNeural` |
| Diarization | enabled (auto) |
| Vocal separation | enabled (Demucs) |
| Video codec | `libx265` |
| CRF | `20` |
| Format | `mp4` |
| CUDA | enabled if GPU available |

---

## When to Override

The above configuration is a general-purpose default. Override when:

| Situation | Override |
|-----------|----------|
| Need specific voice | Use F5-TTS voice clone |
| Higher quality needed | Upgrade to CosyVoice, ElevenLabs, Azure |
| Faster processing | Use SenseVoiceSmall, disable diarization |
| Lower cost | Use local LLM (Ollama) instead of DeepSeek |
| Different language | Change target_language_code |
| Different video source | Change source_language_code |
