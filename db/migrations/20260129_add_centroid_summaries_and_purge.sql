-- 1. Centroid Monthly Summaries
-- Cross-track narrative summary for each centroid/month, generated at freeze time
CREATE TABLE IF NOT EXISTS centroid_monthly_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    centroid_id VARCHAR(100) NOT NULL,
    month DATE NOT NULL,
    summary_text TEXT NOT NULL,
    track_count INTEGER,  -- How many tracks contributed
    total_events INTEGER, -- Total events across all tracks
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(centroid_id, month)
);

CREATE INDEX IF NOT EXISTS idx_centroid_monthly_summaries_lookup
ON centroid_monthly_summaries (centroid_id, month);

COMMENT ON TABLE centroid_monthly_summaries IS 'Cross-track narrative summaries per centroid/month, generated once at freeze time';

-- 2. Tombstone Table for Purged Titles
-- Stores URL hashes of rejected titles to prevent re-ingestion
CREATE TABLE IF NOT EXISTS titles_purged (
    url_hash VARCHAR(64) PRIMARY KEY,
    original_title VARCHAR(500),  -- Keep for debugging/audit
    source_domain VARCHAR(255),
    reason VARCHAR(50) NOT NULL,  -- 'out_of_scope', 'blocked_llm', etc.
    purged_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_titles_purged_reason
ON titles_purged (reason);

COMMENT ON TABLE titles_purged IS 'Tombstone table for rejected titles - prevents re-ingestion via URL hash check';
