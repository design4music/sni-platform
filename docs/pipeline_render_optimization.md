# Pipeline Optimization for Render Deployment

**Date:** 2026-02-24
**Goal:** Reduce API costs, increase resilience for autonomous operation on Render

---

## Current Architecture

### Schedule (8 distinct intervals)

| Phase | Interval | Type | What |
|-------|----------|------|------|
| 1 | 12h | Non-LLM | RSS feed ingestion |
| 2 | 12h | Non-LLM | Centroid keyword matching |
| 3.1 | 10 min | **LLM** | Label + signal extraction (25 titles/batch, 500/run) |
| 3.2 | after 3.1 | Non-LLM | Entity centroid backfill |
| 3.3 | 5 min | **LLM** | Intel gating + track assignment (50 titles/batch) |
| 4 | 30 min | Non-LLM | Event clustering |
| 4.1 | 15 min | **LLM** | Topic aggregation / merge (25 CTMs/run) |
| 4.5a | 15 min | **LLM** | Event summaries (500 events/run) |
| 4.5b | 1h | **LLM** | CTM narrative summaries (50 CTMs/run) |
| Purge | 24h | Non-LLM | Remove rejected titles |

### Token Spend Breakdown (estimated daily, ~5000 titles/day)

| Phase | Tokens/call | Calls/day | Daily tokens | % of spend |
|-------|------------|-----------|-------------|------------|
| 3.1 | ~3,500 | ~120 (20 batches x 6 runs) | ~420k | 16% |
| 3.3 | ~3,000 | ~60 (10 batches x 6 runs) | ~180k | 7% |
| 4.1 | ~2,000 | ~20 CTMs | ~40k | 2% |
| **4.5a** | **~1,500** | **~500 events** (backlog + growth) | **~1.5M** | **58%** |
| 4.5b | ~2,500 | ~20 CTMs | ~50k | 2% |

**Phase 4.5a dominates** because:
- Runs every 15 min with up to 500 events per cycle
- Events get re-summarized when source count grows 50%+
- After each Phase 4 clustering run, new events get mechanical labels and queue for prose
- Phase 4.1 consolidation deletes/merges events, creating new ones that also queue
- In practice ~500-1000 events/day get (re)summarized

**Total estimated: ~2.5M tokens/day (~$0.60-1.50/day on DeepSeek)**

---

## Complete Threshold Reference

### All LLM Prose Generation Thresholds

| Phase | Threshold | Current Value | Env Var | What It Controls |
|-------|-----------|---------------|---------|-----------------|
| 3.1 | Batch size | 25 titles/call | `V3_P31_BATCH_SIZE` | Titles sent to LLM per label extraction call |
| 3.1 | Max titles/run | 500 | `V3_P31_MAX_TITLES` | Cap on titles processed per classification cycle |
| 3.1 | Concurrency | 5 | `V3_P31_CONCURRENCY` | Parallel LLM calls |
| 3.1 | Temperature | 0.1 | `V3_P31_TEMPERATURE` | Very low -- labels should be deterministic |
| 3.1 | Max tokens | 4000 | `V3_P31_MAX_TOKENS` | Output limit per batch |
| 3.1 | Timeout | 180s | `V3_P31_TIMEOUT_SECONDS` | HTTP timeout |
| 3.3 | Centroid batch | 50 titles | `V3_P33_CENTROID_BATCH_SIZE` | Titles per centroid batch for gating + tracks |
| 3.3 | Max titles/run | 1000 | `V3_P33_MAX_TITLES` | Cap on titles processed per gating cycle |
| 3.3 | Concurrency | 8 | `V3_P33_CONCURRENCY` | Parallel gating calls |
| 3.3 | Temperature | 0.0 (config) / 0.2 (gating hardcoded) | `V3_P33_TEMPERATURE` | Near-zero for classification |
| 3.3 | Gate whitelist | 38 action-domain combos | Hardcoded | Skip LLM gating entirely for low-risk combos |
| 4 | Min titles for clustering | 30 | `V3_P4_MIN_TITLES` | CTM needs >= 30 titles before clustering runs |
| 4 | Emergence threshold | 3 titles | Hardcoded | Titles needed for a topic to "emerge" as an event |
| 4 | Join threshold | 0.2 similarity | Hardcoded | Min score for a title to join existing topic |
| 4 | Anchor lock | 5 titles | Hardcoded | After 5 titles, topic anchor signals are frozen |
| 4.1 | Dynamic topic targets | 2-15 domestic, 2-7 bilateral | Hardcoded | Story count targets scaled by bucket size |
| 4.1 | Over-merge guard | 1 story for >= 10 topics | Hardcoded | Prevents aggressive LLM merging |
| 4.1 | Skip condition A | <= 1 event AND catchall < 5 | Hardcoded | Too little content to consolidate |
| 4.1 | Skip condition B | All have topic_core AND catchall < 10 | Hardcoded | Already consolidated |
| 4.1 | Temperature | 0.2 | `LLM_TEMPERATURE` | Low temp for structured merging |
| 4.1 | Max tokens | 1000 | Hardcoded | Consolidation output limit |
| **4.5a** | **MIN_SUMMARY_SOURCES** | **5** | **Hardcoded** | **Below this: title-only mode (no LLM prose)** |
| **4.5a** | **Re-summary growth** | **1.5x AND >= 5 new** | **Hardcoded** | **source_batch_count > summary_source_count * 1.5 AND diff >= 5** |
| 4.5a | Max events/run | 500 | `V3_P45A_MAX_EVENTS` | Events processed per enrichment cycle |
| 4.5a | Adaptive max_tokens | 150/300/500/800 | Hardcoded | Scales with source count: <5/5-19/20-99/100+ |
| 4.5a | Temperature | 0.4 | Hardcoded | Moderate creativity for prose |
| 4.5a | LLM timeout | 90s | Hardcoded | Per-call timeout |
| 4.5a | Max headlines to LLM | 200 | Hardcoded | Title sample cap sent to summarizer |
| **4.5b** | **CTM min titles** | **30** | **`V3_P4_MIN_TITLES`** | **CTM needs >= 30 titles for narrative summary** |
| **4.5b** | **Cooldown** | **24 hours** | **`V3_P45_COOLDOWN_HOURS`** | **Min gap between CTM re-summaries** |
| **4.5b** | **Re-summary trigger** | **event_count > event_count_at_summary** | **Hardcoded** | **New events must exist (any count)** |
| 4.5b | Concurrency | 5 | `V3_P4_MAX_CONCURRENT` | Parallel CTM summaries |
| 4.5b | Temperature | 0.5 | `V3_P4_TEMPERATURE` | Higher creativity for narratives |
| 4.5b | Max tokens | 500 | `V3_P4_MAX_TOKENS` | 150-250 word target |

### General LLM Configuration

| Config | Value | Env Var |
|--------|-------|---------|
| Retry attempts | 3 | `LLM_RETRY_ATTEMPTS` |
| Retry backoff | 2.0x exponential | `LLM_RETRY_BACKOFF` |
| Global timeout | 600s | `LLM_TIMEOUT_SECONDS` |
| Circuit breaker | 3 consecutive errors | Hardcoded `MAX_API_ERRORS` |

---

## Summary Overwrite Analysis

Understanding when summaries get generated, overwritten, or wasted is key to cost optimization.

### Event Summaries (Phase 4.5a) -- Overwrite Scenarios

| Scenario | What Happens | Summary Action | Wasteful? |
|----------|-------------|----------------|-----------|
| **New event created (Phase 4)** | Clustering creates event with mechanical label ("Topic: signal1, signal2") | Queued for prose generation | No -- first write |
| **New event from consolidation (Phase 4.1)** | LLM merges topics, creates new event with `topic_core` label | Queued for prose generation | No -- first write |
| **Event grows modestly** | source_batch_count increases but < 1.5x OR diff < 5 | No re-summary | Correct skip |
| **Event grows significantly** | source_batch_count > summary_source_count * 1.5 AND diff >= 5 | Re-summarized with new titles | Usually wasteful -- summary rarely changes meaningfully |
| **Event absorbed by merge** | Phase 4.1 merges event into larger one, deletes original | Original summary lost; target may grow enough to trigger re-summary | Wasted if original was recently summarized |
| **Clustering creates then consolidation restructures** | Phase 4 creates events, then Phase 4.1 merges/splits them | Events summarized by 4.5a may get deleted minutes later by 4.1 | **Major waste** under current timing |

### CTM Summaries (Phase 4.5b) -- Overwrite Scenarios

| Scenario | What Happens | Summary Action | Wasteful? |
|----------|-------------|----------------|-----------|
| **First summary** | CTM has >= 30 titles + non-catchall enriched events | Generate narrative | No -- first write |
| **New events appear, cooldown not passed** | event_count > event_count_at_summary but < 24h since last | Skipped | Correct skip |
| **New events appear, cooldown passed** | event_count > event_count_at_summary AND >= 24h gap | Re-generate narrative | Usually justified -- new events mean new story developments |
| **No new events** | Event count unchanged | Skipped | Correct skip |

### The Clustering -> Consolidation -> Summary Waste Problem

Under the **current** architecture (separate intervals), this happens regularly:
1. Phase 4 runs (every 30m): creates 20 new events with mechanical labels
2. Phase 4.5a runs (every 15m): summarizes those 20 events (LLM cost)
3. Phase 4.1 runs (every 15m): merges 8 of those events, deletes 4
4. Phase 4.5a runs again: re-summarizes the merged events

**Under the proposed architecture** (enrichment chain: 4 -> 4.1 -> 4.5a -> 4.5b sequential):
1. Phase 4 clusters, Phase 4.1 consolidates, THEN 4.5a summarizes
2. Events are only summarized once per cycle, after all structural changes are done
3. **Eliminates ~60-70% of wasteful re-summarization**

---

## Capacity Analysis: Can 3k Titles Be Fully Processed in 12h?

### Classification Pipeline (Slot 2: every 30 min)

| Phase | Per-Run Capacity | Runs in 12h | 12h Capacity |
|-------|-----------------|-------------|-------------|
| 3.1: Label extraction | 500 titles | 24 runs | **12,000 titles** |
| 3.2: Centroid backfill | Unlimited (non-LLM) | 24 runs | N/A |
| 3.3: Gating + tracks | 1000 titles | 24 runs | **24,000 titles** |

**Verdict: 3k titles easily classified in 12h.** Phase 3.1 is the bottleneck at 500/run, but 24 runs gives 12,000 capacity (4x headroom). In practice, ~3,000 titles would be fully classified in ~3 hours (6 runs of 500).

### Enrichment Pipeline (Slot 3: every 6h = 2 runs in 12h)

| Phase | Per-Run Capacity | Runs in 12h | 12h Throughput |
|-------|-----------------|-------------|---------------|
| 4: Clustering | All pending CTMs (batch 50) | 2 | All CTMs clustered 2x |
| 4.1: Consolidation | All pending CTMs | 2 | All CTMs consolidated 2x |
| 4.5a: Event summaries | 500 events (configurable) | 2 | **1,000 events** |
| 4.5b: CTM summaries | 50 CTMs | 2 | **100 CTMs** |

**How many events do 3k titles create?**
- ~85 centroids, avg ~35 titles/centroid (3000/85)
- Only CTMs with >= 30 titles trigger clustering
- Typical: ~20-30 active CTMs get clustered per cycle
- Each CTM produces ~5-15 events
- Estimate: **150-400 new events per ingestion cycle**

**Verdict: 500 events/run is sufficient.** Even with 2 runs/12h, we can process 1,000 events. With ~300 new events per cycle plus some re-summarization, 500/run provides comfortable headroom.

### Can We Guarantee Full Processing Before Next Ingest?

| Step | Duration Estimate | When |
|------|------------------|------|
| Ingest 3k titles (Phase 1+2) | ~10 min | T+0h |
| Classify all 3k (Phase 3.1/3.2/3.3) | ~3h (6 runs at 30m intervals) | T+0.5h to T+3h |
| First enrichment chain | ~15 min (cluster + consolidate + summarize) | T+6h |
| Second enrichment chain | ~15 min | T+12h |

**Yes, 3k titles are fully processed well within 12h.** Classification completes in ~3h. The first enrichment chain at T+6h handles all clustering, consolidation, and summarization in one pass. The second enrichment at T+12h catches any growth-triggered re-summaries.

---

## Proposed Architecture: 4 Scheduling Slots (CONFIRMED)

### Slot 1: Ingestion (every 12h)
- Phase 1: RSS ingestion
- Phase 2: Centroid matching
- *Unchanged*

### Slot 2: Classification (every 30 min) [was 15 min]
- Phase 3.1: Label + signal extraction
- Phase 3.2: Entity centroid backfill
- Phase 3.3: Intel gating + track assignment
- *Run sequentially: 3.1 -> 3.2 -> 3.3 (natural dependency order)*
- *30 min interval provides 12,000+ title capacity in 12h*

### Slot 3: Enrichment Chain (every 6h) [CONFIRMED]
- Phase 4: Event clustering
- Phase 4.1: Topic aggregation
- Phase 4.5a: Event summaries
- Phase 4.5b: CTM summaries
- *Run sequentially: cluster -> aggregate -> summarize events -> summarize CTMs*
- *Single chain, 4x/day -- eliminates clustering -> summary waste*

### Slot 4: Maintenance (every 24h)
- Daily purge
- Full statistics print (moved from every cycle to every 6h with enrichment)

### Impact

| Metric | Current | Proposed | Change |
|--------|---------|----------|--------|
| Scheduling intervals | 8 | 4 | -50% complexity |
| Phase 4.5a runs/day | ~96 (every 15m) | 4 (every 6h) | -96% |
| Phase 4.1 runs/day | ~96 | 4 | -96% |
| Re-summarization churn | High (cluster -> summarize -> re-cluster -> re-summarize) | Near zero (cluster + summarize in same chain) | **Major reduction** |
| Classification runs | ~144+288 | 48 | Modest reduction |
| Statistics queries | Every cycle (~100/day) | 4/day (with enrichment) | -96% DB load |
| Estimated daily tokens | ~2.5M | ~0.8-1.0M | **~60% reduction** |

### The 6h Trade-off (ACCEPTED)

**What we accept:** Events won't get prose summaries for up to 6 hours after titles are ingested. Users see mechanical labels ("Topic: signal1, signal2") during this window.

**Why this is fine:**
- No traffic currently (demo only)
- Strategic resource, not a hot news feed -- updates don't need to be real-time
- Titles still classify continuously (every 30m), so label/track assignments are current
- Prose summaries are the expensive part; mechanical labels are functional

---

## Threshold Lifting Recommendations

### Phase 4.5a: Event Summaries (58% of spend -- biggest lever)

| Threshold | Current | Recommended | Rationale |
|-----------|---------|-------------|-----------|
| `MIN_SUMMARY_SOURCES` | 5 | **8** | Events with 5-7 sources have thin summaries anyway. At 8+, prose adds real value. Saves ~30% of summary calls. |
| Re-summary growth | 1.5x AND >= 5 | **2.0x AND >= 10** | An event going 5->10 doesn't change the story meaningfully. Require doubling + 10 new sources. Saves ~50% of re-summaries. |
| `V3_P45A_MAX_EVENTS` | 500 | **200** | With 6h enrichment, no rush. 200 events/chain, prioritized by source_batch_count DESC. 4 chains/day = 800 events/day capacity. |
| Adaptive max_tokens | 150/300/500/800 | **100/200/350/600** | Tighten token budgets ~25%. Summaries are still adequate at lower limits. |

**Combined effect:** ~60-70% reduction in Phase 4.5a token spend.

### Phase 4.5b: CTM Summaries (2% of spend -- low priority)

| Threshold | Current | Recommended | Rationale |
|-----------|---------|-------------|-----------|
| Cooldown | 24h | **24h** (keep) | Already conservative. No change needed. |
| Min titles | 30 | **30** (keep) | Good threshold. CTMs below 30 titles don't warrant narrative. |
| Re-summary trigger | event_count > event_count_at_summary | **event_count >= event_count_at_summary * 1.5** | Only re-generate if event count grew 50%+. Prevents re-gen for 1 new event. |

### Phase 4.1: Topic Consolidation (2% of spend)

| Threshold | Current | Recommended | Rationale |
|-----------|---------|-------------|-----------|
| Over-merge guard | 1 story for >= 10 topics | Keep | Good safety net |
| Skip conditions | Already have 2 | Keep | Working well |

### Phase 3.1/3.3: Classification (23% of combined spend)

| Threshold | Current | Recommended | Rationale |
|-----------|---------|-------------|-----------|
| 3.1 batch size | 25 | **30** | Slightly larger batches = fewer calls. DeepSeek handles 30 labels fine. |
| 3.1 max titles/run | 500 | **300** | With 30m intervals, 300/run = still 7,200/12h capacity (2.4x headroom for 3k). |
| 3.3 whitelist | 38 combos | Keep + monitor | Already saves significant gating calls |

---

## Resilience: Must-Haves for Unattended Render

### R1: HTTP 429 / Rate Limit Backoff

**Problem:** Current retry logic (`run_phase_with_retry`) catches all exceptions equally. A 429 from DeepSeek needs longer backoff than a timeout.

**Fix:** In `core/llm_utils.py` or wherever the HTTP call happens, detect 429 status and apply specific backoff:

```python
if response.status_code == 429:
    retry_after = int(response.headers.get('Retry-After', 60))
    print(f"Rate limited, waiting {retry_after}s...")
    await asyncio.sleep(retry_after)
```

Add to: Phase 3.1, 3.3, 4.1, 4.5a, 4.5b LLM call sites.

### R2: Phase-Level Timeouts

**Problem:** If a phase hangs (DeepSeek unresponsive, DB lock), the entire daemon stalls.

**Fix:** Wrap each phase in an overall timeout:

```python
async def run_phase_with_timeout(self, phase_name, phase_func, timeout_seconds, *args):
    try:
        await asyncio.wait_for(phase_func(*args), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        print(f"{phase_name} timed out after {timeout_seconds}s, moving on")
```

Suggested timeouts:
- Classification slot: 10 min (600s)
- Enrichment chain: 30 min (1800s)
- Ingestion: 20 min (1200s)

### R3: Connection Pooling / Cleanup

**Problem:** `get_connection()` creates a new `psycopg2.connect()` every call. Leaked connections can exhaust the pool.

**Render DB status:** 103 max connections, ~11 active (frontend pool). Pipeline should use max 10.

**Fix:** Use a connection pool:

```python
from psycopg2.pool import ThreadedConnectionPool

class PipelineDaemon:
    def __init__(self):
        self.pool = ThreadedConnectionPool(
            minconn=2, maxconn=10,
            host=..., port=..., database=..., user=..., password=...
        )

    def get_connection(self):
        return self.pool.getconn()

    def return_connection(self, conn):
        self.pool.putconn(conn)
```

Ensure every `get_connection()` has a matching `return_connection()` in `finally` blocks.

### R4: Graceful Shutdown Completion

**Problem:** `SIGTERM` on Render sets `self.running = False` but phases don't check mid-run.

**Fix:** Check `self.running` between phases in the enrichment chain. If shutdown requested, commit what's done and exit cleanly.

### R5: Structured Logging for Render

**Fix (minimal):** Add timestamps and phase tags:

```python
def log(self, phase, msg):
    print(f"[{datetime.now().isoformat()}] [{phase}] {msg}")
```

---

## Resolved Open Questions

**Q1: 6h vs 3h enrichment cycle?**
**RESOLVED: 6h.** No traffic, demo-only. Capacity analysis confirms 3k titles are fully processed within 12h with 6h enrichment. If traffic grows, switch to 3h (env var change only).

**Q2: Should classification (Slot 2) also be less frequent?**
**RESOLVED: 30 min.** Labels/tracks aren't user-visible. 30m still gives 12,000+ title capacity per 12h cycle. Saves ~50% of classification API calls vs 15m.

**Q3: Connection pool size for Render?**
**RESOLVED: maxconn=10.** Render DB has 103 max connections (not 20 as assumed). Frontend uses ~10. Pipeline safely uses 10. Total ~20, well within 103 limit.

**Q4: Should we keep full statistics print every cycle?**
**RESOLVED: Every 6h only.** Run stats with the enrichment chain. Saves ~96% of statistics DB queries.

---

## Implementation Order

| Step | Effort | Impact | Risk |
|------|--------|--------|------|
| 1. R1: 429 backoff | 30 min | Must-have | Low |
| 2. R2: Phase timeouts | 30 min | Must-have | Low |
| 3. R3: Connection pooling | 1h | Must-have | Medium (test carefully) |
| 4. Consolidate to 4 slots | 1h | High (simplicity + cost) | Low |
| 5. Lift 4.5a thresholds (MIN_SUMMARY_SOURCES=8, growth 2.0x+10, max_events=200) | 30 min | High (cost) | Low |
| 6. Lift 3.1 batch size (30) + max titles (300) | 15 min | Medium (cost) | Low |
| 7. R5: Structured logging | 30 min | Nice-to-have | Low |
| 8. Lift 4.5b re-summary trigger to 1.5x event growth | 15 min | Low (only 2% spend) | Low |

**Total: ~4.5 hours for everything, ~3 hours for must-haves (R1-R3 + slot consolidation + 4.5a tuning)**

### Estimated Cost After Optimization

| Phase | Current daily | After optimization | Reduction |
|-------|-------------|-------------------|-----------|
| 3.1 | ~420k tokens | ~280k | -33% (larger batches, fewer runs) |
| 3.3 | ~180k tokens | ~120k | -33% (fewer runs) |
| 4.1 | ~40k tokens | ~10k | -75% (4 runs/day vs 96) |
| 4.5a | ~1.5M tokens | ~400k | -73% (chain eliminates churn, lifted thresholds) |
| 4.5b | ~50k tokens | ~20k | -60% (4 runs/day, higher trigger) |
| **Total** | **~2.5M** | **~830k** | **~67% reduction** |

**Estimated daily cost: ~$0.20-0.50/day on DeepSeek** (down from ~$0.60-1.50)
