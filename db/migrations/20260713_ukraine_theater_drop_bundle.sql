-- Ukraine theater: drop fn_anchor bundle + stale title attributions (2026-07-13)
--
-- Per FN_THEATER_BUILD_SPEC.md a theater carries NO fn_anchor bundle and never
-- participates in matching -- it is a pure roll-up of its atomics. Today the
-- theater has a bundle (10 langs) and its 3 coalition narratives claim RESIDUAL
-- titles that atomics didn't take. We invert this: the theater's coalition
-- cards now source their sample titles at query time FROM the member atomics
-- (getFrictionNodeView theater branch), so the theater must stop matching.
--
-- After this migration:
--   * the daemon's fn_refresh no-ops the bundle-less theater (link_titles
--     guard: no aliases -> 0 rows), so nothing re-creates these attributions.
--   * theater narrative rows remain in narratives_v2 (publishers/stance/claim);
--     only their title_narratives are removed.
-- Idempotent: DELETEs are naturally re-runnable.

BEGIN;

-- 1. Remove the theater's fn_anchor bundle (all languages).
DELETE FROM taxonomy_v3
 WHERE taxonomy_function = 'fn_anchor'
   AND linked_id = 'ukraine_war_theater';

-- 2. Remove stale title attributions for the 3 theater narratives. These are
--    now sourced from member atomics at query time and would otherwise show
--    doubled / stale counts. (No ON DELETE CASCADE children on
--    title_narratives -- this is a leaf link table.)
DELETE FROM title_narratives
 WHERE narrative_id IN (
   SELECT id FROM narratives_v2 WHERE fn_id = 'ukraine_war_theater'
 );

COMMIT;
