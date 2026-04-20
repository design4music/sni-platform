# WorldBrief Pipeline Status

**Last updated**: 2026-04-20
**Live**: https://www.worldbrief.info
**Branch**: `main` (synced with origin)

Concise snapshot of what is running, what data exists, and where the
seams currently are. For the design reference see
[`PIPELINE_V4_ARCHITECTURE.md`](PIPELINE_V4_ARCHITECTURE.md).

---

## What is live

### Data coverage (on Render)

All four months of 2026 processed under the v3.0.1 taxonomy and the
day-centric clustering pipeline.

| Month | CTMs | Promoted events | DE titles | Daily briefs |
|---|---|---|---|---|
| Jan | 287 | 23,204 | 99.7% | 1,287 |
| Feb | 293 | 26,933 | 99.9% | 1,566 |
| Mar | 285 | 37,754 | 99.8% | 2,295 |
| Apr | 282 | 21,394+ (daemon live) | 99.9% | 1,231+ |

Jan–Mar rebuilt from scratch 2026-04-17/19 (labels wiped → relabel → wipe
downstream → rebuild → push). April runs continuously via the daemon.

### Daemon state (Render worker)

Running. Four-slot architecture from
[`PIPELINE_V4_ARCHITECTURE.md`](PIPELINE_V4_ARCHITECTURE.md):

- **INGESTION** (12h): RSS + centroid matching
- **LABELING** (15m): Phase 3.1 (LLM) + 3.2 backfill + 3.3 track assignment
- **CLUSTERING** (30m): 3.1 day-beat + 3.2 same-day merge + 3.3 promotion + 4.* materialization
- **ENRICHMENT** (3h): 5.1 event prose (LLM EN+DE) + 5.2 daily briefs (LLM) + 5.3/5.4 narrative matching (LLM)

Recent worker-side optimizations:

- `8c90ce8` Phase 3.3 rewritten as bulk SQL (~450× faster on backfill,
  ~30× under live load). Same function signature, drop-in.
- `44942a4` Fixed `SELECT DISTINCT ... ORDER BY` bug in the describe-
  promoted slot query.
- `485b747` Rerun script nulls inbound `merged_into` pointers before
  deleting a CTM's events (cross-CTM FK hazard).

### Frontend state (live)

Next.js on Render, auto-deploys from main:

- **Calendar hero** on CTM track pages (`/c/*/t/*/calendar`) — stacked
  activity chart, day popover, sector-themed tints (rank-assigned per
  track), dominant-theme chips, daily-brief prose per day.
- **Centroid page hero** (`/c/*`) — cross-track calendar, 2×2 enriched
  TrackCards with theme chips + summary + top-5 events, month nav,
  click-any-day popover with per-track breakdown.
- **Active Narratives** sidebar on centroid pages (replaces Top Signals).
  Foreign-framed narratives flagged with "from {Actor}".
- **Legacy fallback** for months without promoted data (Jan/Feb used to
  hit this — now all months are reprocessed, fallback is effectively
  dead code).

---

## Data architecture snapshot

```
Layer 0  titles_v3            raw headlines (v3.0.1 labels via title_labels)
Layer 1  events_v3            day-centric clusters (promoted ≤ top-20/day per CTM)
Layer 2  daily_briefs         per-day thematic briefs + sector/subject themes
Layer 3  narratives           260 curated strategic narratives
                              linked via event_strategic_narratives
```

Key columns/shapes established in recent work:

- `events_v3.is_promoted` — gates frontend visibility
- `events_v3.merged_into` — soft-merge within a CTM (rare)
- `daily_briefs.themes` — JSONB array of `{sector, subject, weight}`
- `title_labels.sector/subject` — ELO v3.0.1, drives theme aggregation
- `title_labels.industries[]` — economy sector enrichment (v3.0.1 add)

---

## Operational scripts (in `scripts/`)

Consolidated one-shot utilities built during Jan/Feb/Mar reprocess. All
accept `--month` and most accept sharding flags.

| Script | Purpose |
|---|---|
| `finish_month_labels.py` | Phase 3.1 relabel for a target month (v3.0.1). Supports `--shard-idx/--shard-count`. |
| `cluster_month.py` | Phase 3 (incremental clustering + same-day merge) per CTM. Sharded. |
| `promote_describe_month.py` | Phase 4.5a promote + LLM prose per CTM. Sharded. |
| `briefs_month.py` | Phase 4.5d daily briefs per CTM. Sharded. |
| `backfill_prose_by_month.py` | Older single-process variant for prose-only backfill (still works). |
| `reprocess_month_local.py` | Full-pipeline wrapper (rerun_ctm_full_pipeline per CTM). Now superseded by the per-phase scripts above for full reprocesses, but kept for targeted fixes. |
| `push_month_to_render.py` | One-transaction-per-CTM push to Render. Preflight checks + FK-safe delete/insert order. |

Still in `out/beats_reextraction/` (legacy but referenced):

- `pull_april_from_render.py` (one-shot, 2026-04-14)
- `push_april_to_render.py` — the April-specific original. The
  generic `scripts/push_month_to_render.py` imports its helpers, so
  both live side-by-side.
- `rerun_ctm_full_pipeline.py` — single-CTM driver, still called by
  `reprocess_month_local.py`.

---

## Known gaps / open tickets

1. **CTM digests stale** — `ctm.summary_text` is legacy v2 prose, not
   regenerated post-D-058. Ticket: restore + modernize period-level
   summaries for track cards. Needs design (period framing, refresh
   cadence, in-progress-month handling).
2. **Narrative matching hasn't run on Mar/Apr** — daemon Slot 3
   includes Phase 4.2f/g/h but 0 matches written for current months.
   Ticket: investigate matcher filters or data-shape mismatch.
3. **Daemon `last_run` not persisted** — restart fires every slot
   immediately. Nice-to-have, not urgent.
4. **Sidebar stance + deviation persist** — currently recomputed, same
   value across months. Ticket in strategic plan: persist monthly
   snapshot to a `centroid_monthly_stats` table.

---

## What to read next

- [`PIPELINE_V4_ARCHITECTURE.md`](PIPELINE_V4_ARCHITECTURE.md) — design reference (phase names, slot mapping)
- [`BEATS_DIRECTION.md`](BEATS_DIRECTION.md) — why day-centric events replaced families/clusters
- [`FRICTION_NODES_VISION.md`](FRICTION_NODES_VISION.md) — next lighthouse feature
- [`30_DecisionLog.yml`](30_DecisionLog.yml) — decisions D-001 through D-062
