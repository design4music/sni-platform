# Events V3 Migration: JSONB to Normalized Tables

## Overview

**Status**: IMPLEMENTED - Dual-write system active

**Purpose**: Move events from `ctm.events_digest` JSONB to normalized `events_v3` tables for better scalability and flexibility.

## Implementation Strategy

**Parallel Dual-Write System**: Both systems operate simultaneously until frontend is migrated.

```
Phase 4 → writes to BOTH:
  ├── ctm.events_digest (JSONB) ← Frontend reads from here (current)
  └── events_v3 tables (normalized) ← Frontend will read from here (future)
```

## Database Schema

### events_v3 Table

Stores canonical events after batch merging.

```sql
CREATE TABLE events_v3 (
    id UUID PRIMARY KEY,
    ctm_id UUID NOT NULL REFERENCES ctm(id),

    -- Event content
    date DATE NOT NULL,
    summary TEXT NOT NULL,

    -- Metadata
    date_confidence TEXT DEFAULT 'high',  -- 'high' or 'low'
    source_batch_count INT DEFAULT 1,     -- How many batches contributed

    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
```

### event_v3_titles Table

Many-to-many relationship between events and titles.

```sql
CREATE TABLE event_v3_titles (
    event_id UUID NOT NULL REFERENCES events_v3(id),
    title_id UUID NOT NULL REFERENCES titles_v3(id),
    added_from_batch INT DEFAULT 0,

    PRIMARY KEY (event_id, title_id)
);
```

## Event Processing Flow

### 1. Batch-Local Extraction (Phase 4.1)

**Function**: `extract_events_from_titles_single_batch()`

- LLM extracts events from chronologically ordered titles within ONE batch
- Events initially limited to batch's 70 titles
- Batch-level events are **transient** (memory only, not persisted individually)

### 2. Event Merging (Phase 4.1 Consolidation)

**Function**: `consolidate_events()`

- For high-volume CTMs (>70 titles), LLM consolidates events across batches
- Identifies duplicate/similar events and merges them
- Produces ONE canonical event per unique development

### 3. Title Reassignment (Mechanical Union)

**Implementation**: `write_events_to_v3_tables()`

When events A and B merge into event C:
```
Event A has titles: [uuid1, uuid2, uuid3]
Event B has titles: [uuid2, uuid4, uuid5]
→ Event C gets ALL: [uuid1, uuid2, uuid3, uuid4, uuid5]  (mechanical union)
```

**No semantic analysis, no keyword matching, just A ∪ B ∪ C**

### 4. Cleanup

Raw batch-level events are discarded after consolidation. Only canonical merged events persist.

## Files Changed

### Created

1. **db/migrations/20260117_create_events_v3_tables.sql**
   - Creates events_v3 and event_v3_titles tables
   - Indexes for CTM lookups and date queries

2. **pipeline/phase_4/write_events_v3.py**
   - `write_events_to_v3_tables()` - Writes canonical events to tables
   - `cleanup_orphaned_events_v3()` - Safety function for sync

3. **db/backfill_events_v3.py**
   - Migrates historical events from JSONB to v3 tables
   - Idempotent, safe to run multiple times

### Modified

1. **pipeline/phase_4/generate_events_digest.py**
   - Modified `extract_events_from_titles()` to return `(events, batch_count)` tuple
   - Added dual-write call in `process_single_ctm()`
   - Writes to BOTH JSONB and v3 tables in same transaction

## Running the Migration

### Step 1: Tables Already Created ✓

Migration was applied successfully.

### Step 2: Dual-Write is Active ✓

Phase 4 now writes to both systems automatically.

### Step 3: Backfill Historical Data

```bash
# Test with 10 CTMs first
cd db
python backfill_events_v3.py --limit 10

# Then run full backfill
python backfill_events_v3.py
```

### Step 4: Verify Data Integrity

```sql
-- Check migration progress
SELECT
    (SELECT COUNT(*) FROM ctm WHERE events_digest IS NOT NULL) as ctms_with_jsonb,
    (SELECT COUNT(DISTINCT ctm_id) FROM events_v3) as ctms_with_v3;

-- Compare counts for specific CTM
SELECT
    c.id,
    cent.label,
    c.track,
    jsonb_array_length(c.events_digest) as jsonb_events,
    (SELECT COUNT(*) FROM events_v3 WHERE ctm_id = c.id) as v3_events
FROM ctm c
JOIN centroids_v3 cent ON c.centroid_id = cent.id
WHERE c.events_digest IS NOT NULL
LIMIT 10;
```

### Step 5: Update Frontend Queries (Future)

After all data is migrated and verified:

```typescript
// OLD: Query from JSONB
const events = ctm.events_digest;

// NEW: Query from v3 tables
const events = await query(`
  SELECT
    e.id, e.date, e.summary, e.date_confidence,
    array_agg(evt.title_id) as source_title_ids
  FROM events_v3 e
  LEFT JOIN event_v3_titles evt ON e.id = evt.event_id
  WHERE e.ctm_id = $1
  GROUP BY e.id, e.date, e.summary, e.date_confidence
  ORDER BY e.date DESC
`, [ctmId]);
```

### Step 6: Deprecate JSONB (Future)

Once frontend is fully migrated:
```sql
-- Stop writing to events_digest
-- (remove dual-write from Phase 4)

-- Eventually drop column
ALTER TABLE ctm DROP COLUMN events_digest;
```

## Benefits

### 1. Scalability

- JSONB limited by row size (~100KB practical limit)
- V3 tables can store unlimited events/titles per CTM
- No more truncation worries for high-volume CTMs

### 2. Query Performance

```sql
-- Find all events mentioning a specific title (impossible with JSONB)
SELECT e.*
FROM events_v3 e
JOIN event_v3_titles evt ON e.id = evt.event_id
WHERE evt.title_id = 'some-uuid';

-- Find all CTMs covering an event on specific date
SELECT c.*
FROM ctm c
JOIN events_v3 e ON e.ctm_id = c.id
WHERE e.date = '2026-01-15';
```

### 3. Data Integrity

- Foreign key constraints ensure referential integrity
- Can't have orphaned title references
- Easier to validate and debug

### 4. Flexibility

- Can add event metadata without schema migration
- Can implement event versioning/history
- Can track batch contributions per event

## Safety Features

### Transactional Consistency

Both JSONB and v3 writes happen in same transaction - either both succeed or both fail.

### Idempotent Operations

- Backfill script can run multiple times safely
- `write_events_to_v3_tables()` uses UPSERT logic
- Duplicate events are detected by (ctm_id, date, summary)

### No Frontend Disruption

- Frontend continues reading from JSONB
- V3 tables populated in background
- Switch when ready, no downtime

## Monitoring

### Check Sync Status

```python
# db/check_events_sync.py
import psycopg2

# Compare JSONB vs V3 counts
cur.execute("""
    SELECT
        c.id,
        jsonb_array_length(c.events_digest) as jsonb_count,
        (SELECT COUNT(*) FROM events_v3 WHERE ctm_id = c.id) as v3_count
    FROM ctm c
    WHERE c.events_digest IS NOT NULL
      AND jsonb_array_length(c.events_digest) != (
        SELECT COUNT(*) FROM events_v3 WHERE ctm_id = c.id
      )
""")
```

### Phase 4 Output

Dual-write status is logged:
```
Processing: AMERICAS-CANADA / geo_economy / 2026-01 (241 titles)
  OK: 15 events extracted, 15 new events in v3 tables
```

## Future Enhancements

1. **Event Deduplication Across CTMs**
   - Same event appearing in multiple CTMs (e.g., "Trump announces tariffs")
   - Could create global events table with CTM many-to-many

2. **Event Versioning**
   - Track how event summaries evolve as new batches arrive
   - Store edit history in event_v3_history table

3. **Source Attribution**
   - Track which batch/title contributed which phrase to event summary
   - LLM citations in event text

4. **Event Confidence Scoring**
   - Not just date confidence, but overall event quality
   - Based on source count, consistency, LLM certainty

## Rollback Plan

If issues arise:

1. **Frontend still reads from JSONB** - no user impact
2. **Disable dual-write**: Comment out `write_events_to_v3_tables()` call
3. **Drop v3 tables**: `DROP TABLE event_v3_titles; DROP TABLE events_v3;`
4. **Continue with JSONB-only** until issues resolved

## Notes

- Migration preserves ALL data - nothing lost from JSONB
- Both systems can coexist indefinitely
- No rush to complete frontend migration
- Can test v3 queries extensively before switching
