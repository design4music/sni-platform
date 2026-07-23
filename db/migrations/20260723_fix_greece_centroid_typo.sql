-- Fix a pre-existing typo: two Turkey narratives reference EUROPE-GREECE, a
-- centroid id that never existed. Greece (GR) lives in EUROPE-SOUTH.
-- actor_centroids is display-only, so this is cosmetic, but it removes the only
-- dangling centroid reference in narratives_v2. Order-preserving array_replace.
BEGIN;

UPDATE narratives_v2
   SET actor_centroids = array_replace(actor_centroids, 'EUROPE-GREECE', 'EUROPE-SOUTH')
 WHERE 'EUROPE-GREECE' = ANY(actor_centroids);

COMMIT;
