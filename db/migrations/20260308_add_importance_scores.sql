-- Add importance scoring columns to title_labels and events_v3
-- 2026-03-08: Support event importance scoring system

-- Title-level importance (computed after Phase 3.1)
ALTER TABLE title_labels ADD COLUMN IF NOT EXISTS importance_score FLOAT;
ALTER TABLE title_labels ADD COLUMN IF NOT EXISTS importance_components JSONB;

-- Event-level importance (computed after Phase 4)
ALTER TABLE events_v3 ADD COLUMN IF NOT EXISTS importance_score FLOAT;
ALTER TABLE events_v3 ADD COLUMN IF NOT EXISTS importance_components JSONB;

-- Index for sorting/filtering by importance
CREATE INDEX IF NOT EXISTS idx_events_v3_importance ON events_v3(importance_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_title_labels_importance ON title_labels(importance_score DESC NULLS LAST);
