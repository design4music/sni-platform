-- Per-(centroid, track, month, locale) pre-computed CalendarMonthView for
-- the CTM page (/c/[id]/t/[track]) and its day-canonical sub-route
-- (/c/[id]/t/[track]/[date]). Replaces the multi-query getCalendarMonthView
-- path that ran per request; daemon worker materializes once per 12h
-- (skipping frozen months that already have a row).
--
-- Stored shape (JSONB) mirrors the TypeScript CalendarMonthView interface:
-- activity_stripe[] + days[] (with capped clusters[]) + scope + nav.
-- Top-20-clusters-per-day cap is enforced in the materializer so it
-- can't drift the way the pipeline-side promotion did.

CREATE TABLE IF NOT EXISTS mv_calendar_month_view (
    centroid_id TEXT        NOT NULL,
    track       TEXT        NOT NULL,
    month       DATE        NOT NULL,
    locale      TEXT        NOT NULL CHECK (locale IN ('en', 'de')),
    view        JSONB       NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (centroid_id, track, month, locale)
);
