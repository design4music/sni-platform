-- Add parent_ef_id column to track split siblings
-- Date: 2025-10-23
-- Reason: Prevent P3.5d split siblings from re-merging while allowing merges with other EFs

BEGIN;

-- Add parent_ef_id column with foreign key constraint
ALTER TABLE event_families
ADD COLUMN parent_ef_id UUID REFERENCES event_families(id);

-- Add index for efficient sibling lookups
CREATE INDEX idx_event_families_parent_ef_id ON event_families(parent_ef_id);

-- Add comment for documentation
COMMENT ON COLUMN event_families.parent_ef_id IS 'References the parent EF if this was created by P3.5d splitting. Siblings share the same parent_ef_id and should not be merged together.';

COMMIT;
