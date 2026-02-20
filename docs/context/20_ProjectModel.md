# World Brief Project Model (L2)

## High-Level Flow

RSS Headlines
-> Phase 1: Ingestion & Cleaning
-> Phase 2: Accumulative Centroid Matching
-> Phase 3.1: Label + Signal Extraction (LLM)
-> Phase 3.2: Entity Centroid Backfill
-> Phase 3.3: Intel Gating + Track Assignment (LLM)
-> Phase 4: Incremental Topic Clustering (mechanical)
-> Phase 4.1: Topic Consolidation (LLM merge/rescue/dedup)
-> Phase 4.5a: Event Summaries (LLM)
-> Phase 4.5b: CTM Digest Summaries (LLM)
-> Phase 5: Narrative Frame Extraction (LLM)
-> Phase 6: RAI Signal Analysis (local stats + remote LLM)
-> Monthly Freeze (archival boundary)
-> Epic Detection & Enrichment (cross-country stories)
-> Frontend Consumption

---

## Phase 1 -- Ingestion & Normalization

**Input**: RSS feeds (Google News)
**Output**: `titles_v3` rows with `processing_status='pending'`

Key properties:
- NFKC Unicode normalization
- Incremental fetching (ETag / Last-Modified)
- Publisher extraction (real domain, not Google News wrapper)
- Deduplication at ingest

No intelligence is applied here.

---

## Phase 2 -- Centroid Matching (Mechanical Core)

**Purpose**: Assign structural narrative anchors.

### Accumulative Matching
- All centroids checked (geographic + systemic)
- Returns **all matches** (no early-exit)
- One title -> multiple centroids
- Enables bilateral relationship tracking

### Implementation
- Hash-based lookup for single-word aliases
- Precompiled regex patterns for multi-word phrases
- Stop word fast-fail (blocks before matching)
- Script-aware (word boundaries for ASCII, substring for CJK/Arabic)
- Normalization: diacritics stripped, possessives removed, compounds split

**Output**:
- `titles_v3.centroid_ids[]`
- `processing_status='assigned'|'blocked_stopword'|'out_of_scope'`

---

## Phase 3 -- Classification & Routing

Three sub-phases, run in sequence:

### 3.1 Label + Signal Extraction (LLM)
Extracts structured labels (ACTOR->ACTION_CLASS->DOMAIN) and typed signals
(persons, orgs, places, commodities, policies, systems, named_events) plus
entity_countries in a single LLM call per batch. Stored in `title_labels`.

### 3.2 Entity Centroid Backfill
Maps entity_countries from 3.1 to geographic centroids. Adds centroid
assignments for entities not caught by mechanical Phase 2 matching
(e.g., NVIDIA headline -> adds USA centroid via entity mapping).

### 3.3 Intel Gating + Track Assignment (LLM)
Two-stage LLM call: first rejects non-strategic content (sports, celebrity,
weather), then assigns accepted titles to domain-specific tracks using
centroid-specific track configurations. Creates `title_assignments` and
auto-creates CTMs as needed.

**Output**:
- `title_assignments` (title_id, centroid_id, track, ctm_id)
- `ctm` rows created or updated
- Rejected titles marked `processing_status='blocked_llm'`

---

## Phase 4 -- Topic Clustering & Enrichment

### 4.0 Incremental Clustering (Mechanical)
Deterministic signal-based clustering. Early titles define anchor signals
that lock after 5 titles, preventing topic drift. Later titles match via
weighted signal overlap. Geographic bucketing (domestic, bilateral-XX,
other_international) structures events spatially. Unmatched titles go to
catchall events. Non-destructive: existing events and summaries survive
re-runs.

### 4.1 Topic Consolidation (LLM)
Single-pass LLM review per bucket: merge similar events, rescue catchall
titles into real topics, redistribute misplaced Other International titles
to bilateral buckets, cross-bucket deduplication of duplicates.

### 4.5a Event Summaries (LLM)
Per-event title + summary + tags generation. Events with <5 sources get
title only. Role hallucination post-processing applied (e.g., "Former
President" -> "President" for current officeholders).

### 4.5b CTM Digest Summaries (LLM)
150-250 word cohesive digest per CTM, weighted by event source counts.
Journalistic, strategic tone. No opinion, no speculation.

**Output**:
- `events_v3` with title, summary, tags, event_type, bucket_key
- `ctm.summary_text`

---

## Phase 5 -- Narrative Frame Extraction (LLM)

Identifies 2-5 contested narrative frames per entity. Language-stratified
sampling ensures editorial diversity. Separate scripts for CTM, event, and
epic narratives (different fetch logic, sampling, and prompts per type).

Runs daily in daemon. Supports refresh mode: re-extracts when an entity's
source count grows significantly since last extraction.

**Output**: `narratives` table (entity_type + entity_id, label, description,
moral_frame, title_count, top_sources, sample_titles)

---

## Phase 6 -- RAI Signal Analysis

Two-tier architecture:
- **Tier 1 (local)**: Computes hard coverage stats from DB -- publisher HHI,
  language distribution, entity countries, domain balance, actor concentration.
  No LLM calls.
- **Tier 2 (remote)**: Sends stats to RAI service for compact JSON
  interpretation -- adequacy score, framing bias, geographic blind spots,
  missing perspectives.

**Output**: `narratives.signal_stats` (JSONB), `narratives.rai_signals` (JSONB)

---

## Monthly Freeze

End-of-month boundary process:
- Marks all CTMs for the month as `is_frozen = true`
- Generates cross-track centroid summary via LLM (one paragraph per track)
- Stored in `centroid_monthly_summaries`
- New titles after freeze go into fresh CTMs for the next month
- Frozen CTMs and events are immutable (no re-clustering)

---

## Epic Detection (Post-Freeze)

Cross-country story aggregation:
- Identifies events spanning multiple centroids via shared anchor tags
- LLM generates title, summary, timeline, per-centroid perspective summaries
- Narrative frame extraction (2-pass: discover frames, classify all titles)
- RAI analysis applied to epic narratives

**Output**: `epics`, `epic_events`, `narratives` (entity_type='epic')

---

## Event Saga Chaining

Links events that are the same ongoing story across months within the same
centroid+track. Uses tag overlap + title word Dice similarity (no LLM).
Each later-month event matches its single best earlier-month candidate.
Chains grow across months via reused saga UUIDs stored in `events_v3.saga`.

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

### Content Types

| Type | URL Pattern | Source |
|------|-------------|--------|
| Centroid overview | `/c/{centroid_id}` | centroids_v3 + centroid_monthly_summaries |
| CTM track page | `/c/{centroid_id}/t/{track}` | ctm + events_v3 + narratives |
| Event detail | `/events/{event_id}` | events_v3 + narratives + saga siblings |
| Epic list | `/epics` | epics (month-navigated) |
| Epic detail | `/epics/{slug}` | epics + epic_events + narratives |
| Sources list | `/sources` | feeds (active outlets) |
| Outlet profile | `/sources/{feed_name}` | feeds + titles_v3 + narratives |

### Navigation Model

Home
-> Region/System -> Centroid -> Track -> CTM (summary + events + sources)
                                     -> Event detail (summary + saga timeline + narratives + sources)
-> Epics -> Epic detail (timeline + centroid perspectives + narratives)
-> Sources -> Outlet profile (coverage map + narrative participation)

### Architectural Constraint

Any future frontend feature MUST:
- map directly to existing database structures, or
- be backed by a new explicit pipeline phase.

Frontend logic must never compensate for missing backend structure.
