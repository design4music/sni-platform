-- Epic narrative frames extracted via two-pass LLM analysis

CREATE TABLE IF NOT EXISTS epic_narratives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    epic_id UUID NOT NULL REFERENCES epics(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    description TEXT,
    moral_frame TEXT,
    title_count INTEGER NOT NULL DEFAULT 0,
    top_sources TEXT[],
    top_countries TEXT[],
    sample_titles JSONB,
    -- RAI Phase 6 fields (all nullable)
    rai_adequacy FLOAT,
    rai_synthesis TEXT,
    rai_conflicts TEXT[],
    rai_blind_spots TEXT[],
    rai_shifts JSONB,
    rai_analyzed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(epic_id, label)
);

CREATE INDEX IF NOT EXISTS idx_epic_narratives_epic ON epic_narratives(epic_id);
CREATE INDEX IF NOT EXISTS idx_epic_narratives_count ON epic_narratives(title_count DESC);
