-- Migration: Convert taxonomy_v3.centroid_ids from ARRAY to VARCHAR
-- Each CSC item has exactly one centroid (confirmed by analysis)
--
-- Analysis results:
--   - Max centroids per record: 1
--   - Min centroids per record: 1
--   - Records with multiple centroids: 0
--   - Safe to migrate to scalar field

BEGIN;

-- Step 1: Add new VARCHAR column
-- Max observed length: 22 (OCEANIA-PAPUANEWGUINEA)
-- Using VARCHAR(30) for safety
ALTER TABLE taxonomy_v3
ADD COLUMN centroid_id VARCHAR(30);

-- Step 2: Migrate data (extract first element from array)
UPDATE taxonomy_v3
SET centroid_id = centroid_ids[1]
WHERE centroid_ids IS NOT NULL
  AND array_length(centroid_ids, 1) >= 1;

-- Step 3: Verify migration (should return 0 mismatches)
-- Check that all non-NULL arrays have exactly 1 element
DO $$
DECLARE
    mismatch_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO mismatch_count
    FROM taxonomy_v3
    WHERE centroid_ids IS NOT NULL
      AND array_length(centroid_ids, 1) != 1;

    IF mismatch_count > 0 THEN
        RAISE EXCEPTION 'Migration validation failed: % records have multiple centroids', mismatch_count;
    END IF;

    RAISE NOTICE 'Validation passed: All records have 0 or 1 centroid';
END $$;

-- Step 4: Drop old ARRAY column
ALTER TABLE taxonomy_v3
DROP COLUMN centroid_ids;

-- Step 5: Rename new column to original name
ALTER TABLE taxonomy_v3
RENAME COLUMN centroid_id TO centroid_ids;

-- Step 6: Create index for efficient lookups
CREATE INDEX idx_taxonomy_v3_centroid_ids ON taxonomy_v3(centroid_ids)
WHERE is_active = true;

-- Step 7: Add check constraint for format validation (optional but recommended)
-- Ensures centroid IDs follow expected format: REGION-TOPIC or SYS-TOPIC or REGION-SUB-TOPIC
-- Examples: 'ASIA-CHINA', 'NON-STATE-ISIS', 'EUROPE-BALKANS-EAST'
ALTER TABLE taxonomy_v3
ADD CONSTRAINT check_centroid_ids_format
CHECK (
    centroid_ids IS NULL OR
    centroid_ids ~ '^[A-Z]+(-[A-Z]+)+$'
);

COMMIT;

-- Verify final state
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'taxonomy_v3'
  AND column_name = 'centroid_ids';

-- Show distribution after migration
SELECT
    centroid_ids,
    COUNT(*) as count
FROM taxonomy_v3
WHERE is_active = true
GROUP BY centroid_ids
ORDER BY count DESC
LIMIT 10;
