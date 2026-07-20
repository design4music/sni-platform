-- Balkan theater: structural re-scope (spec FN_THEATER_BUILD_SPEC.md sec 2a)
-- 2026-07-20. LOCAL first; Render promotion is a separate authorized step.
--
-- Grounding (180d, EUROPE-BALKANS, 2001 titles):
--   * serbia_kosovo_tensions premise is spent: dialogue/KFOR/normalisation 23
--     titles, north Kosovo/Mitrovica/Banjska 3, Kosovo co-mentioned with Serbia
--     30. Kosovo's live coverage (138 of 168) is its own presidential deadlock,
--     not the Belgrade status dispute.
--   * bosnia_fragmentation premise inverted: Bosnia 46 titles total, Dodik 13,
--     Republika Srpska 5, High Representative/OHR 2. The secession phase ended;
--     what remains is external patronage, absorbed by balkan_foreign_capital.
--   * Two dominant themes had no home anywhere in the system:
--     Serbia's legitimacy crisis (Vucic/SNS 434, protests 139, resignation 36;
--     549 titles across 64 publishers, 224 non-local) and foreign capital vs
--     sovereignty (Kushner/Trump-linked resort 115 + Bosnia pipeline investors).
--   * Serbia's energy leverage (NIS/Gazprom/pipeline sabotage, 156) is folded
--     into the Serbia atomic by explicit decision, not split out.
--
-- Both retained atomics gate on the single EUROPE-BALKANS centroid, which makes
-- moderately generic domain vocabulary safe (cf. taiwan_strait single-centroid
-- lesson). No SERBIA centroid exists, so primary_target stays null on both and
-- precision comes from the bundle (archetype A2, anchor == subject).

BEGIN;

-- 1. Retire the two stale atomics. Deactivate, never delete: event_friction_nodes
--    has ON DELETE CASCADE (incident 2026-07-07).
UPDATE friction_nodes SET is_active = false, updated_at = NOW()
WHERE id IN ('serbia_kosovo_tensions', 'bosnia_fragmentation');

-- 2. Serbia's contested government (incl. external energy leverage).
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope, centroid_ids, primary_target,
    affected_asset_ids, is_active, display_order, created_at, updated_at
) VALUES (
    'serbia_government_legitimacy',
    'Serbia''s contested government',
    'Serbiens umstrittene Regierung',
    'atomic', 'regional', ARRAY['EUROPE-BALKANS'], NULL,
    ARRAY[]::text[], true, 1, NOW(), NOW()
) ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en, name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids, primary_target = EXCLUDED.primary_target,
    is_active = true, updated_at = NOW();

-- 3. Foreign capital and sovereignty (Albania resort, Bosnia investor deals).
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope, centroid_ids, primary_target,
    affected_asset_ids, is_active, display_order, created_at, updated_at
) VALUES (
    'balkan_foreign_capital',
    'Foreign capital and sovereignty',
    'Auslandskapital und Souveränität',
    'atomic', 'regional', ARRAY['EUROPE-BALKANS'], NULL,
    ARRAY[]::text[], true, 2, NOW(), NOW()
) ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en, name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids, primary_target = EXCLUDED.primary_target,
    is_active = true, updated_at = NOW();

-- 4. Re-point the aggregator at the surviving members.
UPDATE friction_nodes
SET member_fn_ids = ARRAY['serbia_government_legitimacy', 'balkan_foreign_capital'],
    name_en = 'Western Balkans political contest',
    name_de = 'Politischer Wettstreit im Westbalkan',
    updated_at = NOW()
WHERE id = 'balkan_theater';

-- 5. Romania is NOT Balkan terrain: it sits in EUROPE-BALKANS-EAST (BG/RO/MD),
--    which shares only 28 titles with EUROPE-BALKANS. The 2024-25 election
--    annulment story is outside the corpus window (Georgescu 1, Simion 1,
--    annulment 5, TikTok/disinformation 8). Romania's live coverage is Russian
--    drone spillover (drone 227, Black Sea 151) -- a centroid gap in the
--    Russia-Europe atomics, which list Baltic/Visegrad/Nordic but omit the
--    Eastern Balkans despite Romania being a front-line incursion victim.
UPDATE friction_nodes
SET centroid_ids = array_append(centroid_ids, 'EUROPE-BALKANS-EAST'),
    updated_at = NOW()
WHERE id IN (
    'russia_airspace_incursions',
    'russia_nato_deterrence',
    'russia_hybrid_warfare',
    'russia_europe_theater'
)
AND NOT (centroid_ids && ARRAY['EUROPE-BALKANS-EAST']);

COMMIT;
