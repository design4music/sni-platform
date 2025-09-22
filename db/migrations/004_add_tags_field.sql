-- Add tags field to event_families table
-- Migration: 004_add_tags_field.sql

ALTER TABLE event_families
ADD COLUMN tags JSONB DEFAULT '[]'::jsonb;

-- Add index for efficient tag queries
CREATE INDEX idx_event_families_tags ON event_families USING GIN (tags);

-- Add comment
COMMENT ON COLUMN event_families.tags IS 'Strategic tags: 2 thematic + 1 geographic (JSON array)';