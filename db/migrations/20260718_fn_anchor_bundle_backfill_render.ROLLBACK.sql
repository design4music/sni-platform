-- ROLLBACK for 20260718_fn_anchor_bundle_backfill_render.sql
--
-- DESTRUCTIVE. Removes the 22 fn_anchor bundles that file inserted and
-- reactivates the russia_sanctions_economy bundle it deactivated.
--
-- Only meaningful if the bundles were genuinely ABSENT on Render beforehand
-- (verified 2026-07-18). If a bundle already existed and the upsert merely
-- refreshed its aliases, this delete removes the pre-existing row too --
-- re-check before running.
--
-- taxonomy_v3.linked_id has no FK, so nothing cascades. But note: if the batch
-- bootstrap has since run on Render, deleting a bundle does NOT remove the
-- event_friction_nodes rows it produced; those become stale until re-bootstrapped.

BEGIN;

DO $$
DECLARE n int;
BEGIN
    SELECT count(*) INTO n FROM event_friction_nodes
    WHERE fn_id IN ('alberta_separatism_us_ties','aukus_alliance_reliability',
      'australia_china_trade_leverage','balochistan_insurgency','canada_sovereignty_pressure',
      'china_threat_assessment','essequibo_dispute','india_pakistan_militancy','indus_water_sharing',
      'kashmir_dispute','latam_eu_market_access','latam_resource_access','latam_us_trade_pressure',
      'myanmar_civil_conflict','pacific_island_contest','pakistan_afghanistan_border',
      'thailand_cambodia_border','us_canada_trade_coercion','us_venezuela_relations',
      'venezuela_political_transition','venezuela_sanctions_oil','us_russia_arms_control');
    IF n > 0 THEN
        RAISE WARNING 'NOTE: % event_friction_nodes rows already exist for these FNs. Removing the bundles leaves that attribution stale until re-bootstrapped.', n;
    END IF;
END $$;

DELETE FROM taxonomy_v3
WHERE taxonomy_function = 'fn_anchor'
  AND linked_id IN ('alberta_separatism_us_ties','aukus_alliance_reliability',
    'australia_china_trade_leverage','balochistan_insurgency','canada_sovereignty_pressure',
    'china_threat_assessment','essequibo_dispute','india_pakistan_militancy','indus_water_sharing',
    'kashmir_dispute','latam_eu_market_access','latam_resource_access','latam_us_trade_pressure',
    'myanmar_civil_conflict','pacific_island_contest','pakistan_afghanistan_border',
    'thailand_cambodia_border','us_canada_trade_coercion','us_venezuela_relations',
    'venezuela_political_transition','venezuela_sanctions_oil','us_russia_arms_control');

UPDATE taxonomy_v3 SET is_active = true, updated_at = now()
WHERE taxonomy_function = 'fn_anchor' AND linked_id = 'russia_sanctions_economy';

COMMIT;
