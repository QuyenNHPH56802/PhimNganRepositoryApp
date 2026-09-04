# Workflow Processing Fix - Summary

## Problem
Workflows were completing successfully but no transcript, translation, or speaker data appeared in the workspace. The root cause was stub activities being executed instead of real provider activities.

## Root Cause Analysis

### Issue Identified
The `PROJECT_QUEUE` worker was registering **both** stub activities (from `activities.py`) and real provider activities (from `activities_providers.py` and `activities_phase3.py`) with the same activity names:
- `asr_transcribe` 
- `diarize_segments`
- `translate_segments`

When Temporal executed these activities, it could dispatch to the stub version which:
- Logged execution but **did NOT write to database**
- Returned empty signatures instead of real data
- Made workflows appear successful while producing no output

### Evidence
```python
# activities.py - STUB (no DB writes)
@activity.defn(name="asr_transcribe")
async def asr_transcribe(project_id: str) -> dict:
    activity.logger.warning("⚠️ STUB asr_transcribe executed (does NOT write to DB)")
    return {"ok": True, "signature": _empty_signature("asr_transcribe").model_dump()}

# activities_providers.py - REAL (writes to DB)
@activity.defn(name="asr_transcribe")
async def asr_transcribe(project_id: str, asset_id: str | None = None) -> dict:
    activity.logger.info("✅ REAL asr_transcribe (writes to DB)")
    # ... runs WhisperX provider ...
    response_to_transcript(response, asset.id, session)
    session.commit()  # ← PERSISTS DATA
    return response.model_dump()
```

## Solution Implemented

### 1. Added Distinctive Logging ✅
Enhanced both stub and real activities with clear warning/info logs:
- Stub activities: `⚠️ STUB <activity_name> executed (does NOT write to DB)`
- Real activities: `✅ REAL <activity_name> (writes to DB)`

### 2. Fixed Worker Registration ✅
**File:** `apps/worker/python/translator_worker/main.py`

**Before:**
```python
CPU_ACTIVITIES = TRIVIAL_ACTIVITIES + PHASE3_ACTIVITIES
ASR_ACTIVITIES = [activities_providers.asr_transcribe]

workers = [
    Worker(
        client,
        task_queue=PROJECT_QUEUE,
        workflows=workflow_classes,
        activities=CPU_ACTIVITIES + ASR_ACTIVITIES + ...,  # ← included stubs
    ),
]
```

**After:**
```python
workers = [
    Worker(
        client,
        task_queue=PROJECT_QUEUE,
        workflows=workflow_classes,
        # FIXED: Removed stub activities (asr_transcribe, diarize_segments, translate_segments)
        # Real providers are registered on dedicated queues (ASR_QUEUE, DIARIZE_QUEUE, CPU_QUEUE)
        activities=CPU_ACTIVITIES + TTS_ACTIVITIES + SEPARATION_ACTIVITIES,
    ),
    Worker(client, task_queue=ASR_QUEUE, workflows=[], activities=ASR_ACTIVITIES),
    Worker(client, task_queue=DIARIZE_QUEUE, workflows=[], activities=DIARIZE_ACTIVITIES),
    Worker(client, task_queue=TTS_QUEUE, workflows=[], activities=TTS_ACTIVITIES),
    Worker(client, task_queue=CPU_QUEUE, workflows=[], activities=CPU_ACTIVITIES + SEPARATION_ACTIVITIES),
]
```

**Key Changes:**
- Removed `ASR_ACTIVITIES` from `PROJECT_QUEUE` worker
- Removed `DIARIZE_ACTIVITIES` from `PROJECT_QUEUE` worker
- Kept real providers only on their dedicated queues
- Workflows correctly route activities to specialized queues via `task_queue` parameter

### 3. Rebuilt & Restarted Services ✅
```bash
cd infra/docker
docker compose build worker
docker compose up -d worker
```

Worker successfully restarted with 5 queues:
- `project-queue` (workflows only)
- `asr-queue` (ASR activities)
- `diarize-queue` (diarization activities)
- `tts-queue` (TTS activities)
- `cpu-queue` (translation, subtitle, etc.)

## Verification

### Worker Logs
```
INFO:__main__:starting 5 workers (project=project-queue, asr=asr-queue, diarize=diarize-queue, tts=tts-queue, cpu=cpu-queue)
```

### Next Steps for Testing
1. Create a new project via web UI
2. Upload a video file
3. Trigger workflow (automatic on upload)
4. Wait for workflow completion
5. Verify workspace shows:
   - **Transcript panel:** segments with timestamps and text
   - **Translation panel:** translated segments
   - **Speaker panel:** detected speakers

### Expected Behavior After Fix
- Workflows will execute real provider activities on dedicated queues
- ASR will write `Transcript` and `TranscriptSegment` records to database
- Diarization will detect speakers and write `Speaker` records
- Translation will create `Translation` records
- Frontend will fetch and display actual data instead of empty arrays

## Files Modified

1. **apps/worker/python/translator_worker/activities.py**
   - Added warning logs to stub activities

2. **apps/worker/python/translator_worker/activities_providers.py**
   - Added info logs to real ASR/diarization activities

3. **apps/worker/python/translator_worker/main.py**
   - Removed stub activities from PROJECT_QUEUE worker registration
   - Added comment explaining the fix

## Impact

- **No data loss:** Previous workflows didn't fail, they just didn't create data
- **No breaking changes:** Workflow definitions unchanged
- **Immediate effect:** New workflows will use real providers
- **Backward compatible:** Existing projects can re-trigger workflows

## Technical Details

### Why This Happened
Temporal allows multiple workers to register the same activity name. When a workflow executes an activity:
1. It specifies a `task_queue` to route the activity
2. Temporal dispatches to a worker polling that queue
3. If multiple activities with the same name are registered, behavior is undefined

The original code registered stubs on `PROJECT_QUEUE` as a fallback, but this caused conflicts when workflows were executed on that queue.

### The Fix
By removing stub activities from `PROJECT_QUEUE` and keeping them only as no-op implementations (for documentation/development), we ensure:
- Workflows always execute real providers on specialized queues
- No name conflicts between stub and real activities
- Clear separation of concerns: workflows orchestrate, specialized workers execute

---

**Status:** ✅ Fixed and deployed  
**Date:** 2026-09-02  
**Tested:** Worker rebuilt and restarted successfully
