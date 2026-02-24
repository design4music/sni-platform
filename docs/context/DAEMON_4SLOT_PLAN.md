# Daemon 4-Slot Consolidation Plan

## Goal
Prepare pipeline daemon for autonomous Render deployment: reduce API costs, simplify scheduling, increase resilience.

## Current State: 8 Scheduling Slots

| Slot | Phase | Interval | LLM? | Notes |
|------|-------|----------|------|-------|
| 1 | Phase 1: RSS Ingestion | 12h | No | Fetches RSS feeds |
| 2 | Phase 2: Centroid Matching | 12h | No | Assigns titles to centroids |
| 3 | Phase 3.1: Label Extraction | 10 min | Yes (DeepSeek) | 500 titles/run, 25/batch, concurrency=5 |
| 4 | Phase 3.3: Intel Gating + Track Assignment | 5 min | Yes (DeepSeek) | 500 titles/run |
| 5 | Phase 4: Event Clustering | 30 min | No | Groups titles into events |
| 6 | Phase 4.1: Topic Aggregation | 15 min | Yes (DeepSeek) | Merges events into topics, 25 CTMs/run |
| 7 | Phase 4.5a: Event Summaries | 15 min | Yes (DeepSeek) | **58% of token spend**, 500 events/run |
| 8 | Phase 4.5b: CTM Summaries | 1h | Yes (DeepSeek) | 50 CTMs/run |

Plus: Phase 3.2 (entity backfill, no LLM) runs inline after 3.1. Daily purge runs every 24h.

### Cost Breakdown
- **Phase 4.5a (event summaries): ~58% of total token spend** -- runs every 15 min, generates prose for each event
- Phase 3.1 (labels): ~20% -- runs every 10 min
- Phase 3.3 (gating): ~10% -- runs every 5 min
- Phase 4.1 (aggregation): ~7% -- runs every 15 min
- Phase 4.5b (CTM summaries): ~5% -- runs every 1h

## Proposed: 4 Scheduling Slots

### Slot 1: Ingestion (every 12h)
- Phase 1: RSS Ingestion
- Phase 2: Centroid Matching
- Runs sequentially (Phase 2 depends on Phase 1 output)
- No change from current behavior
- **No LLM cost**

### Slot 2: Classification (every 15 min)
- Phase 3.1: Label + Signal Extraction (500 titles)
- Phase 3.2: Entity Centroid Backfill (inline, no LLM)
- Phase 3.3: Intel Gating + Track Assignment (500 titles)
- Runs sequentially (3.3 depends on 3.1 labels)
- Currently 3.1=10min + 3.3=5min, consolidate to single 15-min slot
- **~30% of token spend**

### Slot 3: Clustering (every 30 min)
- Phase 4: Event Clustering (no LLM)
- Phase 4.1: Topic Aggregation (25 CTMs, LLM)
- Runs sequentially (4.1 depends on Phase 4 clusters)
- **~7% of token spend**

### Slot 4: Enrichment (every 6h)
- Phase 4.5a: Event Summaries (raise limit to 2000 events/run to clear backlog in one shot)
- Phase 4.5b: CTM Summaries (raise limit to 200 CTMs/run)
- Runs sequentially
- **~63% of token spend -- but only 4x/day instead of 96x/day**
- Net savings: ~90% reduction in enrichment cost

### Daily: Purge (every 24h, unchanged)
- Rejected title cleanup
- api_error_count reset (just added)

## New Intervals Summary

| Slot | Interval | Current Equivalent | Change |
|------|----------|-------------------|--------|
| Ingestion | 12h | 12h | Same |
| Classification | 15 min | 5-10 min | Slightly slower |
| Clustering | 30 min | 15-30 min | Same |
| Enrichment | 6h | 15 min - 1h | **Much slower (biggest cost saving)** |
| Purge | 24h | 24h | Same |

## Quality Trade-off

**Enrichment every 6h means:**
- Events won't get prose summaries for up to 6 hours after clustering
- CTM summary pages will show stale text for up to 6h
- Users see event titles and source counts immediately (from clustering), but no summary prose
- This is acceptable: most users visit for the overview, not real-time prose updates
- On-demand extraction (narratives) is unaffected -- separate API

**Classification every 15 min means:**
- New titles wait up to 15 min to get labels + track assignment (vs 5-10 min now)
- Negligible user impact

## Resilience Items (Must-Haves for Render)

### R1: HTTP 429 Backoff
- DeepSeek returns 429 when rate-limited
- Currently: increment api_error_count, move on (title gets blocked after 3)
- **Fix:** Detect 429 specifically, sleep with exponential backoff (5s, 15s, 45s), retry up to 3 times before incrementing error count
- Apply to: Phase 3.1 (`extract_batch`), Phase 3.3 (`gate_batch`), Phase 4.1, Phase 4.5a, Phase 4.5b
- Location: `core/llm_utils.py` -- add retry wrapper around DeepSeek calls

### R2: Phase Timeouts (already partially done)
- Current timeouts: ingestion=20min, classification=10min, enrichment=30min, purge=5min
- **Adjust for new slots:**
  - Classification: 20 min (3.1 + 3.2 + 3.3 sequential)
  - Clustering: 15 min (Phase 4 + 4.1)
  - Enrichment: 120 min (4.5a processing 2000 events + 4.5b processing 200 CTMs)
  - Already uses `asyncio.wait_for()` -- just update timeout values

### R3: Connection Pool Cleanup
- Current: `ThreadedConnectionPool(minconn=2, maxconn=10)`
- On Render: single web service, fewer concurrent connections needed
- **Fix:** Add connection health check at cycle start, close stale connections
- Add `try/finally` to ensure connections returned to pool even on phase crash
- Already partially done (each phase uses get_connection/return_connection pattern)

### R4: Graceful Shutdown (already done)
- Signal handlers for SIGTERM/SIGINT already in place
- Render sends SIGTERM on deploy -- daemon will finish current phase and exit

## Implementation Steps

### Step 1: Consolidate intervals and slot structure
- Replace 8 interval variables with 4 slot intervals
- Rewrite `run_cycle()` to have 4 blocks instead of 8
- Each block runs its phases sequentially within one `run_with_timeout()`
- Update `last_run` dict to 4 slot keys + purge

### Step 2: Raise enrichment batch sizes
- `v3_p45a_max_events`: 500 -> 2000
- Phase 4.5b `max_ctms`: 50 -> 200
- These run 4x/day so each run must handle the full daily accumulation

### Step 3: Add 429 backoff to LLM calls
- Add retry decorator to `core/llm_utils.py` DeepSeek call function
- Detect HTTP 429, extract Retry-After header if present
- Exponential backoff: 5s, 15s, 45s
- Only then increment api_error_count

### Step 4: Update timeouts
- Classification slot: 20 min
- Clustering slot: 15 min
- Enrichment slot: 120 min

### Step 5: Test locally for 3 days
- Run daemon with new configuration
- Monitor: queue depths, API costs, error rates, cycle times
- Verify enrichment catches up every 6h without growing backlog

### Step 6: Deploy to Render
- Set env vars for batch sizes and intervals
- Monitor first 24h closely

## Estimated Cost Savings

Current daily enrichment API spend (rough):
- 4.5a: 96 runs/day * ~$0.005/run = ~$0.48/day
- 4.5b: 24 runs/day * ~$0.003/run = ~$0.07/day

After consolidation:
- 4.5a: 4 runs/day * ~$0.02/run = ~$0.08/day (bigger batches cost slightly more per run)
- 4.5b: 4 runs/day * ~$0.01/run = ~$0.04/day

**Net savings: ~80% reduction in enrichment costs**

Total daily DeepSeek spend should drop from ~$1.10 to ~$0.30-0.40.
