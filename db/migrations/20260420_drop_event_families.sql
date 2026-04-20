-- Drop the event_families system entirely.
-- Supersedes D-051 / D-053 / completes D-059.
-- See docs/context/EVENT_FAMILIES_REMOVAL.md for rationale + inventory.
--
-- Apply order: local first, verify daemon + frontend clean, then Render.
-- IMPORTANT: frontend + pipeline code removal must be live on Render BEFORE
-- running this migration there, or daemon Slot 3 errors on the dropped column.

BEGIN;

-- 1. Stale indexes on event_families (from db/migrations/20251006_add_performance_indexes.sql).
DROP INDEX IF EXISTS idx_event_families_status;
DROP INDEX IF EXISTS idx_event_families_created_at;
DROP INDEX IF EXISTS idx_event_families_enrichment_queue;

-- 2. Drop the FK column from events_v3. CASCADE handles the FK constraint.
ALTER TABLE events_v3 DROP COLUMN IF EXISTS family_id CASCADE;

-- 3. Drop the table itself.
DROP TABLE IF EXISTS event_families CASCADE;

COMMIT;

-- Post-apply verification:
--   \d events_v3      -- no family_id column
--   \dt event_families  -- 'Did not find any relation named "event_families"'
