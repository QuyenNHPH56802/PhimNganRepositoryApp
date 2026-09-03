# 🛠️ GIT COMMANDS CHEAT SHEET - Translator Project

**Mục đích:** Quick reference cho các git commands hữu ích khi làm việc với AI agent.

---

## 📖 ĐỌC CONTEXT (AI Agent sẽ chạy các lệnh này)

### 1. Xem lịch sử commits
```bash
# 20 commits gần nhất
git log --oneline -20

# Graph view (visual)
git log --all --graph --decorate --oneline -20

# Với thời gian và author
git log --pretty=format:"%h %an %ar: %s" -20
```

### 2. Tìm commits theo keyword
```bash
# Tìm trong commit message
git log --oneline --grep="performance"
git log --oneline --grep="fix"
git log --oneline --grep="feat"

# Tìm trong code changes
git log -S "selectinload" --oneline
```

### 3. Xem chi tiết commit
```bash
# Summary với danh sách files
git show <commit-hash> --stat

# Full diff
git show <commit-hash>

# Chỉ xem một file cụ thể
git show <commit-hash> -- <file-path>
```

### 4. Xem lịch sử của một file
```bash
# Commits đã sửa file này
git log --oneline -- apps/api/python/translator_api/routers_editor.py

# Xem changes cho từng commit
git log -p -- apps/api/python/translator_api/main.py

# Xem ai viết đoạn code nào (blame)
git blame apps/web/app/layout.tsx
```

### 5. So sánh branches
```bash
# Local vs remote
git diff develop origin/develop

# Chỉ xem danh sách files
git diff --stat develop origin/develop

# So sánh 2 branches bất kỳ
git diff main develop
```

---

## 🔍 RESEARCH COMMANDS

### Tìm khi nào một bug được introduce
```bash
# Tìm commit đã thêm/xóa một đoạn code
git log -S "bug_code_snippet" --oneline

# Bisect để tìm commit gây bug (advanced)
git bisect start
git bisect bad HEAD
git bisect good v1.0.0
# Git sẽ hỏi từng commit, bạn test và trả lời good/bad
```

### Xem thống kê contributor
```bash
# Ai commit nhiều nhất
git shortlog -sn

# Thống kê theo file
git log --format='%aN' -- <file-path> | sort | uniq -c
```

### Tìm tags và releases
```bash
# List tất cả tags
git tag -l

# Xem chi tiết một tag
git show v1.3.0

# Tags có chứa một commit
git tag --contains <commit-hash>
```

---

## ✍️ VIẾT COMMITS TỐT

### Commit message convention
```bash
# Format chuẩn
<type>(<scope>): <subject>

<body>

<footer>

# Types:
feat:     New feature
fix:      Bug fix
docs:     Documentation only
style:    Code style (formatting, no logic change)
refactor: Code refactoring
perf:     Performance improvement
test:     Add/fix tests
chore:    Maintenance (build, deps, etc)
security: Security fixes

# Examples:
git commit -m "feat(tts): add DashScope Qwen3 provider"

git commit -m "fix(auth): prevent auth bypass in _require_viewer

- Add proper session validation
- Check user role before allowing access
- Add test coverage for auth flows"

git commit -m "perf(api): optimize N+1 queries with selectinload

Reduced queries from 401 to 8 per request (98% reduction).
Response time improved from 2.3s to 0.18s.

Closes #123"
```

### Staging & Committing
```bash
# Stage specific files
git add apps/api/python/translator_api/routers_editor.py
git add docs/PERFORMANCE_OPTIMIZATION.md

# Stage all changes
git add .

# Interactive staging (chọn từng chunk)
git add -p

# Commit with message
git commit -m "feat(performance): optimize N+1 queries"

# Commit with editor (để viết message dài)
git commit
```

### Amend commits (sửa commit cuối)
```bash
# Sửa message của commit cuối
git commit --amend -m "New message"

# Thêm files vào commit cuối
git add forgotten_file.py
git commit --amend --no-edit
```

---

## 🌿 BRANCH MANAGEMENT

### Tạo & switch branches
```bash
# Tạo branch mới
git branch feature/add-voice-cloning

# Switch sang branch
git checkout feature/add-voice-cloning

# Hoặc tạo và switch luôn
git checkout -b feature/add-voice-cloning

# Modern way (Git 2.23+)
git switch feature/add-voice-cloning
git switch -c feature/new-feature
```

### Xem branches
```bash
# Local branches
git branch

# All branches (local + remote)
git branch -a

# With last commit info
git branch -v
```

### Merge branches
```bash
# Merge feature vào develop
git checkout develop
git merge feature/add-voice-cloning

# Merge với commit message custom
git merge feature/add-voice-cloning -m "Merge: Add voice cloning feature"
```

---

## 🔄 SYNC VỚI REMOTE

### Pull updates
```bash
# Pull develop từ remote
git pull origin develop

# Pull và rebase (tránh merge commits)
git pull --rebase origin develop
```

### Push commits
```bash
# Push lần đầu (set upstream)
git push -u origin develop

# Push thông thường
git push

# Force push (⚠️ cẩn thận!)
git push --force-with-lease
```

### Fetch remote info
```bash
# Fetch tất cả thông tin từ remote (không merge)
git fetch origin

# Xem remote branches
git branch -r
```

---

## 🗑️ UNDO CHANGES

### Undo uncommitted changes
```bash
# Discard changes trong một file
git checkout -- apps/web/app/page.tsx

# Discard tất cả changes (⚠️ cẩn thận!)
git reset --hard HEAD
```

### Undo commits (chưa push)
```bash
# Undo commit cuối, giữ changes
git reset --soft HEAD~1

# Undo commit cuối, discard changes
git reset --hard HEAD~1

# Undo 3 commits cuối
git reset --soft HEAD~3
```

### Undo commits (đã push)
```bash
# Revert một commit (tạo commit mới đảo ngược)
git revert <commit-hash>

# Revert nhiều commits
git revert <commit1> <commit2> <commit3>
```

---

## 🧹 MAINTENANCE

### Clean untracked files
```bash
# Xem files sẽ bị xóa (dry-run)
git clean -n

# Xóa untracked files
git clean -f

# Xóa cả directories
git clean -fd
```

### Stash changes
```bash
# Tạm lưu changes
git stash

# Tạm lưu với message
git stash push -m "Work in progress on TTS optimization"

# Xem stash list
git stash list

# Apply stash mới nhất
git stash pop

# Apply stash cụ thể
git stash apply stash@{2}
```

---

## 🎯 USEFUL ALIASES (Thêm vào .gitconfig)

```bash
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.cm commit
git config --global alias.lg "log --oneline --graph --decorate -20"
git config --global alias.last "log -1 HEAD --stat"
git config --global alias.unstage "reset HEAD --"

# Usage:
git st        # = git status
git lg        # = git log --oneline --graph --decorate -20
git last      # = git log -1 HEAD --stat
```

---

## 🚀 ADVANCED WORKFLOWS

### Cherry-pick specific commits
```bash
# Apply một commit từ branch khác
git cherry-pick <commit-hash>

# Cherry-pick nhiều commits
git cherry-pick <commit1> <commit2>
```

### Interactive rebase (clean history)
```bash
# Rebase 5 commits cuối
git rebase -i HEAD~5

# Commands trong editor:
# pick   - keep commit
# reword - edit commit message
# squash - merge into previous commit
# drop   - remove commit
```

### Search trong code history
```bash
# Tìm khi nào "selectinload" được thêm/xóa
git log -S "selectinload" --oneline --all

# Tìm trong commit messages
git log --grep="N+1" --oneline

# Tìm trong author
git log --author="Quyen" --oneline -20
```

---

## 📊 STATISTICS & REPORTS

### Code statistics
```bash
# Lines changed by author
git log --author="Quyen" --pretty=tformat: --numstat | \
  awk '{ add += $1; subs += $2; loc += $1 - $2 } END \
  { printf "added lines: %s, removed lines: %s, total lines: %s\n", add, subs, loc }'

# Commits per author
git shortlog -sn --all

# Files changed most frequently
git log --pretty=format: --name-only | sort | uniq -c | sort -rg | head -20
```

### Project health check
```bash
# Xem branches chưa merge
git branch --no-merged

# Xem commits chưa push
git log origin/develop..develop

# Kiểm tra conflicts trước khi merge
git diff develop...feature/new-feature
```

---

## 🔐 SECURITY & CLEANUP

### Remove sensitive data
```bash
# Remove file from all history (⚠️ rewrites history!)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Modern way (using git-filter-repo)
git filter-repo --path .env --invert-paths
```

### Verify no secrets in repo
```bash
# Search for potential secrets
git log -p | grep -E "(api_key|password|secret)"

# Use tools like:
# - gitleaks
# - truffleHog
# - git-secrets
```

---

## 📝 EXAMPLES FOR TRANSLATOR PROJECT

### Example 1: Tìm hiểu performance optimization
```bash
# Step 1: Find commits
git log --oneline --grep="performance" -10

# Step 2: View detailed changes
git show f1dba73 --stat

# Step 3: View specific file changes
git show f1dba73 -- apps/api/python/translator_api/routers_editor.py

# Step 4: See current state
git diff f1dba73 HEAD -- apps/api/python/translator_api/routers_editor.py
```

### Example 2: Debug một API endpoint
```bash
# Step 1: When was this endpoint added?
git log -S "def get_transcript_segments" --oneline

# Step 2: View the commit
git show <commit-hash>

# Step 3: Who last modified it?
git blame apps/api/python/translator_api/routers_editor.py | grep "get_transcript_segments"

# Step 4: See all changes to this endpoint
git log -p -- apps/api/python/translator_api/routers_editor.py | \
  grep -A 20 "def get_transcript_segments"
```

### Example 3: Prepare for new sprint
```bash
# Step 1: Sync with remote
git fetch origin
git pull origin develop

# Step 2: Review recent changes
git log --oneline origin/develop -10

# Step 3: Check current status
git status

# Step 4: Create feature branch
git checkout -b feature/sprint2-integration-tests

# Step 5: Do work...
# Step 6: Commit with good message
git add .
git commit -m "feat(tests): add integration tests with Temporal worker

- Setup test Temporal worker
- Add end-to-end pipeline test
- Test upload → transcribe → translate → TTS → render
- Measure latency and verify output quality

Part of Sprint 2 goals."

# Step 7: Push to remote
git push -u origin feature/sprint2-integration-tests
```

---

**Last Updated:** 2026-09-04 00:25 UTC+7  
**Reference:** [Git Documentation](https://git-scm.com/doc)
