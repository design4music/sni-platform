-- Migration: Create events_v3 tables for normalized event storage
-- Date: 2026-01-17
-- Purpose: Parallel implementation alongside ctm.events_digest JSONB
-- Safe: Does not modify existing tables, dual-write pattern

-- events_v3: Canonical events after merging
-- These are the final, merged events shown to users
CREATE TABLE IF NOT EXISTS events_v3 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ctm_id UUID NOT NULL REFERENCES ctm(id) ON DELETE CASCADE,

    -- Event content
    date DATE NOT NULL,
    summary TEXT NOT NULL,

    -- Metadata
    date_confidence TEXT DEFAULT 'high', -- 'high' or 'low' from Phase 4 validation
    source_batch_count INT DEFAULT 1,    -- How many batches contributed to this event

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes for common queries
    CONSTRAINT events_v3_summary_not_empty CHECK (summary <> '')
);

-- Index for CTM lookups (most common query)
CREATE INDEX IF NOT EXISTS idx_events_v3_ctm_id ON events_v3(ctm_id);

-- Index for date-based queries
CREATE INDEX IF NOT EXISTS idx_events_v3_date ON events_v3(date DESC);

-- Composite index for CTM + date (timeline view)
CREATE INDEX IF NOT EXISTS idx_events_v3_ctm_date ON events_v3(ctm_id, date DESC);


-- event_v3_titles: Many-to-many relationship between events and titles
-- Union of all titles from merged events (A ∪ B ∪ C)
CREATE TABLE IF NOT EXISTS event_v3_titles (
    event_id UUID NOT NULL REFERENCES events_v3(id) ON DELETE CASCADE,
    title_id UUID NOT NULL REFERENCES titles_v3(id) ON DELETE CASCADE,

    -- Metadata (for future enhancements)
    added_from_batch INT DEFAULT 0,  -- Which batch contributed this title

    created_at TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (event_id, title_id)
);

-- Index for event -> titles lookup
CREATE INDEX IF NOT EXISTS idx_event_v3_titles_event ON event_v3_titles(event_id);

-- Index for title -> events lookup (reverse search)
CREATE INDEX IF NOT EXISTS idx_event_v3_titles_title ON event_v3_titles(title_id);


-- Trigger to update updated_at on events_v3
CREATE OR REPLACE FUNCTION update_events_v3_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER events_v3_updated_at_trigger
    BEFORE UPDATE ON events_v3
    FOR EACH ROW
    EXECUTE FUNCTION update_events_v3_updated_at();


-- Verification queries
-- View events for a CTM with title counts
COMMENT ON TABLE events_v3 IS 'Canonical events after batch merging. Frontend reads from here (v3 system).';
COMMENT ON TABLE event_v3_titles IS 'Title assignments to events. Mechanical union during merge.';

-- Sample query to retrieve events with title counts
-- SELECT
--     e.id, e.date, e.summary,
--     COUNT(et.title_id) as title_count,
--     e.created_at
-- FROM events_v3 e
-- LEFT JOIN event_v3_titles et ON e.id = et.event_id
-- WHERE e.ctm_id = 'some-ctm-id'
-- GROUP BY e.id, e.date, e.summary, e.created_at
-- ORDER BY e.date DESC;
