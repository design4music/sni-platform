# World Brief Project Model (L2)

## High-Level Flow

RSS Headlines
→ Phase 1: Ingestion & Cleaning
→ Phase 2: Accumulative Centroid Matching
→ Phase 3: Track Assignment & CTM Creation
→ Phase 4: Enrichment (Events + Summary)
→ Frontend Consumption

---

## Phase 1 — Ingestion & Normalization

**Input**: RSS feeds (Google News)
**Output**: `titles_v3` rows with `processing_status='pending'`

Key properties:
- NFKC Unicode normalization
- Incremental fetching (ETag / Last-Modified)
- Publisher extraction (real domain, not Google News wrapper)
- Deduplication at ingest

No intelligence is applied here.

---

## Phase 2 — Centroid Matching (Mechanical Core)

**Purpose**: Assign structural narrative anchors.

### Accumulative Matching
- All centroids checked (geographic + systemic)
- Returns **all matches** (no early-exit)
- One title → multiple centroids
- Enables bilateral relationship tracking

### Implementation
- Hash-based lookup for single-word aliases
- Precompiled regex patterns for multi-word phrases
- Stop word fast-fail (blocks before matching)
- Script-aware (word boundaries for ASCII, substring for CJK/Arabic)
- Normalization: diacritics stripped, possessives removed, compounds split

### Matching is:
- Alias-based, deterministic, and explainable
- Language-aware (filters Romance false positives)
- Performance-optimized (handles 2K+ titles/day)

**Output**:
- `titles_v3.centroid_ids[]`
- `processing_status='assigned'|'blocked_stopword'|'out_of_scope'`

---

## Phase 3 — Track Assignment & CTM Creation

**Purpose**: Strategic classification + aggregation.

### Track Assignment
- Performed via LLM (DeepSeek)
- Uses **dynamic track configurations**
- Track set selected by primary centroid:
  - Systemic > Theater > Macro

### CTM Creation
- CTM key = `(centroid_id, track, yyyymm)`
- Titles may map to multiple CTMs
- CTMs incrementally accumulate titles

**Output**:
- `titles_v3.track`
- `titles_v3.ctm_ids[]`
- `ctm.title_count++`

---

## Phase 4 — CTM Enrichment

### 4.1 Events Digest
- LLM extracts **distinct events**
- Chronological ordering
- Near-duplicate deduplication
- JSONB structured output

### 4.2 Narrative Summary
- 150–250 words
- Journalistic, strategic tone
- Chronological synthesis
- No opinion, no speculation

CTMs may be frozen for historical stability.

---

## Orchestration Model

- Single daemon with adaptive scheduling
- Sequential phases, phase-specific intervals
- Queue-aware execution (skip when empty)
- Designed for observability and recovery

---

## What This Model Is Not

- Not probabilistic clustering
- Not topic modeling
- Not sentiment analysis
- Not real-time streaming intelligence

SNI is a **strategic aggregation engine**, not a discovery toy.

---

## Frontend Consumption Layer (Non-Intelligent)

The frontend is a **read-only presentation layer** over the database.
It introduces no intelligence, inference, or interpretation.

### Principles
- Centroid-first navigation
- CTM is the atomic unit of displayed intelligence
- No aggregation or transformation beyond what exists in DB
- No write paths, no user state, no sessions

### Conceptual Flow

PostgreSQL (source of truth)
→ Server-side queries
→ Deterministic rendering
→ Human reading

### Navigation Model (Conceptual)

Home
→ Centroid
→ Track
→ CTM (summary + events + sources)

The frontend **consumes** CTMs; it does not shape them.

### Architectural Constraint

Any future frontend feature MUST:
- map directly to existing database structures, or
- be backed by a new explicit pipeline phase.

Frontend logic must never compensate for missing backend structure.
