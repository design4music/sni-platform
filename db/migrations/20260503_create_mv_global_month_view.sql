-- Per-(month, locale) pre-computed GlobalMonthView for the trending page
-- (/trending). Replaces the multi-query getGlobalMonthView path that ran
-- per request — 5 sub-queries aggregating across ALL centroids in the
-- month. Daemon worker materializes once per 12h (skipping frozen
-- months that already have a row).
--
-- Stored shape (JSONB) mirrors the TypeScript GlobalMonthView interface
-- PLUS active_narratives folded in (was a separate query — getActive
-- NarrativesGlobal — folded into this blob for past-month efficiency).

CREATE TABLE IF NOT EXISTS mv_global_month_view (
    month       DATE        NOT NULL,
    locale      TEXT        NOT NULL CHECK (locale IN ('en', 'de')),
    view        JSONB       NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (month, locale)
);
