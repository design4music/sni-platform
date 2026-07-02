-- Fix crude 3-4-point LineStrings from the initial batch seed with realistic
-- routed waypoints. Pipelines follow real overland/seabed corridors between
-- named facilities; the two Arctic/Southern-Ocean "sea routes" are
-- reclassified as corridor and re-routed so every waypoint sits in open
-- water. See 20260703_seed_strategic_assets.sql for the original rows.

-- =========================================================================
-- PIPELINES (LineString, land/seabed routes via real waypoints)
-- =========================================================================

-- Power of Siberia: Chayanda field (Yakutia) -> Lensk -> Aldan corridor ->
-- Tynda -> Svobodny -> Blagoveshchensk border crossing -> Heihe, China.
UPDATE strategic_assets SET geometry = '{"type":"LineString","coordinates":[
  [111.5,62.0],
  [112.8,61.3],
  [114.9,60.7],
  [117.0,59.7],
  [119.0,58.6],
  [121.2,57.2],
  [123.0,55.9],
  [124.7,55.2],
  [126.0,53.9],
  [127.2,52.7],
  [128.1,51.4],
  [127.9,50.6],
  [127.5,50.3],
  [127.5,50.2]
]}'::jsonb
WHERE id = 'power_of_siberia';

-- TurkStream: Russkaya compressor station near Anapa -> gentle Black Sea
-- seabed arc south of Crimea, staying in open water -> Kiyikoy, Turkey.
UPDATE strategic_assets SET geometry = '{"type":"LineString","coordinates":[
  [37.3,44.9],
  [36.4,44.6],
  [35.2,44.2],
  [34.0,43.8],
  [32.8,43.4],
  [31.6,42.9],
  [30.4,42.5],
  [29.2,42.1],
  [28.2,41.8],
  [27.6,41.7],
  [27.2,41.6]
]}'::jsonb
WHERE id = 'turkstream';

-- BTC pipeline: Sangachal terminal (Baku) -> Tbilisi -> south-west through
-- eastern Anatolia -> Ceyhan terminal on the Mediterranean.
UPDATE strategic_assets SET geometry = '{"type":"LineString","coordinates":[
  [49.4,40.2],
  [48.0,40.7],
  [46.4,41.3],
  [44.8,41.7],
  [43.4,41.4],
  [42.0,40.9],
  [40.6,40.4],
  [39.2,39.9],
  [37.9,39.2],
  [36.9,38.2],
  [36.2,37.5],
  [35.6,36.9]
]}'::jsonb
WHERE id = 'btc_pipeline';

-- Druzhba (western segment): Almetyevsk -> Samara -> Bryansk -> Mozyr,
-- Belarus -> Adamowo, Poland -> Schwedt, Germany.
UPDATE strategic_assets SET geometry = '{"type":"LineString","coordinates":[
  [52.3,54.9],
  [50.9,54.2],
  [50.1,53.2],
  [45.0,53.0],
  [39.7,53.1],
  [34.4,53.2],
  [31.8,52.6],
  [29.2,52.0],
  [26.3,52.2],
  [23.5,52.3],
  [19.0,52.7],
  [16.5,53.0],
  [14.3,53.1]
]}'::jsonb
WHERE id = 'druzhba_pipeline_west';

-- =========================================================================
-- SEA ROUTES -> reclassified as corridor, re-routed through open water only
-- =========================================================================

-- Northern Sea Route: from Murmansk approach, offshore along the Russian
-- Arctic coast through the Kara Strait (north of Novaya Zemlya), Laptev,
-- East Siberian and Chukchi seas, stopping short of the antimeridian.
UPDATE strategic_assets SET geometry = '{"type":"LineString","coordinates":[
  [33.0,69.5],
  [40.5,70.2],
  [50.0,71.0],
  [58.5,71.8],
  [64.5,74.5],
  [68.5,78.5],
  [78.0,79.5],
  [90.0,78.0],
  [102.0,76.5],
  [115.0,75.0],
  [128.0,73.5],
  [141.0,71.5],
  [155.0,69.8],
  [167.0,68.2],
  [178.5,66.2]
]}'::jsonb,
asset_type = 'corridor'
WHERE id = 'northern_sea_route';

-- Cape of Good Hope Route: mid-South-Atlantic offshore Angola, around the
-- Cape at a safe offshore distance, into the Indian Ocean toward the
-- Mozambique Channel / east of Madagascar.
UPDATE strategic_assets SET geometry = '{"type":"LineString","coordinates":[
  [-5.0,-15.0],
  [1.0,-20.0],
  [6.0,-25.0],
  [10.5,-29.5],
  [14.5,-34.0],
  [18.5,-36.3],
  [22.5,-36.0],
  [27.0,-33.5],
  [32.0,-29.0],
  [37.0,-24.5],
  [42.0,-20.0],
  [48.0,-16.5],
  [55.0,-12.0]
]}'::jsonb,
asset_type = 'corridor'
WHERE id = 'cape_of_good_hope_route';
