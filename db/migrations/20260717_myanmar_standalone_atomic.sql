-- Myanmar: collapse theater -> single standalone atomic (FN_THEATER_BUILD_SPEC 1a).
--
-- Decision (user, 2026-07-17): Myanmar is a remote, low-impact, thinly-covered
-- regional conflict with no superpower principal. It earns one recognizable dot
-- on the global map, not a drill-down theater. The structural assessment already
-- showed the two-atomic split doesn't pay: legitimation is a healthy ~99-title
-- atomic but transnational-crime is only ~13 cleanly-separable titles (the rest
-- can't be split from Cambodia's larger scam story without a Myanmar centroid the
-- taxonomy lacks). So fold everything into one atomic and retire the theater.
--
-- End state: myanmar_civil_conflict is a standalone atomic (no active theater),
-- rendered by getAllFrictionNodesByRegion as a standalone zone and UNION'd into
-- the conflicts-map query. Per 1a it must carry its OWN anchor_point +
-- affected_asset_ids or it vanishes from the map -- moved here from the theater.
-- Crime + China patronage survive as NARRATIVES on this atomic, not as zones.

BEGIN;

-- 1. Rename the survivor to a whole-Myanmar identity and take over the map wiring.
--    (Was myanmar_military_rule -> myanmar_regime_legitimation in the structure
--    migration; now broadened again. FK rule is NO ACTION but this id has zero
--    referencing rows -- no bundle, no narratives, no event/asset-evidence links
--    yet -- so the rename cannot orphan anything.)
UPDATE friction_nodes
SET id                 = 'myanmar_civil_conflict',
    name_en            = 'Myanmar civil conflict',
    fn_type            = 'atomic',
    is_active          = TRUE,
    centroid_ids       = ARRAY['ASIA-SOUTHEAST', 'ASIA-SOUTHASIA', 'ASIA-CHINA'],
    primary_target     = NULL,
    anchor_point       = '{"type":"Point","coordinates":[95.5,21.5]}'::jsonb,
    affected_asset_ids = ARRAY['kachin_rare_earth_zone'],
    display_order      = 1,
    updated_at         = now()
WHERE id = 'myanmar_regime_legitimation';

-- 2. Retire the theater and the crime atomic. Deactivate, never DELETE: every FK
--    to friction_nodes is ON DELETE CASCADE (2026-07-07 incident). Deactivating
--    the theater is what orphans the atomic into standalone rendering (1a).
UPDATE friction_nodes
SET is_active = FALSE, member_fn_ids = NULL, updated_at = now()
WHERE id = 'myanmar_theater';

UPDATE friction_nodes
SET is_active = FALSE, updated_at = now()
WHERE id = 'myanmar_transnational_crime';

COMMIT;
