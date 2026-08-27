# Benchmark Plan: China -> Vietnam Video Translation

**Version:** 1.0 (planned)
**Date:** 2026-08-27
**Status:** Awaiting actual test execution (download in progress)

This document is a TEMPLATE that will be filled in once pyVideoTrans is fully installed
and tested. It cannot be executed without:

1. Completed pyVideoTrans pre-packaged install
2. NVIDIA GPU with CUDA 12.8 support (or fallback to CPU)
3. API keys for DeepSeek / Edge-TTS (Edge-TTS does not require key)
4. Test videos (Chinese language, 1 min / 5 min / 10 min)

---

## Test Environment

### Hardware

| Component | Specification | Notes |
|-----------|---------------|-------|
| CPU | (TBD) | — |
| GPU | (TBD) | NVIDIA recommended |
| VRAM | (TBD) | 8GB+ for FunASR, 16GB+ for F5-TTS |
| RAM | (TBD) | 16GB+ recommended |
| Storage | (TBD) | SSD recommended |

### Software

| Component | Version |
|-----------|---------|
| OS | Windows 10/11 |
| pyVideoTrans | v4.11 |
| FFmpeg | bundled |
| CUDA | 12.8 |
| cuDNN | 9.11 |
| Python | 3.10 (for source deployment) |

---

## Test Videos

### Test 1: 1-minute Chinese Video

| Attribute | Value |
|-----------|-------|
| Source | Chinese drama clip |
| Duration | 60 seconds |
| Speaker count | 1-2 |
| BGM | Yes |
| Subtitles | Chinese hardcoded |

### Test 2: 5-minute Chinese Video

| Attribute | Value |
|-----------|-------|
| Source | Chinese movie scene |
| Duration | 5 minutes |
| Speaker count | 2-4 |
| BGM | Yes |
| Subtitles | No |

### Test 3: 10-minute Chinese Video

| Attribute | Value |
|-----------|-------|
| Source | Chinese TV episode segment |
| Duration | 10 minutes |
| Speaker count | 3-5 |
| BGM | Yes |
| Subtitles | Chinese hardcoded |

---

## Test Matrix

For each test video, run:

### Profile A: Fast

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

### Profile B: Balanced

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

### Profile C: High

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

---

## Metrics to Capture

### Stage Timings

| Stage | Description | Tool |
|-------|-------------|------|
| Setup | Model loading, environment | Log timestamp |
| ASR | Speech recognition duration | Log timestamp |
| Diarization | Speaker detection | Log timestamp |
| Translation | Vietnamese translation | Log timestamp |
| TTS | Vietnamese voice synthesis | Log timestamp |
| Mix | Audio mixing with BGM | Log timestamp |
| Render | Final video encoding | Log timestamp |
| **Total** | End-to-end duration | Log timestamp |

### Resource Usage

| Metric | Tool |
|--------|------|
| GPU utilization | `nvidia-smi -l 1` |
| VRAM peak | `nvidia-smi --query-gpu=memory.used --format=csv` |
| CPU utilization | Task Manager / `top` |
| RAM peak | Task Manager |
| Disk I/O | Resource Monitor |
| Output file size | `dir output/` |

### Quality Metrics

| Metric | Description | Method |
|--------|-------------|--------|
| ASR accuracy | Chinese transcript quality | Manual review |
| Translation quality | Vietnamese naturalness | Manual review |
| TTS alignment | Audio/video sync | Manual review |
| Voice quality | Naturalness | Manual review |
| Subtitle timing | CPS, line breaks | Auto-check |

---

## Benchmark Results Template

### Test 1A: 1-minute video, Fast profile

| Metric | Value |
|--------|-------|
| File | video_1min.mp4 |
| Profile | Fast |
| Duration | 60s |
| Total time | (TBD) |
| ASR time | (TBD) |
| Translation time | (TBD) |
| TTS time | (TBD) |
| Render time | (TBD) |
| GPU VRAM peak | (TBD) MB |
| RAM peak | (TBD) MB |
| Output file size | (TBD) MB |
| Output duration | (TBD) |

### Test 1B: 1-minute video, Balanced profile

(Fill in same template)

### Test 2A: 5-minute video, Balanced profile

(Fill in same template)

### Test 3A: 10-minute video, Balanced profile

(Fill in same template)

---

## Quality Observations Template

### Translation Quality

| Aspect | Observation |
|--------|-------------|
| Naturalness | (1-10) |
| Accuracy | (1-10) |
| Terminology consistency | (1-10) |
| Cultural adaptation | (1-10) |
| Notes | ... |

### TTS Quality

| Aspect | Observation |
|--------|-------------|
| Voice naturalness | (1-10) |
| Audio/video sync | (1-10) |
| Vietnamese diacritics | (1-10) |
| Speed | (1-10) |
| Notes | ... |

---

## Conclusion Template

After all benchmarks complete, document:

1. **Best profile for speed:** Profile X
2. **Best profile for quality:** Profile Y
3. **Best profile for cost-effectiveness:** Profile Z
4. **Recommended default:** ...
5. **Hardware requirements:** ...
6. **Known bottlenecks:** ...
7. **Optimization opportunities:** ...

---

## Status

**Current status:** Awaiting download completion and test execution.

Download progress:
- Pre-packaged .7z file (~2.7 GB) downloading from Hugging Face
- Estimated completion: within next 30-60 minutes

Once download completes:
1. Extract to `pyvideotrans-win/`
2. Run `sp.exe` to verify startup
3. Configure DeepSeek API key in GUI
4. Acquire test videos (Chinese content, 1/5/10 min)
5. Run benchmark matrix
6. Fill in this document with actual results
7. Commit to `feature/china-vietnam-setup` branch

---

## Alternative: Manual Benchmarking

If automated benchmarking is not feasible, manual steps:

1. Run each profile once
2. Time with stopwatch
3. Check `nvidia-smi` for GPU usage
4. Visually review output video quality
5. Document observations in `BENCHMARK_OBSERVATIONS.md` (separate file)
