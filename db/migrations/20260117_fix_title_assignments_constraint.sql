-- Migration: Fix title_assignments UNIQUE constraint to include track
-- Date: 2026-01-17
-- Issue: UNIQUE(title_id, centroid_id) prevents same title from being assigned to multiple tracks
-- Fix: Add track to the constraint

-- Step 1: Drop the old constraint
ALTER TABLE title_assignments
DROP CONSTRAINT IF EXISTS title_assignments_title_id_centroid_id_key;

-- Step 2: Add new constraint with track included
ALTER TABLE title_assignments
ADD CONSTRAINT title_assignments_title_id_centroid_id_track_key
UNIQUE (title_id, centroid_id, track);

-- Step 3: Verify constraint
SELECT
    conname as constraint_name,
    pg_get_constraintdef(oid) as constraint_definition
FROM pg_constraint
WHERE conrelid = 'title_assignments'::regclass
  AND conname LIKE '%title_id%';
