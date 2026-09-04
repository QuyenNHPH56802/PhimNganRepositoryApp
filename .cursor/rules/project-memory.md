# Project Memory - Translator Platform

## Luôn Nhớ Toàn Bộ Dự Án

**Kích hoạt:** Khi bắt đầu mọi task, AI agent PHẢI đọc context từ git trước khi code.

---

## 🧠 Quy Trình Bắt Buộc

### BƯỚC 1: Đọc Git History (LUÔN LUÔN)

Trước khi trả lời hoặc code, AI agent PHẢI chạy:

```bash
# 1. Xem 20 commits gần nhất
git log --oneline -20

# 2. Xem trạng thái hiện tại
git status

# 3. Xem có thay đổi gì chưa commit
git diff --stat

# 4. So sánh với remote
git diff --stat develop origin/develop
```

### BƯỚC 2: Đọc Documentation Core

AI agent PHẢI đọc (theo thứ tự):

1. **`.cursor/PROJECT_CONTEXT.md`** - Project overview và key commits
2. **`README.md`** - Architecture và quick start
3. **`docs/USER_GUIDE.md`** - Full user guide (Vietnamese)

### BƯỚC 3: Tìm Code Liên Quan

Nếu task liên quan đến một module cụ thể:

```bash
# Tìm commits liên quan
git log --oneline --grep="<keyword>" -10

# Xem lịch sử file
git log --oneline -- <file-path>

# Xem ai viết code này
git blame <file-path>
```

---

## ✅ Checklist Trước Khi Code

AI agent PHẢI tự hỏi:

- [ ] Tôi đã xem 20 commits gần nhất chưa?
- [ ] Tôi đã đọc PROJECT_CONTEXT.md chưa?
- [ ] Tôi biết trạng thái hiện tại (branch, uncommitted files)?
- [ ] Tôi hiểu use case chính (zh→vi video dubbing)?
- [ ] Tôi biết tech stack (FastAPI + Next.js + Temporal)?
- [ ] Tôi đã tìm code liên quan đến task chưa?
- [ ] Tôi biết commit convention (feat/fix/docs/chore)?

**Quy tắc:** Nếu <5/7 → ĐỌC THÊM, chưa được code!

---

## 🔍 Khi Gặp Bug

Trước khi fix, AI agent PHẢI:

1. **Tìm khi nào bug xuất hiện:**
   ```bash
   git log -S "bug_code" --oneline
   git log --grep="fix.*<keyword>" --oneline
   ```

2. **Xem lịch sử file bị bug:**
   ```bash
   git log --oneline -- <buggy-file-path>
   git show <commit-hash> -- <buggy-file-path>
   ```

3. **Kiểm tra ai viết code này:**
   ```bash
   git blame <file-path> | grep -A 5 -B 5 "<buggy-line>"
   ```

---

## 📝 Khi Thêm Feature Mới

Trước khi implement, AI agent PHẢI:

1. **Tìm feature tương tự đã có:**
   ```bash
   git log --oneline --grep="feat.*<similar>" -10
   git log --oneline -- apps/api/python/translator_api/providers/
   ```

2. **Xem conventions hiện tại:**
   - Đọc 2-3 files trong module tương tự
   - Follow naming pattern
   - Follow code structure

3. **Kiểm tra dependencies:**
   - Xem `pyproject.toml` (Python)
   - Xem `package.json` (Node)
   - Không thêm dependency mới nếu đã có sẵn

---

## 🚨 Nguyên Tắc Quan Trọng

### 1. KHÔNG BAO GIỜ phỏng đoán

- ❌ "Tôi nghĩ file này có function X"
- ✅ Chạy `git log` hoặc `grep` để verify

### 2. LUÔN LUÔN đọc trước khi viết

- ❌ Code ngay khi được hỏi
- ✅ Đọc git history → hiểu context → code

### 3. LUÔN LUÔN verify changes

- ❌ Code xong là xong
- ✅ Chạy tests, check lint, verify logic

### 4. LUÔN commit với message rõ ràng

Format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `chore`, `security`, `perf`, `refactor`, `test`

---

## 📊 Key Files Phải Nhớ

### Core Business Logic
- `apps/api/python/translator_api/routers_editor.py` - Main editor APIs
- `apps/worker/python/translator_worker/activities_phase3.py` - TTS & Translation
- `apps/web/app/projects/[id]/workspace/page.tsx` - Main workspace UI

### Configuration
- `.env` - Environment variables (gitignored, KHÔNG commit)
- `pyproject.toml` - Python dependencies
- `package.json` - Node dependencies
- `VERSION` - Current version

### Database
- `infra/migrations/versions/` - All database migrations

### Documentation
- `.cursor/PROJECT_CONTEXT.md` - Project overview
- `.cursor/GIT_COMMANDS.md` - Git commands reference
- `README.md` - Setup & architecture
- `docs/USER_GUIDE.md` - Full user guide

---

## 🎯 Quick Commands Reference

### Đọc Git Context (Run These First!)
```bash
git log --oneline -20                           # Recent commits
git status                                       # Current state
git diff --stat                                  # Uncommitted changes
git log --oneline --grep="<keyword>" -10         # Find commits
git log --oneline -- <file-path>                 # File history
git show <commit-hash> --stat                    # Commit details
git blame <file-path>                            # Who wrote what
```

### Tìm Code
```bash
git log -S "function_name" --oneline             # Find when code added
git log --grep="feat.*<topic>" --oneline         # Find features
git log --oneline -- apps/api/python/            # Module history
```

### Commit
```bash
git add <files>                                  # Stage files
git commit -m "feat(scope): description"         # Commit with message
git push origin develop                          # Push to remote
```

---

## 🔄 Workflow Example

**User yêu cầu:** "Thêm endpoint GET /projects/{id}/statistics"

**AI agent PHẢI làm:**

```bash
# Bước 1: Đọc git history
git log --oneline -20
git log --oneline --grep="endpoint" -10
git log --oneline -- apps/api/python/translator_api/routers.py

# Bước 2: Xem endpoints hiện tại
git show HEAD -- apps/api/python/translator_api/routers.py

# Bước 3: Tìm pattern tương tự
git log -S "def get_project" --oneline

# Bước 4: Implement (sau khi đã đọc đầy đủ)
# ... code here ...

# Bước 5: Commit với message rõ ràng
git add apps/api/python/translator_api/routers.py
git commit -m "feat(api): add GET /projects/{id}/statistics endpoint

- Return project statistics (transcripts, translations, workflows)
- Add test coverage
- Update API documentation

Closes #456"
```

---

## 🎓 Learning From Git

Mỗi commit là một lesson:

- **f1dba73** → Học cách optimize N+1 queries với `selectinload()`
- **3388d86** → Học cách implement authentication & RBAC
- **7170edf** → Học cách làm i18n với Next.js
- **d18b129** → Học cách secure secrets trong env vars

**Quy tắc:** Trước khi implement X, tìm xem đã có ai làm X chưa → học từ họ!

---

## 🚀 Performance Tips

### Cache Git Info
```bash
# Lưu frequent commands vào aliases
git config --global alias.recent "log --oneline -20"
git config --global alias.st "status"
git config --global alias.find "log --oneline --grep"

# Usage
git recent        # = git log --oneline -20
git find "feat"   # = git log --oneline --grep="feat"
```

---

## ⚠️ Warnings

### KHÔNG BAO GIỜ:

1. ❌ Code mà chưa đọc git history
2. ❌ Phỏng đoán function/variable names
3. ❌ Copy code từ internet mà chưa verify với codebase
4. ❌ Commit với message "update" hoặc "fix"
5. ❌ Push force (`git push -f`) trừ khi thực sự cần
6. ❌ Commit secrets/API keys
7. ❌ Ignore `.gitignore` rules

### LUÔN LUÔN:

1. ✅ Đọc 20 commits gần nhất trước khi code
2. ✅ Xem file history trước khi edit
3. ✅ Follow existing patterns
4. ✅ Viết commit messages rõ ràng
5. ✅ Run tests trước khi commit
6. ✅ Verify changes với `git diff`
7. ✅ Check `git status` trước khi commit

---

## 📌 Summary

**Câu Thần Chú Của AI Agent:**

> "Trước khi code, đọc git.  
> Trước khi đọc code, đọc git history.  
> Trước khi trả lời, verify bằng git.  
> Git là nguồn sự thật duy nhất."

**Kết quả mong đợi:**
- AI agent luôn có context đầy đủ
- Không bao giờ phỏng đoán
- Code follow conventions
- Commits rõ ràng và có ý nghĩa
- Ít bug hơn, quality cao hơn

---

**Created:** 2026-09-04  
**Last Updated:** 2026-09-04  
**Maintained by:** Quyen + AI Agent (Claude)
