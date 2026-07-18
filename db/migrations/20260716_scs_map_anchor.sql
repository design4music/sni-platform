-- Move the SCS map presence from the retired theater to the standalone atomic.
--
-- Retiring scs_theater (20260716_scs_standalone_atomic.sql) took the South
-- China Sea off the homepage conflicts layer: the map API and the anchor_point
-- both lived on the theater row. This moves that curated map data onto the
-- atomic so the conflict marker is restored -- same epicentre (mid-Spratly),
-- same pressed assets (Malacca chokepoint + Port of Singapore). The API change
-- that makes the map read standalone atomics ships alongside this.
--
-- scope was already 'regional' on the atomic; the conflicts layer needs
-- scope='regional' AND anchor_point (see app/api/friction-nodes-map/route.ts).

BEGIN;

UPDATE friction_nodes
SET anchor_point = '{"type":"Point","coordinates":[114.0,10.0]}'::jsonb,
    affected_asset_ids = ARRAY['strait_of_malacca', 'port_of_singapore'],
    updated_at = NOW()
WHERE id = 'south_china_sea_claims';

-- Clear the retired theater's map data so nothing dangles if it is ever
-- re-read; it is inactive and no longer the SCS map owner.
UPDATE friction_nodes
SET anchor_point = NULL,
    affected_asset_ids = ARRAY[]::text[],
    updated_at = NOW()
WHERE id = 'scs_theater';

COMMIT;
