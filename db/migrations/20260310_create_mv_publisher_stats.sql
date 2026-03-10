-- Materialized publisher analytics: pre-computed stats per feed.
-- Populated by pipeline/phase_4/materialize_publisher_stats.py

CREATE TABLE IF NOT EXISTS mv_publisher_stats (
  feed_name         TEXT PRIMARY KEY,
  stats             JSONB NOT NULL DEFAULT '{}',
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE mv_publisher_stats IS 'Pre-computed publisher analytics (track distribution, geographic focus, actor frequency, etc.)';
