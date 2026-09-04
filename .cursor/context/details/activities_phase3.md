# activities_phase3.py

**Path:** `apps/worker/python/translator_worker/activities_phase3.py`

## Purpose
Phase 3 Temporal activities: translate, QA, subtitle, normalize, TTS, separation, mix, dubbing align, render, export, cleanup.

## Key Activities

### Translation
- **Activity**: `translate_activity()`
- **Provider**: Configurable (Claude, Gemini, OpenAI, Local LLM, Passthrough)
- **Input**: `TranslationInput` (source text, glossary, context)
- **Output**: `TranslationSegment[]` (translated text per segment)
- **Registry Key**: `TRANSLATE`

### QA (Quality Assurance)
- **Activity**: `qa_activity()`
- **Provider**: `RuleBasedQaProvider`
- **Input**: `QaInput` (translation segments)
- **Output**: QA report with warnings/errors
- **Registry Key**: `QA`

### Subtitle Generation
- **Activity**: `subtitle_activity()`
- **Provider**: `CpsWrapperSubtitleProvider`
- **Input**: `SubtitleInput` (translation segments, CPS rules)
- **Output**: Formatted subtitle tracks (SRT/VTT)
- **Registry Key**: `SUBTITLE`

### TTS (Text-to-Speech)
- **Activity**: `tts_activity()`
- **Provider**: Configurable (VietVoice, Azure, ElevenLabs, MeloTTS, CosyVoice, etc.)
- **Input**: `TtsProviderConfig` (text, voice_id, locale)
- **Output**: Audio files per segment
- **Registry Key**: `TTS`

### Audio Separation
- **Activity**: `separation_activity()`
- **Provider**: `Uvr5MdxProvider`
- **Input**: `SeparationInput` (mixed audio)
- **Output**: Separated vocal and instrumental tracks
- **Registry Key**: `AUDIO_SEPARATION`

### Audio Mixing
- **Activity**: `mix_activity()`
- **Provider**: `FfmpegMixProvider`
- **Input**: `MixInput` (vocal, instrumental, background music)
- **Output**: Final mixed audio track
- **Registry Key**: `MIX`

### Dubbing Alignment
- **Activity**: `dubbing_align_activity()`
- **Provider**: `FfmpegAtempoAlignProvider`
- **Input**: `DubbingAlignInput` (audio segments, target durations)
- **Output**: Time-stretched audio matching video timing
- **Registry Key**: `DUBBING`

### Video Rendering
- **Activity**: `render_activity()`
- **Provider**: `FfmpegRenderProvider`
- **Input**: `RenderInput` (video, audio, subtitles)
- **Output**: Final rendered video with translated audio + subtitles
- **Registry Key**: `RENDER`

### Export
- **Activity**: `export_activity()`
- **Provider**: `FfmpegExportProvider`
- **Input**: `ExportInput` (render job, format options)
- **Output**: Exported video in requested format
- **Registry Key**: `EXPORT`

### Cleanup
- **Activity**: `cleanup_activity()`
- **Provider**: `OrphanCleanupProvider`
- **Input**: Project ID
- **Output**: `CleanupReport` (deleted files, freed space)

## Helper Functions

### `_ctx(project_id, asset_id, session) -> ProviderContext`
Creates provider context with:
- Project/asset IDs
- Database session
- Storage instance

### `_record_step(session, project_id, name, status, ...)`
Records workflow step in database:
- Creates `WorkflowStep` record
- Updates workflow status
- Stores signature, message, attempt count

### `_latest_workflow(session, project_id) -> Workflow | None`
Fetches latest workflow for project

## Design Patterns
- **Activity-based architecture**: Each activity is a Temporal activity
- **Provider registry**: Dynamic provider selection via registry
- **Context passing**: `ProviderContext` carries shared dependencies
- **Error handling**: Activities record failures in workflow steps
- **Idempotency**: Activities can be retried safely

## Configuration
All activities use provider configs from database:
```python
config = ProviderConfigRepository(session).get_active_config(
    project_id=project_id,
    provider_type=TRANSLATE
)
```

## Recent Changes
- Added dubbing alignment activity
- Integrated UVR5 MDX audio separation
- Added export activity for multiple formats
- Improved error recording in workflow steps

## Testing Notes
- Each activity should be tested with all supported providers
- Verify idempotency (retry safety)
- Check error handling and step recording
- Test with various input formats

## Related Files
- Workflow: `apps/worker/python/translator_worker/workflows_impl.py`
- Providers: `apps/api/python/translator_api/providers/**/*.py`
- Models: `apps/api/python/translator_api/models/*.py`
- Registry: `apps/api/python/translator_api/providers/registry.py`
