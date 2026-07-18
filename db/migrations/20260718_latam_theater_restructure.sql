-- latam_hemispheric_theater: greenfield restructure (FN_THEATER_BUILD_SPEC 0a, step 2).
--
-- Structural findings from Section 2a grounding:
--   * The theater's stated frame (US-China competition) missed the dominant
--     real cluster: EU-Mercosur market access, 261 titles vs ~45 each for the
--     China-access and US-pressure clusters. Classic "dominant theme with no
--     home" defect -> add an atomic, re-scope the theater.
--   * Infrastructure and minerals are one phenomenon ("China buys access, US
--     objects"), split across 26 and 19 titles -> merge.
--
-- Id renames are safe to do as plain UPDATEs here: narratives_v2,
-- event_friction_nodes, fn_asset_evidence and taxonomy_v3 all hold ZERO rows
-- for these ids (verified pre-migration). Only member_fn_ids arrays reference
-- them. Per FN_ID_NAMING.md the copy->repoint->delete dance is unnecessary
-- when there are no children.
--
-- Centroid design: participants are the three South American centroids ONLY.
-- AMERICAS-USA is deliberately NOT a participant -- it would admit all 134k US
-- titles through the participant gate and blind the alias auditor (the
-- venezuela_theater lesson). US/China/EU co-tag naturally via title text.
-- Because the participant set IS the subject set, the participant gate already
-- does the work of primary_target, so primary_target stays null on all three
-- and domain verbs (tariff, sanction, quota) remain safe.

BEGIN;

-- 1. Merge minerals into a single China-access atomic, and rename to match.
UPDATE friction_nodes
SET id = 'latam_china_access',
    name_en = 'Chinese infrastructure and resource access',
    centroid_ids = ARRAY['AMERICAS-BRAZIL', 'AMERICAS-SOUTHERNCONE', 'AMERICAS-ANDEAN'],
    primary_target = NULL,
    updated_at = now()
WHERE id = 'latam_infrastructure_influence';

UPDATE friction_nodes
SET is_active = false,
    updated_at = now()
WHERE id = 'latam_lithium_minerals';

-- 2. Re-scope the trade atomic from "US-China trade competition" to US pressure.
UPDATE friction_nodes
SET id = 'latam_us_trade_pressure',
    name_en = 'US tariff and sanctions pressure',
    centroid_ids = ARRAY['AMERICAS-BRAZIL', 'AMERICAS-SOUTHERNCONE', 'AMERICAS-ANDEAN'],
    primary_target = NULL,
    updated_at = now()
WHERE id = 'latam_trade_dependence';

-- 3. New atomic for the dominant cluster.
INSERT INTO friction_nodes (id, name_en, fn_type, scope, centroid_ids, primary_target, is_active, display_order)
VALUES (
    'latam_eu_market_access',
    'EU-Mercosur market access',
    'atomic',
    'regional',
    ARRAY['AMERICAS-BRAZIL', 'AMERICAS-SOUTHERNCONE', 'AMERICAS-ANDEAN'],
    NULL,
    true,
    3
)
ON CONFLICT (id) DO NOTHING;

-- 4. Re-scope the theater. AMERICAS-BRAZIL leads centroid_ids because
--    getAllFrictionNodesByRegion routes on centroid_ids[0] -- AMERICAS-USA in
--    that slot filed this theater under North America.
UPDATE friction_nodes
SET name_en = 'External powers in Latin America',
    centroid_ids = ARRAY[
        'AMERICAS-BRAZIL',
        'AMERICAS-SOUTHERNCONE',
        'AMERICAS-ANDEAN',
        'AMERICAS-USA',
        'ASIA-CHINA',
        'NON-STATE-EU'
    ],
    member_fn_ids = ARRAY[
        'latam_china_access',
        'latam_us_trade_pressure',
        'latam_eu_market_access'
    ],
    primary_target = NULL,
    updated_at = now()
WHERE id = 'latam_hemispheric_theater';

-- 5. Patch the retired latam_theater's stale array so it holds no dangling ids.
UPDATE friction_nodes
SET member_fn_ids = array_remove(
        array_remove(
            array_remove(member_fn_ids, 'latam_infrastructure_influence'),
            'latam_trade_dependence'),
        'latam_lithium_minerals'),
    updated_at = now()
WHERE id = 'latam_theater';

COMMIT;
