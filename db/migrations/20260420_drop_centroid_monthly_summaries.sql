-- 2026-04-20 - Drop legacy centroid_monthly_summaries table
--
-- Superseded by centroid_summaries (see 20260420_add_centroid_summaries.sql)
-- which holds both rolling_30d and monthly snapshots with bilingual tier-0 +
-- per-track JSONB payloads.
--
-- Writer removed from pipeline/freeze/freeze_month.py; readers removed from
-- apps/frontend/lib/queries.ts (getCentroidMonthlySummary deleted).

BEGIN;

DROP TABLE IF EXISTS centroid_monthly_summaries CASCADE;

COMMIT;
