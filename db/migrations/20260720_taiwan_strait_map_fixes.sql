-- Taiwan Strait theater: map fixes (Asana task 1216618489706919).
--
-- 1. Port of Kaohsiung wasn't in the theater's curated affected_asset_ids --
--    that's the entire reason it never showed as "under pressure". It's
--    Taiwan's largest container port and carries semiconductor-linked cargo
--    (per its own registry description), squarely inside a Strait-blockade
--    scenario alongside the chokepoint and the two TSMC fabs already listed.
--
-- 2. anchor_point [120, 24.3] sits ~22km from the taiwan_strait chokepoint's
--    own rendered point (its LineString's midpoint, [120, 24.5]) -- close
--    enough that the conflict badge (always drawn on top, higher z-index)
--    visually sits on/hides the chokepoint's asset dot. Moved the anchor
--    into the central strait (median-line area, between Taiwan's west coast
--    and the Fujian coast) -- still a faithful "epicenter" for the
--    confrontation, clearly offset from the chokepoint's own line/midpoint.

BEGIN;

UPDATE friction_nodes
   SET affected_asset_ids = array_append(affected_asset_ids, 'kaohsiung_port'),
       updated_at = now()
 WHERE id = 'taiwan_strait_theater'
   AND NOT ('kaohsiung_port' = ANY(affected_asset_ids));

UPDATE friction_nodes
   SET anchor_point = '{"type": "Point", "coordinates": [119.6, 23.9]}'::jsonb,
       updated_at = now()
 WHERE id = 'taiwan_strait_theater';

COMMIT;
