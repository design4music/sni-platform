# WorldBrief (SNI) v3 Pipeline - Technical Documentation

**Last Updated**: 2026-02-02
**Status**: Production - Full pipeline operational
**Branch**: `main`

---

## Executive Summary

The v3 pipeline processes news headlines through 7 phases to produce intelligence CTMs (Centroid-Track-Month units) with structured events and narrative summaries. The system uses a PostgreSQL-native architecture with LLM-based classification and entity extraction.

### Pipeline Flow

```
RSS Feeds (Google News)
    |
[Phase 1] Ingestion --> titles_v3 (processing_status='pending')
    |
[Phase 2] Centroid Matching --> titles_v3 (centroid_ids assigned, status='assigned')
    |
[Phase 3.1] Label + Signal Extraction --> title_labels (combined LLM call)
    |
[Phase 3.2] Entity Centroid Backfill --> title_labels.entity_countries -> centroids
    |
[Phase 3.3] Intel Gating + Track Assignment --> title_assignments + ctm
    |
[Phase 4] Incremental Topic Clustering --> events_v3 + event_v3_titles
    |
[Phase 4.1] Topic Aggregation (LLM merge/cleanup) --> events_v3 (merged)
    |
[Phase 4.5a] Event Summary Generation --> events_v3.title, summary, tags
    |
[Phase 4.5b] CTM Digest Generation --> ctm.summary_text
    |
Frontend (Next.js) <-- READ-ONLY
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
| Phase 4.1 | (after 4) | all CTMs | Topic aggregation (LLM merge) |
| Phase 4.5a | 15 minutes | 500 events | Event summaries (decoupled) |
| Phase 4.5b | 1 hour | 50 CTMs | CTM digest generation |

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

## Phase 4.1: Topic Aggregation

**Script**: `pipeline/phase_4/aggregate_topics.py`
**Runs**: After Phase 4

### Purpose

LLM-based cleanup and merging of mechanically clustered topics:
- Merge similar topics that should be combined
- Split topics that are too broad
- Improve topic coherence

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
```

**ctm**: Centroid-Track-Month aggregations
```sql
centroid_id, track, month
title_count, summary_text, is_frozen
```

**centroid_monthly_summaries**: Cross-track summaries per centroid per month
```sql
centroid_id, month
summary_text, track_count, total_events
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
|   |-- incremental_clustering.py    # Topic clustering
|   |-- aggregate_topics.py          # LLM topic merge/cleanup
|   |-- generate_event_summaries_4_5a.py  # Event summaries
|   |-- generate_summaries_4_5.py    # CTM digests
|
|-- runner/
|   |-- pipeline_daemon.py           # Orchestration daemon

core/
|-- config.py                        # Configuration + clustering constants
|-- prompts.py                       # All LLM prompts (consolidated)
|-- ontology.py                      # ELO v2.0 definitions

db/
|-- scripts/
|   |-- freeze_month.py             # Monthly freeze + centroid summaries
|-- backfills/
|   |-- backfill_unknown_entities.py # Unknown entity resolution
|-- migrations/                      # SQL migrations

apps/frontend/
|-- app/
|   |-- c/[centroid_key]/page.tsx    # Centroid page (summary + tracks)
|   |-- c/[centroid_key]/t/[track_key]/page.tsx  # CTM track page
|-- lib/
|   |-- queries.ts                   # All DB queries
|   |-- types.ts                     # Shared types (Track, REGIONS, etc.)
|-- components/
|   |-- DashboardLayout.tsx          # Main layout (sidebar + content grid)
|   |-- TrackCard.tsx                # Track card component
|   |-- GeoBriefSection.tsx          # Centroid profile/brief display
|   |-- MonthPicker.tsx              # Month navigation
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

# Phase 4.5a: Event Summaries
python pipeline/phase_4/generate_event_summaries_4_5a.py --max-events 500

# Phase 4.5b: CTM Summaries
python pipeline/phase_4/generate_summaries_4_5.py --max-ctms 50
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

```bash
# 1. Dump from local Docker container
docker exec etl_postgres bash -c \
  "pg_dump -U postgres -d sni_v2 --no-owner --no-privileges --format=custom -f /tmp/sni_v2_live.dump"

# 2. Copy dump to host
docker cp etl_postgres:/tmp/sni_v2_live.dump ./sni_v2_live.dump

# 3. Restore to Render (get connection string from Render dashboard)
docker exec etl_postgres bash -c \
  "pg_restore -d 'postgresql://USER:PASS@HOST/DBNAME' \
   --no-owner --no-privileges --clean --if-exists /tmp/sni_v2_live.dump"
```

### Render Configuration

- `render.yaml`: Worker service definition (pipeline daemon)
- Frontend: Next.js web service, auto-deploys on push to `main`
- Database: Managed PostgreSQL 15, connection via `DATABASE_URL` env var
- Worker: Currently **suspended** (pipeline runs locally only)

### Environment Variables

Local: `.env` file (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DEEPSEEK_API_KEY, etc.)
Remote: Render environment settings (`DATABASE_URL` connection string format)

Frontend connects to DB via `DATABASE_URL` or individual `DB_*` vars (see `apps/frontend/lib/db.ts`).

---

## Current Status (2026-02-02)

**Operational**: Full 7-phase pipeline running locally with daemon orchestration.
January 2026 frozen with 85 centroid summaries. February 2026 pipeline active.

### Recent Changes (since 2026-01-15)

1. **Non-destructive incremental clustering** (Phase 4): No longer deletes events on re-run; loads only unlinked titles, matches against existing events, creates new events for unmatched clusters. LLM summaries preserved.
2. **Events v3 normalized schema**: Migrated from JSONB `events_digest` to `events_v3` + `event_v3_titles` tables. Per-event lifecycle management.
3. **Phase restructuring (3.1/3.2/3.3)**: Label+signal extraction now runs before intel gating. Enables mechanical pre-gating on safe labels (~30% fewer LLM calls).
4. **Monthly freeze process**: `db/scripts/freeze_month.py` freezes CTMs, generates cross-track centroid summaries (per-track paragraphs via LLM), stores in `centroid_monthly_summaries`.
5. **Centroid summaries on frontend**: Frozen months show monthly overview with per-track headings; track navigation moves to sticky sidebar.
6. **Render deployment**: Frontend + DB snapshot on Render for demo. Pipeline worker suspended.
7. **Staleness detection**: `events_v3.summary_source_count` tracks when summaries were generated; Phase 4.5a re-summarizes events that grew >50%.

### Pipeline Statistics (2026-02-02)

- Titles: ~46,000 total (Jan: ~42K, Feb: ~4K so far)
- Active centroids: 85
- CTMs: 667 (437 frozen Jan + 230 active Feb)
- Events: ~5,100
- Centroid monthly summaries: 85 (January)
- Daily ingestion: ~3,000-6,000 titles
- Assignment rate: ~43% assigned, ~40% out-of-scope, ~8% blocked

### Next Steps

1. Monitor February pipeline quality and clustering coherence
2. Tune clustering parameters based on multi-month data
3. Cross-CTM event deduplication
4. Evaluate label clustering for taxonomy refinement
