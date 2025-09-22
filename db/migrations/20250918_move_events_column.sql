-- Migration: Move events column between summary and key_actors for review convenience
-- Date: September 18, 2025
-- Purpose: Reorder events column for easier manual review

-- PostgreSQL doesn't support moving columns directly, so we need to recreate the table
-- First, create a new table with the desired column order
CREATE TABLE event_families_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    summary TEXT,
    events JSONB DEFAULT '[]',
    key_actors TEXT[],
    event_type VARCHAR(50),
    primary_theater VARCHAR(50),
    ef_key VARCHAR(16),
    status VARCHAR(20) DEFAULT 'seed',
    merged_into UUID,
    merge_rationale TEXT,
    event_start TIMESTAMP,
    event_end TIMESTAMP,
    source_title_ids UUID[],
    confidence_score REAL,
    coherence_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processing_notes TEXT,
    last_research_date TIMESTAMP,
    promotion_score REAL DEFAULT 0.0,
    monitoring_start_date TIMESTAMP DEFAULT NOW()
);

-- Copy data from old table to new table
INSERT INTO event_families_new
SELECT
    id, title, summary, events, key_actors, event_type, primary_theater,
    ef_key, status, merged_into, merge_rationale,
    event_start, event_end, source_title_ids,
    confidence_score, coherence_reason, created_at, updated_at,
    processing_notes, NULL, promotion_score, NOW()
FROM event_families;

-- Drop old table and rename new one
DROP TABLE event_families;
ALTER TABLE event_families_new RENAME TO event_families;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_event_families_status ON event_families(status);
CREATE INDEX IF NOT EXISTS idx_event_families_events ON event_families USING GIN(events);

-- Add foreign key constraint for titles table
ALTER TABLE titles ADD CONSTRAINT fk_titles_event_family
    FOREIGN KEY (event_family_id) REFERENCES event_families(id);