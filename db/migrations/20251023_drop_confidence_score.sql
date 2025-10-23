-- Drop confidence_score column from event_families
-- Date: 2025-10-23
-- Reason: Not used in P3.5 pipeline, causing split failures

BEGIN;

-- Drop confidence_score column
ALTER TABLE event_families
DROP COLUMN IF EXISTS confidence_score;

COMMIT;

-- Verification
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'event_families'
ORDER BY ordinal_position;
