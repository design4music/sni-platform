-- Cross-centroid epics: stories that span multiple centroids detected from bridge tag co-occurrence

BEGIN;

CREATE TABLE IF NOT EXISTS epics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug TEXT UNIQUE NOT NULL,
    month DATE NOT NULL,
    title TEXT,
    summary TEXT,
    anchor_tags TEXT[] NOT NULL,
    centroid_count INTEGER NOT NULL,
    event_count INTEGER NOT NULL,
    total_sources INTEGER NOT NULL,
    timeline TEXT,
    narratives JSONB,
    centroid_summaries JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_epics_month ON epics(month DESC);
CREATE INDEX IF NOT EXISTS idx_epics_anchor_tags ON epics USING GIN(anchor_tags);

COMMENT ON TABLE epics IS 'Cross-centroid stories detected from bridge tag co-occurrence';
COMMENT ON COLUMN epics.anchor_tags IS 'Bridge tags that define this epic cluster';
COMMENT ON COLUMN epics.month IS 'The CTM month this epic belongs to';

CREATE TABLE IF NOT EXISTS epic_events (
    epic_id UUID REFERENCES epics(id) ON DELETE CASCADE,
    event_id UUID REFERENCES events_v3(id) ON DELETE CASCADE,
    is_included BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (epic_id, event_id)
);

CREATE INDEX IF NOT EXISTS idx_epic_events_epic ON epic_events(epic_id);
CREATE INDEX IF NOT EXISTS idx_epic_events_event ON epic_events(event_id);

COMMIT;
