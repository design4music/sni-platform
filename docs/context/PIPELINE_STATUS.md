# WorldBrief (SNI) v3 Pipeline - Technical Documentation

**Last Updated**: 2026-01-27
**Status**: Production - Full 6-phase pipeline operational
**Branch**: `main`

---

## Executive Summary

The v3 pipeline processes news headlines through 6 phases to produce intelligence CTMs (Centroid-Track-Month units) with structured events and narrative summaries. The system uses a PostgreSQL-native architecture with LLM-based classification and entity extraction.

### Pipeline Flow

```
RSS Feeds (Google News)
    |
[Phase 1] Ingestion --> titles_v3 (processing_status='pending')
    |
[Phase 2] Centroid Matching --> titles_v3 (centroid_ids assigned, status='assigned')
    |
[Phase 3] Intel Gating + Track Assignment --> title_assignments + ctm
    |
[Phase 3.5] Label Extraction (ELO v2.0) --> title_labels
    |
[Phase 4] Signal-Based Topic Clustering --> events_v3 + event_v3_titles (RESEARCH)
    |
[Phase 4.5a] Event Summary Generation --> events_v3.summary (narrative)
    |
[Phase 4.5b] CTM Digest Generation --> ctm.summary_text
    |
Frontend (Next.js) <-- READ-ONLY
```

---

## Phase 1: RSS Ingestion

**Script**: `pipeline/phase_1/ingest_feeds.py`
**Daemon Interval**: 12 hours
**Purpose**: Fetch headlines from Google News RSS feeds

### Processing

1. Load active feeds from `feeds` table
2. Fetch RSS with conditional GET (ETag/Last-Modified)
3. Parse entries with feedparser
4. Apply NFKC Unicode normalization
5. Extract real publisher from Google News redirect
6. Insert to `titles_v3` with `processing_status='pending'`

### Key Features

- Watermark-based incremental fetching (avoids duplicates)
- NFKC normalization for consistent matching
- Publisher extraction from Google News URLs
- Lookback window: `lookback_days` config (default: 3)

### Database

**Table**: `titles_v3`
```sql
id UUID PRIMARY KEY
title_display TEXT NOT NULL       -- The headline
url_gnews TEXT NOT NULL           -- Google News URL
publisher_name TEXT               -- Extracted publisher
pubdate_utc TIMESTAMP WITH TIME ZONE
detected_language TEXT
processing_status TEXT DEFAULT 'pending'
centroid_ids TEXT[]               -- Assigned in Phase 2
matched_aliases TEXT[]            -- Aliases that matched (Phase 2)
created_at, updated_at TIMESTAMPTZ
```

**Processing Status Values**:
- `pending`: Awaiting Phase 2 centroid matching
- `assigned`: Matched to centroids, awaiting Phase 3
- `out_of_scope`: No centroid match (taxonomy gap)
- `blocked_stopword`: Matched stop word (sports, entertainment)
- `blocked_llm`: Rejected by intel gating (Phase 3)

---

## Phase 2: Centroid Matching

**Script**: `pipeline/phase_2/match_centroids.py`
**Daemon Interval**: 5 minutes
**Purpose**: Match headlines to centroids via taxonomy aliases

### Algorithm

1. Load `taxonomy_v3` aliases (all languages) into memory
2. Build hash map for single-word lookup
3. Precompile regex patterns for multi-word aliases
4. For each pending title:
   - Normalize: lowercase, strip diacritics, NFKC, remove periods
   - Tokenize: strip possessives, split hyphenated compounds
   - Check stop words first (fast-fail to `blocked_stopword`)
   - Match against all centroids (accumulative)
5. Update `titles_v3.centroid_ids` and `matched_aliases`
6. Set `processing_status='assigned'` or `out_of_scope`

### Normalization Rules

```python
# Text normalization
title = unicodedata.normalize('NFKC', title.lower())
title = unidecode.unidecode(title)  # Strip diacritics
title = title.replace('.', '')      # Remove periods
title = re.sub(r'-+', '-', title)   # Normalize dashes

# Tokenization
tokens = re.split(r'[\s]+', title)
tokens = [t.rstrip("'s") for t in tokens]  # Strip possessives
```

### Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `v3_p2_batch_size` | 100 | Titles per batch |
| `v3_p2_max_titles` | 1000 | Max titles per run |
| `v3_p2_timeout_seconds` | 180 | Timeout per batch |

### Database

**Table**: `taxonomy_v3`
```sql
id UUID PRIMARY KEY
item_raw TEXT UNIQUE NOT NULL     -- Entity name (canonical)
aliases JSONB                     -- {"en": ["alias1"], "es": ["alias2"], ...}
is_active BOOLEAN DEFAULT TRUE
is_stop_word BOOLEAN DEFAULT FALSE
centroid_id VARCHAR(30)           -- Links to centroids_v3.id
```

**Table**: `centroids_v3`
```sql
id TEXT PRIMARY KEY               -- e.g., 'AMERICAS-USA', 'SYS-TECH'
label TEXT UNIQUE NOT NULL        -- Human-readable name
class TEXT NOT NULL               -- 'geo' or 'systemic'
primary_theater TEXT              -- e.g., 'AMERICAS', 'EUROPE' (geo only)
is_active BOOLEAN DEFAULT TRUE
track_config_id UUID              -- Links to track_configs
```

---

## Phase 3: Intel Gating & Track Assignment

**Script**: `pipeline/phase_3/assign_tracks_batched.py`
**Daemon Interval**: 10 minutes
**Purpose**: Filter non-strategic content and assign tracks via LLM

### Two-Stage Processing

**Stage 1: Intel Gating**
- LLM evaluates batch of titles for strategic relevance
- Rejects: Sports, entertainment, human interest, local crime, weather
- Accepts: Policy, international relations, economic, security, political
- Rejected titles: `processing_status='blocked_llm'`

**Stage 2: Track Assignment**
- For strategic titles, LLM assigns track using centroid-specific config
- Uses `track_configs` table for per-centroid track lists
- Creates `title_assignments` entries linking title-centroid-track-ctm

### Multi-Centroid Logic

A title with `centroid_ids = ['AMERICAS-USA', 'SYS-ENERGY']` is processed twice:
- Once for AMERICAS-USA using geo track config -> e.g., `geo_energy`
- Once for SYS-ENERGY using systemic track config -> e.g., `energy_coercion`

### Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `v3_p3_centroid_batch_size` | 50 | Titles per centroid batch |
| `v3_p3_concurrency` | 8 | Parallel LLM calls |
| `v3_p3_temperature` | 0.0 | LLM temperature |
| `v3_p3_max_tokens_gating` | 500 | Max tokens for gating |
| `v3_p3_max_tokens_tracks` | 500 | Max tokens for track assignment |

### Database

**Table**: `title_assignments`
```sql
id UUID PRIMARY KEY
title_id UUID NOT NULL REFERENCES titles_v3(id)
centroid_id TEXT NOT NULL REFERENCES centroids_v3(id)
track TEXT NOT NULL               -- e.g., 'geo_economy', 'geo_security'
ctm_id UUID NOT NULL REFERENCES ctm(id)
created_at, updated_at TIMESTAMPTZ
UNIQUE(title_id, centroid_id)     -- One track per title per centroid
```

**Table**: `ctm` (Centroid-Track-Month)
```sql
id UUID PRIMARY KEY
centroid_id UUID NOT NULL
track TEXT NOT NULL
month DATE NOT NULL               -- First day of month
title_count INTEGER DEFAULT 0
events_digest JSONB DEFAULT '[]'  -- Legacy, use events_v3 instead
summary_text TEXT                 -- Generated in Phase 4.5b
is_frozen BOOLEAN DEFAULT FALSE   -- Lock for historical stability
UNIQUE(centroid_id, track, month)
```

**Table**: `track_configs`
```sql
id UUID PRIMARY KEY
name TEXT UNIQUE NOT NULL         -- e.g., 'strategic_default', 'tech_focused'
description TEXT
tracks TEXT[] NOT NULL            -- Available tracks for this config
llm_track_assignment TEXT         -- Prompt for Phase 3 assignment
llm_summary_centroid_focus TEXT   -- Focus line for Phase 4.5 summaries
llm_summary_track_focus JSONB     -- Track-specific focus {track: focus}
is_default BOOLEAN DEFAULT FALSE
```

---

## Phase 3.5: Label Extraction (ELO v2.0)

**Script**: `pipeline/phase_3_5/extract_labels.py`
**Daemon Interval**: 10 minutes
**Purpose**: Extract structured event labels using Event Label Ontology

### Label Format

```
ACTOR -> ACTION_CLASS -> DOMAIN (-> TARGET)
```

Examples:
- `US_EXECUTIVE -> ECONOMIC_PRESSURE -> FOREIGN_POLICY -> EU`
- `RU_ARMED_FORCES -> MILITARY_OPERATION -> SECURITY -> UA`
- `US_CENTRAL_BANK -> POLICY_CHANGE -> ECONOMY`
- `CORPORATION -> ECONOMIC_DISRUPTION -> ECONOMY (actor_entity: NVIDIA)`

### Ontology Structure

**Actors** (with country prefixes):
- State: `XX_EXECUTIVE`, `XX_LEGISLATURE`, `XX_JUDICIARY`, `XX_CENTRAL_BANK`, `XX_ARMED_FORCES`
- IGOs: `UN`, `NATO`, `EU`, `AU`, `ASEAN`
- Generic: `CORPORATION`, `ARMED_GROUP`, `NGO`, `MEDIA_OUTLET`, `UNKNOWN`

**Action Classes (7-tier hierarchy)**:
| Tier | Actions |
|------|---------|
| T1: Formal Decision | LEGAL_RULING, LEGISLATIVE_DECISION, POLICY_CHANGE, REGULATORY_ACTION |
| T2: Coercive | MILITARY_OPERATION, LAW_ENFORCEMENT_OPERATION, SANCTION_ENFORCEMENT |
| T3: Resource | RESOURCE_ALLOCATION, INFRASTRUCTURE_DEVELOPMENT, CAPABILITY_TRANSFER |
| T4: Coordination | ALLIANCE_COORDINATION, STRATEGIC_REALIGNMENT, MULTILATERAL_ACTION |
| T5: Pressure | POLITICAL_PRESSURE, ECONOMIC_PRESSURE, DIPLOMATIC_PRESSURE, INFORMATION_INFLUENCE |
| T6: Contestation | LEGAL_CONTESTATION, INSTITUTIONAL_RESISTANCE, COLLECTIVE_PROTEST |
| T7: Incidents | SECURITY_INCIDENT, SOCIAL_INCIDENT, ECONOMIC_DISRUPTION |

**Domains**: GOVERNANCE, ECONOMY, SECURITY, FOREIGN_POLICY, SOCIETY, TECHNOLOGY, MEDIA

### Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `v3_p35_batch_size` | 50 | Titles per LLM batch |
| `v3_p35_concurrency` | 5 | Parallel workers |
| `v3_p35_temperature` | 0.1 | LLM temperature |
| `v3_p35_max_tokens` | 4000 | Max tokens per batch |

### Database

**Table**: `title_labels`
```sql
title_id UUID PRIMARY KEY REFERENCES titles_v3(id)
actor TEXT NOT NULL               -- e.g., 'US_EXECUTIVE', 'CORPORATION'
action_class TEXT NOT NULL        -- From ACTION_CLASSES ontology
domain TEXT NOT NULL              -- From DOMAINS ontology
target TEXT                       -- Optional target (ISO code or entity)
actor_entity TEXT                 -- For CORPORATION: specific company name
label_version TEXT DEFAULT 'ELO_v2.0'
confidence FLOAT DEFAULT 1.0
created_at, updated_at TIMESTAMPTZ
```

---

## Phase 4: Signal-Based Topic Clustering

**Status**: RESEARCH IN PROGRESS (2026-01-27)
**Current Script**: `pipeline/phase_4/incremental_clustering.py`
**Alternative**: `pipeline/phase_4/cluster_topics.py`
**Daemon Interval**: 30 minutes
**Purpose**: Cluster titles into topics using typed signals with co-occurrence

### Research Context

We are evaluating two signal-based clustering approaches:

| Script | Approach | Status |
|--------|----------|--------|
| `incremental_clustering.py` | Anchor-based, day-by-day, co-occurrence | **Current focus** |
| `cluster_topics.py` | IDF-weighted, batch processing | Alternative |

Both use typed signals from `title_labels` (persons, orgs, places, commodities, policies, systems, named_events) rather than ELO labels (actor, action_class).

### Incremental Clustering (Current)

**Key Concept**: Topics form around **anchor signals** that are locked early, then grow via **co-occurring signals**.

**Example**:
- Week 1: "FED" + "POWELL" become anchor signals (locked after 5 titles)
- Week 2: "LIZA COOK" appears alongside "FED" -> added as co-occurring signal
- Week 3: New titles matching "FED" + "COOK" still join, even if "POWELL" fades

**Algorithm**:
1. Process titles chronologically (oldest first)
2. First 5 titles define **anchor signals** (then locked)
3. Later titles match via weighted overlap with anchors
4. Co-occurring signals tracked but don't define topic identity
5. **Discriminators** reject titles with conflicting key signals (e.g., different orgs in geo_economy)

**Configuration** (from `core/config.py`):
```python
ANCHOR_LOCK_THRESHOLD = 5      # Titles before anchors lock
JOIN_THRESHOLD = 0.2           # Minimum similarity to join topic
HIGH_FREQ_PERSONS = {"TRUMP", "BIDEN", "PUTIN", "ZELENSKY", "XI"}  # Excluded from anchors

TRACK_WEIGHTS = {
    "geo_economy": {"orgs": 3.0, "commodities": 3.0, "policies": 2.0, ...},
    "geo_security": {"places": 3.0, "systems": 2.5, ...},
    ...
}

TRACK_DISCRIMINATORS = {
    "geo_economy": {"orgs": 0.8, "commodities": 0.5},  # Penalty for conflicts
    "geo_security": {"places": 0.7, "systems": 0.5},
    ...
}
```

### Manual Execution (Research)

```bash
# Dry run (see results without saving)
python pipeline/phase_4/incremental_clustering.py --ctm-id <ctm_id> --dry-run

# Write to database
python pipeline/phase_4/incremental_clustering.py --ctm-id <ctm_id> --write

# Alternative approach (for comparison)
python pipeline/phase_4/cluster_topics.py --centroid AMERICAS-USA --track geo_economy --write
```

### Bucket Assignment

Topics are assigned geographic buckets based on title signals:
- `domestic`: Home country events (matches centroid's ISO codes)
- `bilateral-XX`: Events involving specific foreign country XX
- `other_international`: Multi-country or unclear scope

### Database

**Table**: `events_v3`
```sql
id UUID PRIMARY KEY
ctm_id UUID NOT NULL REFERENCES ctm(id)
date DATE NOT NULL                -- Most recent title date
first_seen DATE                   -- Earliest title date (for date ranges)
title TEXT                        -- LLM-generated headline (5-15 words)
summary TEXT NOT NULL             -- LLM narrative (30-60 words)
tags TEXT[]                       -- LLM-extracted entity/topic tags
event_type VARCHAR(20)            -- 'bilateral', 'domestic', 'other_international'
bucket_key VARCHAR(100)           -- For bilateral: country code (e.g., 'CN')
source_batch_count INT DEFAULT 1  -- Title count
is_catchall BOOLEAN DEFAULT FALSE -- UNKNOWN without entity
created_at, updated_at TIMESTAMPTZ
```

**Table**: `event_v3_titles`
```sql
event_id UUID REFERENCES events_v3(id)
title_id UUID REFERENCES titles_v3(id)
PRIMARY KEY (event_id, title_id)
```

---

## Phase 4.5a: Event Summary Generation

**Script**: `pipeline/phase_4/generate_event_summaries_4_5a.py`
**Daemon**: Integrated with Phase 4
**Purpose**: Generate structured event data: title, summary, and tags

### Output Structure

LLM generates JSON for each event cluster:
```json
{
  "title": "Short headline (5-15 words)",
  "summary": "1-3 sentence narrative (30-60 words)",
  "tags": ["entity1", "entity2", "topic1", "topic2", "topic3"]
}
```

### Process

1. Identify events needing enrichment (no title or mechanical labels)
2. Fetch all titles for each event
3. LLM generates structured JSON with title, summary, tags
4. Update `events_v3` with title, summary, tags, first_seen

### Tag Categories

Tags capture key entities and topics for deduplication and filtering:
- People: Names of key figures mentioned
- Organizations: Companies, agencies, institutions
- Places: Countries, cities, regions (beyond the centroid)
- Topics: Key themes (tariffs, sanctions, elections, etc.)

### LLM Prompt (Key Points)

```
You are a news analyst. Generate structured event data from headlines.

OUTPUT FORMAT (JSON):
{
  "title": "Short headline (5-15 words)",
  "summary": "1-3 sentence narrative (30-60 words)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}

Requirements:
- Title: Concise headline capturing the core event
- Summary: Extract key facts, neutral tone, no "reports say"
- Tags: 3-5 tags for entities, places, topics
- Use names ONLY as they appear in headlines

Do NOT:
- Add role descriptions ("President", "Chancellor")
- Infer political offices - they may be outdated
```

---

## Phase 4.5b: CTM Digest Generation

**Script**: `pipeline/phase_4/generate_summaries_4_5.py`
**Daemon Interval**: 1 hour
**Purpose**: Generate 150-250 word monthly digest from event summaries

### Process

1. Query CTMs with events but no summary (or stale > 24h)
2. Fetch event summaries for each CTM
3. LLM generates cohesive digest weighted by source counts
4. Update `ctm.summary_text`

### Input Format

```
Event Summaries:

[137 sources] Trump threatened 25% tariffs on EU goods over Greenland...
[45 sources] Fed raised interest rates by 25 basis points amid inflation...
[23 sources] Senate passed $95 billion foreign aid package...
```

### LLM Prompt (Key Points)

```
Generate a 150-250 word narrative digest from the provided event summaries.

Requirements:
- Synthesize into cohesive monthly digest
- Weight by source count: [137 sources] >> [12 sources]
- Group thematically (2-4 paragraphs)
- Maintain analytic, neutral tone
- Preserve key details: names, figures, outcomes

Do NOT:
- List events as bullet points
- Include source counts in output
- Add role descriptions ("President", "Chancellor")
- Speculate beyond summaries
```

### Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `v3_p4_min_titles` | 30 | Min titles for summary |
| `v3_p4_max_concurrent` | 5 | Parallel LLM calls |
| `v3_p4_temperature` | 0.5 | LLM temperature |
| `v3_p4_max_tokens` | 500 | Max tokens per summary |

---

## Pipeline Daemon

**Script**: `pipeline/runner/pipeline_daemon.py`
**Purpose**: Orchestrate all phases with configurable intervals

### Phase Intervals

| Phase | Interval | Description |
|-------|----------|-------------|
| Phase 1 | 12 hours | RSS ingestion |
| Phase 2 | 5 minutes | Centroid matching |
| Phase 3 | 10 minutes | Intel gating + track assignment |
| Phase 3.5 | 10 minutes | Label extraction |
| Phase 4 | 30 minutes | Event clustering |
| Phase 4.5 | 1 hour | Summary generation |

### Features

- Sequential execution with interval-based scheduling
- Queue monitoring (skips phase if no work available)
- Graceful shutdown on SIGTERM/SIGINT
- Retry logic with exponential backoff (3 attempts)
- Full statistics after each cycle
- Word count monitoring for summaries

### Queue Monitoring Queries

```sql
-- Phase 2 queue
SELECT COUNT(*) FROM titles_v3 WHERE processing_status = 'pending';

-- Phase 3 queue
SELECT COUNT(*) FROM titles_v3
WHERE processing_status = 'assigned'
  AND id NOT IN (SELECT title_id FROM title_assignments);

-- Phase 3.5 queue
SELECT COUNT(*) FROM titles_v3 t
WHERE EXISTS (SELECT 1 FROM title_assignments ta WHERE ta.title_id = t.id)
  AND NOT EXISTS (SELECT 1 FROM title_labels tl WHERE tl.title_id = t.id);

-- Phase 4.5 queue
SELECT COUNT(*) FROM ctm c
WHERE EXISTS (SELECT 1 FROM events_v3 e WHERE e.ctm_id = c.id)
  AND (summary_text IS NULL OR updated_at < NOW() - INTERVAL '24 hours');
```

### Running

```bash
# Development
python pipeline/runner/pipeline_daemon.py

# Production (systemd)
sudo systemctl start sni-v3-pipeline
sudo systemctl enable sni-v3-pipeline
sudo journalctl -u sni-v3-pipeline -f
```

---

## Configuration Reference

**File**: `core/config.py`

### Database

| Setting | Default | Description |
|---------|---------|-------------|
| `db_host` | localhost | PostgreSQL host |
| `db_port` | 5432 | PostgreSQL port |
| `db_name` | sni_v2 | Database name |
| `db_user` | postgres | Database user |
| `db_password` | - | Database password |

### LLM

| Setting | Default | Description |
|---------|---------|-------------|
| `llm_provider` | deepseek | LLM provider |
| `llm_model` | deepseek-chat | Model name |
| `deepseek_api_url` | https://api.deepseek.com/v1 | API endpoint |
| `llm_timeout_seconds` | 600 | Request timeout |
| `llm_retry_attempts` | 3 | Retry count |
| `llm_retry_backoff` | 2.0 | Backoff multiplier |

### Phase-Specific

| Setting | Default | Description |
|---------|---------|-------------|
| `v3_p2_batch_size` | 100 | Phase 2 titles per batch |
| `v3_p3_centroid_batch_size` | 50 | Phase 3 titles per centroid |
| `v3_p35_batch_size` | 50 | Phase 3.5 titles per batch |
| `v3_p35_concurrency` | 5 | Phase 3.5 parallel workers |
| `v3_p4_min_titles` | 30 | Min titles for summary |

---

## Frontend (World Brief UI)

**Location**: `apps/frontend/`
**Technology**: Next.js 14 (App Router)

### Route Structure

```
/
|-- /global                        # Systemic centroids
|-- /region/:region_key            # Geographic region
|   |-- /c/:centroid_key           # Centroid view
|       |-- /t/:track_key?month=YYYY-MM  # CTM content
```

### Data Types

```typescript
interface CTM {
  id: string;
  centroid_id: string;
  track: Track;
  month: Date;
  title_count: number;
  events_digest: Event[];          // From events_v3
  summary_text?: string;           // From ctm.summary_text
  is_frozen: boolean;
}

interface Event {
  date: string;
  first_seen?: string;             // Earliest title date
  title?: string;                  // LLM-generated headline
  summary: string;                 // LLM narrative summary
  tags?: string[];                 // Entity/topic tags
  event_type?: 'bilateral' | 'other_international' | 'domestic';
  bucket_key?: string;             // Country code for bilateral
  source_count?: number;           // Title count
  is_catchall?: boolean;           // UNKNOWN without entity
}
```

### Database Access

Frontend reads from (SELECT-only):
- `centroids_v3` - Centroid metadata
- `ctm` - CTM aggregations with summaries
- `events_v3` - Event data
- `titles_v3` - Title details
- `title_assignments` - Title-CTM relationships

---

## File Map

```
pipeline/
|-- phase_1/
|   |-- ingest_feeds.py            # RSS ingestion
|   |-- feeds_repo.py              # Feed metadata management
|   |-- rss_fetcher.py             # RSS parsing utilities
|
|-- phase_2/
|   |-- match_centroids.py         # Centroid matching
|
|-- phase_3/
|   |-- assign_tracks_batched.py   # Intel gating + track assignment
|
|-- phase_3_5/
|   |-- extract_labels.py          # ELO v2.0 label extraction
|
|-- phase_4/
|   |-- incremental_clustering.py     # Signal-based clustering (current focus)
|   |-- cluster_topics.py             # Alternative: IDF-based clustering
|   |-- cluster_events_mechanical.py  # Legacy: ELO label-based (deprecated)
|   |-- generate_event_summaries_4_5a.py  # Event summaries
|   |-- generate_summaries_4_5.py     # CTM digests
|
|-- runner/
|   |-- pipeline_daemon.py         # Orchestration daemon

core/
|-- config.py                      # Configuration management
|-- ontology.py                    # ELO v2.0 definitions

db/
|-- migrations/                    # SQL migrations
```

---

## Quick Reference Commands

### Manual Phase Execution

```bash
# Phase 1: RSS Ingestion
python pipeline/phase_1/ingest_feeds.py --max-feeds 10

# Phase 2: Centroid Matching
python pipeline/phase_2/match_centroids.py --max-titles 500

# Phase 3: Track Assignment
python pipeline/phase_3/assign_tracks_batched.py --max-titles 100

# Phase 3.5: Label Extraction
python pipeline/phase_3_5/extract_labels.py --max-titles 200
python pipeline/phase_3_5/extract_labels.py --centroid AMERICAS-USA --track geo_economy

# Phase 4: Topic Clustering (research - manual execution)
# Current approach: incremental clustering with anchor signals
python pipeline/phase_4/incremental_clustering.py --ctm-id <ctm_id> --dry-run
python pipeline/phase_4/incremental_clustering.py --ctm-id <ctm_id> --write

# Alternative approach: IDF-weighted clustering
python pipeline/phase_4/cluster_topics.py --centroid AMERICAS-USA --track geo_economy
python pipeline/phase_4/cluster_topics.py --centroid AMERICAS-USA --track geo_economy --write

# Phase 4.5a: Event Summaries
python pipeline/phase_4/generate_event_summaries_4_5a.py --max-events 50

# Phase 4.5b: CTM Summaries
python pipeline/phase_4/generate_summaries_4_5.py --max-ctms 20
```

### Database Queries

```sql
-- Pipeline throughput by status
SELECT processing_status, COUNT(*)
FROM titles_v3
GROUP BY processing_status;

-- Label distribution by actor
SELECT actor, COUNT(*)
FROM title_labels
GROUP BY actor
ORDER BY COUNT(*) DESC LIMIT 20;

-- CTM summary coverage
SELECT
  COUNT(*) as total,
  COUNT(summary_text) as with_summary,
  COUNT(*) FILTER (WHERE title_count >= 30) as eligible
FROM ctm WHERE is_frozen = false;

-- Event type distribution
SELECT event_type, COUNT(*)
FROM events_v3
GROUP BY event_type;
```

---

## Current Status

**Operational**: Full pipeline running with daemon orchestration

**Recent Improvements** (2026-01-27):
- Signal-based clustering replaces ELO label-based clustering
- Consolidated signal constants to `core/config.py` (TRACK_WEIGHTS, TRACK_DISCRIMINATORS, etc.)
- Publisher name removal moved to ingestion time (Phase 1)
- Dropped 10 obsolete database tables
- Moved backfill scripts to `db/backfills/`

**Phase 4 Research** (2026-01-27):
- Evaluating `incremental_clustering.py` (anchor-based) vs `cluster_topics.py` (IDF-based)
- `incremental_clustering.py` is current focus - uses anchor locking and co-occurrence
- Both scripts produce good results; incremental approach better models topic evolution

**Next Steps**:
1. Refine incremental clustering parameters (thresholds, weights)
2. Evaluate clustering quality across different centroids/tracks
3. Finalize Phase 4 approach and integrate with daemon
4. Cross-CTM event deduplication
