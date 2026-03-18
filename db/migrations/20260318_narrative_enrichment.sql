-- Narrative enrichment: tier, matching guidance, clustering, weekly activity
-- 2026-03-18

BEGIN;

-- Enrich strategic_narratives
ALTER TABLE strategic_narratives ADD COLUMN IF NOT EXISTS tier TEXT DEFAULT 'operational';
ALTER TABLE strategic_narratives ADD COLUMN IF NOT EXISTS matching_guidance TEXT;
ALTER TABLE strategic_narratives ADD COLUMN IF NOT EXISTS aligned_with TEXT[];
ALTER TABLE strategic_narratives ADD COLUMN IF NOT EXISTS opposes TEXT[];
ALTER TABLE strategic_narratives ADD COLUMN IF NOT EXISTS example_event_ids UUID[];

-- Weekly activity (incremental, never recomputed from scratch)
CREATE TABLE IF NOT EXISTS narrative_weekly_activity (
    narrative_id TEXT NOT NULL REFERENCES strategic_narratives(id) ON DELETE CASCADE,
    week TEXT NOT NULL,
    event_count INT DEFAULT 0,
    PRIMARY KEY (narrative_id, week)
);

CREATE INDEX IF NOT EXISTS idx_nwa_week ON narrative_weekly_activity(week);

COMMIT;
