-- Per-(signal_type, value, period) pre-computed view for
-- /signals/[type]/[value]. Replaces 2 live queries:
--   - getSignalStats           (total, weekly, geo, tracks)
--   - getRelationshipClusters  (5-stage CTE pipeline — by far the heaviest)
--
-- Stored shape (JSONB):
--   {
--     stats:    SignalDetailStats,
--     clusters: RelationshipCluster[]
--   }
--
-- Materialized only for the top-25 values per type (= what the category
-- page lists). Long-tail values are still reachable via the live query
-- fallback in the frontend helper. ~175 rows.
--
-- Refresh 12h, no frozen-skip.

CREATE TABLE IF NOT EXISTS mv_signal_detail (
    signal_type TEXT        NOT NULL,
    value       TEXT        NOT NULL,
    period      TEXT        NOT NULL DEFAULT 'rolling',
    view        JSONB       NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (signal_type, value, period)
);
