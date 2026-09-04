# PYTHON_SETUP.md

# Python Environment Setup — PhimNganRepositoryApp + pyVideoTrans

**Version:** 1.0
**Updated:** 2026-08-27

---

## Tổng Quan

Dự án chạy **hai stack Python song song**, không merge:

| Stack | Version | Tool | Mục đích |
|-------|---------|------|----------|
| PhimNganRepositoryApp | Python 3.11 | pip / uv | API + Temporal worker |
| pyVideoTrans | Python 3.10 (verify) | uv (recommended) | Video translation engine |

> **Nguyên tắc:** Không cố gắng dùng chung virtual environment. Mỗi stack chạy trong environment riêng.

---

## 1. PhimNganRepositoryApp Stack

### 1.1 Yêu cầu

- **Python:** 3.11 (xác nhận từ `pyproject.toml` — `requires-python = ">=3.11"`, `target-version = "py311"`)
- **OS:** Windows 10/11, macOS, Linux
- **GPU:** Optional — NVIDIA GPU với CUDA 11.8+ cho ASR/TTS local

### 1.2 Cài đặt

```bash
# Tạo virtual environment
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # macOS/Linux

# Cài dependencies
pip install -e .
```

Hoặc dùng `uv` (nhanh hơn):

```bash
uv sync
```

### 1.3 Verify

```bash
python --version
# Output: Python 3.11.x

pip list | grep -E "fastapi|temporal|sqlalchemy"
```

---

## 2. pyVideoTrans Stack

### 2.1 Yêu cầu

- **Python:** 3.10 (khuyến nghị) hoặc 3.11 — **VERIFY từ file cài đặt thực tế**
- **OS:** Windows 10/11 (64-bit)
- **GPU:** NVIDIA GPU với VRAM 6GB+ (RTX 3060 trở lên)
- **FFmpeg:** Bundled trong package hoặc cài riêng

### 2.2 Xác minh Python version từ package

Sau khi tải pyVideoTrans v4.11 (xem [MODEL_SETUP_CHINA_VIETNAM.md](docs/MODEL_SETUP_CHINA_VIETNAM.md)):

```bash
# Nếu dùng source
cd pyvideotrans
uv run python --version

# Nếu dùng pre-built Windows
# Kiểm tra trong thư mục cài đặt:
# pyvideotrans-win\python.exe --version
```

### 2.3 Cài đặt từ source (recommended)

```bash
git clone https://github.com/jianchang512/pyvideotrans.git
cd pyvideotrans
uv sync
```

### 2.4 Verify

```bash
uv --version
# Output: uv 0.x.x

uv run python --version
# Output: Python 3.10.x hoặc 3.11.x

uv run python -c "import pyvideotrans; print(pyvideotrans.__version__)"
```

---

## 3. Hai Stack Song Song

### 3.1 Cấu trúc thư mục đề xuất

```
Translator/                          # PhimNganRepositoryApp (Python 3.11)
├── .venv/
├── apps/
├── packages/
└── docs/

pyvideotrans/                       # pyVideoTrans (Python 3.10)
├── .venv/
├── pyvideotrans/
└── models/
```

### 3.2 Chạy riêng

```bash
# Terminal 1 — PhimNganRepositoryApp
cd Translator
.venv\Scripts\activate
python -m uvicorn apps.api.main:app --reload

# Terminal 2 — pyVideoTrans
cd pyvideotrans
.venv\Scripts\activate
python sp.py    # hoặc GUI launcher tương ứng
```

---

## 4. Common Pitfalls

### 4.1 Python 3.13 — Không dùng

Một số dependency trong cả hai stack chưa hỗ trợ Python 3.13:

- `onnxruntime` — wheel chưa có cho 3.13
- `torch` (CUDA build) — compatibility chưa confirmed
- ` faster-whisper` — onnxruntime dependency

**Nếu máy đang có Python 3.13:** Cài thêm Python 3.11 cho PhimNganRepositoryApp và Python 3.10 cho pyVideoTrans qua [pyenv-win](https://github.com/pyenv-win/pyenv-win) (Windows) hoặc [pyenv](https://github.com/pyenv/pyenv) (macOS/Linux).

### 4.2 PATH — Giữ nguyên system Python

Không gỡ bỏ hoặc thay đổi Python system default. Chỉ dùng venv/uv để isolate.

### 4.3 CUDA / cuDNN

- PhimNganRepositoryApp: CUDA 11.8 hoặc 12.1
- pyVideoTrans: kiểm tra PyTorch version yêu cầu trong `pyproject.toml` của pyVideoTrans

### 4.4 FFmpeg

```bash
# Verify FFmpeg có trong PATH
ffmpeg -version
ffprobe -version

# Nếu thiếu (pyVideoTrans bundled):
# pyvideotrans-win\ffmpeg.exe -version
```

---

## 5. Quick Reference

| Command | PhimNganRepositoryApp | pyVideoTrans |
|---------|----------------------|--------------|
| Check Python | `python --version` | `uv run python --version` |
| Activate env | `.venv\Scripts\activate` | `cd pyvideotrans && uv sync` |
| Install deps | `pip install -e .` | `uv sync` |
| Run | `python -m uvicorn ...` | `python sp.py` |

---

## 6. Troubleshooting

### "ModuleNotFoundError" khi chạy project

```bash
# Kiểm tra đang activate đúng environment
which python   # macOS/Linux
where python   # Windows

# Nếu ra system Python → chưa activate venv
```

### "Python version mismatch" khi install package

```bash
# Kiểm tra pyproject.toml yêu cầu
cat pyproject.toml | grep requires-python

# Tạo env đúng version
python3.11 -m venv .venv
```

### GPU không được detect trong pyVideoTrans

```bash
nvidia-smi
# Nếu lỗi → cài NVIDIA driver trước

uv run python -c "import torch; print(torch.cuda.is_available())"
# True = GPU OK, False = kiểm tra CUDA version
```

---

## 7. References

- [MODEL_SETUP_CHINA_VIETNAM.md](docs/MODEL_SETUP_CHINA_VIETNAM.md) — Model setup cho pyVideoTrans
- [CHINA_VIETNAM_PRODUCTION_CONFIG.md](docs/CHINA_VIETNAM_PRODUCTION_CONFIG.md) — Production config
- pyVideoTrans upstream: https://github.com/jianchang512/pyvideotrans
