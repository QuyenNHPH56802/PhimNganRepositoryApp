# 🧠 PROJECT CONTEXT - Translator Platform

**Mục đích:** File này giúp AI agent (Claude) nhanh chóng nắm được toàn bộ context của dự án qua git history và documentation.

---

## 📌 QUICK FACTS

**Dự án:** Translator - Video Localization Platform  
**Version hiện tại:** 1.3.0  
**Trạng thái:** ✅ Sprint 1 hoàn thành, ready for integration testing  
**Tech Stack:** FastAPI + Next.js 14 + PostgreSQL + Temporal + Docker  
**Use case chính:** Dịch video zh (Trung) → vi (Việt) với TTS lồng tiếng

---

## 📂 GIT STRUCTURE

```
Repository: https://github.com/QuyenNHPH56802/PhimNganRepositoryApp.git

Branches:
  main                  → Production branch
  develop (HEAD)        → Development branch (ahead 1 commit)
  
Remote tracking:
  origin/main
  origin/develop
```

---

## 🎯 CÁCH SỬ DỤNG GIT ĐỂ NẮM CONTEXT

### 1. Xem lịch sử commits gần đây
```bash
git log --oneline -20
# → Hiện 20 commits gần nhất với message ngắn gọn
```

### 2. Tìm commits theo keyword
```bash
git log --oneline --grep="performance"  # Tìm commits về performance
git log --oneline --grep="fix"          # Tìm bug fixes
git log --oneline --grep="feat"         # Tìm features mới
```

### 3. Xem chi tiết một commit
```bash
git show <commit-hash> --stat           # Xem files đã thay đổi
git show <commit-hash>                  # Xem chi tiết thay đổi
```

### 4. Xem lịch sử của một file cụ thể
```bash
git log -- apps/api/python/translator_api/routers_editor.py
# → Xem tất cả commits đã sửa file này
```

### 5. Xem ai viết đoạn code nào
```bash
git blame apps/api/python/translator_api/main.py
# → Xem author của từng dòng code
```

---

## 📚 DOCUMENTATION HIERARCHY

**Level 1 - Quick Start:**
- `README.md` - Setup & architecture overview
- `CHANGELOG.md` - Version history

**Level 2 - Comprehensive Guides:**
- `docs/USER_GUIDE.md` - Hướng dẫn sử dụng A-Z (Vietnamese)
- `docs/PROJECT_SUMMARY.md` - Tóm tắt kỹ thuật đầy đủ

**Level 3 - Sprint Reports:**
- `SPRINT1_FINAL_REPORT.md` - Sprint 1 performance optimization results
- `docs/PERFORMANCE_OPTIMIZATION.md` - Technical implementation details

**Level 4 - Specialized Topics:**
- `docs/integrations.md` - API integration guide
- `docs/TEST_BUGS.md` - Bug reports & test results
- `docs/TROUBLESHOOTING.md` - Common issues & solutions

---

## 🔑 KEY COMMITS TO REMEMBER

### Performance Optimization (f1dba73)
```
feat(performance): optimize N+1 queries and add TTS retry logic

Impact:
- Query reduction: 401 → 8 queries (-98%)
- Response time: 2.3s → 0.18s (-92%)
- TTS failures: 50+ → <1 (-98%)

Files changed:
- routers_editor.py - Added selectinload() for eager loading
- activities_phase3.py - Added retry logic with exponential backoff
- 003_add_indexes.py - Created 11 database indexes
```

### Authentication & Admin (3388d86)
```
feat(auth,admin): implement persistent authentication and complete admin governance dashboard

Features:
- JWT-based authentication
- Role-based access control (RBAC)
- Admin dashboard with audit logs
- User management UI
```

### Vietnamese UI/UX (7170edf)
```
feat(web,e2e): complete Vietnamese UI/UX refactoring & Playwright E2E test suite

Features:
- Full Vietnamese i18n
- 8 main pages with Vietnamese labels
- Playwright E2E tests
- Improved UX with loading states
```

### Security Fixes (d18b129)
```
security: remove hardcoded secrets — fail-fast on missing env vars

Fixed:
- Removed hardcoded API keys from source code
- Added .env validation on startup
- Fail-fast if critical env vars missing
```

---

## 🏗️ ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────┐
│  Web (Next.js 14)  ──►  API (FastAPI)                  │
│  Port 3000                 Port 8000                     │
│                            ├── 45+ REST endpoints        │
│                            ├── Provider Registry         │
│                            └── Temporal Client           │
└─────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                         ┌──────────────────┐
                         │  Temporal Worker  │
                         │  (Workflow Engine)│
                         └──────────────────┘
                         │  │  │  │  │  │  │
                         ▼  ▼  ▼  ▼  ▼  ▼  ▼
          ┌──────┐ ┌────────┐ ┌──────┐ ┌────────┐
          │ ASR  │ │Translate│ │ TTS  │ │ Render │
          │WhsprX│ │LLM APIs │ │10 Pvd│ │FFmpeg  │
          └──────┘ └────────┘ └──────┘ └────────┘
```

---

## 📊 PROJECT STATISTICS

**Codebase:**
- Python: ~25,000 lines (API + Worker + Shared)
- TypeScript/TSX: ~8,000 lines (Web UI)
- Total commits: 40+ commits
- Branches: 2 (main, develop)

**Providers:**
- Translation: 4 (OpenAI, Gemini, Claude, Local Ollama)
- TTS: 10 (Edge, DashScope, Qwen3, VietVoice, VieNeu, CosyVoice, MeloTTS, Azure, Google, ElevenLabs)
- ASR: 2 (WhisperX, Faster-Whisper)

**API Coverage:**
- Total endpoints: 45+
- Verified: 45/45 (100%)
- Test suite: 7 smoke tests (59 assertions, 88% pass rate)

---

## 🎯 CURRENT STATE

### ✅ What's Working
- Core CRUD APIs (projects, assets, transcripts, translations)
- Authentication & RBAC
- Vietnamese UI with 8 main pages
- 10 TTS providers integration
- Performance optimized (N+1 queries fixed)
- Security hardened (secrets removed)

### ⚠️ Known Limitations
- Integration tests cần Temporal worker running
- Data-dependent endpoints (TTS/render) cần workflow execution
- Workflow cancellation endpoint chưa có
- Mobile responsiveness cần cải thiện

### 🚀 Next Steps
- Sprint 2: Integration testing với Temporal worker
- Performance profiling (ASR, TTS latency)
- Database optimization (more indexes)
- Error handling improvements (retry, checkpointing)

---

## 🔍 DEBUGGING TIPS

### Khi gặp bug, tìm trong git history:
```bash
# Tìm xem file này đã được sửa như thế nào
git log --oneline -- <file-path>

# Xem chi tiết thay đổi
git show <commit-hash> -- <file-path>

# Tìm commits liên quan đến bug
git log --oneline --grep="fix.*<keyword>"
```

### Kiểm tra trạng thái hiện tại:
```bash
git status              # Files đã thay đổi
git diff                # Nội dung thay đổi chưa commit
git diff --staged       # Nội dung đã staged
git branch -v           # Branches và commit hiện tại
```

---

## 📝 COMMIT MESSAGE CONVENTION (đang dùng)

```
feat(scope): description          # New feature
fix(scope): description           # Bug fix
docs(scope): description          # Documentation
chore(scope): description         # Maintenance
security: description             # Security fixes

Examples:
✅ feat(performance): optimize N+1 queries and add TTS retry logic
✅ fix(auth): remove hardcoded secrets
✅ docs: add Sprint 1 completion report
✅ chore: remove temporary migration script
```

---

## 🎓 LEARNING FROM GIT

### Example: Tìm hiểu cách TTS được implement
```bash
# Bước 1: Tìm commits về TTS
git log --oneline --grep="tts" -10

# Bước 2: Xem commit quan trọng nhất
git show <commit-hash> --stat

# Bước 3: Xem files liên quan
git log --oneline -- apps/api/python/translator_api/providers/tts/

# Bước 4: Đọc code hiện tại
cat apps/api/python/translator_api/providers/tts/edge.py
```

---

## 🔄 WORKFLOW ĐỀ XUẤT CHO AI AGENT

### Khi bắt đầu một task mới:

**Bước 1: Đọc context từ git (2-3 phút)**
```bash
git log --oneline -20                  # Recent history
git status                             # Current state
git diff develop origin/develop        # Local vs remote
```

**Bước 2: Đọc documentation liên quan (5 phút)**
```bash
README.md                              # Overview
docs/PROJECT_SUMMARY.md                # Technical details
CHANGELOG.md                           # Recent changes
```

**Bước 3: Tìm code liên quan (3-5 phút)**
```bash
git log --grep="<keyword>" -10         # Find related commits
git log -- <file-path>                 # File history
```

**Bước 4: Implement & Test**
- Code với đầy đủ context
- Verify không break existing functionality
- Write clear commit message

**Bước 5: Update documentation**
- Update PROJECT_SUMMARY.md nếu cần
- Add entry vào CHANGELOG.md
- Commit documentation changes

---

## 📌 IMPORTANT FILES TO MONITOR

**Core Configuration:**
- `.env` - Environment variables (gitignored)
- `pyproject.toml` - Python dependencies
- `package.json` - Node dependencies
- `VERSION` - Current version number

**Database:**
- `infra/migrations/versions/` - Database migrations
- Files: 003_add_indexes.py, 004_add_users_is_admin.py, 005_phase5_voice_profile_columns.py

**Core Business Logic:**
- `apps/api/python/translator_api/routers_editor.py` - Main editor APIs
- `apps/worker/python/translator_worker/activities_phase3.py` - TTS & Translation
- `apps/web/app/projects/[id]/workspace/page.tsx` - Main workspace UI

---

## ✅ CHECKLIST: TÔI ĐÃ NẮM CONTEXT CHƯA?

Trước khi bắt đầu code, tự hỏi:

- [ ] Tôi đã đọc 10-20 commits gần nhất chưa?
- [ ] Tôi đã đọc PROJECT_SUMMARY.md chưa?
- [ ] Tôi hiểu use case chính của dự án (zh→vi dubbing)?
- [ ] Tôi biết tech stack (FastAPI + Next.js + Temporal)?
- [ ] Tôi biết trạng thái hiện tại (Sprint 1 done, ready for Sprint 2)?
- [ ] Tôi đã tìm code liên quan đến task hiện tại chưa?
- [ ] Tôi biết conventions (commit message, code style)?

Nếu trả lời YES cho ≥5/7 câu → Bắt đầu code!

---

**Generated:** 2026-09-04 00:25 UTC+7  
**Maintained by:** AI Agent (Claude) + Developer (Quyen)  
**Update frequency:** After major features/sprints
