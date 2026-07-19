-- Panama canal theater -> folded into latam_hemispheric_theater (2026-07-19)
--
-- Structural re-assessment (FN_THEATER_BUILD_SPEC.md 2a) found:
--   * panama_canal_transit_security has NO independent corpus -- every
--     canal-transit title is either the same ports fight or Hormuz-war
--     commodity reporting (a section-3 DROP class). Not an atomic.
--   * The escalation's centre of gravity -- China's maritime coercion
--     (vessel detentions, "port state control inspections", ordering
--     Maersk/MSC out, the Cosco walkout) -- had no home in either draft.
--   * One phenomenon left => section 1a says do not nest it under its own
--     theater. It belongs on latam_hemispheric_theater ("External powers
--     in Latin America"), whose axis is exactly this.
--   * Scoped by phenomenon, not by place (the latam carve rule): Peru's
--     Chancay is the same story and is the live one -- Panama ports went
--     to zero in May while Chancay ran through June.
--
-- Centroid fixes: ASIA-HONGKONG sits on 30 of 115 Panama titles (every
-- Hutchison story) and was absent everywhere; AMERICAS-CENTRAL was missing
-- from the hemispheric theater.

BEGIN;

-- 1. Retire the Panama theater and both draft atomics (rows kept).
UPDATE friction_nodes
SET is_active = false, updated_at = NOW()
WHERE id IN ('panama_canal_theater', 'panama_ports_dispute', 'panama_canal_transit_security');

-- 2. New atomic under the hemispheric theater.
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope, is_active, display_order,
    centroid_ids, primary_target, affected_asset_ids
) VALUES (
    'latam_port_infrastructure_control',
    'Control of strategic port infrastructure',
    'Kontrolle strategischer Hafeninfrastruktur',
    'atomic', 'regional', true, 106,
    ARRAY['AMERICAS-CENTRAL', 'AMERICAS-ANDEAN', 'AMERICAS-USA', 'ASIA-CHINA', 'ASIA-HONGKONG'],
    NULL,                       -- multilateral: action runs in both directions
    ARRAY[]::text[]
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = true,
    updated_at = NOW();

-- 3. Hemispheric theater: add the new member, widen the centroid gate,
--    and inherit the canal assets so they stay on the conflicts map.
UPDATE friction_nodes
SET member_fn_ids = ARRAY['latam_resource_access', 'latam_us_trade_pressure',
                          'latam_eu_market_access', 'latam_port_infrastructure_control'],
    centroid_ids = ARRAY['AMERICAS-BRAZIL', 'AMERICAS-SOUTHERNCONE', 'AMERICAS-ANDEAN',
                         'AMERICAS-CENTRAL', 'AMERICAS-USA', 'ASIA-CHINA',
                         'ASIA-HONGKONG', 'NON-STATE-EU'],
    affected_asset_ids = ARRAY['atacama_lithium_triangle', 'salar_de_uyuni_lithium',
                               'chilean_copper_belt', 'southern_peru_copper_belt',
                               'panama_canal', 'colon_port'],
    updated_at = NOW()
WHERE id = 'latam_hemispheric_theater';

COMMIT;
