# WorldBrief Pipeline v4.0 Architecture

**Date**: 2026-04-20 (last revised)
**Status**: Active on `main`, deployed to Render (worker + web).

## Phase naming (v4.0)

```
PHASE 1 — INGESTION
  1.1  RSS Feed Ingestion
  1.2  Centroid Matching

PHASE 2 — LABELING
  2.1  Signal & Label Extraction (LLM)
  2.2  Entity-Centroid Backfill
  2.3  Track Assignment (mechanical)

PHASE 3 — CLUSTERING
  3.1  Incremental Day-Beat Clustering
  3.2  Sibling Reconciliation (title-Dice, soft-delete, same-CTM + cross-CTM)
  3.3  Promotion (top-N ranking)

PHASE 4 — MATERIALIZATION
  4.1  Centroid Top Signals
  4.2  Signal Graph
  4.3  Publisher Stats
  4.4  Event Triples
  4.5  Centroid Baselines
  4.6  Narrative Matching (mechanical)

PHASE 5 — ENRICHMENT (LLM)
  5.1  Event Titles & Descriptions (EN+DE)
  5.2  Daily Briefs (EN+DE) + Themes
  5.3  Narrative Discovery (LLM, ideological)
  5.4  Narrative Review (LLM, operational)
  5.5  Centroid Summaries — rolling 30d + monthly snapshot (EN+DE)

MAINTENANCE
  Purge: daily cleanup of rejected titles
  Freeze: monthly close (canned small-CTM text, monthly centroid_summaries,
          publisher stance, tombstone purge, is_frozen=true)
```

## Slot mapping

| Slot | Interval | Phases | LLM? | Rationale |
|---|---|---|---|---|
| **INGESTION** | 12h (target: 6h) | 1.1 + 1.2 | No | RSS feeds refresh every few hours. 12h captures 2 full news cycles. |
| **LABELING** | 15m | 2.1 + 2.2 + 2.3 | 2.1 only | 2.1 is the LLM bottleneck (500 titles/batch). 15m drains the queue incrementally. 2.2 and 2.3 are instant. |
| **CLUSTERING** | 30m | 3.1 + 3.2 + 3.3 + 4.* | No | Runs only when `title_count > title_count_at_clustering`. All mechanical. |
| **ENRICHMENT** | 3h | 5.1 + 5.2 + 5.3 + 5.4 + 5.5 | Yes | LLM prose is expensive. Daily briefs only for closed days (T-1). 5.5 budget-capped per run with staleness gate. |
| **PURGE** | 24h | maintenance | No | Tombstone rejected titles older than 24h. |

## Phase details

### Phase 1.1 — RSS Feed Ingestion
- **Input**: Feed URLs from `feeds` table
- **Output**: `titles_v3` (status=pending)
- **Trigger**: Timer (12h)
- **Idempotent**: Yes (dedup by URL hash)
- **Cost**: Free
- **File**: `pipeline/phase_1/ingest_feeds.py`

### Phase 1.2 — Centroid Matching
- **Input**: Pending titles + `taxonomy_v3` stop words
- **Output**: `titles_v3.processing_status` (assigned/out_of_scope/blocked_stopword), `centroid_ids`
- **Trigger**: After 1.1
- **Idempotent**: Yes
- **Cost**: Free
- **File**: `pipeline/phase_2/match_centroids.py`

### Phase 2.1 — Signal & Label Extraction
- **Input**: Assigned titles without `title_labels`
- **Output**: `title_labels` (sector, subject, actor, action_class, target, signals, industries, entity_countries, importance)
- **Trigger**: Timer (15m), 500 titles/batch, concurrency=5
- **Idempotent**: Yes (skip if label exists)
- **Cost**: **DeepSeek API** (~25 titles per call)
- **File**: `pipeline/phase_3_1/extract_labels.py`
- **Note**: Uses ELO v3.0.1 ontology (`core/ontology.py`)

### Phase 2.2 — Entity-Centroid Backfill
- **Input**: New `entity_countries` in labels
- **Output**: Centroid membership updates
- **Trigger**: After 2.1
- **Idempotent**: Yes
- **Cost**: Free
- **File**: `pipeline/phase_3_2/backfill_entity_centroids.py`

### Phase 2.3 — Track Assignment
- **Input**: Labeled titles without `title_assignments`
- **Output**: `title_assignments` + `ctm.title_count` update
- **Trigger**: After 2.1, 500 titles/batch
- **Idempotent**: Yes (ON CONFLICT)
- **Cost**: Free
- **File**: `pipeline/phase_3_3/assign_tracks_mechanical.py`
- **Note**: `SECTOR_TO_TRACK` mapping. NON_STRATEGIC titles skipped.

### Phase 3.1 — Incremental Day-Beat Clustering
- **Input**: Unlinked titles (in `title_assignments` but not in `event_v3_titles`)
- **Output**: New `events_v3` rows or appended `event_v3_titles`
- **Trigger**: `ctm.title_count > title_count_at_clustering`
- **Idempotent**: Yes (skip if no unlinked titles)
- **Cost**: Free
- **Algorithm**: D-056 day-beat clustering on NEW titles only, match to existing events via entity overlap OR title-word Dice >= 0.4. Existing events never deleted.
- **File**: `pipeline/phase_4/incremental_clustering.py` → `process_ctm_for_daemon()`

### Phase 3.2 — Sibling Reconciliation (soft-delete)
- **Input**: Unfrozen-month events, regardless of CTM or promotion state
- **Output**: `merged_into` + `absorbed_centroids` on dupes; title links moved to canonical; `source_batch_count` recomputed on anchor
- **Trigger**: After 3.1, every unfrozen month
- **Idempotent**: Yes (soft-delete gates the next run's fetch)
- **Cost**: Free
- **Algorithm**: Same-date title-word Dice >= 0.55 (D-069). Greedy group assembly; anchor chosen by (source_count, is_promoted, id). Covers both same-CTM and cross-CTM dupes in one pass.
- **File**: `pipeline/phase_4/reconcile_siblings_bulk.py` (bulk SQL) / `reconcile_siblings_v4.py` (detection)
- **Supersedes**: legacy `merge_same_day_events.py` hard-delete merge, which skipped CTMs with promoted events and could not safely soft-delete across the promotion boundary.

### Phase 3.3 — Promotion
- **Input**: All events per CTM
- **Output**: `events_v3.is_promoted = true` on top-N per day
- **Trigger**: After 3.2
- **Idempotent**: Yes (one-way — once promoted, never demoted)
- **Cost**: Free
- **Config**: `TOP_CLUSTERS_PER_DAY` (default 20)
- **File**: `pipeline/phase_4/promote_and_describe_4_5a.py` → `promote_ctm()`

### Phase 4.1–4.6 — Materialization
- **Input**: Events, labels, narratives
- **Output**: `mv_centroid_signals`, `mv_signal_graph`, publisher stats, event triples, centroid baselines, `event_strategic_narratives`
- **Trigger**: After Phase 3
- **Idempotent**: Yes (full rebuild each cycle)
- **Cost**: Free
- **Files**: `pipeline/phase_4/materialize_*.py`, `pipeline/phase_4/match_narratives.py`

### Phase 5.1 — Event Titles & Descriptions
- **Input**: Promoted events where `title_de IS NULL` (never LLM'd)
- **Output**: `events_v3.title`, `title_de`, `summary`, `summary_de`
- **Trigger**: Timer (3h)
- **Idempotent**: Yes (skip if `title_de` exists)
- **Cost**: **DeepSeek API** (1 call per event for >= 5 src; batch DE translation for small clusters)
- **File**: `pipeline/phase_4/promote_and_describe_4_5a.py` → `describe_promoted_events()`

### Phase 5.2 — Daily Briefs
- **Input**: Promoted events for closed days (date < today - 1)
- **Output**: `daily_briefs` (brief_en, brief_de, themes)
- **Trigger**: Timer (3h), day-closure gate
- **Idempotent**: Yes (skip if brief exists for date)
- **Cost**: **DeepSeek API** (1 call per qualifying day)
- **Themes**: Mechanical aggregation from `title_labels` sector/subject (zero LLM cost)
- **File**: `pipeline/phase_4/generate_daily_brief_4_5d.py`

### Phase 5.3 — Narrative Discovery
- **Input**: New events without narrative links
- **Output**: `event_strategic_narratives` (ideological tier)
- **Trigger**: Timer (3h)
- **Cost**: **DeepSeek API**
- **File**: `pipeline/phase_4/match_narratives_llm.py`

### Phase 5.4 — Narrative Review
- **Input**: Existing operational narrative matches
- **Output**: Pruned false positives
- **Trigger**: Timer (3h)
- **Cost**: **DeepSeek API**
- **File**: `pipeline/phase_4/review_narratives_llm.py`

### Phase 5.5 — Centroid Summaries (rolling 30d)
- **Input**: Promoted events for last 30 days per centroid + ambient label context (top persons/orgs/countries/places)
- **Output**: `centroid_summaries` row with `period_kind='rolling_30d'` — tier-0 overall paragraph + per-track JSONB (`{state_en, state_de, supporting_events}`), bilingual.
- **Trigger**: Timer (3h), refreshes rows with `generated_at` older than `centroid_summary_stale_hours` (default 24h) or missing
- **Budget**: `centroid_summary_max_per_run` (default 100 centroids)
- **Tier gates**: 1 (FULL: >=20 events + >=3 strong tracks), 2 (LIGHT: >=5 events), 3 (CANNED: no LLM)
- **Cost**: **DeepSeek API** (1 call per tier 1/2 centroid, bilingual single-shot)
- **File**: `pipeline/phase_5/generate_centroid_summary.py` (daemon: `run_centroid_rolling_summaries`)
- **Monthly snapshot**: the same module is invoked by `pipeline/freeze/freeze_month.py` with `period_kind='monthly'` to produce immutable month-end rows.

## Dependencies

```
1.1 RSS → 1.2 Matching → titles_v3 (assigned)
                              ↓
2.1 Labeling → 2.2 Backfill → 2.3 Track Assignment → title_assignments
                                                          ↓
3.1 Clustering → 3.2 Merge → 3.3 Promote → events_v3 (is_promoted)
                                                ↓              ↓
4.* Materialization                    5.1 Event Prose    5.2 Daily Briefs
                                       5.3/5.4 Narratives 5.5 Centroid Summaries
```

## Code-to-phase mapping

| v4.0 Phase | Current directory/file | v3 legacy name |
|---|---|---|
| 1.1 | `pipeline/phase_1/ingest_feeds.py` | Phase 1 |
| 1.2 | `pipeline/phase_2/match_centroids.py` | Phase 2 |
| 2.1 | `pipeline/phase_3_1/extract_labels.py` | Phase 3.1 |
| 2.2 | `pipeline/phase_3_2/backfill_entity_centroids.py` | Phase 3.2 |
| 2.3 | `pipeline/phase_3_3/assign_tracks_mechanical.py` | Phase 3.3 |
| 3.1 | `pipeline/phase_4/incremental_clustering.py` | Phase 4 |
| 3.2 | `pipeline/phase_4/reconcile_siblings_bulk.py` + `reconcile_siblings_v4.py` | Phase 4.0b (deprecated) |
| 3.3 | `pipeline/phase_4/promote_and_describe_4_5a.py` → `promote_ctm()` | Phase 4.5a-promote |
| 4.1-4.6 | `pipeline/phase_4/materialize_*.py`, `match_narratives.py` | Phase 4.2a-f |
| 5.1 | `pipeline/phase_4/promote_and_describe_4_5a.py` → `describe_promoted_events()` | Phase 4.5a-describe |
| 5.2 | `pipeline/phase_4/generate_daily_brief_4_5d.py` | Phase 4.5-day |
| 5.3 | `pipeline/phase_4/match_narratives_llm.py` | Phase 4.2g |
| 5.4 | `pipeline/phase_4/review_narratives_llm.py` | Phase 4.2h |
| 5.5 | `pipeline/phase_5/generate_centroid_summary.py` | (new) |

## Interval optimization notes

| Current | Issue | Recommendation |
|---|---|---|
| Ingestion 12h | Misses mid-day content until next cycle | Move to **6h** |
| Labeling 15m, 500/batch | Post-ingestion surge (~4000 titles) takes 2h to drain | Increase batch to **1000** or interval to **10m** |
| Clustering 30m | Only fires when new titles exist. Efficient. | **Keep** |
| Enrichment 3h | Acceptable — calendar shows mechanical titles immediately from Phase 3.3 | **Keep** |

## Deprecated phases (removed from daemon)

| Phase | Reason | Decision |
|---|---|---|
| Family assembly (old 4.1) | Families deprecated in frontend (D-059) | Removed |
| Old event summaries (old 4.5a) | Replaced by new 5.1 | Removed (D-058) |
| CTM digests (old 4.5b) | Moved to freeze-only | Removed (D-058) |
| Mechanical titles (old 4.1a) | Handled by clustering fallback | Removed (D-056) |
| Dice merge (old 4.1b) | Replaced by 3.2 same-day merge | Removed (D-056) |
| Same-day hard-delete merge (`merge_same_day_events.py`) | Skipped CTMs with promoted events; couldn't soft-delete across promotion. Replaced by sibling reconciliation. | Removed (D-070) |
| Cross-bucket LLM merge (old 4.3) | Replaced by 3.2 | Removed (D-053) |
| Sibling merge (old 4.4) | Not needed with current design | Removed (D-053) |
| Freeze centroid monthly summary (legacy) | `centroid_monthly_summaries` table; superseded by `centroid_summaries` (5.5 monthly snapshot) | Removed 2026-04-20 |
