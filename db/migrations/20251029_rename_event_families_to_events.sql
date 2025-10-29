-- Migration: Rename event_families to events
-- Date: 2025-10-29
-- Description: Conceptual shift from "Event Families" to individual "Events" as primary entity
--              Events can later be assembled into families rather than starting with families

BEGIN;

-- Step 1: Create backup of event_families table structure and data
CREATE TABLE event_families_backup AS SELECT * FROM event_families;
COMMENT ON TABLE event_families_backup IS 'Backup of event_families before renaming to events (2025-10-29)';

-- Step 2: Drop foreign key constraints that reference event_families
ALTER TABLE framed_narratives DROP CONSTRAINT IF EXISTS framed_narratives_event_family_id_fkey;

-- Step 3: Rename the table
ALTER TABLE event_families RENAME TO events;

-- Step 4: Rename the event_family_id column in framed_narratives to event_id
ALTER TABLE framed_narratives RENAME COLUMN event_family_id TO event_id;

-- Step 5: Rename the event_family_id column in titles table if it exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'titles' AND column_name = 'event_family_id'
    ) THEN
        ALTER TABLE titles RENAME COLUMN event_family_id TO event_id;
    END IF;
END $$;

-- Step 6: Recreate foreign key constraint with new name
ALTER TABLE framed_narratives
ADD CONSTRAINT framed_narratives_event_id_fkey
FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE;

-- Step 7: Update index names to reflect new table name (drop old, create new)
-- These indexes reference the old table name
DROP INDEX IF EXISTS idx_ef_key_active;
CREATE UNIQUE INDEX idx_event_key_active ON events (ef_key) WHERE status = 'active';

DROP INDEX IF EXISTS idx_event_families_confidence;
-- Note: confidence_score column was removed in previous migration, skip index

DROP INDEX IF EXISTS idx_event_families_created_at;
CREATE INDEX idx_events_created_at ON events (created_at DESC);

DROP INDEX IF EXISTS idx_event_families_ef_context;
CREATE INDEX idx_events_context ON events (ef_context);

DROP INDEX IF EXISTS idx_event_families_enrichment_queue;
CREATE INDEX idx_events_enrichment_queue ON events (status, created_at DESC) WHERE status = 'seed';
COMMENT ON INDEX idx_events_enrichment_queue IS 'Optimized for get_enrichment_queue() single query';

DROP INDEX IF EXISTS idx_event_families_primary_theater;
CREATE INDEX idx_events_primary_theater ON events (primary_theater);

DROP INDEX IF EXISTS idx_event_families_status;
CREATE INDEX idx_events_status ON events (status) WHERE status = 'seed';
COMMENT ON INDEX idx_events_status IS 'Speeds up P4 enrichment queue queries';

-- idx_status and idx_theater_type_active don't have table name prefix, so they're fine

-- Step 8: Add comment to new events table
COMMENT ON TABLE events IS 'Strategic events - individual events that can be assembled into families';

COMMIT;

-- Verification queries
SELECT 'Events table created successfully' as status;
SELECT COUNT(*) as events_count FROM events;
SELECT COUNT(*) as backup_count FROM event_families_backup;
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'framed_narratives' AND column_name = 'event_id';
