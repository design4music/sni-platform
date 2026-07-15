-- ASIA-CAUCASUS centroid had NULL map_point, so the friction-nodes-map route
-- (WHERE map_point IS NOT NULL) dropped it from theater participants -> the
-- South Caucasus countries (AM/AZ/GE, already in iso_codes) never highlighted
-- and "Caucasus" was missing from the participant list. Give it a central
-- representative point (Tbilisi area).

BEGIN;

UPDATE centroids_v3
SET map_point = '{"type":"Point","coordinates":[44.8,41.7]}'::jsonb, updated_at = now()
WHERE id = 'ASIA-CAUCASUS';

COMMIT;
