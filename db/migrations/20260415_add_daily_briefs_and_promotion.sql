-- Phase 4.5-day: daily brief + cluster promotion (day-centric frontend)
-- Date: 2026-04-15
-- Adds:
--   1. events_v3.is_promoted boolean (top-N per day get LLM treatment + frontend visibility)
--   2. daily_briefs table (one row per (ctm_id, date) with LLM-generated thematic brief)

BEGIN;

-- 1. Promotion flag on events
ALTER TABLE events_v3
    ADD COLUMN IF NOT EXISTS is_promoted boolean NOT NULL DEFAULT false;

CREATE INDEX IF NOT EXISTS idx_events_v3_ctm_date_promoted
    ON events_v3 (ctm_id, date, is_promoted)
    WHERE is_promoted = true;

-- 2. Daily briefs
CREATE TABLE IF NOT EXISTS daily_briefs (
    ctm_id                  uuid NOT NULL REFERENCES ctm(id) ON DELETE CASCADE,
    date                    date NOT NULL,
    brief_en                text NOT NULL,
    brief_de                text,
    promoted_cluster_count  integer NOT NULL,
    coherent                boolean NOT NULL DEFAULT true,
    generated_at            timestamptz NOT NULL DEFAULT NOW(),
    PRIMARY KEY (ctm_id, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_briefs_date
    ON daily_briefs (date);

COMMIT;

-- Addendum 2026-04-16: day-level thematic labels (mechanical, computed from title_labels)
ALTER TABLE daily_briefs ADD COLUMN IF NOT EXISTS themes jsonb;
COMMENT ON COLUMN daily_briefs.themes IS 'Top sector/subject pairs with normalized weights, computed from promoted cluster title_labels';
