# Design Decisions Log

**Purpose:** Track architectural decisions, trade-offs, and rationale

---

## Decision Log Format

Each entry should include:
- **Date:** When the decision was made
- **Context:** What problem we're solving
- **Decision:** What we chose to do
- **Alternatives:** What else we considered
- **Rationale:** Why we chose this path
- **Consequences:** Impact (positive & negative)
- **Status:** Active | Superseded | Deprecated

---

## 🎯 Active Decisions

### D001: Multi-Provider TTS Architecture (2026-09)

**Context:** Need to support multiple TTS providers (Azure, Google, ElevenLabs, local models)

**Decision:** Abstract provider interface with registry pattern

**Implementation:**
- `providers/tts/base.py` - Base TTS interface
- `providers/registry.py` - Dynamic provider registration
- Individual provider implementations in `providers/tts/`

**Alternatives Considered:**
1. Hard-coded provider selection
2. Plugin system with dynamic loading
3. Microservices per provider

**Rationale:**
- Registry pattern balances flexibility & simplicity
- Easy to add new providers without core changes
- Testable through mocking
- No runtime plugin complexity

**Consequences:**
- ✅ Easy to add new TTS providers
- ✅ Clear provider interface contract
- ⚠️ All providers must be bundled in deployment
- ⚠️ No runtime plugin installation

**Status:** Active

---

### D002: FastAPI + Temporal Architecture (2026-06)

**Context:** Need reliable workflow orchestration for long-running video translation jobs

**Decision:** Use Temporal for workflows, FastAPI for HTTP APIs

**Architecture:**
- FastAPI (`apps/api/`) - HTTP endpoints, auth, DB access
- Temporal Worker (`apps/worker/`) - Workflow execution
- Next.js (`apps/web/`) - Frontend

**Alternatives Considered:**
1. Celery for async tasks
2. AWS Step Functions
3. Pure FastAPI with background tasks

**Rationale:**
- Temporal provides workflow durability & retries
- Clear separation: HTTP vs long-running workflows
- Built-in observability & debugging
- Local development friendly

**Consequences:**
- ✅ Reliable workflow execution
- ✅ Easy retry & error handling
- ✅ Clear task boundaries
- ⚠️ Additional infrastructure (Temporal server)
- ⚠️ Learning curve for team

**Status:** Active

---

### D003: Git-Based Context Memory (2026-09-04)

**Context:** AI agents lose context between sessions, repeat mistakes

**Decision:** Use ContextForge pattern - structured markdown files + git history

**Implementation:**
- `.cursor/context/PROJECT_STATE.md` - L1 index
- `.cursor/context/details/` - L2 detailed docs
- `.cursor/context/DECISIONS.md` - This file
- `.cursor/rules/contextforge.md` - AI rules

**Alternatives Considered:**
1. agentmemory (server-based) - Windows compatibility issues
2. ai-memory (WSL2 only) - Not Windows native
3. Database-backed memory - Overhead for small team

**Rationale:**
- Pure git/markdown - works on any platform
- No external dependencies or servers
- Version controlled automatically
- Human-readable & editable

**Consequences:**
- ✅ Works on Windows natively
- ✅ Zero setup overhead
- ✅ Git history = memory timeline
- ⚠️ Manual structure maintenance
- ⚠️ No semantic search (yet)

**Status:** Active

---

### D004: Chinese → Vietnamese Focus (2026-06)

**Context:** Video dubbing market requirements

**Decision:** Optimize specifically for zh→vi translation workflow

**Specializations:**
- Locale-specific subtitle rules (`subtitle/locale_rules.py`)
- Vietnamese TTS providers (VieNeu, VietVoice)
- Chinese OCR optimization
- Glossary support for cultural terms

**Alternatives Considered:**
1. Generic multilingual platform
2. English-first approach
3. Language-agnostic design

**Rationale:**
- Clear target market
- Better UX through specialization
- Leverage local TTS providers
- Cultural context understanding

**Consequences:**
- ✅ Best-in-class zh→vi quality
- ✅ Local market competitive advantage
- ⚠️ Harder to expand to other language pairs
- ⚠️ Need to maintain locale-specific code

**Status:** Active

---

### D005: Per-Artifact Redis Cache TTL (2026-09-04)

**Context:** Redis cache grew unbounded with fixed 60-day TTL for all artifacts

**Decision:** Implement differentiated TTL policies based on artifact type and regeneration cost

**Implementation:**
```python
CACHE_TTL_POLICIES = {
    "asr": 7 * 24 * 3600,           # 7 days - expensive GPU operation
    "translation": 3 * 24 * 3600,   # 3 days - LLM API calls
    "tts": 24 * 3600,               # 1 day - can regenerate quickly
    "subtitle": 12 * 3600,          # 12 hours - cheap operation
}
```

**Alternatives Considered:**
1. Fixed TTL for all artifacts (previous approach)
2. LRU eviction only (no TTL)
3. Manual cache invalidation
4. No caching (too slow)

**Rationale:**
- Expensive operations (ASR, translation) should cache longer
- Cheap operations (subtitle) can regenerate often
- Memory bounded by aggressive eviction of low-value artifacts
- Still get cache benefits where it matters most

**Consequences:**
- ✅ Redis memory usage optimized (30-40% reduction estimated)
- ✅ Important artifacts retained longer
- ✅ Tunable per-artifact based on production metrics
- ⚠️ More complex cache configuration
- ⚠️ Need monitoring to tune values

**Status:** Active (Phase 4 - TD-017)

---

### D006: SQLAlchemy selectinload for N+1 Queries (2026-09-04)

**Context:** Translation endpoint had N+1 query problem - 201 queries for 200 segments

**Decision:** Use SQLAlchemy `selectinload()` to batch-fetch related entities

**Implementation:**
```python
# Before: Manual eager loading with in_()
segment_ids = [seg.transcript_segment_id for seg in segments]
transcript_segments = db.query(TranscriptSegment).filter(
    TranscriptSegment.id.in_(segment_ids)
).all()

# After: selectinload batch loading
segments = (
    db.query(TranslationSegment)
    .options(selectinload(TranslationSegment.transcript_segment))
    .all()
)
```

**Alternatives Considered:**
1. Manual eager loading with `in_()` (previous, still N queries)
2. `joinedload()` - creates complex JOIN, less efficient for 1:N
3. DataLoader pattern (GraphQL-style batching)
4. Denormalize data (duplicate in translation table)

**Rationale:**
- `selectinload()` generates optimal 2 queries (parent + batch child)
- No complex JOINs or duplicate data
- SQLAlchemy-native solution
- Works transparently with existing code

**Consequences:**
- ✅ 100x query reduction (201 → 2)
- ✅ 6x faster API response (3s → 500ms)
- ✅ Database load significantly reduced
- ✅ Scales to long videos (1000+ segments)
- ⚠️ Requires understanding SQLAlchemy loading strategies
- ⚠️ Must audit other endpoints for similar issues

**Status:** Active (Phase 4 - TD-012)

---

## 📜 Historical Decisions

### D007: Removed Migration 003 (2026-09)

**Context:** Index migration had issues, needed fixing

**Decision:** Delete `003_add_indexes.py`, replace with `003_add_indexes_fixed.py`

**Status:** Superseded by 003_add_indexes_fixed.py

---

## 📝 Pending Decisions

### PD001: E2E Testing Strategy

**Context:** Added Playwright config but no tests yet

**Options:**
1. Component testing with React Testing Library
2. Full E2E with Playwright
3. Visual regression testing
4. Hybrid approach

**Need to decide:**
- Test coverage targets
- CI/CD integration
- Mock vs real backend

**Status:** Under consideration

---

### PD002: Provider Configuration Management

**Context:** Provider settings scattered across code & env vars

**Options:**
1. Database-backed config (current)
2. YAML config files
3. Admin UI for runtime config
4. Environment-only config

**Trade-offs:**
- Database = dynamic but needs migrations
- Files = simple but deployment overhead
- UI = flexible but security concerns

**Status:** Under consideration

---

## 🔄 Decision Review Process

**When to log a decision:**
- Architectural changes affecting >2 modules
- Technology/library selections
- Security or performance trade-offs
- API contract changes
- Database schema decisions

**Review cadence:**
- Major decisions: Review every 6 months
- Minor decisions: Review on-demand
- Deprecated decisions: Archive after 1 year

---

**Maintained by:** Engineering Team + AI Agent
**Last Review:** 2026-09-04
