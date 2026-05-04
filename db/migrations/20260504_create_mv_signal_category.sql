-- Per-(signal_type, period) pre-computed view for /signals/[type] AND
-- the /signals heatmap (which derives from the top 3 of each category).
-- Replaces 2 live queries:
--   - getSignalHeatmap         (top signals across all 7 types + sparklines)
--   - getSignalCategoryDetail  (top 25 per type + sparklines + contexts)
--
-- Stored shape (JSONB):
--   {
--     entries: SignalCategoryEntry[]   // top 25 of this type with weekly + context
--   }
--
-- 7 rows total (period='rolling' for now; per-month variants if ever needed).
-- Refresh 12h, no frozen-skip (rolling 30d window).

CREATE TABLE IF NOT EXISTS mv_signal_category (
    signal_type TEXT        NOT NULL,
    period      TEXT        NOT NULL DEFAULT 'rolling',
    view        JSONB       NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (signal_type, period)
);
