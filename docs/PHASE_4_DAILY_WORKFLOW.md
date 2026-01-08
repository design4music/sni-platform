# Phase 4 Daily Workflow

## Overview

Phase 4 operates in two modes:
1. **Daily Processing**: High-volume CTMs get daily updates (events + summaries)
2. **Month-End Finalization**: All CTMs processed before freezing

---

## Daily Processing (Daemon Mode)

**Runs**: Every day as part of pipeline daemon
**Target**: CTMs with ≥20 titles (configurable via `v3_p4_min_titles`)
**Behavior**: Re-processes CTMs daily to keep content fresh

### Phase 4.1: Events Digest Generation

**Script**: `v3/phase_4/generate_events_digest.py`

**Queue Selection**:
```sql
SELECT c.id, c.centroid_id, c.track, c.month, c.title_count, cent.label
FROM ctm c
JOIN centroids_v3 cent ON c.centroid_id = cent.id
WHERE c.title_count >= 20
  AND c.is_frozen = false
ORDER BY c.title_count DESC, c.month DESC
```

**Processing**:
- For CTMs ≤70 titles: Single LLM call
- For CTMs >70 titles: Batched processing with consolidation
  1. Split into batches of 70 titles
  2. Extract events from each batch
  3. Consolidation LLM call to deduplicate across batches

**Output**: Updates `ctm.events_digest` (JSONB array of events)

### Phase 4.2: Summary Generation

**Script**: `v3/phase_4/generate_summaries.py`

**Queue Selection**:
```sql
SELECT c.id, c.centroid_id, c.track, c.month,
       c.events_digest, c.title_count,
       cent.label, cent.class, cent.primary_theater
FROM ctm c
JOIN centroids_v3 cent ON c.centroid_id = cent.id
WHERE c.events_digest IS NOT NULL
  AND jsonb_array_length(c.events_digest) > 0
  AND c.is_frozen = false
  AND c.title_count >= 20
ORDER BY c.title_count DESC, c.month DESC
```

**Processing**:
- Generates 150-250 word narrative from events digest
- Strategic intelligence tone
- Chronological flow

**Output**: Updates `ctm.summary_text`

---

## Month-End Finalization

**Script**: `v3/phase_4/finalize_month.py`
**Runs**: Manually at end of month before freezing
**Target**: ALL CTMs regardless of title count (even 1 title)

### Usage

```bash
# Finalize specific month
python v3/phase_4/finalize_month.py 2026-01

# Finalize all unfrozen CTMs
python v3/phase_4/finalize_month.py
```

### Behavior

Processes every unfrozen CTM:
- CTMs with 0 titles: Skipped
- CTMs with 1-19 titles: Processed (not in daily queue)
- CTMs with 20+ titles: Re-processed (final pass)

This ensures:
- Complete historical record
- Low-volume but important stories captured
- Final consolidated view before archiving

### After Finalization

Freeze the month's CTMs:
```sql
UPDATE ctm
SET is_frozen = true
WHERE TO_CHAR(month, 'YYYY-MM') = '2026-01';
```

---

## Configuration

**File**: `core/config.py`

```python
v3_p4_batch_size: int = 70           # Max titles per batch (API limit)
v3_p4_min_titles: int = 20           # Minimum for daily processing
v3_p4_temperature: float = 0.5       # Summary creativity
v3_p4_max_tokens: int = 500          # Summary length
v3_p4_timeout_seconds: int = 600     # LLM timeout
```

**Adjusting Threshold**:
- Current: 20 titles (~55 CTMs qualify daily)
- Future options: 30, 50, 100 based on performance/cost
- Set via environment: `V3_P4_MIN_TITLES=30`

---

## CTM Lifecycle Example

**Day 1** (Jan 1):
- USA geo_politics: 15 titles → Not processed (below threshold)
- Germany geo_politics: 25 titles → Processed (5 events, summary)

**Day 2** (Jan 2):
- USA geo_politics: 22 titles → Joins daily processing (new entries)
- Germany geo_politics: 30 titles → Re-processed (updated events/summary)

**Day 5** (Jan 5):
- Caracas operation breaks → USA geo_politics spikes to 400 titles
- Daily processing: Re-extracts events from 400 titles (6 batches)
- Consolidation: Deduplicates across batches
- Summary: Regenerated with full context

**Day 31** (Jan 31):
- Month-end finalization script runs
- Process ALL CTMs including:
  - Iceland geo_politics: 3 titles (below daily threshold)
  - Micronesia geo_security: 1 title
- Freeze month: `is_frozen = true`

---

## Current Stats (2026-01)

Total CTMs: 299

**Daily Processing Eligible** (≥20 titles):
- 55 CTMs (~18% of total)
- Combined: ~3,000 titles/day
- Processing time: ~2-3 hours

**Month-End Processing** (<20 titles):
- 244 CTMs (~82% of total)
- Many with 1-5 titles
- One-time comprehensive sweep

---

## Benefits

**Daily Updates**:
- Fresh content for news platform users
- Captures evolving stories (like Caracas crisis)
- Focuses resources on high-signal CTMs

**Month-End Finalization**:
- Complete historical record
- No stories lost (even 1-title CTMs)
- Final consolidated view

**Batching with Consolidation**:
- Handles any CTM size (tested up to 578 titles)
- Intelligent deduplication (578 titles → 40 events)
- Maintains chronological coherence

---

## Future Optimization

**Threshold Calibration**:
- Monitor API costs vs. coverage
- Consider dynamic thresholds by centroid importance
- Example: USA = 50 titles, smaller countries = 10 titles

**Incremental Updates**:
- Current: Full re-processing daily
- Future: Delta processing (only new titles since last run)
- Requires tracking `last_processed_at` per CTM

**Smart Scheduling**:
- High-volume CTMs: Process early in day
- Low-volume CTMs: Batch at night
- Spread load for API rate limits
