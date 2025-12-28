# SNI v3 Project Model (L2)

## High-Level Flow

RSS Headlines
→ Phase 1: Ingestion & Cleaning
→ Phase 2: 3-Pass Centroid Matching
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

### 3-Pass Matching
1. **Theater Pass** (priority 100)
   - Geographic / geopolitical anchors
2. **Systemic Pass** (priority 10)
   - Domains like AI, Climate, Migration
3. **Macro Pass** (priority 1)
   - High-level strategic dimensions

### Rules
- Stop words applied only to systemic pass
- Romance-language false positives explicitly filtered
- Matching is alias-based, deterministic, and explainable

**Output**:
- `titles_v3.centroid_ids[]`
- `processing_status='assigned'`

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
