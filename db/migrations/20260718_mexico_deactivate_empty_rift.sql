-- cartel_us_culpability_rift attributed 0 titles: the Russian/Chinese bloc
-- does not push a cartel-specific US-culpability line in this corpus (their
-- Mexico coverage is China-Mexico trade + Cuba solidarity). Deactivate the
-- empty atomic card; the theater rift roll-up is served by anti_hegemony_rift.
-- LOCAL 2026-07-18. Reversible.
BEGIN;
UPDATE narratives_v2 SET is_active = false, updated_at = now()
WHERE id = 'cartel_us_culpability_rift';
COMMIT;
