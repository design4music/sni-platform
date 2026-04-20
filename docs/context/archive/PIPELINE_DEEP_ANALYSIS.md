# Pipeline Deep Analysis Report

**Date**: 2026-03-27
**Branch**: `feat/sector-clustering`
**Context**: Pre-merge analysis of full pipeline (Phase 1-4), integration of experimental clustering code, optimization opportunities.

---

## 1. FUNCTIONAL OVERLAPS & SIMPLIFICATION OPPORTUNITIES

### A. Phase 3.3 (Intel Gating) is redundant with Sector/Subject classification

The experimental branch already classifies titles into sectors including `NON_STRATEGIC`. Phase 3.3 makes a separate LLM call to decide "strategic vs not strategic" -- the same judgment. With sector/subject now extracted in Phase 3.1, we can gate mechanically:
- `sector == NON_STRATEGIC` -> reject (no LLM needed)
- Everything else -> strategic

**Cost saved:** ~$0.007 per 500 titles x every 15-min cycle = significant over time.

**Track assignment** in Phase 3.3 is also redundant with `SECTOR_TO_TRACK` mapping. The LLM-based track assignment was needed before sectors existed. Now it's a mechanical lookup.

**Proposal: Eliminate Phase 3.3 entirely.** Replace with:
- Mechanical NON_STRATEGIC filter after Phase 3.1
- Mechanical `SECTOR_TO_TRACK` lookup for track assignment
- Save 2 LLM calls per batch (gating + track assignment)

### B. Phase 4.1 (Topic Aggregation/Consolidation) overlaps with rebuild_centroid's merge logic

The daemon's incremental clustering creates events, then Phase 4.1 uses LLM to merge duplicates. But `rebuild_centroid.py` has mechanical merge + LLM candidate-pair merge built-in. If we wire `rebuild_centroid.incremental_update()` into the daemon (which is planned), Phase 4.1 becomes unnecessary.

**Proposal:** Replace `incremental_clustering.py` + `consolidate_topics.py` (Phase 4.1) with `rebuild_centroid.incremental_update()` -- one step instead of two.

### C. Phase 4.3 (Cross-Bucket Merge) partially overlaps with candidate-pair LLM merge

The `merge_related_events.py` does cross-bucket merging via LLM. The experimental `_llm_merge_clusters()` in rebuild_centroid.py does the same thing pre-DB. Once rebuild_centroid is wired as the clustering engine, Phase 4.3 may be redundant for the current month. Keep it only for retroactive fixes on frozen months.

### Summary of collapse

| Current | Proposed |
|---------|----------|
| Phase 3.1 + 3.2 + 3.3 (3 steps) | Phase 3.1 + 3.2 + mechanical gating (2 steps, 0 extra LLM) |
| Phase 4 + 4.1 + 4.3 (3 steps) | rebuild_centroid.incremental_update() (1 step) |
| **6 daemon sub-phases** | **3 daemon sub-phases** |

---

## 2. OUTDATED CODE

| File | Issue |
|------|-------|
| `pipeline/phase_4/incremental_clustering.py` | Replaced by `rebuild_centroid.py` (experimental). Still wired as daemon Phase 4 |
| `pipeline/phase_4/consolidate_topics.py` | Phase 4.1 -- redundant once rebuild_centroid handles merge |
| `core/signal_aliases.py` | **Already deleted** (2026-03-27 session) |
| `pipeline/phase_4/normalize_signals.py` | **Already deleted** (2026-03-27 session) |
| `scripts/apply_signal_aliases.py` | **Already deleted** (2026-03-27 session) |
| Phase 3.3 gating LLM logic | Redundant with sector-based NON_STRATEGIC filtering |
| Phase 3.3 track LLM logic | Redundant with SECTOR_TO_TRACK mechanical mapping |
| `core/config.py` `COSINE_THRESHOLD_*` values in .env | No longer used (cosine similarity removed) |
| `core/config.py` Phase 5/6 settings | Phases 5 & 6 removed from daemon (D-030) |
| `HIGH_FREQ_PERSONS`/`HIGH_FREQ_ORGS` in config | Used by incremental_clustering only, replaced by dynamic ubiquitous labels |

---

## 3. HARDCODED VALUES & VOCABULARIES

### Critical (should be in config or DB)

| What | Where | Should be |
|------|-------|-----------|
| `SECTOR_TO_TRACK` mapping | `rebuild_centroid.py:66` | `config.py` or `track_configs` table |
| `FILTERED_SUBJECTS` | `rebuild_centroid.py:82` | `config.py` |
| `GATE_WHITELIST` (46 tuples) | `config.py:318` | Eliminate entirely (replaced by sector filter) |
| `CENTROID_TO_PREFIX` (38 entries) | `match_narratives.py:34` | DB table or `centroids_v3.profile_json` |
| `PREFIX_TO_CENTROID` (27 entries) | `match_narratives.py` | Derive from above |
| `KEYWORD_TO_CENTROID` (35 entries) | `match_narratives.py` | Derive from taxonomy_v3 |
| Clustering thresholds (12+) | Scattered across 5 files | `config.py` with env overrides |
| `ACTION_CLASS_SEVERITY` scores | `config.py:262` | Acceptable in config (stable ontology) |

### Vocabularies that should be DB-driven

- Sector/Subject taxonomy: already in prompt, but validated against hardcoded sets in `extract_labels.py:276`. Should come from a config table.
- Narrative matching mappings: should derive from `centroids_v3` and `taxonomy_v3`.

### All hardcoded thresholds across pipeline

| File | Constant | Value | Purpose |
|------|----------|-------|---------|
| rebuild_centroid.py | UBIQUITOUS_RATIO | 0.10 | Labels in >10% of titles excluded |
| rebuild_centroid.py | SOCIETY_MIN_CLUSTER | 10 | Min cluster size for geo_society |
| rebuild_centroid.py | LOUVAIN_SPLIT_THRESHOLD | 50 | Min titles to trigger Louvain |
| rebuild_centroid.py | TARGET_SPLIT_MIN | 3 | Min target group size |
| rebuild_centroid.py | ANCHOR_MIN_COUNT | 8 | Signal must appear in >=8 titles |
| rebuild_centroid.py | ANCHOR_MAX_RATIO | 0.40 | Signal must appear in <40% of group |
| rebuild_centroid.py | TEMPORAL_WINDOW_DAYS | 5 | Hard split threshold |
| rebuild_centroid.py | TEMPORAL_GAP_DAYS | 3 | Natural gap threshold |
| incremental_clustering.py | ANCHOR_LOCK_THRESHOLD | 5 | Titles before anchor lock |
| incremental_clustering.py | EMERGENCE_THRESHOLD | 3 | Min titles for topic emergence |
| incremental_clustering.py | JOIN_THRESHOLD | 0.25 | Similarity threshold for join |
| incremental_clustering.py | MAX_TOPIC_SIZE | 200 | Max titles per topic |
| consolidate_topics.py | CATCHALL_MAX_AGE_DAYS | 3 | Max age for catchall titles |
| consolidate_topics.py | DICE_THRESHOLD | 0.35 | Similarity for dedup candidates |
| merge_related_events.py | CTM_IMPORTANCE_THRESHOLD | 0.5 | Min importance for merge |
| merge_related_events.py | MIN_EVENTS_FOR_MERGE | 4 | Min events to attempt merge |
| match_narratives.py | THRESHOLD | 0.55 | Confidence threshold for narrative links |
| match_narratives.py | MIN_KEYWORD_LEN | 3 | Min keyword length |
| match_narratives_llm.py | MIN_KEYWORD_OVERLAP | 2 | Min keyword overlap for LLM match |
| chain_event_sagas.py | SAME_TRACK_THRESHOLD | 0.35 | Same-track event similarity |
| chain_event_sagas.py | CROSS_TRACK_THRESHOLD | 0.38 | Cross-track event similarity |
| detect_cross_centroid_siblings.py | SIBLING_THRESHOLD | 0.40 | Cross-centroid similarity |
| detect_cross_centroid_siblings.py | MIN_SOURCES | 20 | Min source count for siblings |
| generate_event_summaries_4_5a.py | MIN_SUMMARY_SOURCES | 5 | Min sources for summary |
| generate_event_summaries_4_5a.py | CORE_TITLE_COUNT | 10 | Max titles sent to LLM |
| generate_summaries_4_5.py | MAX_EVENTS | 20 | Max events per CTM digest |

---

## 4. PROCESSING TIMING ANALYSIS

### Current daemon cycle timing (worst case, everything fires)

**Slot 1 INGESTION (12h interval, 20m timeout):**
- Phase 1 RSS: ~5-10 min (213 feeds x 2-5s each)
- Phase 2 Match: ~1-2 min (mechanical, fast)
- Total: ~6-12 min

**Slot 2 CLASSIFICATION (15m interval, 20m timeout):**
- Phase 3.1: ~8-12 min (500 titles, 20 batches x 5 concurrent = ~25s/batch)
- Phase 3.2: ~30s (mechanical backfill)
- Phase 3.3: ~3-5 min (LLM gating + tracks)
- TOTAL: ~12-18 min -- EXCEEDS 15m interval sometimes

**Slot 3 CLUSTERING (30m interval, 15m timeout per sub):**
- Phase 4: ~2-5 min (incremental, few new events)
- Phase 4.1: ~3-5 min (25 CTMs x LLM)
- Phase 4.3: ~2-3 min (10 CTMs x LLM)
- Phase 4.4: ~1 min (sibling merge)
- Phase 4.2a-f: ~2-3 min (materialization queries)
- TOTAL: ~10-17 min

**Slot 4 ENRICHMENT (3h interval, 180m timeout):**
- Phase 4.5a: ~20-60 min (500 events x LLM)
- Phase 4.5b: ~10-30 min (200 CTMs x LLM)
- Phase 4.2g: ~5-10 min (narrative LLM discovery)
- Phase 4.2h: ~2-5 min (narrative review)
- TOTAL: ~37-105 min

### Bottleneck

Slot 2 can exceed its 15m interval. If 500+ titles queue up, Phase 3.1 alone takes 12+ minutes. Adding Phase 3.3 LLM calls pushes it over.

### After simplification (eliminate Phase 3.3 LLM + replace Phase 4/4.1)

```
Slot 2: Phase 3.1 (8-12 min) + Phase 3.2 (30s) + mechanical gating (seconds)
  TOTAL: ~9-13 min -- fits in 15m

Slot 3: rebuild_centroid.incremental_update() (3-5 min) + 4.2a-f (2-3 min)
  TOTAL: ~5-8 min -- easily fits in 30m
```

---

## 5. LLM API COST BREAKDOWN

**DeepSeek pricing:** Input $0.14/1M tokens, Output $0.28/1M tokens

### Current costs

| Phase | Per-run cost | Frequency | Daily cost |
|-------|-------------|-----------|------------|
| 3.1 Label extraction | ~$0.036 (500 titles) | Every 15m | ~$3.46 |
| 3.3 Gating + Tracks | ~$0.014 (500 titles) | Every 15m | ~$1.34 |
| 4.1 Consolidation | ~$0.10 (25 CTMs) | Every 30m | ~$4.80 |
| 4.3 Cross-bucket merge | ~$0.05 (10 CTMs) | Every 30m | ~$2.40 |
| 4.5a Event summaries | ~$0.50 (500 events) | Every 3h | ~$4.00 |
| 4.5b CTM digests | ~$0.20 (200 CTMs) | Every 3h | ~$1.60 |
| 4.2g Narrative LLM | ~$0.10 | Every 3h | ~$0.80 |
| **TOTAL** | | | **~$18.40/day** |

### After simplification (remove 3.3, 4.1, 4.3)

| Phase | Daily cost |
|-------|------------|
| 3.1 Label extraction | ~$3.46 |
| 4.5a Event summaries | ~$4.00 |
| 4.5b CTM digests | ~$1.60 |
| 4.2g Narrative LLM | ~$0.80 |
| **TOTAL** | **~$9.86/day (~47% reduction)** |

### Token usage per phase

| Phase | Per-batch tokens | Batch size | Notes |
|-------|-----------------|------------|-------|
| 3.1 Extract labels | ~5,000 (sys+user+response) | 25 titles | System prompt ~2,500 tokens (ontology) |
| 3.3 Gating | ~2,000 | 50 titles | Can be eliminated |
| 3.3 Tracks | ~2,000 | 50 titles | Can be eliminated |
| 4.5a Event title (small) | ~500-800 | 1 event | Titles-only, fast |
| 4.5a Event summary (large) | ~2,000-3,000 | 1 event | Core titles + context |
| 4.5b CTM digest | ~4,500-5,500 | 1 CTM | Up to 20 events input |
| 4.2g Narrative match | ~2,000 | 1 narrative | Pre-filtered candidates |

### DB load

Heaviest queries are materialized views (4.2a-f) -- UNNEST + aggregation + GROUP BY on large tables. These are bounded by month and run infrequently. Signal graph (4.2b) disables JIT for expensive query.

---

## 6. AUTOMATION READINESS ASSESSMENT

### Ready

- Daemon runs indefinitely with signal handlers (SIGINT/SIGTERM) for graceful shutdown
- All phase timeouts prevent hangs (`asyncio.wait_for`)
- Circuit breaker (`MAX_API_ERRORS=3`) prevents stuck titles
- DB state persistence survives restarts (`title_count_at_clustering`, `last_summary_at`, etc.)
- Connection pool (2-10 connections via `ThreadedConnectionPool`)
- Retry logic with exponential backoff (3 attempts, 2.0x)
- Conditional execution (skip phases when no work queued)

### Not ready

- `incremental_clustering.py` is still wired as Phase 4, not `rebuild_centroid.py`
- Enrichment interval mismatch: docstring says 6h, code says 3h (10800s)
- No health check endpoint or heartbeat
- No alert mechanism for stuck phases or queue buildup
- Node dev server memory leak (needs periodic restart, per memory note)
- Daily purge resets `api_error_count` globally -- could re-queue bad titles
- No processing debt monitoring (events without titles, CTMs without summaries)

### Action needed for production readiness

1. Wire `rebuild_centroid.incremental_update()` into daemon Slot 3 as Phase 4 replacement
2. Fix enrichment_interval docstring/code mismatch
3. Add processing debt metric to daemon stats
4. Consider adding a simple health check (e.g., last successful cycle timestamp to a file)

---

## 7. INGESTION FREQUENCY ANALYSIS (12h -> 6h -> 1h)

### Current at 12h

~5,000-8,000 new titles/day (based on 210K total over ~6 months). Ingestion runs 2x/day.

### At 6h

Same daily volume, fresher data. Ingestion runs 4x/day instead of 2x. Minimal cost impact (RSS fetching is free, Phase 2 is mechanical).

### At 1h

Same daily volume, near-real-time. 24 runs/day. ~200-300 titles/hour.

### Cost impact of more frequent ingestion

- Phase 1+2: **$0** (no LLM, only HTTP + DB)
- Phase 3.1 runs more often but processes same total volume: **no cost increase** (it processes whatever is in the queue)
- Downstream phases triggered by queue depth, not ingestion frequency

### Processing chain at 1h ingestion

```
Hour 0:00  Ingest ~300-400 titles
Hour 0:02  Phase 2 matches them (~seconds)
Hour 0:15  Phase 3.1 extracts labels (500/run, covers the batch)
Hour 0:30  Phase 4 clusters new titles into events
Hour 3:00  Phase 4.5a/b generates summaries for new events
```

### The tension

At 1h ingestion, titles arrive continuously but enrichment (4.5a/b) runs every 3h. New events sit without titles/summaries for up to 3 hours.

### Solution

Split enrichment into two tiers:
- **4.5a (event titles):** Run every 30m (cheap, fast, user-visible)
- **4.5b (CTM digests):** Keep at 3h (less urgent, more expensive)

---

## 8. VOLUME STATISTICS & PROCESSING DEBT

### Daily ingestion profile (March 2026)

- **Min:** 2,167 titles/day
- **Max:** 7,940 titles/day (Iran war spike)
- **Average:** 4,719 titles/day
- **Total March:** 122,708 titles across 26 days

### Processing status breakdown (March)

- `assigned`: 76,452 (62%)
- `out_of_scope`: 37,775 (31%)
- `blocked_stopword`: 6,704 (5%)
- `blocked_llm`: 1,777 (1.4%)
- **Strategic titles/day:** ~2,900 avg (62% of daily volume)

### Current processing debt

- Events without LLM-generated title: 3,681
- CTMs without summary: 320

### Processing capacity vs volume

| Phase | Capacity/cycle | Cycle interval | Daily capacity | Daily need | Headroom |
|-------|---------------|----------------|----------------|------------|----------|
| 3.1 Labels | 500 titles | 15m | 48,000 | ~2,900 | 16.5x |
| 4 Clustering | All new titles | 30m | unlimited | ~2,900 | OK |
| 4.5a Summaries | 500 events | 3h | 4,000 | ~100-200 new | 20x |
| 4.5b CTM digests | 200 CTMs | 3h | 1,600 | ~50-100 | 16x |

### Ensuring zero processing debt

At 1h ingestion with ~200-300 titles/hour:
- Phase 3.1 (500/run, every 15m) = 48K/day capacity >> 2,900 need
- Phase 4 (every 30m) handles all new titles each cycle
- Phase 4.5a (every 30m if adjusted) keeps events titled within 30m
- Phase 4.5b (every 3h) keeps CTM digests fresh within 3-6h

**Monitoring suggestion:** Add a "processing debt" metric to daemon stats: count of (events without titles) + (CTMs without summaries). Alert if growing across 3+ consecutive cycles.

---

## 9. TENSIONS & SOLUTIONS

### Tension 1: Incremental clustering quality vs speed

The current `incremental_clustering.py` is fast but produces lower quality (no sector gates, no temporal splits, needs Phase 4.1 LLM cleanup). `rebuild_centroid.incremental_update()` is higher quality but untested in daemon context.

**Solution:** Wire `incremental_update()` into daemon. It already handles the incremental case (only new titles). Test with one centroid first (France), monitor for 24h, then roll out.

### Tension 2: Volume spikes (Iran war: 8K/day) vs classification capacity

At 500 titles/run x 15m interval, Phase 3.1 handles 48K/day -- well above the 8K spike. But if ingestion moves to 1h, spikes could queue up faster than classification processes.

**Solution:** Make `v3_p31_max_titles` dynamic: if queue > 1000, increase batch to 1000 for that run. Already configurable via env var.

### Tension 3: CTM summary cooldown (24h) vs freshness

Users see stale summaries for up to 24 hours after new events are added. With 1h ingestion, this becomes more noticeable.

**Solution:** Reduce `v3_p45_cooldown_hours` to 6h. Cost impact minimal (CTM digests are cheap, ~$0.01 each).

### Tension 4: Enrichment interval (3h) creates visible gaps

New events appear on frontend without titles/summaries for up to 3 hours.

**Solution:** Split enrichment into two tiers:
- **4.5a (event titles):** Run every 30m (cheap, fast, user-visible)
- **4.5b (CTM digests):** Keep at 3h (less urgent, more expensive)

### Tension 5: DB load from materialized views

Phases 4.2a-f run heavy aggregation queries every 30 minutes. Under increased volume, these compete with frontend queries.

**Solution:** Move mv_* refresh to off-peak (run every 3h instead of every 30m). Signal graphs don't change meaningfully in 30 minutes.

---

## RECOMMENDED ACTION PLAN

### Phase 1 -- Immediate (this branch, before merge)

1. Wire `rebuild_centroid.incremental_update()` into daemon Slot 3
2. Eliminate Phase 3.3 LLM calls -- replace with mechanical sector filter + SECTOR_TO_TRACK
3. Move clustering thresholds to config.py

### Phase 2 -- Post-merge optimization

4. Remove Phase 4.1 (`consolidate_topics.py`) -- handled by rebuild_centroid
5. Split enrichment: 4.5a every 30m, 4.5b every 3h
6. Reduce CTM summary cooldown to 6h
7. Add processing debt monitoring to daemon stats
8. Move narrative matching mappings to DB (derive from centroids_v3)

### Phase 3 -- Ingestion upgrade

9. Change ingestion to 6h first, monitor for 1 week
10. Then move to 1h if stable
11. Make Phase 3.1 max_titles dynamic (scale with queue depth)

### Estimated impact

- **LLM costs:** ~47% reduction ($18 -> $10/day)
- **Pipeline complexity:** 6 daemon sub-phases -> 3
- **Processing latency:** Events get titles within 30m instead of 3h
- **Automation readiness:** Production-ready after items 1-3

---

## APPENDIX: DAEMON 4-SLOT ARCHITECTURE (CURRENT)

```
SLOT 1 INGESTION (12h):
  Phase 1: RSS Feed fetching (213 feeds)
  Phase 2: Centroid matching (taxonomy_v3 lookup)

SLOT 2 CLASSIFICATION (15m):
  Phase 3.1: Extract labels + signals (LLM, 500 titles/run, concurrency 5)
  Phase 3.2: Entity centroid backfill (mechanical)
  Phase 3.3: Intel gating + track assignment (LLM) [TO BE ELIMINATED]

SLOT 3 CLUSTERING (30m):
  Phase 4: Incremental event clustering [TO BE REPLACED by rebuild_centroid]
  Phase 4.1: Topic aggregation/dedup (LLM) [TO BE ELIMINATED]
  Phase 4.3: Cross-bucket event merge (LLM) [TO BE ELIMINATED for current month]
  Phase 4.4: Cross-centroid sibling merge
  Phase 4.2a: Materialize centroid signals
  Phase 4.2b: Materialize signal graph
  Phase 4.2c: Materialize publisher stats
  Phase 4.2d: Materialize event triples
  Phase 4.2e: Materialize baselines
  Phase 4.2f: Mechanical narrative matching

SLOT 4 ENRICHMENT (3h):
  Phase 4.5a: Event title/summary generation (LLM)
  Phase 4.5b: CTM digest generation (LLM)
  Phase 4.2g: LLM narrative discovery
  Phase 4.2h: LLM narrative review

DAILY PURGE (24h):
  Remove rejected titles > 24h old
  Reset api_error_count
```

## APPENDIX: FULL CONFIG INVENTORY (core/config.py)

### Database
- `db_host` (env: DB_HOST, default: localhost)
- `db_port` (env: DB_PORT, default: 5432)
- `db_name` (env: DB_NAME, default: sni_v2)
- `db_user` (env: DB_USER, default: postgres)
- `db_password` (env: DB_PASSWORD, default: "")

### LLM
- `llm_provider` (env: LLM_PROVIDER, default: deepseek)
- `llm_model` (env: LLM_MODEL, default: deepseek-chat)
- `deepseek_api_key` (env: DEEPSEEK_API_KEY)
- `deepseek_api_url` (env: DEEPSEEK_API_URL, default: https://api.deepseek.com/v1)
- `llm_temperature` (env: LLM_TEMPERATURE, default: 0.2)
- `llm_timeout_seconds` (env: LLM_TIMEOUT_SECONDS, default: 600)
- `llm_retry_attempts` (env: LLM_RETRY_ATTEMPTS, default: 3)
- `llm_retry_backoff` (env: LLM_RETRY_BACKOFF, default: 2.0)

### Phase 1
- `max_items_per_feed` (env: MAX_ITEMS_PER_FEED, default: None)
- `lookback_days` (env: LOOKBACK_DAYS, default: 3)
- `http_retries` (env: HTTP_RETRIES, default: 3)
- `http_timeout_sec` (env: HTTP_TIMEOUT_SEC, default: 30)

### Phase 2
- `v3_p2_batch_size` (env: V3_P2_BATCH_SIZE, default: 100)
- `v3_p2_timeout_seconds` (env: V3_P2_TIMEOUT_SECONDS, default: 180)
- `v3_p2_max_titles` (env: V3_P2_MAX_TITLES, default: None)

### Phase 3.1
- `v3_p31_temperature` (env: V3_P31_TEMPERATURE, default: 0.1)
- `v3_p31_max_tokens` (env: V3_P31_MAX_TOKENS, default: 4000)
- `v3_p31_batch_size` (env: V3_P31_BATCH_SIZE, default: 25)
- `v3_p31_concurrency` (env: V3_P31_CONCURRENCY, default: 5)
- `v3_p31_timeout_seconds` (env: V3_P31_TIMEOUT_SECONDS, default: 180)
- `v3_p31_max_titles` (env: V3_P31_MAX_TITLES, default: 500)

### Phase 3.3
- `v3_p33_temperature` (env: V3_P33_TEMPERATURE, default: 0.0)
- `v3_p33_max_tokens_gating` (env: V3_P33_MAX_TOKENS_GATING, default: 500)
- `v3_p33_max_tokens_tracks` (env: V3_P33_MAX_TOKENS_TRACKS, default: 500)
- `v3_p33_centroid_batch_size` (env: V3_P33_CENTROID_BATCH_SIZE, default: 50)
- `v3_p33_concurrency` (env: V3_P33_CONCURRENCY, default: 8)
- `v3_p33_timeout_seconds` (env: V3_P33_TIMEOUT_SECONDS, default: 300)
- `v3_p33_max_titles` (env: V3_P33_MAX_TITLES, default: 1000)

### Phase 4
- `v3_p4_batch_size` (env: V3_P4_BATCH_SIZE, default: 70)
- `v3_p4_min_titles` (env: V3_P4_MIN_TITLES, default: 30)
- `v3_p4_max_concurrent` (env: V3_P4_MAX_CONCURRENT, default: 5)
- `v3_p4_temperature` (env: V3_P4_TEMPERATURE, default: 0.5)
- `v3_p4_max_tokens` (env: V3_P4_MAX_TOKENS, default: 500)
- `v3_p4_timeout_seconds` (env: V3_P4_TIMEOUT_SECONDS, default: 180)

### Phase 4.5
- `v3_p45_cooldown_hours` (env: V3_P45_COOLDOWN_HOURS, default: 24)
- `v3_p45a_max_events` (env: V3_P45A_MAX_EVENTS, default: 500)
- `v3_p45a_interval` (env: V3_P45A_INTERVAL, default: 900)

### Daemon slot intervals (hardcoded in pipeline_daemon.py)
- `ingestion_interval`: 43,200s (12h)
- `classification_interval`: 900s (15m)
- `clustering_interval`: 1,800s (30m)
- `enrichment_interval`: 10,800s (3h, docstring says 6h -- MISMATCH)
- `social_interval`: 3,600s (1h)
- `purge_interval`: 86,400s (24h)

### Daemon slot timeouts (hardcoded in pipeline_daemon.py)
- `timeout_ingestion`: 1,200s (20m)
- `timeout_classification`: 1,200s (20m)
- `timeout_clustering`: 900s (15m per sub-phase)
- `timeout_enrichment`: 10,800s (180m)
- `timeout_social`: 300s (5m)
- `timeout_purge`: 300s (5m)

### Daemon batch sizes (hardcoded in pipeline_daemon.py)
- `classification_batch_size`: 500
- `aggregation_max_ctms`: 25
- `enrichment_max_events`: 500
- `enrichment_max_ctms`: 200
