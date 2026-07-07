-- Systematic affected_asset_ids backfill across the theaters that didn't
-- get individual attention in the earlier wiring/Iran passes. Applies the
-- D-090 mechanism framework (home territory / demonstrated reach / named
-- economic lever) per theater, not a blanket centroid-intersection query.
--
-- Two real bugs found and fixed:
-- - japan_china_theater was wired to taiwan_strait + tsmc_hsinchu -- Taiwan
--   assets on a Japan-China (Senkaku/East China Sea) theater, evidently a
--   copy-paste from taiwan_strait_theater/us_china_theater. Cleared; no
--   Japan-China-specific registry asset exists yet (Senkaku/ECS itself has
--   no economic installation), so this theater is correctly empty for now.
-- - sahel_theater carried guinea_bauxite_belt despite Guinea not being one
--   of its centroids at all (centroid_ids = Sahel, Nigeria, France, USA,
--   Russia). Replaced with niger_delta_basin -- Nigeria IS a listed
--   centroid and is genuine home territory for this theater's jihadist-
--   spillover-into-Nigeria and oil-funded-security-response dynamics.
--
-- Additions (mechanism 1, home territory, evidenced per-theater judgment,
-- not a mechanical scan of every asset in every listed centroid):
-- - arctic_theater: Norwegian Arctic gas (Hammerfest/Melkoya LNG,
--   Norwegian Shelf field) -- genuinely Arctic geography, unlike e.g.
--   Athabasca which is sub-Arctic Canada and was deliberately NOT added.
-- - australia_china_theater: Australian wheat belt -- the actual
--   commodity China imposed tariffs on in the 2020-21 trade coercion
--   episode (iron ore/lithium were never targeted; China needs them too
--   much -- kept as already-wired but not re-justified here).
-- - caucasus_theater: Shah Deniz field -- Azerbaijan's flagship gas field,
--   home territory alongside the existing BTC pipeline.
-- - great_lakes_theater: Bisie tin mine -- North Kivu, DRC, directly in
--   the M23 conflict zone (more on-point than Katanga, which is southern
--   DRC and less directly conflict-affected; both now wired).
-- - horn_africa_theater: GERD -- the literal central asset of the
--   Ethiopia-Egypt-Sudan water dispute atomic; should have been here from
--   the start.
-- - india_pakistan_theater: Tarbela Dam -- on the Indus, the central asset
--   of the indus_water_sharing atomic.
-- - taiwan_strait_theater: TSMC Fab 18/Tainan -- Taiwan's most advanced
--   node, alongside the existing Hsinchu fab.
-- - us_china_theater: SMIC Shanghai -- the direct target of US
--   semiconductor export controls (named economic lever, D-090
--   mechanism 3), more on-point than Malacca for the tech-restriction
--   atomics specifically.
--
-- Left unchanged / confirmed correctly empty (institutional, domestic-
-- politics, or territorial disputes with no economic installation at the
-- actual contested location): balkan_theater, cuba_theater,
-- eu_cohesion_theater, europe_sovereignty_theater, haiti_theater,
-- india_china_theater, syria_theater, us_domestic_theater.

UPDATE friction_nodes SET affected_asset_ids = ARRAY['northern_sea_route','hammerfest_melkoya_lng','norwegian_shelf_gas'], updated_at = now() WHERE id = 'arctic_theater';
UPDATE friction_nodes SET affected_asset_ids = ARRAY['pilbara_iron_belt','australian_lithium_belt','australian_wheat_belt'], updated_at = now() WHERE id = 'australia_china_theater';
UPDATE friction_nodes SET affected_asset_ids = ARRAY['btc_pipeline','shah_deniz_field'], updated_at = now() WHERE id = 'caucasus_theater';
UPDATE friction_nodes SET affected_asset_ids = ARRAY['katanga_copper_belt','bisie_tin_mine'], updated_at = now() WHERE id = 'great_lakes_theater';
UPDATE friction_nodes SET affected_asset_ids = ARRAY['bab_el_mandeb','gerd_dam'], updated_at = now() WHERE id = 'horn_africa_theater';
UPDATE friction_nodes SET affected_asset_ids = ARRAY['tarbela_dam'], updated_at = now() WHERE id = 'india_pakistan_theater';
UPDATE friction_nodes SET affected_asset_ids = ARRAY[]::text[], updated_at = now() WHERE id = 'japan_china_theater';
UPDATE friction_nodes SET affected_asset_ids = ARRAY['niger_delta_basin'], updated_at = now() WHERE id = 'sahel_theater';
UPDATE friction_nodes SET affected_asset_ids = ARRAY['taiwan_strait','tsmc_hsinchu','tsmc_fab18_tainan'], updated_at = now() WHERE id = 'taiwan_strait_theater';
UPDATE friction_nodes SET affected_asset_ids = ARRAY['taiwan_strait','tsmc_hsinchu','strait_of_malacca','smic_shanghai'], updated_at = now() WHERE id = 'us_china_theater';
