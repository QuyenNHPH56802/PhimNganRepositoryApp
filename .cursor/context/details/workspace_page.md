# workspace/page.tsx

**Path:** `apps/web/app/projects/[id]/workspace/page.tsx`

## Purpose
Main editor workspace UI for video translation projects. Central hub for all editing operations.

## Key Features
- **Video player**: Toggle between raw and rendered video
- **Timeline**: Waveform + segment visualization
- **Multi-panel editor**: Transcript, Translation, Speaker, Voice, Subtitle, Audio, Render, Progress
- **Real-time updates**: Workflow stream via SSE
- **Keyboard shortcuts**: Undo/Redo, panel switching
- **Autosave**: Automatic save with status indicator

## State Management
Uses Zustand store (`@/lib/store`) for:
- Current panel selection
- Project ID
- Video sources (raw/rendered)
- Editor data (transcript, translation, speakers, voices, subtitles, audio)
- Undo/redo history

## Panels (Tabs)
```typescript
const tabs: { id: Panel; label: string }[] = [
  { id: "transcript", label: "Bản ghi" },
  { id: "translation", label: "Bản dịch" },
  { id: "speaker", label: "Người nói" },
  { id: "voice", label: "Giọng nói" },
  { id: "subtitle", label: "Phụ đề" },
  { id: "audio", label: "Âm thanh" },
  { id: "render", label: "Render" },
  { id: "progress", label: "Tiến trình" },
];
```

## Workflow Progress Tracking
```typescript
const WORKFLOW_STEP_LABELS: Record<string, string> = {
  ingest: "Tải & chuẩn hoá video",
  asr: "Nhận dạng giọng nói (ASR)",
  align: "Canh chỉnh thời gian",
  diarize: "Phân tách người nói",
  translate: "Dịch Trung → Việt",
  tts: "Tổng hợp giọng nói (TTS)",
  align_audio: "Canh chỉnh audio",
  render: "Render video cuối",
};

const STAGE_WEIGHT: Record<string, number> = {
  ingest: 10,
  asr: 20,
  align: 10,
  diarize: 10,
  translate: 15,
  tts: 20,
  align_audio: 5,
  render: 10,
};
```

## Real-time Updates
Uses `useWorkflowStream()` hook to:
- Subscribe to SSE events from `/api/workflows/{id}/events`
- Update progress bar in real-time
- Show current step and status

## Keyboard Shortcuts
- `Ctrl+Z`: Undo
- `Ctrl+Y` / `Ctrl+Shift+Z`: Redo
- Panel switching shortcuts (defined in `useShortcuts()`)

## API Integration
Calls backend endpoints:
- `GET /api/v1/projects/{id}` - Fetch project metadata
- `GET /api/v1/projects/{id}/transcript` - Load transcript
- `GET /api/v1/projects/{id}/translation` - Load translation
- `GET /api/v1/projects/{id}/speakers` - Load speakers
- `GET /api/v1/projects/{id}/voices` - Load voices
- `GET /api/v1/projects/{id}/subtitles` - Load subtitles
- `GET /api/v1/projects/{id}/audio` - Load audio tracks

## Error Handling
- Shows toast notifications for errors
- Displays empty states when data not ready
- Handles 404 gracefully (artifact not generated yet)

## Performance Optimization
- Memoized panel components
- Lazy loading of heavy components
- Debounced autosave

## Related Files
- Backend: `apps/api/python/translator_api/routers_editor.py`
- Store: `apps/web/lib/store.ts`
- Types: `apps/web/lib/types.ts`
- Workflow Stream: `apps/web/lib/useWorkflowStream.ts`
- All panel components: `apps/web/components/panels/*.tsx`
