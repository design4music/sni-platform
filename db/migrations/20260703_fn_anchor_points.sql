-- Conflict anchor points: a regional friction node is a place, not just
-- pressure on assets. anchor_point (GeoJSON Point, [lon, lat]) marks the
-- conflict epicenter and renders as a distinct conflict marker on the map.
-- Without it, conflicts that spin no commodities (Gaza) would be invisible
-- on an asset-only map. NULL = no marker (global rivalries, or theaters
-- fully represented by their assets).

ALTER TABLE friction_nodes ADD COLUMN IF NOT EXISTS anchor_point jsonb;

UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[34.45,31.5]}'   WHERE id = 'israel_theater';          -- Gaza
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[37.8,48.0]}'    WHERE id = 'ukraine_war_theater';     -- Donbas front
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[51.4,35.7]}'    WHERE id = 'iran_theater';            -- Tehran
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[36.3,33.5]}'    WHERE id = 'syria_theater';           -- Damascus
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[32.9,39.9]}'    WHERE id = 'turkey_theater';          -- Ankara
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[44.2,15.35]}'   WHERE id = 'yemen_red_sea_theater';   -- Sanaa
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[74.8,34.1]}'    WHERE id = 'india_pakistan_theater';  -- Kashmir LoC
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[78.0,34.5]}'    WHERE id = 'india_china_theater';     -- Ladakh LAC
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[123.5,25.75]}'  WHERE id = 'japan_china_theater';     -- Senkaku
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[126.7,37.95]}'  WHERE id = 'korea_theater';           -- DMZ
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[120.0,24.3]}'   WHERE id = 'taiwan_strait_theater';   -- strait midline
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[114.0,10.0]}'   WHERE id = 'scs_theater';             -- Spratlys
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[95.5,21.5]}'    WHERE id = 'myanmar_theater';         -- central Myanmar
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[0.9,14.4]}'     WHERE id = 'sahel_theater';           -- Liptako-Gourma tri-border
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[45.3,2.05]}'    WHERE id = 'horn_africa_theater';     -- Mogadishu
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[29.2,-1.68]}'   WHERE id = 'great_lakes_theater';     -- Goma
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[20.9,42.9]}'    WHERE id = 'balkan_theater';          -- Kosovo / Mitrovica
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[46.75,39.8]}'   WHERE id = 'caucasus_theater';        -- Karabakh
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[-66.9,10.5]}'   WHERE id = 'latam_theater';           -- Caracas
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[15.6,78.2]}'    WHERE id = 'arctic_theater';          -- Svalbard
UPDATE friction_nodes SET anchor_point = '{"type":"Point","coordinates":[20.5,54.7]}'    WHERE id = 'russia_europe_theater';   -- Kaliningrad
-- australia_china_theater: trade conflict, no battlefield -- its assets
-- (Pilbara, lithium belt) carry it. No anchor.
