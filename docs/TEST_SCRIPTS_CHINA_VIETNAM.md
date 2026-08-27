# China-VNE Test Scripts

Cac scripts de test pipeline pyVideoTrans cho China -> Vietnamese.

---

## Chuẩn bị

### Tao thu muc test

```cmd
mkdir "C:\Users\Administrator\Downloads\china-vne-tests"
```

### Dat video Trung Quoc test

Dat video Trung Quoc ngan (30-60 giay) vao:
```
C:\Users\Administrator\Downloads\china-vne-tests\sample_zh.mp4
```

---

## Test 1: Chinese ASR (Fast)

```cmd
cd "C:\Users\Administrator\Downloads\App\pyvideotrans-src\pyvideotrans"

uv run cli.py --task stt ^
  --name "C:\Users\Administrator\Downloads\china-vne-tests\sample_zh.mp4" ^
  --recogn_type 4 ^
  --source_language_code zh-cn
```

Expected output: `sample_zh.srt` trong `_video_out/`

---

## Test 2: Subtitle Translation (DeepSeek)

Tao file SRT mau (test_zh.srt):
```srt
1
00:00:01,000 --> 00:00:03,000
你好,世界

2
00:00:03,500 --> 00:00:06,000
今天天气真好

3
00:00:06,500 --> 00:00:09,000
我喜欢吃越南河粉
```

Chay dich:
```cmd
cd "C:\Users\Administrator\Downloads\App\pyvideotrans-src\pyvideotrans"

uv run cli.py --task sts ^
  --name "C:\Users\Administrator\Downloads\china-vne-tests\test_zh.srt" ^
  --target_language_code vi ^
  --translate_type 5
```

Expected output: `test_zh.vi.srt` (phu de tieng Viet)

---

## Test 3: Vietnamese TTS (Edge-TTS)

Tao file SRT tieng Viet mau (test_vi.srt):
```srt
1
00:00:01,000 --> 00:00:03,000
Xin chào, thế giới

2
00:00:03,500 --> 00:00:06,000
Hôm nay thời tiết thật đẹp

3
00:00:06,500 --> 00:00:09,000
Tôi thích ăn phở Việt Nam
```

Chay TTS:
```cmd
cd "C:\Users\Administrator\Downloads\App\pyvideotrans-src\pyvideotrans"

uv run cli.py --task tts ^
  --name "C:\Users\Administrator\Downloads\china-vne-tests\test_vi.srt" ^
  --tts_type 0 ^
  --voice_role "vi-VN-HoaiMyNeural"
```

Expected output: file WAV cho moi cau tieng Viet trong `_video_out/`

---

## Test 4: Full Pipeline (Video Translation)

```cmd
cd "C:\Users\Administrator\Downloads\App\pyvideotrans-src\pyvideotrans"

uv run cli.py --task vtv ^
  --name "C:\Users\Administrator\Downloads\china-vne-tests\sample_zh.mp4" ^
  --recogn_type 4 ^
  --translate_type 5 ^
  --tts_type 0 ^
  --source_language_code zh-cn ^
  --target_language_code vi ^
  --voice_role "vi-VN-HoaiMyNeural" ^
  --cuda
```

Expected output: `sample_zh_vi.mp4` (video tieng Viet)

---

## Test 5: Multi-speaker (Diarization)

```cmd
cd "C:\Users\Administrator\Downloads\App\pyvideotrans-src\pyvideotrans"

uv run cli.py --task vtv ^
  --name "C:\Users\Administrator\Downloads\china-vne-tests\sample_multi.mp4" ^
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

---

## Kiem tra output

### Subtitle
```cmd
type "%USERPROFILE%\.cache\pyvideotrans\_video_out\sample_zh.srt"
```

### Audio (Vietnamese TTS)
```cmd
dir "%USERPROFILE%\.cache\pyvideotrans\_video_out\*.wav"
```

### Final video
```cmd
dir "%USERPROFILE%\.cache\pyvideotrans\_video_out\*.mp4"
```

---

## Troubleshooting

### "uv not found"
Source deployment can uv. Cai dat:
```cmd
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### "model download failed"
Kiem tra ket noi internet, hoac dat proxy:
```cmd
set HF_ENDPOINT=https://hf-mirror.com
```

### "CUDA error"
GPU khong tuong thich. Tat CUDA:
```cmd
# Bo --cuda
```

### Test khong chay
Kiem tra Python 3.10:
```cmd
python --version
```
