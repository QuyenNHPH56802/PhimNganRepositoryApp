# ContextForge Memory System

**Status:** ✅ Active  
**Created:** 2026-09-04  
**Version:** 1.0

---

## 🎯 What is This?

ContextForge is a **structured memory system** for AI agents. It helps AI remember:
- What files exist and what they do (L1 index)
- Deep context for complex modules (L2 details)
- Why design decisions were made (decision log)
- What was done in previous sessions (task progress)

**Key insight:** Git tracks *what changed*, ContextForge tracks *why* and *context*.

---

## 📂 Directory Structure

```
.cursor/
├── rules/
│   ├── project-memory.md      ← Git workflow rules (existing)
│   └── contextforge.md        ← ContextForge rules (new)
├── context/
│   ├── PROJECT_STATE.md       ← L1: File index (fast lookup)
│   ├── DECISIONS.md           ← Design decisions log
│   ├── TASK_PROGRESS.md       ← Current session progress
│   ├── README.md              ← This file
│   └── details/
│       ├── workspace_page.md
│       ├── routers_editor.md
│       ├── activities_phase3.md
│       └── *.md               ← L2: Per-file deep context
└── PROJECT_CONTEXT.md         ← Project overview (existing)
```

---

## 🚀 Quick Start for Humans

### Reading Context
```bash
# Quick overview
cat .cursor/context/PROJECT_STATE.md

# Recent decisions
tail -50 .cursor/context/DECISIONS.md

# What was done last session
cat .cursor/context/TASK_PROGRESS.md

# Deep dive on specific file
cat .cursor/context/details/workspace_page.md
```

### Updating Context
```bash
# After working on code, update relevant files
vim .cursor/context/PROJECT_STATE.md      # If files changed
vim .cursor/context/DECISIONS.md          # If made design decision
vim .cursor/context/TASK_PROGRESS.md      # Task summary

# Commit changes
git add .cursor/context/
git commit -m "docs(context): update state after [task description]"
```

---

## 🤖 Quick Start for AI Agents

### Every Task: Read Context First
```bash
# 1. Git history (from project-memory.md)
git log --oneline -20
git status

# 2. L1 index
cat .cursor/context/PROJECT_STATE.md

# 3. Recent decisions
tail -50 .cursor/context/DECISIONS.md

# 4. Session context
cat .cursor/context/TASK_PROGRESS.md

# 5. Deep context (if working on specific file)
cat .cursor/context/details/[file].md
```

### After Task: Update State
1. **PROJECT_STATE.md** if files added/removed/renamed
2. **DECISIONS.md** if made important design choice
3. **TASK_PROGRESS.md** with task summary
4. **details/*.md** if deep context needs update

---

## 📖 File Descriptions

### PROJECT_STATE.md (L1 Index)
**Purpose:** Fast lookup - which file does what  
**Format:** Markdown tables grouped by module  
**Update when:** Files added/removed/purpose changed  
**Read by:** AI every task, humans for overview

**Example:**
```markdown
| File | Purpose | Last Changed |
|------|---------|--------------|
| routers_editor.py | Editor CRUD APIs | 2026-09-04 |
```

### DECISIONS.md
**Purpose:** Track *why* decisions were made  
**Format:** Timestamped entries with Context → Decision → Rationale  
**Update when:** Important architectural/tech decisions  
**Read by:** AI before similar decisions, humans for onboarding

**Example:**
```markdown
## 2026-09-04 - Use Temporal for Workflows

**Context:** Need reliable long-running video translation jobs
**Decision:** Use Temporal instead of Celery
**Rationale:** Built-in retries, workflow durability, better debugging
**Trade-offs:** ✅ Reliability ⚠️ Infrastructure overhead
```

### TASK_PROGRESS.md
**Purpose:** Session continuity - what was done recently  
**Format:** Completed tasks + in-progress + next tasks  
**Update when:** After each work session  
**Read by:** AI at start of new session, team for status

### details/*.md (L2 Deep Context)
**Purpose:** Deep understanding of complex files  
**Format:** Structured docs with purpose, APIs, patterns, gotchas  
**Create when:** File >300 LOC OR complex logic OR frequently edited  
**Update when:** Major refactors or API changes

---

## 🎯 Design Philosophy

### Two-Source Truth System
1. **Git history** = *What* happened (commits, diffs, code)
2. **ContextForge** = *Why* + *Context* (decisions, purpose, patterns)

Both required for full understanding.

### Layers of Detail
- **L1 (PROJECT_STATE.md)**: Breadth - scan all files quickly
- **L2 (details/*.md)**: Depth - understand specific modules deeply

### Human-Readable & Editable
- Plain markdown, no special tools needed
- Version controlled with git
- Humans can edit manually anytime

### Discipline Required
- AI must update after tasks (not optional)
- Small updates accumulate to complete picture
- Outdated context worse than no context

---

## ✅ Benefits

**For AI Agents:**
- 🧠 Remember context across sessions
- 🎯 Make consistent decisions
- 📚 Learn from past decisions
- 🚀 Faster ramp-up on tasks

**For Humans:**
- 📖 Better onboarding docs
- 🤔 Understand why decisions were made
- 🔍 Find relevant code quickly
- 📊 See project evolution over time

**For Teams:**
- 🤝 Shared understanding of architecture
- 📝 Living documentation that stays current
- 🧭 Clear decision history
- 🔄 Easier knowledge transfer

---

## 🔄 Integration with Existing Workflow

ContextForge **complements** existing Git workflow:

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `project-memory.md` | Git commands & workflow | Every task |
| `ContextForge` | Structured state & context | Every task |
| Git history | See what changed | Code investigation |
| PROJECT_STATE.md | See what exists | Task planning |
| DECISIONS.md | Understand why | Making similar decisions |

**They work together, not separately.**

---

## 📏 Rules Summary

### Always Read Before Working
- Git history (20 commits)
- PROJECT_STATE.md (L1 index)
- DECISIONS.md (recent decisions)
- TASK_PROGRESS.md (session context)

### Always Update After Working
- PROJECT_STATE.md (if files changed)
- DECISIONS.md (if made decisions)
- TASK_PROGRESS.md (task summary)
- L2 details (if deep changes)

### Commit Context with Code
```bash
git add .cursor/context/ <other-files>
git commit -m "feat(api): add export endpoint

- Create async export via Temporal
- Update context state files

Refs: .cursor/context/DECISIONS.md (export decision)"
```

---

## 🎓 Example Workflow

**Task:** Add new TTS provider (e.g., OpenAI TTS)

### 1. Read Context
```bash
git log --oneline --grep="TTS" -10
cat .cursor/context/PROJECT_STATE.md | grep -i tts
tail -50 .cursor/context/DECISIONS.md | grep -i provider
cat .cursor/context/details/activities_phase3.md
```

**Learn:**
- TTS providers live in `apps/api/python/translator_api/providers/tts/`
- Use registry pattern for provider selection
- Follow `BaseTtsProvider` interface
- See how other providers implemented

### 2. Implement
```python
# Create apps/api/python/translator_api/providers/tts/openai_tts.py
# Follow pattern from azure.py, google.py, etc.
```

### 3. Update Context

**PROJECT_STATE.md:**
```markdown
| `providers/tts/openai_tts.py` | OpenAI TTS provider | 2026-09-04 |
```

**DECISIONS.md:**
```markdown
## 2026-09-04 - Add OpenAI TTS Provider

**Context:** Users request OpenAI TTS (better quality, more voices)

**Decision:** Add as new provider following registry pattern

**Implementation:**
- Created `openai_tts.py` following `BaseTtsProvider`
- Registered in `registry_constants.py`
- Added config schema in `provider_configs.py`

**Trade-offs:**
- ✅ Easy to add following existing pattern
- ✅ No core changes needed
- ⚠️ Requires OpenAI API key (cost consideration)

**Status:** ✅ Implemented
```

**TASK_PROGRESS.md:**
```markdown
## ✅ Completed Today

### Add OpenAI TTS Provider
- Implemented BaseTtsProvider interface
- Added registry entry
- Updated config schemas
- Tested with sample audio
- **Result:** Users can now use OpenAI TTS voices
```

### 4. Commit
```bash
git add apps/api/python/translator_api/providers/tts/openai_tts.py \
        apps/api/python/translator_api/providers/registry_constants.py \
        packages/shared/python/translator_shared/provider_configs.py \
        .cursor/context/

git commit -m "feat(tts): add OpenAI TTS provider

- Implement BaseTtsProvider interface
- Support all OpenAI voices
- Add configuration schema
- Update context state files

Refs: .cursor/context/DECISIONS.md (2026-09-04 OpenAI TTS)"
```

---

## 🛠️ Maintenance

### Weekly Review
```bash
# Check for outdated entries
git log --since="7 days ago" --oneline -- .cursor/context/

# Review PROJECT_STATE.md accuracy
# Update file purposes if changed
# Remove deleted files
```

### Monthly Cleanup
- Archive old TASK_PROGRESS entries (keep last 30 days)
- Review DECISIONS.md for superseded decisions
- Update L2 details for heavily-modified files

### As Needed
- Create new L2 details for growing files (>300 LOC)
- Update decision statuses (Active → Superseded)
- Add new sections to PROJECT_STATE.md for new modules

---

## 📚 Resources

- **Full Rules:** `.cursor/rules/contextforge.md` (541 lines)
- **Git Workflow:** `.cursor/rules/project-memory.md`
- **Project Overview:** `.cursor/PROJECT_CONTEXT.md`
- **This README:** `.cursor/context/README.md`

---

## 💡 Tips

1. **Start small:** Don't try to document everything at once
2. **Update immediately:** Don't wait until end of day
3. **Be specific:** "Added export" ❌ → "Added async export via Temporal" ✅
4. **Write for future you:** Assume reader knows nothing about task
5. **Commit context:** State files are code, commit them like code

---

## 🤝 Contributing

**Humans:** Edit any file manually, commit changes

**AI Agents:** Follow rules in `.cursor/rules/contextforge.md`

**Everyone:** Keep context current = better decisions tomorrow

---

**Maintained by:** Engineering Team + AI Agents  
**Questions?** Check `.cursor/rules/contextforge.md` for details
