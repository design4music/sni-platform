# WorldBrief (SNI) v3 Pipeline - Technical Documentation

**Last Updated**: 2026-01-24
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
[Phase 4] Mechanical Event Clustering --> events_v3 + event_v3_titles
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

## Phase 4: Mechanical Event Clustering

**Script**: `pipeline/phase_4/cluster_events_mechanical.py`
**Daemon Interval**: 30 minutes
**Purpose**: Cluster labeled titles into events using entity-centric grouping

### Clustering Hierarchy

1. **Bucket Assignment**: Split by geographic scope
   - `domestic`: Home country events
   - `bilateral_XX`: Events involving foreign country XX

2. **Entity-Centric Clustering** (takes priority):
   - Institutional entities (US_CENTRAL_BANK, US_JUDICIARY) -> one event per institution
   - Corporate entities (NVIDIA, META) -> one event per corporation

3. **Action-Based Clustering** (fallback):
   - Group by (actor, action_class) tuple
   - Minimum cluster size: 3 titles

4. **Spike Detection**:
   - Large UNKNOWN clusters split by activity spikes
   - Threshold: 2x average daily volume

### Entity Grouping Rules

**Institutional Entities** (cluster ALL actions together):
```python
INSTITUTIONAL_ENTITIES = {
    "US_CENTRAL_BANK", "US_JUDICIARY", "US_LEGISLATURE",
    "EU_CENTRAL_BANK", "CN_CENTRAL_BANK", "UK_CENTRAL_BANK", "JP_CENTRAL_BANK"
}
```

**Corporate Entities** (from actor_entity or known targets):
```python
KNOWN_CORPORATE_TARGETS = {
    "META", "OPENAI", "NVIDIA", "APPLE", "GOOGLE", "AMAZON", "MICROSOFT",
    "TESLA", "BOEING", "JPMORGAN", "SPACEX", "NETFLIX", "DISNEY", ...
}
```

### Algorithm Flow

```python
def cluster_titles(titles, centroid_id):
    # Step 1: Assign buckets
    buckets = defaultdict(list)
    for t in titles:
        bucket = assign_bucket(t, centroid_id)  # Uses target, actor, aliases
        buckets[bucket].append(t)

    # Step 2: Cluster within each bucket
    events = []
    for bucket_name, bucket_titles in buckets.items():
        # Entity-centric grouping
        for key, cluster in cluster_by_labels(bucket_titles).items():
            if key[0] == "INSTITUTION":
                # All Fed news in one event
                events.append(create_event(bucket_name, key[1], None, None, cluster))
            elif key[0] == "CORPORATION":
                # All NVIDIA news in one event
                events.append(create_event(bucket_name, "CORPORATION", key[1], None, cluster))
            else:
                # Standard (actor, action) grouping
                events.append(create_event(bucket_name, key[1], None, key[2], cluster))

    return events
```

### Database

**Table**: `events_v3`
```sql
id UUID PRIMARY KEY
ctm_id UUID NOT NULL REFERENCES ctm(id)
date DATE NOT NULL                -- Most recent title date
summary TEXT NOT NULL             -- Mechanical label or LLM narrative
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
**Purpose**: Generate 1-3 sentence narrative summaries for event clusters

### Process

1. Identify events with mechanical labels (contain `->` or `titles)`)
2. Fetch all titles for each event
3. LLM generates 1-3 sentence summary from headlines
4. Update `events_v3.summary` with narrative text

### LLM Prompt (Key Points)

```
You are a news analyst. Summarize these headlines into 1-3 concise sentences.

Requirements:
- Extract key facts: who, what, where, specific figures/names
- Write as if describing events directly (not "headlines report...")
- Capture the arc if there's progression (threat -> escalation -> resolution)
- Neutral, factual tone
- 1-3 sentences only (30-60 words)
- Use names ONLY as they appear in headlines

Do NOT:
- Mention "headlines", "articles", "reports"
- Add role descriptions like "President", "former President", "Chancellor"
- Infer current political offices - they may be outdated
- Use any descriptive titles not explicitly in the headlines
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
  summary: string;                 // Narrative summary
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
|   |-- cluster_events_mechanical.py  # Entity-centric clustering
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

# Phase 4: Event Clustering
python pipeline/phase_4/cluster_events_mechanical.py --centroid AMERICAS-USA --track geo_economy
python pipeline/phase_4/cluster_events_mechanical.py --centroid AMERICAS-USA --track geo_economy --write

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

**Recent Improvements** (2026-01-24):
- Entity-centric clustering (institutions, corporations)
- Two-tier summary architecture (events -> CTM digest)
- Role description fix (no inferred titles)
- All USA tracks processed with new mechanism

**Next Steps**:
1. Backfill labels for all existing titles
2. Refine entity extraction for non-US centroids
3. Cross-CTM event deduplication
4. Frontend display enhancements
