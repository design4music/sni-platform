-- Per-centroid coverage stats — replaces inline SUM(events_v3.source_batch_count)
-- aggregations in getCentroidsByTheater and getCentroidsByClass that ran on every
-- /region/* and homepage request. Refreshed by
-- pipeline/phase_4/materialize_centroid_stats.py on a 12h staleness gate.

CREATE TABLE IF NOT EXISTS mv_centroid_stats (
    centroid_id          TEXT        PRIMARY KEY,
    source_count         INT         NOT NULL DEFAULT 0,  -- all-time
    month_source_count   INT         NOT NULL DEFAULT 0,  -- current calendar month
    last_article_date    DATE,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
