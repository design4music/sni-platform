-- Drop friction_nodes.topic_keywords. Replaced by taxonomy_v3 fn_anchor bundle
-- (since Phase 2 unification). No remaining readers after frontend cleanup.
-- 2026-05-12.

BEGIN;
ALTER TABLE friction_nodes DROP COLUMN IF EXISTS topic_keywords;
COMMIT;
