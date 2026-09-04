# ContextForge Memory System - Quick Reference

**🎯 1-Minute Guide for AI Agents & Developers**

---

## 🤖 For AI Agent

### Every Task Start:
```bash
# Read these 4 files (30 seconds total):
cat .cursor/context/PROJECT_STATE.md      # File index
tail -50 .cursor/context/DECISIONS.md     # Recent decisions  
cat .cursor/context/TASK_PROGRESS.md      # What's done
git log --oneline -20                     # Git history
```

### Every Task End:
Update relevant files:
- `TASK_PROGRESS.md` - Always (task summary)
- `DECISIONS.md` - If made design choice
- `PROJECT_STATE.md` - If files changed
- `details/*.md` - If deep changes to module

---

## 👨‍💻 For Developers

### View Project State:
```bash
cat .cursor/context/PROJECT_STATE.md      # What files exist
cat .cursor/context/DECISIONS.md          # Why decisions made
cat .cursor/context/TASK_PROGRESS.md      # What AI did recently
```

### After Working:
```bash
# Update context (optional but recommended)
vim .cursor/context/TASK_PROGRESS.md

# Commit with code
git add .cursor/context/ <your-files>
git commit -m "feat: your change

Updated context state"
```

---

## 📂 File Structure

```
.cursor/
├── rules/
│   ├── contextforge.md         # 541 lines - AI behavior rules
│   └── project-memory.md       # 308 lines - Git workflow
├── context/
│   ├── README.md               # 375 lines - System documentation
│   ├── PROJECT_STATE.md        # 130 lines - L1 file index
│   ├── DECISIONS.md            # 224 lines - Design decisions
│   ├── TASK_PROGRESS.md        # 91 lines - Current progress
│   └── details/
│       ├── workspace_page.md   # 100 lines - Frontend detail
│       ├── routers_editor.md   # 51 lines - Backend detail
│       └── activities_phase3.md # 129 lines - Worker detail
└── CONTEXTFORGE_SETUP.md       # 265 lines - Setup summary (this directory)
```

**Total:** 9 files, ~2,064 lines

---

## 🎯 What Each File Does

| File | Purpose | Update When | Read When |
|------|---------|-------------|-----------|
| `PROJECT_STATE.md` | File index | Files change | Every task |
| `DECISIONS.md` | Why decisions | Design choice | Before similar task |
| `TASK_PROGRESS.md` | Task history | Task done | New session |
| `details/*.md` | Deep context | Major refactor | Working on module |

---

## ✅ Success Criteria

**System works when:**
- [ ] AI reads context before answering (no blind guessing)
- [ ] AI updates context after tasks (discipline)
- [ ] New chat sessions start with full context
- [ ] No repeated "Where is file X?" questions
- [ ] Decisions are consistent with past patterns

---

## 🚀 Quick Commands

```bash
# Check what AI did
cat .cursor/context/TASK_PROGRESS.md

# See recent decisions
tail -50 .cursor/context/DECISIONS.md

# Find file in index
grep -i "keyword" .cursor/context/PROJECT_STATE.md

# View module details
cat .cursor/context/details/workspace_page.md

# Commit context
git add .cursor/context/ && git commit -m "docs(context): update"
```

---

## 🎓 Learn More

- **Full Guide:** `.cursor/context/README.md` (375 lines)
- **AI Rules:** `.cursor/rules/contextforge.md` (541 lines)
- **Setup Story:** `.cursor/CONTEXTFORGE_SETUP.md` (265 lines)
- **Git Workflow:** `.cursor/rules/project-memory.md` (308 lines)

---

## 💡 Pro Tips

1. **Commit context with code** - they're versioned together
2. **Read before you code** - 30 seconds saves 10 minutes
3. **Update immediately** - don't wait until end of day
4. **Be specific** - "Added TTS" ❌ → "Added OpenAI TTS provider" ✅
5. **Write for future you** - assume reader knows nothing

---

## 🐛 Quick Troubleshooting

**AI not reading context?**
→ Say: "Please follow ContextForge rules in .cursor/rules/contextforge.md"

**Context outdated?**
→ Update TASK_PROGRESS.md manually

**Too verbose?**
→ Read only PROJECT_STATE.md (1-line summaries)

**Want deep context?**
→ Read details/*.md for specific modules

---

## 🎉 Bottom Line

**ContextForge = Git + Markdown + Discipline**

- No server, no Docker, no setup
- Read → Work → Update → Commit
- Works on Windows, Mac, Linux
- Human & AI readable

**Result:** AI remembers everything, humans have docs.

---

**Created:** 2026-09-04  
**Status:** Production Ready ✅  
**Version:** 1.0
