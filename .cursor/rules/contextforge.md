# ContextForge - Structured Project Memory

**Kích hoạt:** Mọi task, AI agent PHẢI đọc và update structured state files.

---

## 🎯 Mục Đích

ContextForge bổ sung cho Git-based memory (`.cursor/rules/project-memory.md`) bằng cách:
- **L1 Layer:** File index + 1-line summaries (fast lookup)
- **L2 Layer:** Detailed per-file context (deep understanding)
- **Decision log:** Track why, not just what
- **Task progress:** Session continuity

---

## 📂 Cấu Trúc Files

```
.cursor/
├── rules/
│   ├── project-memory.md    (Git workflow - ĐÃ CÓ)
│   └── contextforge.md       (Structured state - FILE NÀY)
├── context/
│   ├── PROJECT_STATE.md      (L1 - file index)
│   ├── DECISIONS.md          (design decisions)
│   ├── TASK_PROGRESS.md      (current session)
│   └── details/
│       ├── routers_editor.md
│       ├── activities_phase3.md
│       └── *.md              (L2 - per-file details)
└── PROJECT_CONTEXT.md        (Overview - ĐÃ CÓ)
```

---

## 🔄 Workflow: Đọc Trước - Update Sau

### BƯỚC 1: Đọc Context (Mỗi Task)

```bash
# 1. Đọc Git history (như project-memory.md)
git log --oneline -20
git status

# 2. Đọc L1 index
cat .cursor/context/PROJECT_STATE.md

# 3. Đọc decisions log
cat .cursor/context/DECISIONS.md | tail -50

# 4. Đọc task progress (session trước)
cat .cursor/context/TASK_PROGRESS.md
```

### BƯỚC 2: Làm Việc

- Follow guidelines từ `project-memory.md`
- Implement changes
- Take notes về decisions

### BƯỚC 3: Update State (Sau Mỗi Task)

**Luôn luôn update 3 files này:**

1. **PROJECT_STATE.md** - Nếu thêm/xóa/đổi tên files
2. **DECISIONS.md** - Nếu có design decision mới
3. **TASK_PROGRESS.md** - Summary task vừa làm

---

## 📋 L1: PROJECT_STATE.md Format

**Mục đích:** Fast lookup - AI scan nhanh để biết file nào chứa gì.

### Cấu trúc:

```markdown
# Project State Index (L1)

**Last Updated:** 2026-09-04 01:00 AM
**Total Files:** 187

## API Core Files

| File | Purpose | Last Changed |
|------|---------|--------------|
| `apps/api/python/translator_api/routers_editor.py` | Editor APIs (transcript, translation CRUD) | 2026-09-03 |
| `apps/api/python/translator_api/routers_providers.py` | Provider config APIs | 2026-09-04 |

## Worker Files

| File | Purpose | Last Changed |
|------|---------|--------------|
| `apps/worker/python/translator_worker/activities_phase3.py` | TTS & Translation activities | 2026-09-03 |

## Frontend Files

| File | Purpose | Last Changed |
|------|---------|--------------|
| `apps/web/app/projects/[id]/workspace/page.tsx` | Main workspace UI | 2026-09-03 |
```

### Update Rules:

- **Thêm file mới:** Thêm row vào table phù hợp
- **Đổi file:** Update "Last Changed" + "Purpose" nếu cần
- **Xóa file:** Xóa row

---

## 🧠 DECISIONS.md Format

**Mục đích:** Track why we made choices - giúp AI understand context.

### Cấu trúc:

```markdown
# Design Decisions Log

**Format:** Each decision is a timestamped entry.

---

## 2026-09-04 01:00 AM - Setup ContextForge Memory

**Context:** Cần persistent memory cho AI agent trên Windows.

**Decision:** Dùng ContextForge pattern (Git + structured files) thay vì agentmemory server.

**Reasoning:**
- agentmemory yêu cầu iii-engine binary/Docker phức tạp trên Windows
- ContextForge 100% git-based, không cần external dependencies
- Kết hợp được với Git workflow hiện tại

**Trade-offs:**
- ❌ Không có auto-capture như agentmemory
- ❌ AI phải manually update state files
- ✅ Đơn giản, reliable, Windows-friendly
- ✅ Version-controlled như code

**Status:** ✅ Implemented

---

## 2026-09-03 11:30 PM - Add Provider Config API

**Context:** Frontend cần fetch provider configs động.

**Decision:** Tạo `routers_providers.py` với endpoint GET `/providers/configs`.

**Reasoning:**
- Hardcode configs trong frontend không scalable
- Backend là source of truth cho provider configs
- Dễ maintain hơn khi thêm providers mới

**Trade-offs:**
- ✅ Centralized config management
- ✅ Easy to add new providers
- ⚠️ Thêm 1 API call khi load workspace

**Status:** ✅ Implemented

---
```

### Update Rules:

- **Mỗi design decision quan trọng** → Thêm entry mới
- **Format:** Context → Decision → Reasoning → Trade-offs → Status
- **Đủ detail:** Người (hoặc AI) đọc sau 6 tháng vẫn hiểu why

---

## 📌 TASK_PROGRESS.md Format

**Mục đích:** Session continuity - AI tiếp tục từ task trước.

### Cấu trúc:

```markdown
# Task Progress - Current Session

**Last Updated:** 2026-09-04 01:15 AM

---

## ✅ Completed Today (2026-09-04)

### Setup ContextForge Memory System
- Created `.cursor/context/` structure
- Created L1 index (PROJECT_STATE.md)
- Created decision log (DECISIONS.md)
- Created task progress (TASK_PROGRESS.md)
- Created ContextForge rules file
- **Result:** AI có structured memory system

### Research Memory Solutions
- Evaluated agentmemory, ai-memory, ContextForge
- Tested agentmemory (failed on Windows)
- Decided on ContextForge pattern
- **Result:** Clear path forward

---

## 🚧 In Progress

*None*

---

## 📋 Next Tasks

### High Priority
- [ ] Scan codebase và populate PROJECT_STATE.md với tất cả core files
- [ ] Review git history và extract design decisions vào DECISIONS.md
- [ ] Update `.cursor/rules/project-memory.md` để integrate với ContextForge

### Medium Priority
- [ ] Tạo L2 details cho top 10 core files
- [ ] Test workflow với task thực tế
- [ ] Document examples trong ContextForge rules

---

## 💭 Notes

- ContextForge hoạt động tốt với Git workflow hiện tại
- AI cần discipline để update state files consistently
- Consider tạo git pre-commit hook để remind update state
```

### Update Rules:

- **Sau mỗi task hoàn thành:** Di chuyển từ "In Progress" → "Completed"
- **Bắt đầu task mới:** Thêm vào "In Progress"
- **Think of next steps:** Update "Next Tasks"
- **Keep recent:** Chỉ giữ tasks 7 ngày gần nhất

---

## 📝 L2: details/*.md Format (Optional)

**Mục đích:** Deep context cho complex files.

**Khi nào tạo:** File >300 lines HOẶC complex logic HOẶC frequently modified.

### Template:

```markdown
# File Detail: routers_editor.py

**Path:** `apps/api/python/translator_api/routers_editor.py`
**Last Updated:** 2026-09-04
**LOC:** 450

## Purpose

Main editor APIs cho workspace UI. Handle CRUD operations cho:
- Transcripts (segments)
- Translations
- Speakers
- Project settings

## Key Functions

### `get_transcript_segments(project_id)`
- **Purpose:** Fetch all segments của project
- **Returns:** List[TranscriptSegment]
- **Called by:** Frontend workspace page on load
- **DB queries:** 1 query với joinedload(speakers)

### `update_translation(segment_id, text)`
- **Purpose:** Update translation text cho segment
- **Validates:** Text length, project access
- **Side effects:** Invalidate cache, trigger re-render workflow
- **Related:** `activities_phase3.py` để regenerate audio

## Dependencies

- `translator_api.models.transcript` - Transcript models
- `translator_api.repositories.transcript_repository` - DB operations
- `translator_api.security.rbac` - Permission checks

## Common Patterns

- **Auth:** Mọi endpoint dùng `require_project_access()`
- **Error handling:** Raise HTTPException với status codes chuẩn
- **Cache invalidation:** Gọi `cache.invalidate()` sau mỗi mutation

## Recent Changes

- **2026-09-03:** Add bulk update endpoint cho translations
- **2026-09-02:** Optimize N+1 queries với selectinload

## Known Issues

- None

## Testing

- Unit tests: `tests/api/test_routers_editor.py`
- Coverage: 87%
```

---

## ✅ AI Agent Checklist

Trước mỗi task, AI PHẢI:

- [ ] Đọc `git log --oneline -20`
- [ ] Đọc `PROJECT_STATE.md` (L1 index)
- [ ] Đọc `DECISIONS.md` (tail -50)
- [ ] Đọc `TASK_PROGRESS.md` (session context)
- [ ] Đọc L2 details cho files liên quan (nếu có)

Sau mỗi task, AI PHẢI update:

- [ ] `PROJECT_STATE.md` nếu thêm/xóa/đổi files
- [ ] `DECISIONS.md` nếu có design decision mới
- [ ] `TASK_PROGRESS.md` với task summary
- [ ] L2 details nếu modify complex file

---

## 🚨 Nguyên Tắc

### 1. Two-Source Truth System

- **Git history** = What happened (commits, code changes)
- **Structured state** = Why & context (decisions, progress)
- **Both** are required cho full understanding

### 2. Update Discipline

- ❌ KHÔNG skip updates vì "task nhỏ"
- ✅ LUÔN update state files, even for small changes
- **Lý do:** Small changes accumulate → lost context

### 3. Keep It Current

- **L1 (PROJECT_STATE.md):** Update immediately khi file thay đổi
- **DECISIONS.md:** Update khi make important choices
- **TASK_PROGRESS.md:** Update cuối mỗi session

### 4. Write for Future You

- Giả sử người đọc (AI hoặc human) không biết gì về task
- Đủ detail nhưng không verbose
- Focus on WHY, not just WHAT

---

## 🔍 Example Workflow

**Task:** "Add endpoint GET /projects/{id}/export"

### 1. Read Context

```bash
# Git history
git log --oneline -20 | grep -i export

# L1 index
grep -i export .cursor/context/PROJECT_STATE.md

# Recent decisions
tail -20 .cursor/context/DECISIONS.md

# Session progress
cat .cursor/context/TASK_PROGRESS.md
```

**Discovery:**
- Có `routers.py` với export logic cũ (PDF only)
- Decision log shows: "Export should be async via Temporal"
- Previous task: "Setup export workflow"

### 2. Implement

```python
# apps/api/python/translator_api/routers.py

@router.get("/projects/{project_id}/export")
async def export_project(
    project_id: int,
    format: str = "srt",
    db: Session = Depends(get_db)
):
    # Trigger Temporal workflow
    workflow_id = await temporal_client.start_export_workflow(
        project_id, format
    )
    return {"workflow_id": workflow_id, "status": "started"}
```

### 3. Update State

**PROJECT_STATE.md:**
```markdown
| `apps/api/python/translator_api/routers.py` | CRUD APIs + Export endpoint | 2026-09-04 |
```

**DECISIONS.md:**
```markdown
## 2026-09-04 01:30 AM - Make Export Async

**Context:** Export lớn (>1000 segments) timeout API.

**Decision:** Move export logic to Temporal workflow.

**Reasoning:**
- Long-running operations không phù hợp với HTTP request
- Temporal provides retry + monitoring
- Consistent với workflow pattern khác (TTS, translation)

**Trade-offs:**
- ✅ No timeout issues
- ✅ Better UX (progress tracking)
- ⚠️ More complex (need workflow + activity)

**Status:** ✅ Implemented
```

**TASK_PROGRESS.md:**
```markdown
## ✅ Completed Today

### Add Async Export Endpoint
- Created GET `/projects/{id}/export`
- Trigger Temporal workflow instead of sync processing
- Frontend polls workflow status
- **Result:** Export không timeout, có progress tracking
```

### 4. Commit

```bash
git add apps/api/python/translator_api/routers.py \
        .cursor/context/PROJECT_STATE.md \
        .cursor/context/DECISIONS.md \
        .cursor/context/TASK_PROGRESS.md

git commit -m "feat(api): add async export endpoint

- Create GET /projects/{id}/export
- Trigger Temporal workflow for large exports
- Prevent timeout for >1000 segments
- Follow async pattern from other workflows

Refs: .cursor/context/DECISIONS.md (2026-09-04 01:30 AM)"
```

---

## 🎓 Learning From State

### Quick Queries

```bash
# Tìm file liên quan đến feature
grep -i "translation" .cursor/context/PROJECT_STATE.md

# Xem decisions gần đây
tail -100 .cursor/context/DECISIONS.md

# Check progress tuần trước
git log --oneline --since="7 days ago" -- .cursor/context/TASK_PROGRESS.md

# Tìm khi nào decision được made
git log --oneline -- .cursor/context/DECISIONS.md | grep -i "export"
```

### Pattern Recognition

**AI học patterns từ DECISIONS.md:**
- "Async operations → use Temporal workflow"
- "Provider configs → centralize in backend"
- "Auth → always use require_project_access()"

**Result:** AI make consistent decisions, follow conventions.

---

## 📊 Integration với Git Workflow

ContextForge **BỔ SUNG** cho `project-memory.md`, không thay thế:

| Aspect | project-memory.md | ContextForge |
|--------|-------------------|--------------|
| **Source of truth** | Git commits | Structured state files |
| **What it tracks** | Code changes (what) | Decisions + progress (why) |
| **When to read** | Every task start | Every task start |
| **When to update** | Git commit | After completing task |
| **Format** | Git history | Markdown tables + logs |
| **Best for** | Seeing what changed | Understanding why |

**Together:** Complete context = Git history (what) + Structured state (why + progress)

---

## 🚀 Quick Start Commands

### Daily Workflow

```bash
# Morning: Check context
git log --oneline -20
cat .cursor/context/TASK_PROGRESS.md
tail -50 .cursor/context/DECISIONS.md

# During work: Take notes
# (mental notes về decisions + progress)

# Evening: Update state
vim .cursor/context/PROJECT_STATE.md     # Update file index
vim .cursor/context/DECISIONS.md         # Add decisions
vim .cursor/context/TASK_PROGRESS.md     # Summary tasks

# Commit
git add .cursor/context/
git commit -m "docs(context): update state after today's work"
```

---

## 💡 Tips

1. **Update immediately:** Đừng đợi đến cuối ngày, update ngay sau task
2. **Be specific:** "Added export" ❌ → "Added async export via Temporal workflow" ✅
3. **Link things:** Reference commits, files, decisions in state updates
4. **Review weekly:** Mỗi tuần review state files, clean up outdated info
5. **Commit state:** State files là part of codebase, commit như code

---

**Created:** 2026-09-04 01:00 AM  
**Author:** AI Agent (Claude) + Quyen  
**Version:** 1.0
