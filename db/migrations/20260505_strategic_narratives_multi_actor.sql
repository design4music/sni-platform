-- Add multi-actor support to strategic_narratives.
--
-- Reality: many narratives are held by COALITIONS of actors, not single
-- countries. "Russia is an existential threat" is the shared position of
-- US + EU + NATO + UK + Baltic + Nordic + Eastern frontline states.
-- Forcing one narrative per actor created 5+ near-identical sibling
-- narratives that no keyword scheme could distinguish.
--
-- New `actor_centroids` array column lets one narrative belong to a
-- coalition. Old single `actor_centroid` is kept for backwards
-- compatibility (treated as the "primary" actor) and backfilled into
-- the array.

ALTER TABLE strategic_narratives
    ADD COLUMN IF NOT EXISTS actor_centroids TEXT[] NOT NULL DEFAULT '{}';

-- Backfill: every narrative starts as a single-actor coalition.
UPDATE strategic_narratives
   SET actor_centroids = ARRAY[actor_centroid]::TEXT[]
 WHERE actor_centroid IS NOT NULL
   AND (actor_centroids IS NULL OR cardinality(actor_centroids) = 0);

-- Index for the matcher's "any actor in array" lookups.
CREATE INDEX IF NOT EXISTS idx_strategic_narratives_actor_centroids
    ON strategic_narratives USING GIN (actor_centroids);
