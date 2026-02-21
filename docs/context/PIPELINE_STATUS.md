# WorldBrief (SNI) v3 Pipeline - Technical Documentation

**Last Updated**: 2026-02-21
**Status**: Production - Full pipeline operational
**Live URL**: https://www.worldbrief.info
**Branch**: `main`

---

## Executive Summary

The v3 pipeline processes news headlines through automated daemon phases (1 through 4.5b) to produce intelligence CTMs (Centroid-Track-Month units) with structured events and narrative summaries. Narrative extraction and RAI analysis are on-demand (user-triggered via frontend). The system uses a PostgreSQL-native architecture with LLM-based classification and entity extraction.

### Pipeline Flow

```
RSS Feeds (Google News)
    |
[Phase 1] Ingestion --> titles_v3 (processing_status='pending')              \
    |                                                                          \
[Phase 2] Centroid Matching --> titles_v3 (centroid_ids, status='assigned')    |
    |                                                                          |
[Phase 3.1] Label + Signal Extraction --> title_labels (combined LLM call)    | DAEMON
    |                                                                          | (automated)
[Phase 3.2] Entity Centroid Backfill --> entity_countries -> centroids        |
    |                                                                          |
[Phase 3.3] Intel Gating + Track Assignment --> title_assignments + ctm       |
    |                                                                          |
[Phase 4] Incremental Topic Clustering --> events_v3 + event_v3_titles        |
    |                                                                          |
[Phase 4.1] Topic Consolidation (LLM merge/rescue/dedup) --> consolidated     |
    |                                                                          |
[Phase 4.5a] Event Summary Generation --> events_v3.title, summary, tags      |
    |                                                                         /
[Phase 4.5b] CTM Digest Generation --> ctm.summary_text                     /
    |
    |--- [On-demand] User clicks "Extract & Analyse" ------\
    |                                                       | ON-DEMAND
    |    Narrative Extraction --> narratives                 | (user-triggered,
    |    |                                                  |  auth-gated)
    |    RAI Analysis --> signal_stats + rai_signals         |
    |    |                                                  |
    |    Analysis Page (/analysis/[id])  ------------------/
    |
[Epic Detection] --> epics + epic_events (post-freeze, manual)
    |
[Epic Enrichment] --> epics.timeline, narratives, centroid_summaries
    |
Frontend (Next.js, auth via NextAuth v5)
```

---

## Daemon Schedule

**Script**: `pipeline/runner/pipeline_daemon.py`

| Phase | Interval | Batch Size | Description |
|-------|----------|------------|-------------|
| Phase 1 | 12 hours | all feeds | RSS ingestion |
| Phase 2 | 12 hours | all titles | Centroid matching (mechanical) |
| Phase 3.1 | 10 minutes | 500 titles | Label + signal extraction (concurrency=5) |
| Phase 3.2 | (after 3.1) | 500 titles | Entity centroid backfill |
| Phase 3.3 | 10 minutes | 100 titles | Intel gating + track assignment |
| Phase 4 | 30 minutes | all CTMs | Incremental clustering |
| Phase 4.1 | (after 4) | all CTMs | Topic consolidation (LLM merge/rescue/dedup) |
| Phase 4.5a | 15 minutes | 500 events | Event summaries (decoupled) |
| Phase 4.5b | 1 hour | 50 CTMs | CTM digest generation |
| Daily purge | 24 hours | all | Remove rejected titles to tombstone table |

Phases 5 (narrative extraction) and 6 (RAI analysis) were removed from the daemon
in D-030. They now run on-demand via the frontend extraction API.

---

## Phase 1: RSS Ingestion

**Script**: `pipeline/phase_1/ingest_feeds.py`
**Interval**: 12 hours

### Processing

1. Load active feeds from `feeds` table
2. Fetch RSS with conditional GET (ETag/Last-Modified)
3. Parse entries with feedparser
4. Apply NFKC Unicode normalization
5. Extract real publisher from Google News redirect
6. Strip publisher name patterns from title (configurable via `feeds.strip_patterns`)
7. Insert to `titles_v3` with `processing_status='pending'`

### Key Features

- Watermark-based incremental fetching
- NFKC normalization for consistent matching
- Publisher extraction from Google News URLs
- Publisher name stripping from headlines

---

## Phase 2: Centroid Matching

**Script**: `pipeline/phase_2/match_centroids.py`
**Interval**: 12 hours

### Algorithm

1. Load `taxonomy_v3` aliases into memory (hash map + precompiled regex)
2. For each pending title:
   - Normalize: lowercase, strip diacritics, NFKC, remove periods
   - Tokenize: strip possessives, split hyphenated compounds
   - Check stop words first (fast-fail to `blocked_stopword`)
   - Match against all centroids (accumulative)
3. Update `titles_v3.centroid_ids` and `matched_aliases`
4. Set `processing_status='assigned'` or `out_of_scope`

### Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| Interval | 12 hours | Same as Phase 1 |
| Batch size | all | No limit (processes all pending) |

---

## Phase 3.1: Label + Signal Extraction

**Script**: `pipeline/phase_3_1/extract_labels.py`
**Interval**: 10 minutes

### Combined Extraction (Single LLM Call)

Extracts both structured labels AND typed signals in one call:

**Labels** (ELO v2.0):
```
ACTOR -> ACTION_CLASS -> DOMAIN (-> TARGET)
```

**Signals** (for clustering):
- `persons`: People mentioned (e.g., TRUMP, POWELL)
- `orgs`: Organizations (e.g., FED, NATO)
- `places`: Locations beyond centroid
- `commodities`: Resources (e.g., oil, chips)
- `policies`: Policy areas (e.g., tariffs, sanctions)
- `systems`: Systems/weapons (e.g., S-400, F-35)
- `named_events`: Named events (e.g., G20 Summit)

### Queue Query

Selects titles with `processing_status='assigned'` and `centroid_ids IS NOT NULL`
that do not yet have `title_labels`. No dependency on `title_assignments`.

### Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `v3_p31_max_titles` | 500 | Titles per run |
| `v3_p31_batch_size` | 50 | Titles per LLM call |
| `v3_p31_concurrency` | 5 | Parallel workers |
| `v3_p31_temperature` | 0.1 | LLM temperature |

---

## Phase 3.2: Entity Centroid Backfill

**Script**: `pipeline/phase_3_2/backfill_entity_centroids.py`
**Runs**: After Phase 3.1

Uses `entity_countries` from Phase 3.1 to:
1. Map entities (persons, orgs) to country ISO codes
2. Add corresponding geographic centroids to titles
3. Enables bilateral relationship tracking (e.g., NVIDIA story -> adds USA centroid)

---

## Phase 3.3: Intel Gating & Track Assignment

**Script**: `pipeline/phase_3_3/assign_tracks_batched.py`
**Interval**: 10 minutes

### Two-Stage Processing

**Stage 1: Intel Gating**
- LLM evaluates batch of titles for strategic relevance
- Rejects: Sports, entertainment, human interest, local crime, weather
- Accepts: Policy, international relations, economic, security, political
- Rejected titles: `processing_status='blocked_llm'`

**Stage 2: Track Assignment**
- LLM assigns track using centroid-specific config
- Creates `title_assignments` entries linking title-centroid-track-ctm

### Multi-Centroid Logic

A title with `centroid_ids = ['AMERICAS-USA', 'SYS-ENERGY']` is processed twice:
- Once for AMERICAS-USA -> e.g., `geo_energy`
- Once for SYS-ENERGY -> e.g., `energy_coercion`

---

## Phase 4: Incremental Topic Clustering

**Script**: `pipeline/phase_4/incremental_clustering.py`
**Interval**: 30 minutes

### Algorithm

**Key Concept**: Topics form around **anchor signals** that lock early, then grow via co-occurrence.

1. Process titles chronologically (oldest first)
2. First 5 titles define **anchor signals** (then locked)
3. Later titles match via weighted overlap with anchors
4. Co-occurring signals tracked but don't define topic identity
5. **Discriminators** reject titles with conflicting key signals
6. Unmatched titles go to "Other coverage" catchall events

### Bucket Assignment

Topics are assigned geographic buckets:
- `domestic`: Home country events (matches centroid's ISO codes)
- `bilateral-XX`: Events involving specific foreign country XX
- `other_international`: Multi-country or unclear scope

### Configuration (core/config.py)

```python
ANCHOR_LOCK_THRESHOLD = 5      # Titles before anchors lock
JOIN_THRESHOLD = 0.2           # Minimum similarity to join topic
HIGH_FREQ_PERSONS = {"TRUMP", "BIDEN", "PUTIN", "ZELENSKY", "XI"}

TRACK_WEIGHTS = {
    "geo_economy": {"orgs": 3.0, "commodities": 3.0, "policies": 2.0, ...},
    "geo_security": {"places": 3.0, "systems": 2.5, ...},
    ...
}
```

---

## Phase 4.1: Topic Consolidation

**Script**: `pipeline/phase_4/consolidate_topics.py`
**Runs**: After Phase 4

### Purpose

Single-pass LLM consolidation of mechanically clustered topics. One LLM call per bucket:
- Merge similar events that should be combined
- Rescue titles from "Other Coverage" catchalls into real topic events
- Redistribute Other International catchall titles to bilateral buckets
- Cross-bucket deduplication of duplicate events

### Key Features

**Catchall Rescue**: When catchall has >= 10 titles, LLM sees catchall items with indices and can assign them to existing events via `rescue_catchall_ids`. Positional index mapping (not text matching) ensures accuracy.

**Centroid Validation Gate**: For bilateral buckets, catchall rescue validates that each title's `centroid_ids` contains the bucket centroid before moving it. Prevents contamination from previous bugs.

**Cross-Bucket Deduplication** (`cross_bucket_dedup()`): Scans `other_international` events for duplicates already present in bilateral buckets. Merges titles into the bilateral event and deletes the OI duplicate.

**OI Redistribution** (`redistribute_oi_catchall()`): Moves Other International catchall titles to bilateral catchalls based on each title's foreign geo centroids. Single-centroid titles go to that country's bucket; multi-centroid to the largest.

**LLM Retry**: Exponential backoff (configurable via `config.llm_retry_attempts` and `config.llm_retry_backoff`). Falls back gracefully on persistent failure.

**Zombie Event Cleanup**: After consolidation, deletes any events that ended up with 0 titles (e.g., from failed catchall rescues).

---

## Phase 4.5a: Event Summary Generation

**Script**: `pipeline/phase_4/generate_event_summaries_4_5a.py`
**Interval**: 15 minutes (decoupled from Phase 4)

### Output Structure

LLM generates conversational summaries for each event:
```json
{
  "title": "Short headline (5-15 words)",
  "summary": "1-3 sentence narrative (30-60 words)",
  "tags": ["person:trump", "org:fed", "topic:tariffs"]
}
```

### Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `v3_p45a_max_events` | 500 | Events per run |
| `v3_p45a_interval` | 900 | 15 minutes |

---

## Phase 4.5b: CTM Digest Generation

**Script**: `pipeline/phase_4/generate_summaries_4_5.py`
**Interval**: 1 hour

### Process

1. Query CTMs with events but no summary (or stale > 24h)
2. Fetch event summaries for each CTM
3. LLM generates 150-250 word cohesive digest weighted by source counts
4. Update `ctm.summary_text`

---

## On-Demand Narrative Extraction & RAI Analysis

**Extraction service**: `api/extraction_api.py` (FastAPI)
**Frontend routes**: `app/api/extract-narratives/route.ts`, `app/api/rai-analyse/route.ts`
**Trigger**: User clicks "Extract & Analyse" (requires authentication)

Previously daemon Phases 5 & 6, now on-demand (D-030). Scripts and stats modules unchanged.

### Narrative Extraction

Single-pass LLM analysis identifies 2-5 contested narrative frames per entity. Stores results in the unified `narratives` table with `entity_type` = 'ctm' or 'event'.

**CTM Narratives**:
- Selection: CTMs with `title_count >= 100` (config: `v3_p5_min_titles`), not frozen
- Sampling: Language-stratified (200 titles max), publisher round-robin within strata

**Event Narratives**:
- Selection: Events with `source_batch_count >= 30` (config: `v3_p5e_min_sources`)
- Sampling: Same language-stratified sampling

**Coherence Check**: Before extraction, LLM checks whether the topic cluster is coherent enough for meaningful narrative extraction. Result stored in `events_v3.coherence_check` JSONB.

### RAI Analysis

**Tier 1 -- Local Stats** (`core/signal_stats.py`):
- Pure SQL + Python aggregation, no LLM calls
- `compute_event_stats()`, `compute_ctm_stats()`, `compute_epic_stats()` share `_aggregate_rows()` helper
- Stats: publisher HHI, language distribution, entity countries, domain/action_class distribution, top actors/persons/orgs, narrative frame count, date range, label coverage
- Stored in `narratives.signal_stats` JSONB

**Tier 2 -- Local RAI Engine** (`apps/frontend/lib/rai-engine.ts`):
- 33 analytical modules with 46 premises (covering coverage adequacy, framing, source diversity, geographic bias, narrative shifts, etc.)
- LLM pre-pass selects 3 context-appropriate modules per entity
- Signal stats from Tier 1 injected into analysis prompt
- DeepSeek generates prose analysis + assessment scores (0-1 scale)
- Results cached in `narratives.rai_signals` JSONB + `rai_signals_at` timestamp

### Analysis Page

Dedicated `/analysis/[narrative_id]` page with:
- Sidebar: assessment scores (displayed as %), coverage stats (sources, languages, publishers)
- Main: analysis prose, synthesis, shift indicators
- Appendix: sample headlines used in analysis

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `v3_p5_min_titles` | 100 | CTM min titles for extraction |
| `v3_p5e_min_sources` | 30 | Event min sources for extraction |
| `DEEPSEEK_API_KEY` | env var | Required for RAI analysis LLM calls |

### Known Limitations

- **No auto-refresh**: Narratives are not re-extracted when coverage grows (see Q-001)
- **No re-extraction**: Existing narratives cannot be overwritten by user (see Q-002)

---

## Epic Detection & Enrichment

**Script**: `pipeline/epics/build_epics.py`
**Runs**: Manual (after month freeze)

### Epic Detection

1. Query events with high source counts across multiple centroids
2. Extract anchor tags (shared signals that link events)
3. Group events into epics by anchor tag overlap
4. Filter: minimum 3 centroids, 50+ total sources

### Epic Enrichment (LLM)

For each epic, generates:
- **Title**: Descriptive headline
- **Summary**: 2-3 sentence overview
- **Timeline**: Chronological narrative of how events unfolded
- **Narratives**: Key storylines (title + description pairs)
- **Centroid Summaries**: Per-country perspective on the epic

### Epic Narrative Extraction

**Script**: `pipeline/epics/extract_narratives.py`

Two-pass LLM approach:
- **Pass 1**: Sample ~150 titles, discover 3-7 narrative frames
- **Pass 2**: Classify ALL titles into frames, batch by publisher (~60/batch)
- TF-IDF style source scoring for over-indexed outlets

### Output Tables

- `epics`: Epic metadata (slug, month, title, summary, anchor_tags, stats)
- `epic_events`: Links events to epics (event_id, epic_id, is_included)
- `narratives` (entity_type='epic'): Frame analysis with RAI scores

---

## Database Schema

### Core Tables

**titles_v3**: News headlines
```sql
processing_status: 'pending' | 'assigned' | 'out_of_scope' | 'blocked_stopword' | 'blocked_llm'
centroid_ids: TEXT[]  -- Assigned in Phase 2
```

**title_labels**: Labels + signals from Phase 3.1
```sql
actor, action_class, domain, target  -- ELO labels
persons, orgs, places, commodities, policies, systems, named_events  -- Signals
entity_countries JSONB  -- Entity->ISO mapping
```

**title_assignments**: Many-to-many title-centroid-track
```sql
title_id, centroid_id, track, ctm_id
UNIQUE(title_id, centroid_id)
```

**events_v3**: Clustered events
```sql
ctm_id, date, first_seen
title, summary, tags  -- From Phase 4.5a
event_type: 'bilateral' | 'domestic' | 'other_international'
bucket_key, source_batch_count, is_catchall
topic_core JSONB  -- Anchor signals for consolidation context
saga TEXT  -- UUID linking same story across months (from chain_event_sagas)
coherence_check JSONB  -- LLM coherence assessment before narrative extraction
```

**ctm**: Centroid-Track-Month aggregations
```sql
centroid_id, track, month
title_count, summary_text, is_frozen
events_digest JSONB  -- Denormalized event list for frontend
last_aggregated_at, title_count_at_aggregation  -- Staleness tracking
```

**centroid_monthly_summaries**: Cross-track summaries per centroid per month
```sql
centroid_id, month
summary_text, track_count, total_events
```

**epics**: Cross-country story aggregations
```sql
id, slug, month, title, summary
anchor_tags TEXT[], centroid_count, event_count, total_sources
timeline TEXT, narratives JSONB, centroid_summaries JSONB
```

**epic_events**: Events linked to epics
```sql
epic_id, event_id, is_included BOOLEAN
```

**narratives**: Unified narrative frames (CTM, event, epic)
```sql
entity_type: 'ctm' | 'event' | 'epic'
entity_id UUID, label, description, moral_frame
title_count, top_sources TEXT[], sample_titles JSONB
signal_stats JSONB      -- Tier 1 pre-computed stats (publisher HHI, languages, etc.)
rai_signals JSONB       -- Tier 2 RAI-interpreted signals (compact JSON)
rai_signals_at TIMESTAMPTZ
-- Legacy full RAI analysis fields:
rai_adequacy FLOAT, rai_synthesis TEXT, rai_conflicts TEXT[], rai_blind_spots TEXT[]
rai_shifts JSONB, rai_full_analysis TEXT, rai_analyzed_at TIMESTAMPTZ
UNIQUE(entity_id, label)
```

**monthly_signal_rankings**: Pre-computed signal rankings with LLM context
```sql
month, signal_type, rank, value, count, context TEXT
```

---

## File Map

```
pipeline/
|-- phase_1/
|   |-- ingest_feeds.py              # RSS ingestion
|
|-- phase_2/
|   |-- match_centroids.py           # Centroid matching
|
|-- phase_3_1/
|   |-- extract_labels.py            # Combined label + signal extraction
|
|-- phase_3_2/
|   |-- backfill_entity_centroids.py # Entity->centroid mapping
|
|-- phase_3_3/
|   |-- assign_tracks_batched.py     # Intel gating + track assignment
|
|-- phase_4/
|   |-- incremental_clustering.py    # Topic clustering (anchor signals + buckets)
|   |-- consolidate_topics.py        # LLM consolidation (merge, rescue, dedup)
|   |-- generate_event_summaries_4_5a.py  # Event summaries
|   |-- generate_summaries_4_5.py    # CTM digests
|   |-- extract_ctm_narratives.py    # CTM narrative extraction (Phase 5a)
|   |-- extract_event_narratives.py  # Event narrative extraction (Phase 5b)
|   |-- analyze_event_rai.py         # RAI signal analysis (legacy batch, now on-demand)
|   |-- chain_event_sagas.py         # Cross-month event saga linking
|
|-- epics/                           # Epic lifecycle (cron/manual)
|   |-- build_epics.py               # Epic detection + enrichment
|   |-- extract_narratives.py        # Narrative frame extraction
|   |-- analyze_rai.py               # RAI analysis
|   |-- detect_epics.py              # Epic detection logic
|   |-- explore_epic.py              # Epic exploration tool
|
|-- freeze/                          # Monthly freeze (cron)
|   |-- freeze_month.py              # CTM freeze + centroid summaries
|   |-- generate_signal_rankings.py  # Monthly signal rankings

|-- runner/
|   |-- pipeline_daemon.py           # Orchestration daemon
|   |-- backfill_pipeline.py         # One-time catch-up (4.5a + 4.1)

api/
|-- extraction_api.py                # FastAPI service for on-demand narrative extraction

core/
|-- config.py                        # Configuration + clustering constants
|-- prompts.py                       # All LLM prompts (consolidated)
|-- ontology.py                      # ELO v2.0 definitions
|-- llm_utils.py                     # Shared LLM utilities (extract_json, fix_role_hallucinations)
|-- signal_stats.py                  # Tier 1 coverage stats (HHI, language dist, etc.)

db/
|-- scripts/
|   |-- fix_outdated_titles.py       # One-off data fix utilities
|-- backfills/
|   |-- backfill_unknown_entities.py # Unknown entity resolution
|-- migrations/                      # SQL migrations

apps/frontend/
|-- auth.ts                          # NextAuth v5 config (credentials provider, JWT)
|-- app/
|   |-- c/[centroid_key]/page.tsx    # Centroid page (summary + tracks)
|   |-- c/[centroid_key]/t/[track_key]/page.tsx  # CTM track page
|   |-- events/[event_id]/page.tsx   # Event detail page (saga timeline)
|   |-- analysis/[narrative_id]/page.tsx  # Dedicated RAI analysis page
|   |-- epics/page.tsx               # Epic list page (month navigation)
|   |-- epics/[slug]/page.tsx        # Epic detail page
|   |-- sources/page.tsx             # Media outlet list
|   |-- sources/[feed_name]/page.tsx # Outlet profile page
|   |-- search/page.tsx              # Full-text search
|   |-- sign-in/page.tsx             # Authentication sign-in
|   |-- sign-up/page.tsx             # Authentication sign-up
|   |-- api/extract-narratives/route.ts  # Proxy to extraction API
|   |-- api/rai-analyse/route.ts     # On-demand RAI analysis (auth-gated)
|   |-- api/auth/signup/route.ts     # User registration endpoint
|-- lib/
|   |-- cache.ts                     # In-memory TTL cache (Map-based, lazy cleanup)
|   |-- db.ts                        # PostgreSQL pool (max 10, idle 30s, conn 5s)
|   |-- queries.ts                   # All DB queries (9 cached with 5-10 min TTL)
|   |-- types.ts                     # Shared types (Track, REGIONS, Epic, etc.)
|   |-- rai-engine.ts               # Local RAI analysis engine (33 modules, DeepSeek)
|   |-- logos.ts                     # Self-hosted outlet favicon paths
|-- components/
|   |-- DashboardLayout.tsx          # Main layout (sidebar + content grid)
|   |-- TrackCard.tsx                # Track card component
|   |-- EventList.tsx                # Event list with expand/collapse
|   |-- EventAccordion.tsx           # Single event accordion item (freshness dot)
|   |-- CountryAccordion.tsx         # Country section with events
|   |-- GeoBriefSection.tsx          # Centroid profile/brief display + mini-map
|   |-- CentroidMiniMap.tsx          # Geographic mini-map for centroid cards
|   |-- MonthNav.tsx                 # Month navigation sidebar
|   |-- TableOfContents.tsx          # Sticky TOC for track page
|   |-- EpicCountries.tsx            # Country accordion for epics
|   |-- NarrativeOverlay.tsx         # Narrative cards (links to analysis page)
|   |-- ExtractButton.tsx            # "Extract & Analyse" CTA (auth-gated)
|   |-- NarrativeNav.tsx             # Prev/next dots + arrows for sibling narratives
|   |-- AnalysisContent.tsx          # Client-side analysis prose + score broadcast
|   |-- AssessmentScores.tsx         # Client component for live score rendering

archive/phase_4_old/                 # Deprecated Phase 4 scripts
|-- aggregate_topics.py              # Replaced by consolidate_topics.py
|-- bucketed_clustering.py           # Replaced by incremental_clustering.py
|-- cluster_topics.py                # Old clustering approach
|-- cluster_events_mechanical.py     # Old mechanical clustering
|-- test_incremental_nondestructive.py  # Old test harness
```

---

## Quick Reference Commands

### Manual Phase Execution

```bash
# Phase 1: RSS Ingestion
python pipeline/phase_1/ingest_feeds.py --max-feeds 10

# Phase 2: Centroid Matching
python pipeline/phase_2/match_centroids.py --max-titles 500

# Phase 3.1: Label + Signal Extraction
python pipeline/phase_3_1/extract_labels.py --max-titles 500 --concurrency 5

# Phase 3.3: Intel Gating + Track Assignment
python pipeline/phase_3_3/assign_tracks_batched.py --max-titles 100

# Phase 4: Topic Clustering
python pipeline/phase_4/incremental_clustering.py --ctm-id <ctm_id> --write

# Phase 4.1: Topic Consolidation (LLM merge + rescue)
python pipeline/phase_4/consolidate_topics.py --ctm-id <ctm_id>

# Phase 4.5a: Event Summaries
python pipeline/phase_4/generate_event_summaries_4_5a.py --max-events 500

# Phase 4.5b: CTM Summaries
python pipeline/phase_4/generate_summaries_4_5.py --max-ctms 50

# Narrative Extraction (on-demand, or manual CLI)
python pipeline/phase_4/extract_ctm_narratives.py --month 2026-02 --dry-run
python pipeline/phase_4/extract_event_narratives.py --dry-run --limit 20

# RAI Signal Analysis (on-demand via frontend, or manual CLI)
python pipeline/phase_4/analyze_event_rai.py --limit 10
python pipeline/phase_4/analyze_event_rai.py --entity-type ctm --limit 5

# Event Saga Chaining (cross-month story linking)
python -m pipeline.phase_4.chain_event_sagas --dry-run
python -m pipeline.phase_4.chain_event_sagas --centroid-id MIDEAST-IRAN --track geo_domestic
python -m pipeline.phase_4.chain_event_sagas --threshold 0.35
```

### Queue Monitoring

```sql
-- Phase 2 queue
SELECT COUNT(*) FROM titles_v3 WHERE processing_status = 'pending';

-- Phase 3.1 queue (titles needing labels)
SELECT COUNT(*) FROM titles_v3 t
WHERE t.processing_status = 'assigned'
  AND t.centroid_ids IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM title_labels tl WHERE tl.title_id = t.id);

-- Phase 3.3 queue (titles needing track assignment)
SELECT COUNT(*) FROM titles_v3
WHERE processing_status = 'assigned'
  AND centroid_ids IS NOT NULL
  AND id NOT IN (SELECT title_id FROM title_assignments);

-- Phase 4.5a queue (events needing summaries)
SELECT COUNT(*) FROM events_v3 WHERE title IS NULL;

-- Phase 4.5b queue (CTMs needing digest)
SELECT COUNT(*) FROM ctm c
WHERE EXISTS (SELECT 1 FROM events_v3 e WHERE e.ctm_id = c.id)
  AND (summary_text IS NULL OR updated_at < NOW() - INTERVAL '24 hours');
```

---

## Infrastructure & Deployment

### Architecture

| Component | Local (dev) | Remote (demo) |
|-----------|-------------|---------------|
| **Database** | Docker: `pgvector/pgvector:pg15` on port 5432 | Render managed PostgreSQL (Frankfurt) |
| **Frontend** | `npm run dev` (localhost:3000) | Render web service (auto-deploy from `main`) |
| **Pipeline** | `python pipeline/runner/pipeline_daemon.py` | Render worker (suspended) |
| **Redis** | Docker: `redis:7-alpine` on port 6379 | Not used on remote |

### Source of Truth

**Local is authoritative.** The pipeline runs only locally to avoid doubling LLM API
costs. Remote is a read-only demo with a database snapshot.

### Database Sync (local -> remote)

The remote DB is a **full snapshot** of local. There is no selective sync or
migration -- dump the entire local DB and restore over the remote one.
This is safe because the remote has no pipeline running (no data to lose).

**When to sync**: After pipeline runs, after freeze, after any DB schema change,
or whenever the live demo needs to show current data.

**Step 1: Dump local DB** (runs inside the Docker container):
```bash
docker exec etl_postgres bash -c \
  "pg_dump -U postgres -d sni_v2 --no-owner --no-privileges --format=custom -f /tmp/sni_v2_live.dump"
```

**Step 2: Restore to Render** (also runs from the Docker container, which has `pg_restore`):
```bash
docker exec etl_postgres bash -c \
  "pg_restore -d 'postgresql://USER:PASS@HOST/DBNAME' \
   --no-owner --no-privileges --clean --if-exists /tmp/sni_v2_live.dump"
```

The Render external connection string is in the Render dashboard under
PostgreSQL > Info > External Database URL. Format:
`postgresql://USER:PASS@dpg-XXXXX-a.frankfurt-postgres.render.com/sni_v2`

**Step 3 (optional): Verify**:
```bash
docker exec etl_postgres bash -c \
  "psql 'postgresql://USER:PASS@HOST/DBNAME' -c 'SELECT COUNT(*) FROM titles_v3;'"
```

Notes:
- Step 2 uses `--clean --if-exists` which drops and recreates all objects. No
  need to run migrations separately -- the dump includes the full schema.
- `docker cp` to host is NOT required. The dump stays in `/tmp` inside the
  container and `pg_restore` reads it from there directly.
- The dump file is ~30 MB and restore takes ~1 minute to Frankfurt.
- Local `pg_dump`/`pg_restore` binaries are NOT installed on Windows. Always
  run these commands via `docker exec etl_postgres bash -c "..."`.

### Render Configuration

- `render.yaml`: Worker service definition (pipeline daemon)
- Frontend: Next.js web service, auto-deploys on push to `main`
- Database: Managed PostgreSQL 15, connection via `DATABASE_URL` env var
- Worker: Currently **suspended** (pipeline runs locally only)
- **Custom Domain**: www.worldbrief.info (SSL auto-provisioned via Let's Encrypt)
- **Analytics**: Google Analytics 4 (G-LF3GZ04SMF)

### Environment Variables

Local: `.env` file (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DEEPSEEK_API_KEY, RAI_API_KEY, etc.)
Remote: Render environment settings (`DATABASE_URL` connection string format)

Frontend connects to DB via `DATABASE_URL` or individual `DB_*` vars (see `apps/frontend/lib/db.ts`).

### RAI Analysis

- **Primary path**: Local RAI engine in `lib/rai-engine.ts` (calls DeepSeek directly)
- **Legacy path**: Remote RAI service at `RAI_API_URL` (retained for `/worldbrief/signals` endpoint)
- Required env vars: `DEEPSEEK_API_KEY` (frontend), `AUTH_SECRET` (NextAuth JWT signing)

---

## Current Status (2026-02-21)

**Operational**: Daemon runs Phases 1 through 4.5b + daily purge locally. Narrative extraction and RAI analysis are on-demand (user-triggered, auth-gated). January 2026 frozen with 85 centroid summaries. February 2026 pipeline active. User authentication live. Production site at https://www.worldbrief.info

### Recent Changes (2026-02-21)

1. **User Authentication**: Email/password auth via NextAuth v5 (D-029). Sign-in/sign-up pages, JWT sessions, user menu in navigation. Extraction and analysis API routes require authentication.
2. **On-Demand Extraction & Analysis**: Narrative extraction and RAI analysis moved from daemon (Phases 5 & 6) to user-triggered on-demand flow (D-030). FastAPI extraction service (`api/extraction_api.py`), frontend proxy routes, ExtractButton component. Users see "Extract & Analyse" CTA on entities without narratives.
3. **Local RAI Engine**: Analysis ported from remote RAI service to frontend-local engine (D-031). `lib/rai-engine.ts` with 33 modules / 46 premises, LLM-driven module selection, signal stats injection. Dedicated `/analysis/[narrative_id]` page with sidebar scores + prose.
4. **Daemon Simplified**: Phases 5 & 6 removed from `pipeline_daemon.py`. Daemon now runs Phases 1-4.5b + daily purge only.
5. **Coherence Check**: LLM evaluates topic cluster coherence before extraction. Result stored in `events_v3.coherence_check` JSONB, shown as amber warning in event sidebar.
6. **Self-Hosted Assets**: 152 flag PNGs + 176 outlet favicon PNGs self-hosted under `public/flags/` and `public/logos/`. CSP `img-src` tightened to `'self'`.
7. **Search**: Full-text search page (`/search`) across centroids, events, CTMs.
8. **Freshness Badges**: Green pulsing dot on events with recent coverage. Geographic mini-maps on centroid cards.
9. **Security Headers**: CSP, X-Frame-Options, Referrer-Policy added to Next.js config.

### Previous Changes (2026-02-21 early)

1. **Frontend Performance Optimization**: ISR revalidation replacing `force-dynamic` on all 13 pages (D-028). In-memory TTL cache for 9 queries. CTE query rewrites. Sitemap N+1 fix. Connection pool tuning.

### Previous Changes (2026-02-20)

1. **Event Saga Chaining**: `chain_event_sagas.py` links events across months using tag+title Dice similarity (no LLM). 432 story chains created across Jan-Feb, 757 events linked via `events_v3.saga` UUID. Event detail pages show Story Timeline with clickable siblings.
2. **Media Outlet Profile Pages**: New `/sources/{feed_name}` route showing per-outlet geographic coverage, top CTMs, and narrative frame participation. Publisher name normalization via shared CTE mapping.
3. **Inline Month Switch Removed**: CTM track page no longer has inline month pills in main content; month switching is sidebar-only (MonthNav component).

### Previous Changes (2026-02-17)

1. **Signals-First RAI Integration**: Two-tier architecture. Tier 1 = local stats computation (`core/signal_stats.py`), Tier 2 = RAI LLM interpretation via `/api/v1/worldbrief/signals`. Compact JSON signals stored in `narratives.rai_signals` JSONB. Full HTML analysis kept via `--full` flag.
2. **CTM Narrative Extraction (Phase 5a)**: `extract_ctm_narratives.py` with language-stratified sampling (200 titles, language floor of 5, publisher round-robin). Threshold: 100+ titles. Integrated into daemon (24h interval, limit 20 CTMs).
3. **Event Narrative Extraction (Phase 5b)**: Full rewrite of `extract_event_narratives.py`. Fixed column name bugs, added language-stratified sampling, frozen CTM filter, sync LLM, daemon integration (24h, limit 50). Threshold: 30+ sources.
4. **Refresh Mode**: Both narrative scripts support `--refresh` to re-extract when entities grow significantly. CTM refresh: title_count grew by 100+. Event refresh: source_batch_count grew by 50+ (tracked via `signal_stats.source_count_at_extraction`).
5. **Unified Narratives Table**: All entity types (epic, event, ctm) in one `narratives` table with `entity_type` + `entity_id`. Signal columns: `signal_stats` JSONB, `rai_signals` JSONB, `rai_signals_at` TIMESTAMPTZ.
6. **Phase 6 Daemon Integration**: `analyze_event_rai.py` generalized for both event + CTM narratives. `compute_ctm_stats` added with shared `_aggregate_rows` helper (DISTINCT ON to avoid double-counting). `process_rai_signals()` daemon callable runs both entity types. 24h interval, limit 20.
7. **Role Hallucination Fixes**: `core/llm_utils.py` adds `fix_role_hallucinations()` to post-process LLM prose. Fixes Trump ("Former President" -> "President") and Merz ("opposition leader" -> "Chancellor") due to DeepSeek training cutoff. Applied in Phase 4.5a and 4.5b.
8. **Title-Only Mode for Small Events**: Events with <5 sources get title only (no summary) in Phase 4.5a, reducing unnecessary LLM output.
9. **RAI Standalone Cleanup**: Deleted archive files, rotated API keys, env-var config, premise ID instructions.

### Previous Changes (2026-02-08 to 2026-02-10)

1. **Phase 4.1 Rewrite** (`consolidate_topics.py`): Replaced `aggregate_topics.py` with single-pass LLM consolidation. One call per bucket handles merge, rescue, and cleanup simultaneously. Old multi-step approach archived.
2. **Catchall Rescue**: Titles stuck in "Other Coverage" catchalls are now rescued into real topic events. LLM sees catchall items with positional indices; code uses parallel `title_ids` array (not fragile text matching) for DB updates.
3. **Centroid Validation Gate**: Bilateral catchall rescue validates each title's `centroid_ids` contains the bucket centroid before moving. Prevents cross-bucket contamination from propagating.
4. **Cross-Bucket Deduplication**: `cross_bucket_dedup()` finds and merges duplicate events across OI and bilateral buckets.
5. **OI Redistribution**: `redistribute_oi_catchall()` moves Other International catchall titles to bilateral catchalls based on foreign geo centroids.
6. **LLM Retry with Backoff**: All Phase 4 LLM calls use exponential backoff (configurable via `config.llm_retry_attempts`, `config.llm_retry_backoff`).
7. **Shared `extract_json`**: Deduplicated JSON extraction from 3 modules into `core/llm_utils.py`.
8. **Zombie Event Cleanup**: Events with 0 titles (from failed rescues or stale data) are automatically deleted during consolidation.
9. **Orphaned Title Routing**: `fix_orphaned_titles.py` routes titles present in `title_assignments` but missing from `event_v3_titles` into appropriate catchall events.
10. **Frontend Cleanup**: Removed standalone "Other Sources" section from track page. Hidden zero-source events via `source_batch_count > 0` filter in query.
11. **Entity Countries Backfill**: Extracted entity_countries from 12,859 Feb titles via LLM. Maps entity mentions to ISO codes for bilateral relationship tracking.
12. **Prompt Rule - No "Former"**: LLM explicitly forbidden from adding "Former" to politician roles unless headline contains it.
13. **Script Archive**: 5 obsolete Phase 4 scripts moved to `archive/phase_4_old/`.

### Previous Changes (2026-02-02 to 2026-02-07)

1. **Epics Feature (Phase 5)**: Cross-country story detection. Identifies events that span multiple centroids via shared anchor tags. Generates timeline, narratives, and per-centroid summaries.
2. **Narrative Extraction (Phase 5.5)**: Two-pass LLM approach extracts media framing from epic titles. Identifies 3-7 contested narratives per epic with moral frames and source attribution.
3. **RAI Analysis (Phase 6)**: Sends narratives to RAI (Risk Assessment Intelligence) service for adequacy scoring, conflict detection, and blind spot analysis. Full HTML reports stored.
4. **Signal Rankings**: Pre-computed monthly signal rankings with LLM-generated context (persons, orgs, places, etc.) displayed on epics page.
5. **Epic Frontend**: Epic list page with month navigation, detail pages with country accordion, narrative overlay with RAI scores and full analysis.
6. **Custom Domain**: Live at https://www.worldbrief.info (SSL via Render)
7. **Google Analytics**: GA4 tracking added (G-LF3GZ04SMF)
8. **Script Reorganization**: Epic scripts moved to `pipeline/epics/`, freeze scripts to `pipeline/freeze/`. Clear separation between worker phases and cron jobs.
9. **Prompt Consolidation**: All LLM prompts consolidated into `core/prompts.py` with shared prose writing rules (no-causality, no-roles, neutral-tone).

### Previous Changes (2026-01-15 to 2026-02-02)

1. **Non-destructive incremental clustering** (Phase 4): No longer deletes events on re-run; loads only unlinked titles, matches against existing events, creates new events for unmatched clusters. LLM summaries preserved.
2. **Events v3 normalized schema**: Migrated from JSONB `events_digest` to `events_v3` + `event_v3_titles` tables. Per-event lifecycle management.
3. **Phase restructuring (3.1/3.2/3.3)**: Label+signal extraction now runs before intel gating. Enables mechanical pre-gating on safe labels (~30% fewer LLM calls).
4. **Monthly freeze process**: `db/scripts/freeze_month.py` freezes CTMs, generates cross-track centroid summaries (per-track paragraphs via LLM), stores in `centroid_monthly_summaries`.
5. **Centroid summaries on frontend**: Frozen months show monthly overview with per-track headings; track navigation moves to sticky sidebar.
6. **Render deployment**: Frontend + DB snapshot on Render for demo. Pipeline worker suspended.
7. **Staleness detection**: `events_v3.summary_source_count` tracks when summaries were generated; Phase 4.5a re-summarizes events that grew >50%.

### Pipeline Statistics (2026-02-20)

- Titles: ~100,000+ total (~50k Jan frozen + ~50k Feb active)
- Active centroids: 85
- CTMs: ~870+ (437 frozen Jan + ~430 active Feb)
- Events: ~7,000+ (757 linked via saga chains)
- Epics: 9 (January 2026)
- Epic narratives: ~50 with RAI analysis
- Centroid monthly summaries: 85 (January)
- Daily ingestion: ~3,000-6,000 titles
- Saga chains: 432 cross-month story links

### Known Issues

1. **Phase 2 centroid gap**: Some topics appear under "Domestic" when they should be bilateral (e.g., Lebanon/UNIFIL under MIDEAST-ISRAEL domestic). Titles only have the home centroid, missing the foreign centroid (e.g., MIDEAST-LEVANT). Phase 2 mechanical matching doesn't catch all geographic references.
2. **Node memory leak**: Frontend dev server leaks to 2GB+ after ~3 days. Requires restart.
3. **Stale narratives**: No auto-refresh after removing daemon Phase 5. See OpenQuestions Q-001.
4. **No re-extraction path**: Users cannot re-extract narratives for entities that already have them. See OpenQuestions Q-002.

### Next Steps

1. **February Freeze**: End-of-month freeze + centroid summaries + epic detection
2. **Phase 2 Improvement**: Better centroid matching for bilateral relationships
3. **Staleness indicators**: Show users when narratives are outdated relative to current coverage
4. Monitor on-demand extraction usage patterns and quality
