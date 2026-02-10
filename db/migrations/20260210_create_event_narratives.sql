-- Unified narratives table: replaces epic_narratives, supports epic/event/ctm entity types
-- Migration: create new table, copy data, drop old table

-- Step 1: Create unified table
CREATE TABLE IF NOT EXISTS narratives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL,       -- 'epic', 'event', 'ctm'
    entity_id UUID NOT NULL,         -- references epics.id, events_v3.id, or ctm.id
    label TEXT NOT NULL,
    description TEXT,
    moral_frame TEXT,
    title_count INTEGER NOT NULL DEFAULT 0,
    top_sources TEXT[],
    proportional_sources TEXT[],
    top_countries TEXT[],
    sample_titles JSONB,
    -- RAI analysis fields
    rai_adequacy FLOAT,
    rai_synthesis TEXT,
    rai_conflicts TEXT[],
    rai_blind_spots TEXT[],
    rai_shifts JSONB,
    rai_full_analysis TEXT,
    rai_analyzed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(entity_id, label)
);

CREATE INDEX IF NOT EXISTS idx_narratives_entity ON narratives(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_narratives_count ON narratives(title_count DESC);

-- Step 2: Migrate existing epic_narratives data
INSERT INTO narratives (
    id, entity_type, entity_id, label, description, moral_frame,
    title_count, top_sources, proportional_sources, top_countries, sample_titles,
    rai_adequacy, rai_synthesis, rai_conflicts, rai_blind_spots,
    rai_shifts, rai_full_analysis, rai_analyzed_at, created_at
)
SELECT
    id, 'epic', epic_id, label, description, moral_frame,
    title_count, top_sources, proportional_sources, top_countries, sample_titles,
    rai_adequacy, rai_synthesis, rai_conflicts, rai_blind_spots,
    rai_shifts, rai_full_analysis, rai_analyzed_at, created_at
FROM epic_narratives
ON CONFLICT (entity_id, label) DO NOTHING;

-- Step 3: Drop old table
DROP TABLE IF EXISTS epic_narratives;
