-- Ukraine theater: consolidate affected_asset_ids onto the theater (2026-07-13)
--
-- The index map (app/api/friction-nodes-map/route.ts) reads affected_asset_ids
-- only for fn_type='theater' and ignores atomic asset links. So the 4 assets
-- that lived only on ukraine_infrastructure_war (ZNPP, Kerch Strait, Omsk
-- refinery, Primorsk/Ust-Luga terminals) never reached the map. Move all asset
-- links up to the theater (union with its existing 5) and clear the atomic, so
-- the full Ukraine asset set registers theater stress.
-- Idempotent: explicit target arrays, guarded by id.

BEGIN;

-- Theater: existing 5 + infra_war's 4 unique (novorossiysk_port,
-- druzhba_pipeline_west already present) = 9.
UPDATE friction_nodes SET affected_asset_ids = ARRAY[
    'ukrainian_grain_belt',
    'odesa_port',
    'novorossiysk_port',
    'druzhba_pipeline_west',
    'turkish_straits',
    'zaporizhzhia_npp',
    'kerch_strait',
    'omsk_refinery',
    'primorsk_ust_luga_terminals'
]
WHERE id = 'ukraine_war_theater';

-- Atomic: assets now live on the theater.
UPDATE friction_nodes SET affected_asset_ids = ARRAY[]::text[]
WHERE id = 'ukraine_infrastructure_war';

COMMIT;
