-- Migration: Add title and tags columns to events_v3 for deduplication
-- Date: 2026-01-24
-- Purpose: Enable semantic deduplication via LLM-generated titles and tags

-- Add title column (short headline, 5-15 words)
ALTER TABLE events_v3
ADD COLUMN IF NOT EXISTS title TEXT;

-- Add tags column (array of lowercase keywords for matching)
ALTER TABLE events_v3
ADD COLUMN IF NOT EXISTS tags TEXT[];

-- Add date_end for date ranges (rename existing 'date' conceptually to date_start)
-- We keep 'date' as the primary/latest date, add first_seen for range
ALTER TABLE events_v3
ADD COLUMN IF NOT EXISTS first_seen DATE;

-- Index for tag-based queries and deduplication
CREATE INDEX IF NOT EXISTS idx_events_v3_tags ON events_v3 USING GIN(tags);

-- Index for title-based lookups
CREATE INDEX IF NOT EXISTS idx_events_v3_title ON events_v3(title);

-- Comments
COMMENT ON COLUMN events_v3.title IS 'LLM-generated short headline (5-15 words) for UI and deduplication';
COMMENT ON COLUMN events_v3.tags IS 'Lowercase keyword tags for matching and filtering';
COMMENT ON COLUMN events_v3.first_seen IS 'Earliest title date (date column is latest)';
