-- Add timestamp to track when a CTM was last aggregated (Phase 4.1)
-- This enables incremental processing - only re-aggregate CTMs with new content

ALTER TABLE ctm ADD COLUMN IF NOT EXISTS last_aggregated_at TIMESTAMPTZ;
ALTER TABLE ctm ADD COLUMN IF NOT EXISTS title_count_at_aggregation INTEGER;

-- Index for efficient lookup of CTMs needing aggregation
CREATE INDEX IF NOT EXISTS idx_ctm_needs_aggregation
ON ctm (last_aggregated_at, title_count)
WHERE is_frozen = false;

COMMENT ON COLUMN ctm.last_aggregated_at IS 'When this CTM was last processed by Phase 4.1 topic aggregation';
COMMENT ON COLUMN ctm.title_count_at_aggregation IS 'Title count when last aggregated - used to detect new content';
