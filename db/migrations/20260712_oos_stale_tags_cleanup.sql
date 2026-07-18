-- Out-of-scope stale-tag cleanup (2026-07-12)
-- The Phase 2 matcher historically did not clear centroid_ids /
-- matched_aliases when marking a title out_of_scope. Harmless for fresh
-- titles (no prior tags), but on a REMATCH (2026-07-11 weapon-anchor fix)
-- 231 titles kept their phantom tags after being demoted to out_of_scope,
-- and 114 of them leaked back into title_narratives through the stale
-- centroid_ids (attribution joins do not check processing_status).
-- Matcher fixed in pipeline/phase_2/match_centroids.py (both out_of_scope
-- and blocked_stopword branches now clear the fields); this migration
-- cleans the existing residue. title_narratives rows are derived data,
-- regenerable by bootstrap.

BEGIN;

DELETE FROM title_narratives
 WHERE title_id IN (
   SELECT id FROM titles_v3
   WHERE processing_status = 'out_of_scope'
     AND cardinality(centroid_ids) > 0);

UPDATE titles_v3
   SET centroid_ids = '{}',
       matched_aliases = NULL,
       updated_at = NOW()
 WHERE processing_status = 'out_of_scope'
   AND cardinality(centroid_ids) > 0;

COMMIT;
