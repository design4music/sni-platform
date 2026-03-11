-- Comparative RAI analysis per entity (event, ctm, epic).
-- Stores one unified analytical report across all stance-clustered narratives.

CREATE TABLE IF NOT EXISTS entity_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL,          -- 'event', 'ctm', 'epic'
    entity_id UUID NOT NULL,
    cluster_count INTEGER NOT NULL,     -- how many clusters were analysed
    sections TEXT,                      -- JSON array of RaiSection[]
    scores JSONB,                       -- comparative scores (per-cluster + overall)
    synthesis TEXT,                     -- 1-2 sentence overall synthesis
    blind_spots TEXT[],                 -- collective blind spots
    conflicts TEXT[],                   -- cross-cluster conflicts
    sections_de TEXT,                   -- cached DE translation
    synthesis_de TEXT,
    blind_spots_de TEXT[],
    conflicts_de TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(entity_type, entity_id)
);

CREATE INDEX IF NOT EXISTS idx_entity_analyses_entity
    ON entity_analyses(entity_type, entity_id);
