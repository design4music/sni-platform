# Fix: Title Assignments Missing

## Problem Summary

**Issue**: Only ~36% of assigned titles have entries in `title_assignments` table.

**Impact**: Track pages show 18 sources instead of 241 for AMERICAS-CANADA geo_economy.

## Root Causes

1. **Wrong UNIQUE constraint** on title_assignments:
   - Current: `UNIQUE (title_id, centroid_id)`
   - Problem: When a title is assigned to multiple tracks for the same centroid, only the LAST assignment is kept
   - Example: Title assigned to CANADA + geo_economy, then later to CANADA + geo_politics → geo_economy assignment is OVERWRITTEN

2. **Phase 3 re-processes all assigned titles**:
   - Query selects ALL titles with `processing_status='assigned'`
   - Every run re-processes the same titles
   - Combined with constraint issue, this causes constant overwrites

3. **Silent failures**:
   - When LLM doesn't return a track assignment, titles are skipped silently
   - Only increments `title_errors` counter, no logging

## Statistics

```
Titles with status='assigned':     16,661
Title_assignments records:         10,628  (64% missing!)
Sum of CTM.title_count:            74,675  (inflated due to re-processing)
```

## The Fix

### 1. Database Migration

**File**: `db/migrations/20260117_fix_title_assignments_constraint.sql`

Changes UNIQUE constraint from:
```sql
UNIQUE (title_id, centroid_id)
```

To:
```sql
UNIQUE (title_id, centroid_id, track)
```

This allows a title to be assigned to multiple tracks for the same centroid.

### 2. Phase 3 Code Update

**File**: `pipeline/phase_3/assign_tracks_batched.py`

**Change 1**: Only process unassigned titles (line 617-627)
```sql
-- Before: processed ALL assigned titles
WHERE processing_status = 'assigned'

-- After: only unprocessed titles
WHERE processing_status = 'assigned'
  AND NOT EXISTS (SELECT 1 FROM title_assignments WHERE title_id = t.id)
```

**Change 2**: Add logging for skipped titles (line 535)
```python
if title_id not in track_assignments:
    print(f"WARNING: No track assigned for title {title_id}: {title_display[:60]}...")
    title_errors += 1
```

## Running the Fix

### Step 1: Apply Migration

```bash
cd db
python run_migration_fix_assignments.py
```

This will:
- Show current statistics
- Drop old constraint
- Add new constraint with track
- Count unprocessed titles

### Step 2: Restart Pipeline Daemon

The pipeline will automatically process the ~10,695 unassigned titles.

Monitor output for:
```
Phase 3: Intel Gating + Track Assignment (Centroid-Batched)
Total titles to process: 10695
```

### Step 3: Verify Fix

After pipeline runs, check:

```sql
SELECT COUNT(*) FROM titles_v3 WHERE processing_status = 'assigned';
SELECT COUNT(*) FROM title_assignments;
```

Should be much closer (allowing for multi-centroid assignments).

## Expected Outcome

**Before**:
- AMERICAS-CANADA geo_economy: 18 sources shown (241 in title_count)

**After**:
- All ~241 sources will appear in title_assignments
- Track pages will show proper source counts
- Events accordion will show all related sources

## Notes

- The migration is **non-destructive** - only changes constraint
- Existing data remains intact
- Phase 3 will populate missing assignments
- CTM.title_count may still be inflated from old runs (harmless)

## Future Considerations

1. **Event source limits**: For CTMs with 7k+ titles, consider:
   - Store only top 50-100 source_title_ids per event in events_digest
   - Create separate page "View all sources" for large events

2. **CTM title_count cleanup**: Consider recalculating from actual assignments:
   ```sql
   UPDATE ctm
   SET title_count = (
     SELECT COUNT(*) FROM title_assignments WHERE ctm_id = ctm.id
   )
   ```

3. **Monitoring**: Add Phase 3 metrics to track:
   - Assignment success rate
   - Skipped titles (no track assigned)
   - Processing time per batch
