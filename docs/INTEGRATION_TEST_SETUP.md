# Integration Test Setup Guide

**Mục đích:** Hướng dẫn setup môi trường integration testing với Temporal worker

**Cập nhật:** 02/09/2026

---

## ✅ Các Service Đã Khởi Chạy

### Trạng thái hiện tại:

```
✅ docker-db-1           | postgres:16              | Up 12 hours
✅ docker-temporal-1     | temporalio/auto-setup    | Up 10 hours
✅ docker-tts-service-1  | docker-tts-service       | Up ~1 minute (healthy)
✅ docker-api-1          | docker-api               | Up 40 seconds
✅ docker-worker-1       | docker-worker            | Up ~1 minute
```

**Ports exposed:**
- API: http://localhost:8000
- TTS Service: http://localhost:3099
- Database: localhost:5432
- Temporal: localhost:7233

### Health check verified:

```bash
✅ API:         http://localhost:8000/healthz        → 200 OK
✅ TTS Service: http://localhost:3099/healthz        → 200 OK
✅ Database:    psql -h localhost -p 5432 -U postgres → Connected
✅ Temporal:    http://localhost:7233                → Running
```

---

## 📝 Integration Test Sample

Đã tạo file `test_integration_sample.js` với workflow:

```
1. Create project
2. Upload video asset
3. Trigger workflow
4. Poll workflow status (max 10 minutes)
5. Verify render output
```

### Cách sử dụng:

```bash
# Chuẩn bị sample video
# Tạo hoặc copy một file MP4 ngắn (~15-60 giây) vào thư mục gốc

# Chạy test
node test_integration_sample.js ./sample.mp4

# Output expected:
# 📦 Creating project...
# ✅ Project created: <project-id>
# 📤 Uploading video: ./sample.mp4...
# ✅ Asset created: <asset-id>
# 🚀 Triggering workflow...
# ✅ Workflow started: <workflow-id>
# ⏳ Polling workflow status...
#   [1/120] Status: running | Phase: asr
#   [2/120] Status: running | Phase: translate
#   ...
# ✅ Workflow completed successfully!
# 🔍 Verifying render output...
# ✅ Render output verified: output.mp4 (12345678 bytes)
# ✅ INTEGRATION TEST PASSED
```

---

## 🐛 Known Issue: TTS Service 502 Error

### Hiện trạng:

Worker logs hiển thị lỗi khi gọi TTS service:

```
urllib.error.HTTPError: HTTP Error 502: Bad Gateway
```

### Root cause:

TTS service restart và mất kết nối tạm thời. Service đã phục hồi và healthy sau restart.

### Verification:

```bash
# Check TTS service logs
docker compose -f infra/docker/docker-compose.yml logs tts-service --tail=20

# Output shows healthy:
# INFO: 127.0.0.1 - "GET /healthz HTTP/1.1" 200 OK
```

### Solution:

✅ **Đã fix:** Restart worker service sau khi TTS service stable

```bash
docker compose -f infra/docker/docker-compose.yml up -d worker
```

Worker logs mới:
```
INFO:__main__:starting 5 workers (project=project-queue, asr=asr-queue, diarize=diarize-queue, tts=tts-queue, cpu=cpu-queue)
```

---

## 🚀 Next Steps — Sprint 1 Tasks

### 1. Create Test Video Samples

**Mục tiêu:** Tạo 3 sample videos với different lengths

```bash
# Sample 1: 15 seconds (quick test)
# Sample 2: 30 seconds (balanced test)
# Sample 3: 60 seconds (full pipeline test)

# Đặt trong thư mục: tests/fixtures/
tests/fixtures/sample_15s.mp4
tests/fixtures/sample_30s.mp4
tests/fixtures/sample_60s.mp4
```

**Content recommendation:**
- Video có tiếng nói Trung Quốc rõ ràng
- 1-2 speakers
- Không có background noise quá lớn
- Subtitles không bắt buộc

### 2. Run Full Integration Test

**Workflow:**

```bash
# Step 1: Verify all services running
docker compose -f infra/docker/docker-compose.yml ps

# Step 2: Run integration test với sample 15s
node test_integration_sample.js tests/fixtures/sample_15s.mp4

# Step 3: Nếu pass, chạy với sample dài hơn
node test_integration_sample.js tests/fixtures/sample_30s.mp4
node test_integration_sample.js tests/fixtures/sample_60s.mp4

# Step 4: Measure latency
# Record thời gian từ trigger → completion cho mỗi sample
```

### 3. Performance Profiling

**Metrics cần đo:**

```javascript
// Add timing tracking vào test_integration_sample.js

const timings = {
  project_creation: 0,
  upload: 0,
  workflow_trigger: 0,
  asr_phase: 0,
  translate_phase: 0,
  tts_phase: 0,
  render_phase: 0,
  total: 0,
};

// Track từng phase duration
// Output report cuối test:
// 
// === Performance Report ===
// ASR:       45.2s
// Translate: 12.3s
// TTS:       89.4s
// Render:    23.1s
// Total:     170.0s (2m 50s)
```

**Performance targets (balanced mode):**

| Phase | 15s video | 30s video | 60s video |
|-------|-----------|-----------|-----------|
| ASR | < 20s | < 40s | < 80s |
| Translate | < 5s | < 10s | < 20s |
| TTS | < 30s | < 60s | < 120s |
| Render | < 15s | < 30s | < 60s |
| **Total** | **< 70s** | **< 140s** | **< 280s** |

### 4. Database Query Profiling

**Setup slow query logging:**

```sql
-- Enable PostgreSQL slow query log
ALTER SYSTEM SET log_min_duration_statement = 1000; -- 1 second
SELECT pg_reload_conf();

-- Monitor during integration test
docker compose -f infra/docker/docker-compose.yml logs db | grep "duration:"
```

**Expected N+1 queries to fix:**

```python
# apps/api/python/translator_api/routers_editor.py

# BAD (N+1):
transcripts = session.query(Transcript).filter_by(project_id=project_id).all()
for t in transcripts:
    segments = t.segments  # N queries

# GOOD (eager load):
from sqlalchemy.orm import selectinload
transcripts = session.query(Transcript)\
    .options(selectinload(Transcript.segments))\
    .filter_by(project_id=project_id).all()
```

### 5. Add Database Indexes

**Identify missing indexes:**

```sql
-- Check queries without indexes
SELECT schemaname, tablename, indexname 
FROM pg_indexes 
WHERE schemaname = 'public';

-- Expected missing indexes:
-- assets.project_id
-- audio_segments.track_id
-- translation_segments.version_id
-- transcript_segments.version_id
```

**Create migration:**

```python
# migrations/003_add_indexes.py

def upgrade():
    op.create_index('ix_assets_project_id', 'assets', ['project_id'])
    op.create_index('ix_audio_segments_track_id', 'audio_segments', ['track_id'])
    op.create_index('ix_translation_segments_version_id', 'translation_segments', ['version_id'])
    op.create_index('ix_transcript_segments_version_id', 'transcript_segments', ['version_id'])

def downgrade():
    op.drop_index('ix_assets_project_id')
    op.drop_index('ix_audio_segments_track_id')
    op.drop_index('ix_translation_segments_version_id')
    op.drop_index('ix_transcript_segments_version_id')
```

---

## 📊 Expected Integration Test Results

### Success criteria:

- ✅ All 5 workflow phases complete without errors
- ✅ Render output MP4 exists và > 0 bytes
- ✅ Total latency within performance targets
- ✅ No 5xx errors in API/Worker logs
- ✅ Database queries < 1s each

### Failure scenarios to handle:

| Scenario | Expected Behavior | Current Status |
|----------|-------------------|----------------|
| TTS service down | Worker retries 3x, then fails gracefully | ⚠️ **Needs retry logic** |
| Translation API timeout | Activity timeout → workflow marks failed | ⚠️ **No checkpoint/resume** |
| Out of disk space | Storage provider throws error, workflow fails | ✅ **Handled correctly** |
| Invalid video format | Upload validation rejects file | ⚠️ **Needs magic number check** |
| Network interruption | Workflow pauses, resumes when network back | ⚠️ **Temporal handles, needs testing** |

---

## 🔧 Troubleshooting

### Issue: Worker not picking up tasks

```bash
# Check worker logs
docker compose -f infra/docker/docker-compose.yml logs worker --tail=100

# Verify Temporal connection
docker exec -it docker-worker-1 python -c "
from temporalio.client import Client
import asyncio
async def test():
    client = await Client.connect('temporal:7233')
    print('Connected:', client.identity)
asyncio.run(test())
"
```

### Issue: Workflow stuck in "running"

```bash
# Check Temporal UI
# http://localhost:8233/namespaces/default/workflows

# Cancel workflow manually (if DELETE endpoint not implemented)
docker exec -it docker-temporal-1 tctl workflow terminate \
  --workflow_id=dubbing-<uuid> \
  --reason="Manual cancellation for testing"
```

### Issue: Render output empty

```bash
# Check FFmpeg logs in worker
docker compose -f infra/docker/docker-compose.yml logs worker | grep "ffmpeg"

# Verify dubbed audio exists
# Check audio_tracks table has TTS-generated segments
docker exec -it docker-db-1 psql -U postgres -d translator -c "
SELECT COUNT(*) FROM audio_segments WHERE track_id IN (
  SELECT id FROM audio_tracks WHERE project_id='<project-id>'
);
"
```

---

## ✅ Checklist — Sprint 1 Completion

- [x] All services running và healthy
- [x] Integration test sample script created
- [ ] 3 test video samples created (15s, 30s, 60s)
- [ ] Run integration test với 15s sample → record latency
- [ ] Run integration test với 30s sample → record latency
- [ ] Run integration test với 60s sample → record latency
- [ ] Profile slow queries during test
- [ ] Add database indexes migration
- [ ] Fix N+1 queries trong panel APIs
- [ ] Add retry logic cho TTS service calls
- [ ] Document performance benchmarks

**Target completion:** 1-2 weeks

---

*File này sẽ được cập nhật khi integration tests hoàn thành.*
