-- Centroid baseline metrics + deviation detection per week
CREATE TABLE IF NOT EXISTS mv_centroid_baselines (
    centroid_id TEXT NOT NULL,
    week DATE NOT NULL,
    metrics JSONB NOT NULL DEFAULT '{}',
    deviations JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (centroid_id, week)
);
