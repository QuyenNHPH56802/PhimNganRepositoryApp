# Provider Contracts and Chinese → Vietnamese Translation/TTS Evaluation

Tài liệu này định nghĩa contract giữa domain (lõi ứng dụng) và các provider (bên ngoài: ASR, alignment, diarization, translation, TTS, audio separation, OCR, text removal, storage). Mục tiêu: domain không phụ thuộc SDK hoặc model cụ thể; việc đổi provider là thay implementation, không phải sửa domain.

Mọi contract đều dùng chung:

- **Input/Output**: Pydantic schema, versioned (`schema_version`), backward-compatible ở minor.
- **Capabilities**: enum `CapabilityFlag` để domain biết provider có hỗ trợ tính năng hay không (ví dụ `voice_cloning`, `accent_northern`, `forced_alignment_zh`).
- **Artifact signature**: provider tự ghi `ArtifactSignature` (input hash, model id/version, config hash, prompt version, glossary version, provider build hash) để cache invalidation.
- **Error**: lớp `ProviderError` phân cấp `Transient` (retry), `Permanent` (không retry), `CapabilityUnsupported` (fallback), `Quota` (backoff), `ConsentMissing` (chặn).
- **Timeouts**: `start_to_close`, `schedule_to_close`, `heartbeat_interval`. Worker sẽ cấu hình theo từng provider.
- **Cancellation**: activity phải handle `CancelledError` ở checkpoint an toàn.
- **Fallback**: provider phải đăng ký `FallbackPolicy` (none → raise; prefer_alt → dùng provider phụ; silent_fail → bị cấm).

---

## 1. ASRProvider

```text
ASRRequest {
  audio_ref: AssetRef
  language_hint: Literal["auto", "zh", "yue", "vi", "en", ...]
  model_id: str
  compute_type: Literal["fp16", "fp32", "int8"]
  batch_size: int
  vad_provider: VadProviderId
  vad_options: VadOptions
  hotwords: list[str] | None  # từ glossary, optional
  schema_version: int
}
ASRResponse {
  language_detected: str
  segments: list[TranscriptSegment]   # raw_text + normalized_text + words + quality flags
  artifact_signature: ArtifactSignature
}
TranscriptSegment {
  segment_id: str
  start: float
  end: float
  raw_text: str
  normalized_text: str
  words: list[WordTiming]
  quality_flags: list[Literal["low_confidence","no_alignment","music_overlap","filler_heavy"]]
  language_code: str
}
WordTiming {
  word_id: str
  text: str
  start: float
  end: float
  confidence: float | None
}
```

Yêu cầu với Chinese:
- Bắt buộc trả `words` cho cả ký tự CJK có thể align; nếu dictionary alignment không khớp thì mark `quality_flag` chứ không drop.
- `raw_text` giữ nguyên; `normalized_text` chỉ thêm punctuation, sentence break, numeral/date/unit conversion. Domain không được phép sửa `raw_text`.

## 2. AlignmentProvider

Mặc định WhisperX `align` (cùng nhà cung cấp với ASR), nhưng contract tách riêng để có thể dùng alignment model tốt hơn.

```text
AlignRequest {
  segments: list[TranscriptSegment]
  audio_ref: AssetRef
  language_code: str
  model_id: str | None  # None = provider tự chọn theo language_code
  return_char_alignments: bool
}
AlignResponse {
  segments: list[TranscriptSegment]   # đã có word-level timing
  artifact_signature: ArtifactSignature
}
```

## 3. DiarizationProvider

```text
DiarizeRequest {
  audio_ref: AssetRef
  min_speakers: int | None
  max_speakers: int | None
  model_id: str
}
DiarizeResponse {
  speaker_segments: list[SpeakerSegment]
  artifact_signature: ArtifactSignature
}
SpeakerSegment {
  start: float
  end: float
  speaker_id: str  # raw label từ provider
  overlap: list[(start, end, speaker_id)]
}
```

Domain sẽ remap `speaker_id` sang `character_profiles.id` và lưu raw label để audit; overlap phải được giữ lại, không được gộp vào một speaker.

## 4. TranslationProvider

Provider contract quan trọng nhất. Domain không gọi SDK; provider adapter tự ánh xạ sang SDK hoặc HTTP.

```text
TranslationRequest {
  source_language: "zh"
  target_language: "vi"
  segments: list[SourceSegment]
  context: TranslationContext
  style: TranslationStyle
  glossary_id: str | None
  character_bible_id: str | None
  provider_options: dict[str, Any]
  schema_version: int
}
TranslationResponse {
  translations: list[TranslationSegment]
  usage: dict[str, Any]
  artifact_signature: ArtifactSignature
  warnings: list[TranslationWarning]
}
SourceSegment {
  segment_id: str
  raw_text: str
  normalized_text: str
  start: float
  end: float
  speaker_label: str | None
}
TranslationContext {
  prev: list[SourceSegment]   # sliding window
  current: SourceSegment
  next: list[SourceSegment]
  speaker_role: str | None
  genre: GenreLiteral
  pronouns_hint: dict[str, list[str]] | None
  glossary_snapshot_id: str | None
  character_bible_snapshot_id: str | None
  project_language_profile: str   # "zh-vi" cho pipeline chuyên sâu
}
TranslationStyle {
  preset: Literal["natural", "literal", "drama", "short_video", "narration"]
  honorifics: Literal["auto", "casual", "formal", "archaic"]
  length_policy: Literal["loose", "tight", "strict"]
  reading_speed_cps: float | None
}
TranslationSegment {
  segment_id: str
  display_text: str
  tts_text: str | None   # provider có thể gợi ý; domain sẽ normalize lại
  confidence: float | None
  applied_glossary_terms: list[str]
  applied_aliases: list[str]
}
TranslationWarning {
  code: Literal["missing_info", "extra_info", "wrong_name", "wrong_pronoun", "wrong_number", "glossary_violation", "untranslated_zh", "naturalness"]
  segment_id: str
  message: str
}
```

### Translation QA adapter

QA là một provider riêng, dùng cùng schema để audit translation.

```text
QaRequest { translations: list[TranslationSegment]; context: TranslationContext; glossary_snapshot_id: str | None; }
QaResponse { verdicts: list[QaVerdict]; }
QaVerdict {
  segment_id: str
  status: Literal["PASS","WARNING","REVISE"]
  issues: list[TranslationWarning]
}
```

## 5. TTSProvider

```text
TtsRequest {
  texts: list[TtsSegment]
  voice_profile_id: str | None
  provider_options: dict[str, Any]   # speed, accent, emotion cues
  schema_version: int
}
TtsResponse {
  audio_segments: list[TtsAudio]
  artifact_signature: ArtifactSignature
  warnings: list[ProviderWarning]
}
TtsSegment {
  segment_id: str
  display_text: str
  tts_text: str
  voice_id: str
  speaker_label: str | None
  speed: float | None
  emotion_cues: list[str] | None
}
TtsAudio {
  segment_id: str
  audio_ref: AssetRef
  duration_ms: int
  sample_rate: int
  channels: int
  raw_metadata: dict[str, Any]
}
```

Voice profile phải khai báo `consent_status`, `reference_audio_hash`, `provider_specific_voice_id`. Không cho phép clone voice thiếu consent.

## 6. AudioSeparationProvider

```text
SeparateRequest {
  audio_ref: AssetRef
  targets: list[Literal["vocals","drums","bass","other","music","sfx"]]
  model_id: str
  chunk_strategy: Literal["auto", "manual"]
  chunk_seconds: float | None
}
SeparateResponse {
  stems: list[AudioStem]
  artifact_signature: ArtifactSignature
}
AudioStem { target: str; audio_ref: AssetRef; duration_ms: int; }
```

## 7. OCRProvider

```text
OcrRequest {
  frames: list[FrameRef]
  language_hint: Literal["zh","zh-Hans","zh-Hant","en","vi"]
  detect_only: bool
  model_id: str
}
OcrResponse {
  detections: list[OcrDetection]
  artifact_signature: ArtifactSignature
}
OcrDetection { text: str; bbox: BBox; frame_ts: float; confidence: float; }
```

## 8. TextRemovalProvider

```text
TextRemovalRequest { video_ref: AssetRef; bbox_per_frame: list[(frame_ts, BBox)]; strategy: Literal["inpaint","cover","blur"]; }
TextRemovalResponse { video_ref: AssetRef; artifact_signature: ArtifactSignature; }
```

## 9. StorageProvider

```text
StorageObject { key: str; etag: str; size: int; mime: str; metadata: dict[str,str]; }
PresignedUploadRequest { key: str; mime: str; size: int; expires_in: int; }
PresignedUploadResponse { url: str; headers: dict[str,str]; key: str; }
```

Contract dùng S3 API chuẩn. MinIO local dev được dùng làm một implementation; production cần deployment có license hợp lệ (xem `licenses.md`).

---

## 10. Chinese → Vietnamese translation design

### 10.1 Pipeline stages

1. **Pre-normalize** (trước khi đưa vào LLM): punctuation restoration, sentence segmentation, numeral/date/unit conversion, English/code-switch detection. Lưu `normalized_text` riêng.
2. **Context packing**: sliding window `[PREV][CURRENT][NEXT]` với `speaker_role`, `glossary_snapshot`, `character_bible_snapshot`, `genre`, `style.preset`. Window size mặc định: prev=2, next=2; có thể tăng cho genre drama.
3. **Provider call**: gọi `TranslationProvider` với request contract ở trên. Provider trả `TranslationSegment` kèm `applied_glossary_terms` và `applied_aliases`.
4. **QA pass**: `TranslationQa` provider audit từng segment, ra `PASS|WARNING|REVISE`.
5. **Name resolution**: nếu `applied_aliases` thiếu hoặc alias xung đột, chạy `NameResolver` riêng (alias map + Han-Viết policy + user override).
6. **Display vs TTS split**: `display_text` giữ nguyên câu hiển thị; `tts_text` đi qua `VietnameseTextNormalizer` → `PronunciationDictionary` → `TtsScriptBuilder` → provider.
7. **Versioning**: append `translation_version`; `translation_versions` là append-only, rollback bằng cách trỏ active version.

### 10.2 Glossary và character memory

- Glossary: dạng `chinese → vietnamese` với `category` (proper name, skill, place, organization, item, game term). Mỗi project có nhiều glossary, mỗi glossary nhiều term; provider phải nhận `glossary_snapshot_id` để đảm bảo reproducibility.
- Character bible: lưu name, aliases, gender, age_group, role, relationships, preferred_pronouns, preferred_honorifics, default voice. Provider nhận `character_bible_snapshot_id` để dùng trong prompt và ghi log khi apply.
- Alias resolution: cùng `speaker_label` có thể có nhiều alias trong bible; resolver chọn theo thứ tự ưu tiên `explicit_user_override > active_scene_alias > default_label`.

### 10.3 Cache & invalidation

`translation_cache_key = hash(source_hash + target + context_hash + provider_id + model_id + prompt_version + glossary_snapshot_id + character_bible_snapshot_id + style_hash + language_profile_version)`

Context hash gồm: prev/next window text (normalized), speaker_role, genre, honorifics policy, reading_speed_cps. Bất kỳ thay đổi nào ở các trường trên làm cache entry invalid. Domain giữ cache ở lớp provider, không viết logic invalidation trong domain.

### 10.4 Style presets

- `natural`: tiếng Việt tự nhiên, đại tỳ phổ biến; default.
- `literal`: bám sát cấu trúc nguồn, dịch đúng thứ tự.
- `drama`: phim Trung Quốc — tự nhiên, cảm xúc, xưng hô theo vai.
- `short_video`: câu ngắn, dễ nghe, dễ đọc, không chêm giải thích.
- `narration`: mạch lạc, dễ nghe TTS, nối liền hơn.

### 10.5 Quality pipeline (khuyến nghị)

- Mỗi segment phải có 1 trong 3 verdict sau QA: `PASS` → dùng luôn; `WARNING` → giữ nhưng gắn cờ review; `REVISE` → provider phải regen với feedback (1 lần regen; lần 2 nếu vẫn `REVISE` thì đưa vào human review queue).
- `TranslationWarning.code` bắt buộc cho phép dashboard lọc: glossary violation, missing info, extra info, wrong name/pronoun/number, untranslated Chinese, naturalness.

## 11. Vietnamese TTS evaluation rubric

### 11.1 Test corpora

- `tests/golden/chinese_vietnamese/` chứa fixture audio + transcript + translation do người dịch có quyền. Không dùng video YouTube/Bilibili/Douyin không có quyền.
- Mỗi fixture ghi rõ: source path/hash, license, người cung cấp, ngày, phạm vi sử dụng, accent mục tiêu, độ tuổi/giới tính/role nếu có.

### 11.2 Tiêu chí đánh giá (tự động + human)

1. **Pronunciation**: phát âm đúng 6 thanh, không nhầm dấu, tên riêng, địa danh, Hán-Việt; số/đơn vị/ngày đọc đúng; English code-switch đọc đúng.
2. **Naturalness**: nghe như người Việt; không có hiện tượng word-by-word, không bị “robotic”, ngắt hơi tự nhiên.
3. **Intelligibility**: nghe rõ trong môi trường có nhạc nền; không bị chìm tiếng.
4. **Speaker consistency**: cùng voice profile cho nhiều segment phải đồng nhất về giọng, tone, pace.
5. **Emotion/prosody**: khớp với ngữ cảnh (drama, narration, short video).
6. **Speaking rate**: CPS nằm trong khoảng 12–18 chars/giây cho narration; 14–20 cho drama. Vượt ngưỡng → warning.
7. **Timing alignment**: TTS duration so với target slot, validate overflow trước khi accept.
8. **Clipping/pause**: không clipping, không pause bất thường, không pop noise.
9. **Reproducibility**: cùng input + cùng voice profile + cùng provider/model phải sinh audio hash giống nhau (hoặc chênh lệch dưới ngưỡng cho phép).
10. **Consent/usage**: voice profile phải có consent_status hợp lệ.

### 11.3 Voice preview

- Voice preview 5–10 giây trước khi render full; user nghe và accept/reject.
- Preview lưu audio hash + provider/model + voice profile id + signature để có thể reuse cache.

### 11.4 Rubric scoring

- Mỗi fixture chấm điểm 1–5 theo 10 tiêu chí; ngưỡng pass tổng ≥ 4.0, không có tiêu chí nào < 3.
- Lưu kết quả vào `tts_evaluations` để so sánh giữa các provider/model.

## 12. Áp dụng contract vào DAG

- Mỗi node trong DAG (`asr`, `align`, `diarize`, `translate`, `qa`, `tts`, `separate`, `mix`, `render`) là một activity gọi provider tương ứng.
- Activity input/output đều đi qua schema versioned; nếu schema thay đổi breaking, phải tạo provider implementation mới, không sửa domain.
- Artifact signature là contract output bắt buộc: nó vừa là cache key vừa là audit trail.

## 13. Cache key & invalidation convention

Cache key cho mỗi provider output phải là `sha256(input_hash | model_id | model_version | provider_build | config_hash | prompt_version | glossary_snapshot_id | character_bible_snapshot_id | language_profile_version)`. Các lớp cache chính:

1. **Transcription cache** (`AsrResponse` + `AlignResponse`): key thêm `audio_fingerprint` (sha256 đầu/cuối N byte + size) thay vì hash toàn audio để tiết kiệm.
2. **Diarization cache** (`DiarizeResponse`): key thêm `audio_fingerprint` + `model_id`.
3. **Translation cache** (`TranslationResponse`): key đầy đủ theo công thức trên; context đ�i (prev/next window, speaker_role, honorifics, style preset, glossary/character snapshot) làm cache invalid.
4. **TTS cache** (`TtsResponse`): key thêm `voice_profile_id` + `provider_specific_voice_id` + `pronunciation_dict_version` + speed/emotion config.
5. **OCR cache**: key theo `frame_fingerprint` + `model_id`.
6. **Separation cache**: key theo `audio_fingerprint` + `model_id` + `chunk_strategy`.

Rules:
- Storage ưu tiên S3-compatible; metadata tag `cache_key_version` để dễ revalidate khi đổi convention.
- Khi đổi `model_version`, `provider_build`, `prompt_version`, `glossary_snapshot_id`, `character_bible_snapshot_id` hay `language_profile_version`, mọi cache entry cũ phải được đánh dấu stale (không delete ngay) và chỉ xóa sau retention window.
- Không cache kết quả từ provider có `ConsentMissing` hoặc `CapabilityUnsupported`.
