-- Per-(centroid, month, locale) pre-computed CentroidMonthView for the
-- centroid page hero. Replaces the multi-query getCentroidMonthView path
-- that ran per request; daemon worker materializes once per 12h.
--
-- Stored shape (JSONB) mirrors the TypeScript CentroidMonthView interface:
--   { centroid_id, month, activity_stripe[], tracks[], prev_month, next_month }
-- Track-card top events are pre-deduped (title-Dice >= 0.3) on the worker
-- side so the frontend just reads + renders.

CREATE TABLE IF NOT EXISTS mv_centroid_month_view (
    centroid_id TEXT        NOT NULL,
    month       DATE        NOT NULL,
    locale      TEXT        NOT NULL CHECK (locale IN ('en', 'de')),
    view        JSONB       NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (centroid_id, month, locale)
);

-- Lookup index already covered by PK; no extra needed.
