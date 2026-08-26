# Providers Catalog

Bảng các provider đã được đăng ký trong hệ thống. Mọi provider đều nằm
trong `apps/api/python/translator_api/providers/<kind>/`. Đăng ký qua
`translator_api.providers.registry.bootstrap()`.

| Phase | Kind | Provider id | Mô tả | License | Verified |
|---|---|---|---|---|---|
| 2 | asr | whisperx_faster_whisper | WhisperX (large-v3 / turbo / distil-large-v3) | MIT (code) / Apache-2.0 (model weights) | ✅ |
| 2 | align | wav2vec2 | jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn | Apache-2.0 | ✅ |
| 2 | diarize | pyannote_3_1 | pyannote/speaker-diarization-3.1 | MIT (code) / CC-BY-4.0 (model gated) | ✅ |
| 3 | translate | openai_compatible_http | OpenAI / GPT-4o-mini ... | OpenAI TOS (proprietary) | ⚠ caller's key |
| 3 | translate | gemini_compatible_http | Gemini generateContent | Google TOS | ⚠ caller's key |
| 3 | translate | claude_compatible_http | Anthropic Messages | Anthropic TOS | ⚠ caller's key |
| 3 | translate | local_llm | llama.cpp / Ollama | MIT | ✅ |
| 3 | qa | rule_based | Kiểm tra glossary / alias / length / pinyin / Hán tự | internal | ✅ |
| 3 | subtitle | cps_wrapper | CPS-aware segmentation | internal | ✅ |
| 3 | tts | vietvoice_tts | Vietnamese TTS on-prem | Apache-2.0 (target) | ✅ |
| 3 | tts | vieneu_v3_turbo | VieNeu clone voice (consent gate) | Apache-2.0 (target) | ⚠ needs consent |
| 3 | tts | cosyvoice_3 | CosyVoice 3 multilingual | Apache-2.0 (model) | ✅ |
| 3 | tts | melo_tts_vi | MeloTTS preset vi | MIT | ✅ |
| 3 | tts | cloud_azure | Azure Speech TTS | Microsoft TOS | ⚠ caller's key |
| 3 | tts | cloud_google | Google Cloud TTS | Google TOS | ⚠ caller's key |
| 3 | tts | cloud_elevenlabs | ElevenLabs TTS | ElevenLabs TOS | ⚠ caller's key |
| 3 | audio_separation | uvr5_mdx | UVR5 MDX23K | MIT | ✅ |
| 3 | audio_separation | demucs | htdemucs | MIT | ✅ |
| 3 | audio_separation | bs_roformer | BS-Roformer | MIT | ✅ |
| 3 | audio_mix | ffmpeg_mix | FFmpeg filtergraph mix | FFmpeg (LGPL/GPL) | ✅ |
| 3 | dubbing_align | ffmpeg_atempo | FFmpeg atempo chain | FFmpeg | ✅ |
| 3 | render | ffmpeg_render | FFmpeg video compose | FFmpeg | ✅ |
| 3 | export | ffmpeg_export | Multi-format export | FFmpeg | ✅ |
| 3 | cleanup | orphan_cleanup | DB-vs-storage reconciliation | internal | ✅ |

## Thay đổi qua từng phase

- **Phase 1**: chưa có provider thật. Toàn bộ activity là stub.
- **Phase 2**: thêm `asr`, `align`, `diarize`. Lazy-load; không tải weight.
- **Phase 3**: thêm `translate`, `qa`, `subtitle`, `tts`, `audio_separation`,
  `audio_mix`, `dubbing_align`, `render`, `export`, `cleanup`.

## Activity ↔ Task Queue mapping

| Activity | Queue |
|---|---|
| asr_transcribe | asr-queue |
| diarize_segments | diarize-queue |
| tts_synthesize | tts-queue |
| validate_inputs, detect_subtitle_stream, analyze_media, chunk_plan, align_text, normalize_chinese, translate_segments, translation_qa, subtitle_segment, audio_separate, dubbing_align, audio_mix, render_build, export_assemble, cleanup_orphans | cpu-queue |