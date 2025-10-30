# SNI Pipeline Flow v2

**Complete guide to the Strategic News Intelligence processing pipeline**

---

## Overview

The SNI pipeline transforms raw multilingual news feeds into structured strategic intelligence through 6 phases:

- **P1: Ingestion** - Fetch and store raw news titles
- **P2: Entity Enrichment** - Extract actors, actions, targets, and entities
- **P3: Event Generation** - Cluster titles and generate discrete Events
- **P3.5: Event Validation** - Validate, merge, split, and refine Events
- **P4: Event Enrichment** - Add strategic context and analysis (future)
- **P5: Narrative Detection** - Identify propaganda patterns (future)
- **P6: Framing Analysis** - Detect rhetorical strategies (future)

---

## Phase 1: Ingestion (P1)

**Purpose:** Fetch news from RSS feeds and store in database

**Process:**
1. Fetch from configured RSS feeds
2. Parse title, URL, publisher, publication date
3. Detect language (30+ languages supported)
4. Store in `titles` table with status='raw'

**Scripts:**
- `apps/ingest/run_p1.py` - Main ingestion script
- `apps/ingest/feed_fetcher.py` - RSS feed parsing logic

**Output:** Raw titles in database with basic metadata

---

## Phase 2: Entity Enrichment (P2)

**Purpose:** Extract structured information from titles using LLM

**Process:**
1. **Actor-Action-Target (AAT) Triple Extraction:**
   - ACTOR: Main entity performing action (person, org, country)
   - ACTION: Main verb or action phrase
   - TARGET: Entity receiving/affected by action
   - Allows partial triples (null components OK)
   - Format: `ACTOR|ACTION|TARGET` (e.g., "US|sanctions|Russia")

2. **Entity Extraction:**
   - Geopolitical entities (countries, regions, organizations)
   - Key actors and institutions
   - Stored as JSON array in `entities` field

3. **Strategic Filtering (gate_keep):**
   - LLM determines if title is strategically significant
   - Excludes: sports, entertainment, weather, celebrity news
   - Includes: diplomacy, military, policy, international relations
   - Sets `gate_keep=true` for strategic titles

**Scripts:**
- `apps/filter/run_p2.py` - Main P2 orchestrator
- `apps/filter/entity_enrichment.py` - AAT and entity extraction logic
- `apps/filter/strategic_filter.py` - Strategic significance detection

**Configuration:**
```bash
python apps/filter/run_p2.py --max-titles 2000 --hours 168
```
- `--max-titles`: Batch size for processing
- `--hours`: Look back window (default: 168 = 1 week)

**Output:**
- `action_triple` field: `{"actor": "...", "action": "...", "target": "..."}`
- `entities` field: `["United States", "China", "NATO"]`
- `gate_keep=true` for strategic titles

---

## Phase 3: Event Generation (P3)

**Purpose:** Cluster related titles and generate discrete time-bounded Events

### Two Alternative Implementations:

#### **P3 Classic (run_p3.py)** - Pure LLM clustering
- **MAP Phase:** Pure LLM-based clustering (expensive, slow)
- **REDUCE Phase:** Event Family generation
- **Use case:** Fallback option, smaller batches

#### **P3 v1 (run_p3_v1.py)** ⭐ RECOMMENDED
- **MAP Phase:** Hybrid graph-based clustering (fast, scalable)
- **REDUCE Phase:** Event Family generation (same as classic)
- **Use case:** Production, large-scale processing

---

### P3 v1 Architecture (Hybrid Clustering)

#### Prerequisites - Neo4j Cache Generation:

**1. Sync Titles to Neo4j:**
```bash
python apps/generate/sync_titles_to_neo4j.py
```
- Syncs `gate_keep=true` titles to Neo4j as nodes
- Creates `:Title` nodes with properties (id, text, pubdate, entities)
- Incremental sync (only new/updated titles)

**2. Create AAT Triple Relationships:**
```bash
python apps/generate/neo4j_cluster_prep.py
```
- Creates `:HAS_ENTITY` relationships: `(:Title)-[:HAS_ENTITY]->(:Entity)`
- Creates `:AAT_TRIPLE` relationships: `(:Title)-[:AAT_ACTOR|AAT_ACTION|AAT_TARGET]->(:Entity)`
- Enables graph-pattern clustering on entity co-occurrence

**3. Build Connectivity Cache:**
```bash
python apps/generate/connectivity_cache.py
```
- Computes connectivity scores from Neo4j entity overlaps
- Jaccard similarity (50% weight) + Actor matching (20% weight)
- Stores in `title_connectivity_cache` table for O(1) lookups
- Rebuilds in ~30 seconds for full corpus

**Validation:**
```bash
python apps/generate/validate_p3v1_setup.py
```
- Checks Neo4j connection and data
- Validates connectivity cache
- Verifies title sync status

---

#### P3 v1 MAP Phase - Hybrid Clustering

**Script:** `apps/generate/run_p3_v1.py`

**Process:**
1. **Fetch unassigned strategic titles** (`gate_keep=true`, `event_id IS NULL`)
2. **Load connectivity cache** from Postgres
3. **Graph-based clustering** using hybrid scoring:
   - **Tight clusters** (score ≥ 0.7): High confidence, auto-accept
   - **Moderate clusters** (0.4 ≤ score < 0.7): Optional LLM validation
   - **Weak connections** (score < 0.4): Too loose, ignore
4. **LLM validation** (moderate clusters only):
   - Validates cluster coherence
   - Rejects false positives
   - Minimal LLM usage (~5% of old P3)

**Clustering Logic:** `apps/generate/hybrid_clusterer.py`

**Output:**
- List of `IncidentCluster` objects
- Each cluster contains title IDs and incident name/rationale

**Performance:**
- MAP phase: ~3 seconds for 873 titles (vs ~5+ minutes for LLM-only)
- 80%+ clustering rate on strategic titles
- 90% cost reduction vs pure LLM clustering

---

#### P3 REDUCE Phase - Event Family Generation

**Script:** `apps/generate/reduce_assembler.py`

**Process:**
1. **Parallel LLM calls** for each incident cluster (concurrency: 10)
2. **Extract discrete Events** (not sagas):
   - Event = ONE occurrence with ≤72h temporal span
   - Must include: Actor + Concrete Action + Specific Place + Date
   - Split if temporal span > 72h
   - Remove near-duplicates
3. **Event metadata extraction:**
   - `event_title`: Verifiable microfact with all 4 components
   - `event_type`: Classify from taxonomy (Strategy/Tactics, Diplomacy, etc.)
   - `primary_theater`: Mechanically inferred from entity frequencies
   - `strategic_purpose`: One-sentence narrative unifying the events
   - `events`: Timeline of discrete factual events within the incident

**Event Title Requirements:**
- ✅ GOOD: "Turkey: 7.8 magnitude earthquake strikes Gaziantep region - Feb 6, 2025"
- ✅ GOOD: "Amazon announces workforce restructuring (12,000 layoffs) - Jan 15, 2025"
- ❌ BAD: "Turkey earthquake developments" (too broad, vague)
- ❌ BAD: "US positioning on Gaza" (positioning = continuous state not event)

**Output:**
- `EventFamily` objects ready for P3.5 validation
- Each contains: title, summary, strategic_purpose, events timeline

**Performance:**
- REDUCE phase: ~300-400 seconds for 126 clusters
- Parallel processing with configurable concurrency

---

### Running P3 v1:

**Full pipeline with limit:**
```bash
python apps/generate/run_p3_v1.py 500
```
- Processes up to 500 unassigned strategic titles
- Runs MAP → REDUCE → P3.5 pipeline
- Creates Events in database

**Testing/debugging:**
```bash
python apps/generate/reset_test_data.py  # Reset for clean run
python apps/generate/run_p3_v1.py 50      # Small test batch
```

---

## Phase 3.5: Event Validation (P3.5)

**Purpose:** Refine and validate generated Events through 5 sub-phases

**Script:** `apps/generate/p35_pipeline.py`

### P3.5 Sub-phases:

#### **P3.5a: Seed Validation**
- **Script:** `apps/generate/seed_validator.py`
- **Purpose:** Validate Event Families meet quality thresholds
- **Process:**
  - LLM checks coherence, strategic significance, temporal bounds
  - Promotes `seed` → `active` if valid
  - Marks `seed` → `recycled` if rejected
  - Orphans titles from rejected Events

#### **P3.5b: Title Recycling**
- **Script:** `apps/generate/title_recycler.py`
- **Purpose:** Reassign orphaned titles to existing Events
- **Process:**
  - Find titles with `event_id IS NULL` but previously assigned
  - Match to existing `active` Events using thematic similarity
  - Prevents title loss from rejected Events

#### **P3.5c: Event Merging**
- **Script:** `apps/generate/ef_merger.py`
- **Purpose:** Merge semantically identical Events
- **Process:**
  - Find Events with same `ef_key` (theater + event_type)
  - LLM validates if they describe the same strategic situation
  - Merge duplicates, combine titles
  - Prevents redundant Event proliferation

#### **P3.5d: Event Splitting**
- **Script:** `apps/generate/ef_splitter.py`
- **Purpose:** Split overly broad Events
- **Process:**
  - Detect Events with >72h span or multiple distinct incidents
  - LLM proposes split into discrete Events
  - Creates new Events from splits
  - Ensures temporal bounds (≤72h per Event)

#### **P3.5e: Thematic Validation**
- **Script:** `apps/generate/thematic_validator.py`
- **Purpose:** Validate new titles still fit existing Events
- **Process:**
  - For each active Event, check if member titles still match strategic_purpose
  - LLM validates thematic coherence
  - Orphan mismatched titles for reassignment

**Output:**
- Refined `active` Events in database
- Titles properly assigned to validated Events
- Rejected Events marked as `recycled`

---

## Phase 4-6: Future Phases

### Phase 4: Event Enrichment (P4)
- **Purpose:** Add strategic context and analysis to Events
- **Scripts:** `apps/enrich/run_p4.py`, `apps/enrich/processor.py`
- **Status:** Partial implementation

### Phase 5: Narrative Detection (P5)
- **Purpose:** Identify propaganda patterns and information operations
- **Status:** Not yet implemented

### Phase 6: Framing Analysis (P6)
- **Purpose:** Detect rhetorical strategies and bias patterns
- **Scripts:** `apps/generate/run_p6.py`, `apps/generate/framing_processor.py`
- **Status:** Partial implementation

---

## Complete Pipeline Execution

### Full Production Run:

```bash
# 1. Run P1 (Ingestion)
python apps/ingest/run_p1.py

# 2. Run P2 (Entity Enrichment)
python apps/filter/run_p2.py --max-titles 2000 --hours 168

# 3. Prepare Neo4j cache (if needed)
python apps/generate/sync_titles_to_neo4j.py
python apps/generate/neo4j_cluster_prep.py
python apps/generate/connectivity_cache.py

# 4. Run P3 v1 (Event Generation + P3.5 Validation)
python apps/generate/run_p3_v1.py 1000

# 5. (Future) Run P4-P6 enrichment phases
# python apps/enrich/run_p4.py
```

### Incremental Updates:

```bash
# Daily ingestion + enrichment
python apps/ingest/run_p1.py && python apps/filter/run_p2.py --max-titles 500 --hours 24

# Update Neo4j cache (incremental)
python apps/generate/sync_titles_to_neo4j.py  # Only syncs new titles

# Rebuild connectivity cache (if new strategic titles)
python apps/generate/connectivity_cache.py    # ~30 seconds

# Process new strategic titles
python apps/generate/run_p3_v1.py 500
```

---

## Scripts Reference

### Phase 1: Ingestion
- `apps/ingest/run_p1.py` - Main ingestion orchestrator
- `apps/ingest/feed_fetcher.py` - RSS feed parsing

### Phase 2: Entity Enrichment
- `apps/filter/run_p2.py` - Main P2 orchestrator
- `apps/filter/entity_enrichment.py` - AAT + entity extraction
- `apps/filter/strategic_filter.py` - Strategic filtering

### Phase 3: Event Generation

#### P3 Classic (Legacy)
- `apps/generate/run_p3.py` - Pure LLM clustering

#### P3 v1 (Recommended)
- `apps/generate/run_p3_v1.py` - Main P3 v1 orchestrator
- `apps/generate/hybrid_clusterer.py` - Hybrid clustering logic
- `apps/generate/reduce_assembler.py` - Event Family generation

#### Neo4j Cache Preparation
- `apps/generate/sync_titles_to_neo4j.py` - Sync titles to Neo4j
- `apps/generate/neo4j_cluster_prep.py` - Create AAT relationships
- `apps/generate/connectivity_cache.py` - Build connectivity cache
- `apps/generate/validate_p3v1_setup.py` - Validate setup

#### Testing & Utilities
- `apps/generate/reset_test_data.py` - Reset test data for clean runs

### Phase 3.5: Event Validation
- `apps/generate/p35_pipeline.py` - Main P3.5 orchestrator
- `apps/generate/seed_validator.py` - P3.5a: Seed validation
- `apps/generate/title_recycler.py` - P3.5b: Title recycling
- `apps/generate/ef_merger.py` - P3.5c: Event merging
- `apps/generate/ef_splitter.py` - P3.5d: Event splitting
- `apps/generate/thematic_validator.py` - P3.5e: Thematic validation

### Phase 4-6 (Partial)
- `apps/enrich/run_p4.py` - Event enrichment orchestrator
- `apps/enrich/processor.py` - Enrichment processor
- `apps/generate/run_p6.py` - Framing analysis orchestrator
- `apps/generate/framing_processor.py` - Framing detection

### Core Infrastructure
- `core/llm_client.py` - All LLM prompts and API calls
- `core/database.py` - Database session management
- `core/neo4j_sync.py` - Neo4j connection management
- `core/config.py` - Configuration management

---

## Database Schema

### Key Tables

#### `titles`
- Raw news titles with enrichment
- Fields: `id`, `title_display`, `pubdate_utc`, `entities`, `action_triple`, `gate_keep`, `event_id`
- Status: Links to Events via `event_id`

#### `events`
- Discrete time-bounded strategic Events
- Fields: `id`, `title`, `summary`, `strategic_purpose`, `event_type`, `primary_theater`, `key_actors`, `events`, `status`
- Status values: `seed`, `active`, `recycled`

#### `title_connectivity_cache`
- Pre-computed connectivity scores for clustering
- Fields: `title_id_1`, `title_id_2`, `co_occurs_score`, `same_actor_score`, `total_score`, `shared_actor`
- Rebuilt from Neo4j entity overlaps

---

## Performance Metrics

### P2 (Entity Enrichment)
- **Throughput:** ~500-1000 titles per run
- **Cost:** 3 LLM calls per title (AAT + entities + strategic filter)
- **Time:** ~1-2 minutes for 500 titles

### P3 v1 (Event Generation)
- **MAP phase:** ~3 seconds for 873 titles
- **REDUCE phase:** ~300-400 seconds for 126 clusters
- **Clustering rate:** 80%+ on strategic titles
- **Cost reduction:** 90% vs pure LLM clustering

### P3.5 (Event Validation)
- **P3.5a (Seed):** ~5-10 minutes for 126 Events
- **P3.5b-e:** Minimal time (<1 minute each)
- **Total P3.5:** ~5-15 minutes depending on batch size

### Neo4j Cache Generation
- **Title sync:** ~10-30 seconds (incremental)
- **AAT relationships:** ~30-60 seconds
- **Connectivity cache:** ~30 seconds full rebuild

---

## Monitoring & Debugging

### Database Queries

**Check pipeline status:**
```sql
-- Total titles by status
SELECT
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE gate_keep = true) as strategic,
  COUNT(*) FILTER (WHERE event_id IS NOT NULL) as assigned,
  COUNT(*) FILTER (WHERE gate_keep = true AND event_id IS NULL) as unassigned_strategic
FROM titles;

-- Events by status
SELECT status, COUNT(*) FROM events GROUP BY status;

-- Connectivity cache stats
SELECT COUNT(*) as total_connections,
       AVG(total_score) as avg_score,
       COUNT(*) FILTER (WHERE total_score >= 0.7) as strong_connections
FROM title_connectivity_cache;
```

### Log Monitoring

**Key log patterns:**
- `REDUCE: Analyzing incident cluster` - REDUCE phase progress
- `P3.5a: Validating seed` - P3.5 validation progress
- `Clustering complete:` - MAP phase results
- `Total Event Families:` - REDUCE phase results

---

## Configuration

### Environment Variables
- `DATABASE_URL` - Postgres connection string
- `NEO4J_URI` - Neo4j connection URI
- `NEO4J_USER` / `NEO4J_PASSWORD` - Neo4j credentials
- `DEEPSEEK_API_KEY` - LLM API key

### Key Config Parameters (core/config.py)
- `reduce_concurrency` - Parallel REDUCE workers (default: 10)
- `llm_max_tokens_generic` - Token limit for LLM calls
- `llm_temperature` - LLM creativity (0.0-1.0)
- `ef_title_max_length` - Max Event title length (120 chars)
- `ef_summary_max_length` - Max Event summary length (500 chars)

---

## Troubleshooting

### Common Issues

**1. Neo4j cache out of sync:**
```bash
# Rebuild from scratch
python apps/generate/sync_titles_to_neo4j.py
python apps/generate/neo4j_cluster_prep.py
python apps/generate/connectivity_cache.py
```

**2. Low clustering rate (<50%):**
- Check connectivity cache is populated
- Verify Neo4j has AAT relationships
- Review entity extraction quality in P2

**3. Events too broad (>72h):**
- P3.5d (splitting) should catch these
- Check REDUCE prompts enforce ≤72h requirement
- Review `date_range_hours` validation

**4. LLM errors/timeouts:**
- Check API key is valid
- Monitor rate limits
- Reduce concurrency in config

---

## Future Improvements

### Planned Enhancements
- [ ] Real-time ingestion (streaming)
- [ ] Multi-language Event consolidation
- [ ] Automated theater inference improvements
- [ ] P4-P6 full implementation
- [ ] Web dashboard for monitoring
- [ ] API endpoints for Event querying

---

**Last Updated:** 2025-10-30
**Pipeline Version:** v2.0 (P3 v1 hybrid clustering)
