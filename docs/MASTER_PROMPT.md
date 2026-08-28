# CHINA-VNE — MASTER IMPLEMENTATION PROMPT
# Kiến trúc thực tế: FastAPI + Temporal + Provider Registry + Next.js

---

## 1. BỐI CẢNH HỆ THỐNG HIỆN TẠI

### Frontend (apps/web/)
- Next.js 14, React 18
- Không có state library (Zustand/Redux/React Query)
- Inline styles + Tailwind classes hỗn hợp
- Một số pages gọi `/api/*` không tồn tại (admin/voice/workflow)
- Không có: video player, timeline, editor panels, workspace shell, undo/redo, autosave, keyboard shortcuts, virtualization

### Backend (apps/api/python/translator_api/)
- FastAPI + SQLAlchemy + PostgreSQL
- 31 endpoints qua 5 router files
- Temporal đã cấu hình nhưng **worker process nằm ngoài repo**
- **pyVideoTrans không được tích hợp** — chỉ tham khảo trong docstrings

### Provider Registry
| Category | Provider | Trạng thái |
|---|---|---|
| ASR | whisperx_faster_whisper | **Thật** |
| Diarization | pyannote_3_1 | **Thật** |
| Translation | openai_compatible_http | **Thật** |
| Translation | gemini_compatible_http | **Thật** |
| Translation | claude_compatible_http | **Thật** |
| Translation | local_llm | **Thật** |
| QA | rule_based | **Thật** |
| Subtitle | cps_wrapper | **Thật** |
| Mix | ffmpeg_mix | **Thật** |
| Dubbing align | ffmpeg_atempo | **Thật** |
| Render | ffmpeg_render | **Thật** |
| Export | ffmpeg_export | **Thật** |
| TTS (cloud) | edge_tts, dashscope_tts, azure, google, elevenlabs | **Thật** |
| TTS (local) | vietvoice_tts, melo_tts_vi, cosyvoice_3, vieneu_v3_turbo | **STUB** |
| OCR | paddleocr, easyocr, craft | **STUB** |
| Voice clone | vieneu_voice_clone, cosyvoice3_voice_clone | **STUB** |
| Audio separation | uvr5_mdx, demucs, bs_roformer | **STUB** |

---

## 2. MỤC TIÊU

Xây dựng China-VNE thành webapp AI video localization hoàn chỉnh:

```
USER → WEBAPP → PROJECT → UPLOAD → ASR → TRANSCRIPT → TRANSLATE → SPEAKER/VOICE → TTS → SUBTITLE → AUDIO MIX → RENDER → PREVIEW → EXPORT
```

Frontend là professional video editor UX. Backend là provider registry điều khiển bởi Temporal worker.

---

## 3. WORKFLOW STATE MACHINE

### Trạng thái chính
```
PROJECT_CREATED
      ↓
ASSET_UPLOADED
      ↓
ANALYZING
      ↓
ASR_PROCESSING
      ↓
TRANSCRIPT_READY
      ↓
TRANSLATING
      ↓
TRANSLATION_READY
      ↓
REVIEW (WAITING_FOR_INPUT)
      ↓
VOICE_ASSIGNMENT
      ↓
TTS_PROCESSING
      ↓
SUBTITLE_READY
      ↓
AUDIO_MIXING
      ↓
RENDERING
      ↓
COMPLETED
```

### Trạng thái lỗi
```
FAILED / CANCELLED / PAUSED
```

---

## 4. APPLICATION SHELL

```
┌───────────────────────────────────────────────────┐
│ China-VNE                         Project / User  │
├─────────────┬─────────────────────────────────────┤
│ Dashboard   │                                     │
│ Projects    │                                     │
│ Voices      │         MAIN CONTENT                │
│ Assets      │                                     │
│ Settings    │                                     │
│             │                                     │
├─────────────┴─────────────────────────────────────┤
│ Global status / background jobs                    │
└───────────────────────────────────────────────────┘
```

---

## 5. DASHBOARD

Hiển thị:
- Recent Projects
- Active Jobs
- Completed Jobs
- Failed Jobs
- Create Project

CTA chính: `+ Tạo dự án China → Việt Nam`

---

## 6. CREATE PROJECT FLOW

```
Create Project
      ↓
Select Video
      ↓
Upload (drag & drop, progress, retry, cancel)
      ↓
Detect metadata (duration, resolution, fps, audio)
      ↓
Source = Chinese / Target = Vietnamese
      ↓
Choose quality (Fast / Balanced / High)
      ↓
Create Project
```

---

## 7. PROJECT WORKSPACE (TRUNG TÂM CỦA WEBAPP)

```
┌─────────────────────────────────────────────────┐
│ Project Header                                  │
├──────────────┬──────────────────────────────────┤
│ TOOL PANEL   │                                  │
│              │           VIDEO PREVIEW           │
│ Transcript   │                                  │
│ Translation  │                                  │
│ Speakers     │                                  │
│ Voices       │                                  │
│ Subtitle     │                                  │
│ Audio        │                                  │
├──────────────┴──────────────────────────────────┤
│ Timeline                                         │
├──────────────────────────────────────────────────┤
│ Properties / Inspector                           │
└──────────────────────────────────────────────────┘
```

### Navigation
- Không reload page khi đổi giữa Transcript / Translation / Speaker / Voice / Subtitle / Audio
- Dùng workspace tabs hoặc left tool navigation
- Video player luôn accessible

---

## 8. VIDEO PREVIEW

Controls:
- Play / Pause
- Seek
- Volume
- Speed
- Fullscreen
- Frame step
- Current time display

---

## 9. TRANSCRIPT MODE

Hiển thị:
```
timestamp | speaker | Chinese text
```

Click segment → seek video + highlight timeline + highlight speaker

---

## 10. TRANSLATION MODE

Hiển thị:
```
Chinese
Vietnamese
Speaker
Timestamp
```

Cho phép: Edit / Save / Regenerate / Accept

Mỗi segment có status:
```
AUTO / REVIEW / EDITED / APPROVED / ERROR
```

---

## 11. SPEAKER MODE

```
Speaker 01
Speaker 02
Speaker 03
```

Cho phép: Rename / Gender / Voice / Preview

Speaker → Character → Voice mapping nếu backend hỗ trợ.

---

## 12. VOICE MODE

Voice Library với card:
```
Voice Name | Gender | Provider | Model | Language | Preview | Use
```

---

## 13. TTS FLOW

```
Generate TTS → Queued → Generating → Completed → Failed
```

Hiển thị audio preview.

Mỗi segment:
```
Vietnamese text | Voice | Duration | Generated audio
```

Buttons: ▶ Preview / Regenerate / Change voice

---

## 14. SUBTITLE MODE

Components:
```
Video | Waveform | Timeline | Subtitle list | Inspector
```

Segment:
```
Start | End | Text
```

Actions:
```
Add | Split | Merge | Delete | Move | Resize
```

---

## 15. AUDIO PANEL

Hiển thị:
```
Original Voice | Vietnamese Voice | Music | SFX
```

Controls:
```
Volume | Mute | Solo
```

Chỉ hiển thị controls mà backend thật sự hỗ trợ.

---

## 16. PROCESSING CENTER

Pipeline visualization:
```
✓ Analyze
✓ ASR
✓ Alignment
✓ Diarization
✓ Translate
● TTS
○ Subtitle
○ Audio
○ Render
```

Mỗi stage: status / progress / duration / error

---

## 17. RENDER PAGE

Settings:
```
Output | Resolution | FPS | Video Codec | Audio Codec | Subtitle | Audio Mode | Quality
```

CTA: `Render Video`

Sau render: Preview / Open / Export / Render Again

---

## 18. WORKFLOW MODES

### Auto
```
Upload → Process all → Render
```

### Assisted
```
ASR → Review → Translate → Review → TTS → Render
```

### Professional
Cho phép kiểm soát từng stage.

---

## 19. REAL-TIME UPDATES

Ưu tiên: SSE (đã có `useWorkflowStream`)

Backup: polling với interval hợp lý

---

## 20. ERROR HANDLING

User-facing:
```
[TTS generation failed]
[Retry] [Change Voice] [View Details]
```

Developer details (stacktrace, provider response, job ID) — không hiển thị mặc định.

---

## 21. HUMAN-IN-THE-LOOP

Cho phép user can thiệp:
```
ASR Review | Translation Review | Speaker Review | Voice Review | Subtitle Review
```

Nhưng cũng có Auto Mode để chạy tự động.

---

## 22. UNDO / REDO

Hỗ trợ cho:
```
subtitle | translation | timestamp | split | merge | speaker assignment | voice assignment
```

---

## 23. AUTOSAVE

Hiển thị:
```
Saving... | Saved | Unsaved changes
```

---

## 24. KEYBOARD SHORTCUTS

Tối thiểu:
```
Space — Play/Pause
← → — Frame step
Ctrl/Cmd + Z — Undo
Ctrl/Cmd + Shift + Z — Redo
Delete — Delete segment
Enter — Confirm
I O — Set in/out
```

---

## 25. SEARCH / FILTER

Transcript:
```
Search Chinese | Search Vietnamese | Filter Speaker | Filter status
```

---

## 26. I18N

Mặc định: Vietnamese

Hỗ trợ: vi-VN / en-US / zh-CN

---

## 27. RESPONSIVE

Ưu tiên: 1280×720 → 1920×1080

Desktop-first.

---

## 28. DESIGN SYSTEM

Ưu tiên UI hiện tại:
```
Tailwind + Radix / shadcn/ui nếu có
```

Phong cách:
```
Dark-first | Professional | Minimal | Dense | Fast | Video-editor feel | AI tool
```

---

## 29. COMPONENTS CẦN TẠO

```
AppShell
Sidebar
ProjectHeader
VideoPlayer
Timeline
TimelineTrack
TimelineSegment
TranscriptPanel
TranslationPanel
SpeakerPanel
VoicePanel
SubtitlePanel
AudioPanel
ProcessingPanel
JobStatus
RenderPanel
AssetLibrary
Inspector
UploadDropzone
```

---

## 30. STATE MANAGEMENT

Dùng Zustand cho editor state:

```typescript
currentTime: number
duration: number
selectedSegment: Segment | null
selectedTrack: Track | null
zoom: number
playing: boolean
volume: number
```

---

## 31. PERFORMANCE

- Timeline không lag
- Không rerender 1000 segments mỗi khi playhead thay đổi
- Dùng memoization, virtualization, debouncing, throttling, lazy loading khi cần

---

## 32. UPLOAD UX

```
Drag & Drop | Browse File
Upload Progress | Cancel Upload | Retry
```

Sau upload hiển thị:
```
Video thumbnail | Filename | Duration | Resolution | FPS | Audio | Size
```

---

## 33. CAPABILITY GATING

Backend expose `/capabilities` endpoint:

```json
{
  "asr": true,
  "translation": true,
  "tts": true,
  "diarization": true,
  "voice_clone": false,
  "audio_separation": false,
  "ocr": false,
  "text_removal": false
}
```

Frontend dựa vào capability này — không hiển thị button giả.

---

## 34. API CONTRACT

Frontend cần:

```
POST /projects
POST /projects/{id}/assets
GET  /projects/{id}
GET  /projects/{id}/workflows
POST /projects/{id}/workflows
GET  /projects/{id}/workflows/{workflow_id}/steps
GET  /workflows/{workflow_id}/events  (SSE)
GET  /workflows/{workflow_id}/ws      (WebSocket)

GET  /projects/{id}/transcript
PUT  /projects/{id}/transcript

GET  /projects/{id}/translation
PUT  /projects/{id}/translation

GET  /projects/{id}/speakers
PUT  /projects/{id}/speakers

GET  /projects/{id}/voices
PUT  /projects/{id}/voices

GET  /projects/{id}/subtitles
PUT  /projects/{id}/subtitles

GET  /projects/{id}/provider-configs
PUT  /projects/{id}/provider-configs

GET  /capabilities

POST /projects/{id}/jobs/{job_id}/pause
POST /projects/{id}/jobs/{job_id}/resume
POST /projects/{id}/jobs/{job_id}/cancel
```

---

## 35. PARTIAL WORKFLOW / ERROR RECOVERY

Nếu TTS fail:
```
Retry TTS
```

Không:
```
Restart Everything
```

Chỉ restart stage cần thiết.

---

## 36. VERSIONING ARTIFACTS

```
TranscriptVersion
TranslationVersion
SubtitleVersion
TTSVersion
RenderVersion
```

---

## 37. STATUS BADGES

```
Draft | Processing | Review | Ready | Completed | Failed | Outdated
```

---

## 38. SECURITY

Không expose:
```
API keys | provider secrets | database credentials | Temporal credentials
```

Frontend chỉ nhận config an toàn.

---

## 39. IMPLEMENTATION PHASES

### PHASE 0 — AUDIT ✓ (đã xong)

### PHASE 1 — SỬA BUG BACKEND
1. Fix `routers.py:77` hardcode `owner_id=UUID(int=0)` → derive từ auth
2. Fix `routers.py:118` hardcode `asset_id=UUID(int=0)` → tạo Asset row trước khi trả presign URL
3. Fix `routers_governance.py:197-215` `set_quality_mode` → ghi `payload.mode` không phải provider name
4. Fix `ProviderConfigRepository` → thêm upsert, không insert duplicate
5. Fix `models/voice.py` → thêm `speaker_id`, `updated_at`, `embedding_storage_key`
6. Fix `models/project.py` → đổi `quality_mode` default thành giá trị hợp lệ
7. Thêm `/capabilities` endpoint
8. Thêm audit log cho project / workflow / provider-config mutations

### PHASE 2 — FRONTEND FOUNDATION
1. Thêm Tailwind config
2. Thêm Zustand cho editor state
3. Tạo `lib/api.ts` — unified API client với Bearer token
4. Sửa API base inconsistency — tất cả pages dùng `NEXT_PUBLIC_API_BASE_URL`
5. Tạo proxy routes cho `/api/*` pages (admin/voice/workflow) → forward đến backend
6. Tạo `AppShell` component
7. Tạo `Sidebar` component
8. Cập nhật `layout.tsx` → AppShell + Sidebar
9. Cập nhật `app/page.tsx` → Real Dashboard

### PHASE 3 — PROJECT WORKSPACE
1. Tạo `app/projects/[id]/workspace/page.tsx`
2. Tạo `VideoPlayer` component
3. Tạo workspace layout (tool panel + preview + timeline + inspector)
4. Implement workspace navigation (tabs/query params, không reload)
5. Tạo Zustand store cho editor state
6. Implement SSE connection cho workflow progress
7. Tạo `ProcessingPanel` component

### PHASE 4 — UPLOAD
1. Tạo `UploadDropzone` với drag & drop
2. Chunked presigned upload với progress
3. Retry / cancel support
4. Sau upload → hiển thị metadata

### PHASE 5 — TRANSCRIPT
1. Tạo `TranscriptPanel` component
2. Hiển thị segments (timestamp / speaker / Chinese text)
3. Click segment → seek video
4. Search / filter

### PHASE 6 — TRANSLATION
1. Tạo `TranslationPanel` component
2. Side-by-side Chinese / Vietnamese
3. Edit / Save / Regenerate / Accept
4. Status badges per segment

### PHASE 7 — SPEAKER / VOICE
1. Tạo `SpeakerPanel` component
2. Tạo `VoicePanel` component
3. Speaker → Voice assignment
4. Voice preview

### PHASE 8 — TTS
1. Tạy `TTSPanel` component
2. Generate TTS cho segments
3. Progress / retry / outdated state
4. Audio preview

### PHASE 9 — SUBTITLE
1. Tạo `SubtitlePanel` component
2. Timeline với waveform nếu backend cung cấp
3. Split / merge / resize segments
4. Sync với video

### PHASE 10 — AUDIO
1. Tạo `AudioPanel` component
2. Volume / mute / solo controls

### PHASE 11 — TIMELINE
1. Tạo `Timeline` component
2. Track types: Video / Original Audio / Voice / Music / SFX / Subtitle
3. Interactions: select / drag / resize / split / merge / snap / zoom / scroll / seek

### PHASE 12 — RENDER
1. Tạo `RenderPanel` component
2. Render settings UI
3. Render progress
4. Output preview

### PHASE 13 — UNDO/REDO + AUTOSAVE
1. Implement history stack
2. Implement autosave với status indicator

### PHASE 14 — KEYBOARD SHORTCUTS
1. Implement shortcuts

### PHASE 15 — POLISH
1. Empty states
2. Loading states
3. Error toasts
4. Accessibility

---

## 40. NGƯỜI THỰC HIỆN

**Bắt đầu từ Phase 1 — Sửa Bug Backend**

Chỉ sửa bug. Không thêm feature mới.
