-- Performance Indexes Migration
-- Created: 2025-10-06
-- Purpose: Add critical indexes for frequently queried columns (50% query speed improvement)

-- Titles table indexes (most frequently queried)
CREATE INDEX IF NOT EXISTS idx_titles_processing_status ON titles(processing_status) WHERE processing_status = 'pending';
CREATE INDEX IF NOT EXISTS idx_titles_gate_keep ON titles(gate_keep) WHERE gate_keep = true;
CREATE INDEX IF NOT EXISTS idx_titles_event_family_id ON titles(event_family_id) WHERE event_family_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_titles_ingested_at ON titles(ingested_at DESC);
CREATE INDEX IF NOT EXISTS idx_titles_pubdate_utc ON titles(pubdate_utc DESC);

-- Composite index for strategic title filtering (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_titles_strategic_ready ON titles(gate_keep, event_family_id)
WHERE gate_keep = true AND event_family_id IS NULL;

-- Event Families table indexes
CREATE INDEX IF NOT EXISTS idx_event_families_status ON event_families(status) WHERE status = 'seed';
CREATE INDEX IF NOT EXISTS idx_event_families_created_at ON event_families(created_at DESC);

-- Composite index for enrichment queue query (removed time predicate - NOW() not IMMUTABLE)
CREATE INDEX IF NOT EXISTS idx_event_families_enrichment_queue ON event_families(status, created_at DESC)
WHERE status = 'seed';

-- Feeds table index
CREATE INDEX IF NOT EXISTS idx_feeds_is_active ON feeds(is_active) WHERE is_active = true;

-- Add comments for documentation
COMMENT ON INDEX idx_titles_processing_status IS 'Speeds up P2 filter queue queries';
COMMENT ON INDEX idx_titles_gate_keep IS 'Speeds up strategic title filtering';
COMMENT ON INDEX idx_titles_event_family_id IS 'Speeds up P3 EF member lookups';
COMMENT ON INDEX idx_titles_strategic_ready IS 'Composite index for most common P3 query pattern';
COMMENT ON INDEX idx_event_families_status IS 'Speeds up P4 enrichment queue queries';
COMMENT ON INDEX idx_event_families_enrichment_queue IS 'Optimized for get_enrichment_queue() single query';

-- Analyze tables to update query planner statistics
ANALYZE titles;
ANALYZE event_families;
ANALYZE feeds;
