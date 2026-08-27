# Next Steps Plan — China-Vietnam pyVideoTrans

**Date:** 2026-08-27
**Branch:** `feature/china-vietnam-setup`
**Status:** Code pushed, ready for next phase

---

## ✅ Completed (Phases 0-11)

| Phase | Item | Status |
|-------|------|--------|
| 0 | Legacy v1.3.0 status audit | ✅ |
| 0 | pyVideoTrans adoption plan | ✅ |
| 1 | Source code audit (PYVIDEOTRANS_SOURCE_AUDIT.md) | ✅ |
| 1 | Channel mapping (ASR/Translation/TTS indices) | ✅ |
| 2 | `develop` + `feature/china-vietnam-setup` branches | ✅ |
| 3 | Pre-packaged v4.11 downloaded (2.93 GB) + extracted (7.26 GB) | ✅ |
| 4 | GPU verified: RTX 4060 8GB, CUDA 13.2 | ✅ |
| 4 | FFmpeg verified (bundled in ffmpeg/) | ✅ |
| 4 | PyTorch cu128 bundled | ✅ |
| 9 | Production config documented (CHINA_VIETNAM_PRODUCTION_CONFIG.md) | ✅ |
| 10 | 4 Windows .bat scripts: setup/start/doctor/update | ✅ |
| 11 | HUONG-DAN-CHINA-VIETNAM-A-Z.md (user guide) | ✅ |
| 14 | PYVIDEOTRANS_GAPS_FOR_CHINA_VIETNAM.md (gap analysis) | ✅ |
| Extra | MODEL_SETUP_CHINA_VIETNAM.md | ✅ |
| Extra | TROUBLESHOOTING.md | ✅ |
| Extra | TEST_SCRIPTS_CHINA_VIETNAM.md | ✅ |
| Extra | BENCHMARK_CHINA_VIETNAM.md | ✅ |

**Total commits:** 6 commits on `feature/china-vietnam-setup`

---

## ⚠️ Pending — Cannot Complete Without User Action

| Phase | Item | Reason |
|-------|------|--------|
| 5 | Test Chinese ASR (FunASR) with video | Need test video (Chinese content) + interactive GUI |
| 6 | Test Chinese → Vietnamese translation | Need DeepSeek API key from user |
| 7 | Test Vietnamese TTS (Edge-TTS) | Need interactive GUI access |
| 8 | Test full pipeline | Depends on 5,6,7 |
| 12 | Regression tests | Depends on test videos |
| 13 | Performance benchmarks | Depends on test videos |

**Blockers:**
- No sample Chinese test videos provided
- No DeepSeek API key configured
- GUI requires interactive desktop (this session is CLI-only)

---

## 📋 Next Steps (Priority Order)

### Immediate (requires user)

1. **Configure DeepSeek API key**
   - Get key: https://platform.deepseek.com/
   - Open `sp.exe` GUI → Tools → Settings → Translation → DeepSeek
   - Test with a short Chinese video clip

2. **Provide test videos** (place in `C:\Users\Administrator\Downloads\china-vne-tests\`)
   - Chinese drama clip (1 min, 5 min, 10 min variants)
   - Optional: noisy video with BGM
   - Optional: multi-speaker video

3. **Run real benchmark**
   - Open `sp.exe`
   - Run Fast / Balanced / High profiles
   - Fill in BENCHMARK_CHINA_VIETNAM.md with actual results

### Short-term (1-2 weeks)

4. **Create translation glossary**
   - Common character names (古装剧 names)
   - Common Wuxia terms
   - Custom translation prompt

5. **Voice clone setup**
   - Pick 1-2 Vietnamese reference voices
   - Place in `pyvideotrans-win\f5-tts\`
   - Test F5-TTS cloning quality

6. **Build batch wrapper script**
   - Folder-based batch processing
   - External metadata CSV for series tracking
   - Automated CLI loop

### Medium-term (1-2 months)

7. **Monitor upstream pyVideoTrans**
   - Watch for OCR feature (gap #1)
   - Watch for text removal/inpainting (gap #2)
   - Watch for translation memory (gap #3)

8. **Custom thin wrappers** (only if gaps not addressed upstream)
   - Pre-processing: character name glossary
   - Series metadata manager
   - Translation memory from prior videos

9. **Performance tuning**
   - Test on 10/30/60 minute videos
   - Profile memory usage
   - Optimize VRAM allocation

### Long-term (3+ months)

10. **Multi-project dashboard** (only if team grows)
    - Web-based project tracker
    - Per-video progress
    - Character voice mapping per project

11. **Cloud deployment** (only if needed)
    - Docker image with all models
    - GPU node pool
    - API layer

12. **Production hardening**
    - Auto-restart on failure
    - Queue with retry
    - Disk space monitoring

---

## 🎯 Critical Decisions Pending

| Decision | Options | Default |
|----------|---------|---------|
| Translation provider | DeepSeek vs ChatGPT vs Ollama | DeepSeek |
| TTS provider | Edge-TTS vs F5-TTS vs CosyVoice | Edge-TTS |
| Voice role | vi-VN-HoaiMyNeural vs vi-VN-NamMinhNeural | HoaiMy (female) |
| Diarization | On vs Off | On for multi-speaker |
| BGM handling | Preserve vs Remove | Preserve |
| Video codec | libx264 vs libx265 | libx265 (HEVC) |
| CRF | 18-23 | 20 |
| Pipeline | CLI vs GUI | GUI for now, CLI later |

---

## 📁 Files to Review Before Merge

| File | Purpose | Reviewer Notes |
|------|---------|---------------|
| `docs/PYVIDEOTRANS_SOURCE_AUDIT.md` | Technical audit of pyVideoTrans | Validate channel indices |
| `docs/PYVIDEOTRANS_ADOPTION_PLAN.md` | High-level adoption strategy | Validate decisions |
| `docs/HUONG-DAN-CHINA-VIETNAM-A-Z.md` | Vietnamese user guide | Validate Vietnamese translations |
| `scripts/china-vietnam/setup.bat` | Windows installer | Test on clean system |
| `scripts/china-vietnam/start.bat` | Windows launcher | Test GUI launch |
| `scripts/china-vietnam/doctor.bat` | Diagnostic | Run after install |
| `scripts/china-vietnam/update.bat` | Update script | Test backup/restore |
| `.gitignore` | Exclude pyvideotrans-win/ | Verify exclusions |

---

## 🚀 How to Continue

### Option A: Continue with current approach
1. User runs `sp.exe` interactively
2. Reports back benchmark results
3. Fill in `BENCHMARK_CHINA_VIETNAM.md`
4. Iterate on configuration

### Option B: Switch to source deployment
1. Install Python 3.10 + uv on machine
2. Use `pyvideotrans-src\pyvideotrans\` (already cloned)
3. Can run `uv run cli.py` from terminal
4. Enables true headless testing

### Option C: Docker deployment
1. Build Docker image from `Dockerfile` in source
2. Run as container
3. WebUI accessible on port 7860
4. Suitable for server/cloud

### Option D: Pivot strategy
1. Re-evaluate if pyVideoTrans is the right choice
2. Consider alternatives (Rask AI, Heygen, etc.)
3. Continue with custom PhimNganRepositoryApp platform

---

## 📞 Contact / Questions

For issues with:
- pyVideoTrans: https://bbs.pyvideotrans.com or GitHub Issues
- This config: check `docs/TROUBLESHOOTING.md`
- Doctor script: run `scripts\china-vietnam\doctor.bat`

---

**Last updated:** 2026-08-27 13:01 (UTC+7)