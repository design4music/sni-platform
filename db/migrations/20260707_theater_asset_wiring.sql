-- Theater asset wiring (item C) + participant trim (item D).
--
-- C: of 13 theaters with affected_asset_ids = {}, 4 get real registry
-- assets wired in; the other 9 stay empty BY DESIGN -- they are domestic-
-- politics, territorial-dispute, or institutional phenomena with no
-- direct economic installation in the registry (balkan, cuba,
-- eu_cohesion, europe_sovereignty, haiti, india_china, india_pakistan,
-- syria, us_domestic). An empty affected_asset_ids is a valid, reviewed
-- state, not an oversight.
--
-- D: Syria and Turkey theaters carried 15 centroids each (every country
-- that appears in commentary, not just actual participants). Trimmed to
-- the theaters' actual state actors per their member atomics, so
-- selection spokes stay readable (~6 max, matching other theaters).
-- Full participant history remains in each member atomic's own
-- centroid_ids; only the theater-level rollup is trimmed.

BEGIN;

-- C1: Korea -- rich in registry assets (asset_type facility/port cluster).
UPDATE friction_nodes SET
  affected_asset_ids = ARRAY['ulsan_industrial','kori_saeul_npp','samsung_pyeongtaek_hwaseong','sk_hynix_icheon','busan_port','incheon_pyeongtaek_lng'],
  updated_at = now()
WHERE id = 'korea_theater';

-- C2: Myanmar -- Kachin rare-earth zone is conflict-financed extraction,
-- a precise fit for myanmar_ethnic_conflicts / china_border_influence.
UPDATE friction_nodes SET
  affected_asset_ids = ARRAY['kachin_rare_earth_zone'],
  updated_at = now()
WHERE id = 'myanmar_theater';

-- C3: Europe-US -- the theater's four atomics (transatlantic trade,
-- Greenland, EU strategic autonomy, defence burden-sharing) map to the
-- transatlantic trade corridors, not a single installation.
UPDATE friction_nodes SET
  affected_asset_ids = ARRAY['lane_transatlantic','lane_us_europe_lng','lane_us_europe_energy'],
  updated_at = now()
WHERE id = 'europe_us_theater';

-- C4: US-Russia -- sanctions-target framing (Yamal/Novatek and West
-- Siberian production are direct US sanctions objects), distinct from
-- russia_europe_theater's Europe-facing pipeline set and arctic_theater's
-- northern_sea_route (no duplication across theaters here).
UPDATE friction_nodes SET
  affected_asset_ids = ARRAY['yamal_lng','west_siberian_basin','samotlor_field'],
  updated_at = now()
WHERE id = 'us_russia_theater';

-- D1: Syria -- trim to actual state actors (Levant, Turkey, Israel,
-- Iran, US, Russia). Drops commentary-only participants (Gulf states,
-- Iraq, Egypt, UK, France, Germany, Ukraine, EU) from the theater
-- rollup; those remain on the relevant member atomics.
UPDATE friction_nodes SET
  centroid_ids = ARRAY['MIDEAST-LEVANT','MIDEAST-TURKEY','MIDEAST-ISRAEL','MIDEAST-IRAN','AMERICAS-USA','EUROPE-RUSSIA'],
  updated_at = now()
WHERE id = 'syria_theater';

-- D2: Turkey -- trim to actual state actors (Turkey, Iran, Israel,
-- Russia, US, NATO as institutional actor for the membership-tension
-- angle). Drops the same commentary-only tail.
UPDATE friction_nodes SET
  centroid_ids = ARRAY['MIDEAST-TURKEY','MIDEAST-IRAN','MIDEAST-ISRAEL','EUROPE-RUSSIA','AMERICAS-USA','NON-STATE-NATO'],
  updated_at = now()
WHERE id = 'turkey_theater';

COMMIT;
