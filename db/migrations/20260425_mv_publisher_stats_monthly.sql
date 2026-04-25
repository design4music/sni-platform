-- Per-(outlet, month) publisher analytics. Same JSONB shape as the lifetime
-- mv_publisher_stats (see 20260310_create_mv_publisher_stats.sql) but
-- restricted to titles published within the named month.
--
-- Drops the lifetime-only fields that don't make sense per month:
--   - dow_distribution / peak_hour: structural, kept aggregate-only
--   - narrative_frame_count: retired (D-071)
--
-- The remaining fields all become more interesting when month-scoped:
-- top_actors and top_centroids show monthly editorial focus, geo_hhi
-- shows whether the outlet's coverage was concentrated or spread out
-- in that month, etc.

CREATE TABLE IF NOT EXISTS mv_publisher_stats_monthly (
    feed_name   TEXT        NOT NULL,
    month       DATE        NOT NULL,
    stats       JSONB       NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (feed_name, month)
);

CREATE INDEX IF NOT EXISTS idx_mv_publisher_stats_monthly_month
    ON mv_publisher_stats_monthly (month, feed_name);

COMMENT ON TABLE mv_publisher_stats_monthly IS
    'Per-(outlet, month) publisher analytics. Backed by '
    'pipeline/phase_4/materialize_publisher_stats_monthly.py. Refreshed '
    'monthly via freeze + daily for the current month (same cadence as '
    'outlet_entity_stance, D-071).';
