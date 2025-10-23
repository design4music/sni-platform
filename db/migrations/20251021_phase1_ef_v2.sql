-- Phase 1: EF Generation v2 Migration
-- Date: 2025-10-21
-- Description: Clean existing EFs and add strategic_purpose column

BEGIN;

-- Step 1: Drop all framed_narratives (depends on event_families)
TRUNCATE TABLE framed_narratives CASCADE;

-- Step 2: Drop all event_families
TRUNCATE TABLE event_families CASCADE;

-- Step 3: Reset titles.event_family_id
UPDATE titles SET event_family_id = NULL WHERE event_family_id IS NOT NULL;

-- Step 4: Add strategic_purpose column
ALTER TABLE event_families
ADD COLUMN IF NOT EXISTS strategic_purpose TEXT;

-- Step 5: Add comment
COMMENT ON COLUMN event_families.strategic_purpose IS 'One-sentence core narrative for thematic validation (Phase 1 EF v2)';

-- Step 6: Create index for P3.5 queries (future)
CREATE INDEX IF NOT EXISTS idx_ef_event_type_status
ON event_families(event_type, status)
WHERE status IN ('seed', 'active');

COMMIT;

-- Verification queries
SELECT COUNT(*) as remaining_efs FROM event_families;
SELECT COUNT(*) as remaining_fns FROM framed_narratives;
SELECT COUNT(*) as titles_with_ef FROM titles WHERE event_family_id IS NOT NULL;
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'event_families'
AND column_name = 'strategic_purpose';
