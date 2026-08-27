# pyVideoTrans Gaps for China-Vietnam

**Document version:** 1.0
**Date:** 2026-08-27
**Source:** pyVideoTrans v4.11
**Purpose:** Inventory of features NOT available in pyVideoTrans that are relevant to the China-Vietnam use case

---

## Overview

pyVideoTrans is a mature, capable video translation engine. However, it lacks several features
that the PhimNganRepositoryApp custom platform provides. This document inventories those
gaps honestly — without inflating or minimizing them — to guide future development decisions.

**Rule:** Features listed here should NOT be developed immediately. First check if upstream
pyVideoTrans has added them. Then check for plugin/workaround options. Custom development
is the last resort.

---

## 1. Chinese OCR / Text Detection

**Priority:** High
**Current status:** NOT available in pyVideoTrans v4.11

pyVideoTrans does not have built-in OCR for detecting and removing Chinese text overlaid
on video frames. The PhimNganRepositoryApp had this via PaddleOCR, EasyOCR, and CRAFT.

**Impact for China-Vietnam:**
- Chinese subtitles hardcoded in video frames will appear on top of Vietnamese subtitles
- Chinese text overlays (signs, banners, credits) remain visible
- Video may be confusing to watch with mixed Chinese + Vietnamese text

**Workaround options:**
- Use video editing software to manually remove/replace Chinese text
- Use an external tool like Video-subtitle-remover before processing
- Rely on soft subtitles only (no burned-in text)

**Recommended action:** Monitor pyVideoTrans releases for future OCR support.

---

## 2. Chinese Text Removal / Inpainting

**Priority:** High
**Current status:** NOT available in pyVideoTrans v4.11

No built-in mechanism to remove/replace detected Chinese text regions with inpainting.

**Impact:** Same as #1 — Chinese hardcoded text persists.

**Recommended action:** Check Video-subtitle-remover project (separate tool), or build a
pre-processing step in the China-VNE workflow.

---

## 3. Translation Memory / Glossary

**Priority:** Medium
**Current status:** NOT available

pyVideoTrans translates each segment independently. There is no:
- Translation memory (TM) database
- Glossary/term database
- Character name consistency system
- Series/episode memory

**Impact for China-Vietnam:**
- Character names may be translated differently in episode 1 vs episode 5
- Inconsistent terminology (e.g., "Long" sometimes as "Rồng", sometimes as "Dragon")
- No way to enforce naming conventions

**Current workaround:**
- Use translation prompt engineering to include character names
- Edit SRT files manually before TTS step
- Accept inconsistency

**Recommended action:** Build a glossary-aware pre-processing step (external script).

---

## 4. Multi-Project Management

**Priority:** Medium
**Current status:** NOT available

pyVideoTrans is designed for single-video workflow. There is no:
- Project database
- Multi-video queue
- Series/episode grouping
- Progress tracking across videos

**Impact:**
- Cannot manage a 40-episode Chinese drama as one project
- No way to share settings across multiple videos
- Manual tracking required

**Recommended action:** Use folder organization + batch CLI scripting as a workaround.
Long-term: build a thin wrapper that manages project metadata externally.

---

## 5. Team Collaboration / RBAC

**Priority:** Low
**Current status:** NOT available

pyVideoTrans has no multi-user concept:
- No user accounts
- No roles (admin, translator, reviewer)
- No permissions
- No audit trail per user

**Impact:** Single-user only. Not suitable for team workflows.

**Recommended action:** Not in scope for China-VNE. Would require significant architecture
change or separate orchestration layer.

---

## 6. Character Bible / Voice Character Database

**Priority:** Medium
**Current status:** NOT available

PhimNganRepositoryApp had:
- `CharacterProfile` model (character names, aliases, personality)
- `CharacterAlias` model (alternative name translations)
- `VoiceProfile` model (TTS voice per character)

pyVideoTrans has:
- Speaker diarization (detects "speaker 1", "speaker 2")
- Manual voice role assignment per segment
- NO persistent character database

**Impact:**
- Character names must be manually tracked
- Voice assignments reset per video
- No way to say "Speaker 1 is always the female lead"

**Recommended action:** Build a thin external database (CSV or SQLite) for character
voice mapping, usable as a pre-processing step.

---

## 7. SDK / Programmatic API

**Priority:** Medium
**Current status:** NOT available

pyVideoTrans provides CLI and GUI only. No:
- REST API
- Python SDK
- Webhook for completion notifications
- Streaming status updates

**Impact:**
- Cannot integrate into automated pipelines easily
- Cannot trigger from web applications
- Cannot monitor progress programmatically

**Recommended action:** Wrap CLI calls in Python scripts for automation. Monitor for future
API support in pyVideoTrans.

---

## 8. Batch Queue System

**Priority:** Medium
**Current status:** NOT available natively

pyVideoTrans supports batch mode in GUI, but no:
- Persistent job queue
- Progress persistence across restarts
- Priority scheduling
- Failure recovery with checkpoints

**Impact:**
- Long video queues require uninterrupted runtime
- System restart loses progress
- No way to pause/resume queue

**Recommended action:** Use CLI batch loop with manual progress tracking.

---

## 9. Series / Episode Management

**Priority:** Medium
**Current status:** NOT available

Chinese dramas often have 40+ episodes. pyVideoTrans treats each video as independent:
- No series-level glossary
- No consistent translation across episodes
- No batch processing with shared context
- No episode numbering conventions

**Recommended action:** Build external series metadata + batch CLI wrapper.

---

## 10. Cloud-Native Deployment

**Priority:** Low
**Current status:** Docker only

PhimNganRepositoryApp had full Kubernetes/Helm deployment. pyVideoTrans only has:
- Single Docker container
- No Kubernetes manifests
- No Helm chart
- No horizontal scaling design

**Impact:** Not suitable for production cloud deployment at scale.

**Recommended action:** Not in scope for China-VNE unless explicitly needed.

---

## 11. Custom Translation Prompts (Per Genre)

**Priority:** Low-Medium
**Current status:** Partially available

pyVideoTrans allows translation prompt text in Advanced Options, but:
- No saved prompt presets
- No genre-specific templates
- No per-series prompt override

**Impact:** Users must manually configure prompts for each video.

**Recommended action:** Document best-practice prompts for Chinese dramas as part of
China-VNE documentation.

---

## 12. Audit Logging

**Priority:** Low
**Current status:** NOT available

PhimNganRepositoryApp had:
- `AuditLog` table
- Per-user action tracking
- Compliance requirements

pyVideoTrans has no audit trail.

**Recommended action:** Not in scope for China-VNE.

---

## Gap Summary Table

| # | Feature | Priority | Status | Workaround | Custom Dev? |
|---|---------|----------|--------|-----------|------------|
| 1 | Chinese OCR | High | Not available | External tool | No (monitor upstream) |
| 2 | Text removal | High | Not available | External tool | No (monitor upstream) |
| 3 | Translation memory | Medium | Not available | Pre-processing script | Maybe later |
| 4 | Multi-project | Medium | Not available | CLI batch loop | Maybe later |
| 5 | Team collaboration | Low | Not available | N/A | No |
| 6 | Character bible | Medium | Not available | External CSV/DB | Maybe later |
| 7 | SDK/API | Medium | Not available | CLI wrapper | Maybe later |
| 8 | Batch queue | Medium | Not available | CLI batch loop | Maybe later |
| 9 | Series management | Medium | Not available | Folder + naming | Maybe later |
| 10 | Cloud deployment | Low | Docker only | N/A | No |
| 11 | Genre prompts | Low-Medium | Partial | Docs | Maybe later |
| 12 | Audit logging | Low | Not available | N/A | No |

---

## Decision Framework for Future Development

Before developing any custom feature:

```
1. Is the feature in a newer pyVideoTrans release?
   → If yes, upgrade

2. Is there a plugin/extension mechanism?
   → If yes, build a plugin

3. Is there an external tool that integrates cleanly?
   → If yes, use as pre/post-processing step

4. Is the feature essential for the China-Vietnam use case?
   → If yes, build the smallest possible solution

5. Can it be a simple script/config rather than a full application?
   → If yes, prefer the script
```

**Principle:** Every custom addition increases maintenance burden. Prefer upstream,
plugins, and external tools over custom code.

---

## Priority Backlog

### Immediate (within 1 month)
None — use pyVideoTrans as-is for China-Vietnam

### Short-term (1-3 months)
- External pre-processing script for character name glossary
- Series metadata CSV + batch CLI wrapper
- Video-subtitle-remover integration guide

### Medium-term (3-6 months)
- Translation memory pre-processor
- SDK wrapper for Python automation
- Chinese OCR integration (if upstream still unavailable)

### Long-term (6+ months)
- Full multi-project management (only if team needs grow)
- Cloud-native deployment (only if scale requires it)
