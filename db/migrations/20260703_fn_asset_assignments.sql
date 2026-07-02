-- Assign affected_asset_ids + scope for the 28 existing friction_node
-- theaters, linking each theater to the strategic_assets it credibly
-- puts under stress (see 20260703_seed_strategic_assets.sql for asset ids).
-- Plain UPDATEs by primary key: safe to re-run.

-- Global theaters: bilateral/systemic rivalries, relationships not places.
-- scope = 'global' controls map rendering only; assets may still be listed
-- where the rivalry has concrete physical flashpoints.

UPDATE friction_nodes SET affected_asset_ids = '{}', scope = 'global' WHERE id = 'us_russia_theater';
UPDATE friction_nodes SET affected_asset_ids = '{taiwan_strait,tsmc_hsinchu,strait_of_malacca}', scope = 'global' WHERE id = 'us_china_theater';
UPDATE friction_nodes SET affected_asset_ids = '{}', scope = 'global' WHERE id = 'us_domestic_theater';
UPDATE friction_nodes SET affected_asset_ids = '{}', scope = 'global' WHERE id = 'eu_cohesion_theater';
UPDATE friction_nodes SET affected_asset_ids = '{}', scope = 'global' WHERE id = 'europe_us_theater';
UPDATE friction_nodes SET affected_asset_ids = '{}', scope = 'global' WHERE id = 'europe_sovereignty_theater';

-- Regional theaters: places with concrete geometry on the map.

UPDATE friction_nodes SET affected_asset_ids = '{ukrainian_grain_belt,odesa_port,novorossiysk_port,druzhba_pipeline_west,turkish_straits}', scope = 'regional' WHERE id = 'ukraine_war_theater';
UPDATE friction_nodes SET affected_asset_ids = '{bab_el_mandeb,suez_canal}', scope = 'regional' WHERE id = 'israel_theater';
UPDATE friction_nodes SET affected_asset_ids = '{northern_sea_route}', scope = 'regional' WHERE id = 'arctic_theater';
UPDATE friction_nodes SET affected_asset_ids = '{}', scope = 'regional' WHERE id = 'india_pakistan_theater';
UPDATE friction_nodes SET affected_asset_ids = '{druzhba_pipeline_west,turkstream,danish_straits}', scope = 'regional' WHERE id = 'russia_europe_theater';
UPDATE friction_nodes SET affected_asset_ids = '{}', scope = 'regional' WHERE id = 'india_china_theater';
UPDATE friction_nodes SET affected_asset_ids = '{taiwan_strait,tsmc_hsinchu}', scope = 'regional' WHERE id = 'japan_china_theater';
UPDATE friction_nodes SET affected_asset_ids = '{turkish_straits,btc_pipeline,turkstream}', scope = 'regional' WHERE id = 'turkey_theater';
UPDATE friction_nodes SET affected_asset_ids = '{}', scope = 'regional' WHERE id = 'syria_theater';
UPDATE friction_nodes SET affected_asset_ids = '{taiwan_strait,tsmc_hsinchu}', scope = 'regional' WHERE id = 'taiwan_strait_theater';
UPDATE friction_nodes SET affected_asset_ids = '{strait_of_malacca,port_of_singapore}', scope = 'regional' WHERE id = 'scs_theater';
UPDATE friction_nodes SET affected_asset_ids = '{}', scope = 'regional' WHERE id = 'myanmar_theater';
UPDATE friction_nodes SET affected_asset_ids = '{pilbara_iron_belt,australian_lithium_belt}', scope = 'regional' WHERE id = 'australia_china_theater';
UPDATE friction_nodes SET affected_asset_ids = '{}', scope = 'regional' WHERE id = 'korea_theater';
UPDATE friction_nodes SET affected_asset_ids = '{guinea_bauxite_belt}', scope = 'regional' WHERE id = 'sahel_theater';
UPDATE friction_nodes SET affected_asset_ids = '{bab_el_mandeb,suez_canal}', scope = 'regional' WHERE id = 'yemen_red_sea_theater';
UPDATE friction_nodes SET affected_asset_ids = '{panama_canal}', scope = 'regional' WHERE id = 'latam_theater';
UPDATE friction_nodes SET affected_asset_ids = '{katanga_copper_belt}', scope = 'regional' WHERE id = 'great_lakes_theater';
UPDATE friction_nodes SET affected_asset_ids = '{}', scope = 'regional' WHERE id = 'balkan_theater';
UPDATE friction_nodes SET affected_asset_ids = '{bab_el_mandeb}', scope = 'regional' WHERE id = 'horn_africa_theater';
UPDATE friction_nodes SET affected_asset_ids = '{btc_pipeline}', scope = 'regional' WHERE id = 'caucasus_theater';
UPDATE friction_nodes SET affected_asset_ids = '{strait_of_hormuz,ras_tanura,ghawar_field}', scope = 'regional' WHERE id = 'iran_theater';
