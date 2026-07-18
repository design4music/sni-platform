-- Cross-centroid sibling groups: same story appearing under different country centroids.
-- Events sharing a sibling_group UUID are the same real-world story viewed from different country lenses.

ALTER TABLE events_v3 ADD COLUMN IF NOT EXISTS sibling_group UUID;
CREATE INDEX IF NOT EXISTS idx_events_v3_sibling_group
    ON events_v3(sibling_group) WHERE sibling_group IS NOT NULL;
