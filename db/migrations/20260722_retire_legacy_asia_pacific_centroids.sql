-- Retire 14 legacy ASIA-PACIFIC-* centroid rows.
--
-- These are an old per-country naming scheme (ASIA-PACIFIC-SOUTH-KOREA,
-- ASIA-PACIFIC-JAPAN, ...) superseded by the ASIA-* / OCEANIA-* buckets, but
-- left is_active = true in centroids_v3. The frontend lists active centroids
-- and resolves labels via the `centroids` i18n namespace, where these ids do
-- not exist -- producing the runtime errors:
--   MISSING_MESSAGE: Could not resolve `centroids.ASIA-PACIFIC-VIETNAM` ...
--
-- The fix is deactivation, NOT adding translations: translating them would
-- legitimise dead duplicates of live centroids.
--
-- Verified dead before retiring:
--   titles_v3 carrying any of the 14 ......... 0
--   title_assignments / centroid_summaries /
--   publisher_stance / ctm / strategic_narratives  0 rows each
--   references ............................... 2, both on thailand_cambodia_border,
--                                              and both already carry ASIA-SOUTHEAST
--
-- Zero attribution impact: a centroid matching 0 titles contributes nothing to
-- the participant OR-gate, so removing it from centroid_ids cannot change
-- which titles attribute. (ASIA-PACIFIC-THAILAND being empty is the known
-- ASEAN centroid bug -- see the thailand_cambodia_border curated bundle note.)

BEGIN;

UPDATE centroids_v3
   SET is_active = false, updated_at = NOW()
 WHERE id IN (
   'ASIA-PACIFIC-BHUTAN', 'ASIA-PACIFIC-BRUNEI', 'ASIA-PACIFIC-FIJI',
   'ASIA-PACIFIC-INDONESIA', 'ASIA-PACIFIC-JAPAN', 'ASIA-PACIFIC-MALAYSIA',
   'ASIA-PACIFIC-MYANMAR', 'ASIA-PACIFIC-NORTH-KOREA',
   'ASIA-PACIFIC-PHILIPPINES', 'ASIA-PACIFIC-SOLOMON-ISLANDS',
   'ASIA-PACIFIC-SOUTH-KOREA', 'ASIA-PACIFIC-TAIWAN',
   'ASIA-PACIFIC-THAILAND', 'ASIA-PACIFIC-VIETNAM'
 );

-- Drop the two dangling references (both retain ASIA-SOUTHEAST).
UPDATE friction_nodes
   SET centroid_ids = array_remove(centroid_ids, 'ASIA-PACIFIC-THAILAND'),
       updated_at = NOW()
 WHERE id = 'thailand_cambodia_border';

UPDATE narratives_v2
   SET actor_centroids = array_remove(actor_centroids, 'ASIA-PACIFIC-THAILAND'),
       updated_at = NOW()
 WHERE id = 'thaicam_thai_sovereignty_defence';

COMMIT;
