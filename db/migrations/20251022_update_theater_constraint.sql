-- Phase 1 EF v2: Update theater constraint for multi-theater system
-- Date: 2025-10-22
-- Description: Remove restrictive theater constraint to allow country names and bilateral patterns

BEGIN;

-- Drop old constraint
ALTER TABLE event_families DROP CONSTRAINT IF EXISTS chk_primary_theater;

-- Add new flexible constraint
-- Allows: country names, bilateral patterns (e.g., "US-China Relations"), "Global", or NULL
-- We'll validate theater values in application code instead of strict DB constraint
ALTER TABLE event_families
ADD CONSTRAINT chk_primary_theater_not_empty
CHECK (primary_theater IS NULL OR LENGTH(TRIM(primary_theater)) > 0);

COMMENT ON CONSTRAINT chk_primary_theater_not_empty ON event_families IS
'Flexible theater constraint for Phase 1 EF v2: allows country names, bilateral patterns, and Global';

COMMIT;

-- Verification
SELECT
    conname as constraint_name,
    pg_get_constraintdef(c.oid) as definition
FROM pg_constraint c
JOIN pg_class t ON c.conrelid = t.oid
WHERE t.relname = 'event_families'
AND conname LIKE '%theater%';
