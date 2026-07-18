-- Thailand-Cambodia atomic: widen centroid scope to where the content lives.
--
-- Diagnosed during the build (2026-07-17): the ASEAN centroid bug routes ASEAN
-- content to ASIA-SOUTHASIA. Of 29 sharp-anchor Thai-Cambodia conflict titles in
-- 180d, ALL 29 carry ASIA-SOUTHASIA but only 15 carry ASIA-SOUTHEAST, and the
-- Chinese-state mediation coverage is tagged ASIA-CHINA. Gating on ASIA-SOUTHEAST
-- alone captured 15/29.
--
-- The fn_anchor bundle is sharp (country-pair compound, Preah Vihear/Ta Moan/MOU44
-- toponyms + framework) -- a title cannot contain one of these anchors without
-- being on-topic -- so widening participant scope is safe and only improves recall
-- (same logic as the Arctic A2 anchor==subject sub-case). centroid_ids[0] stays
-- ASIA-SOUTHEAST so the map/region label remains Southeast Asia.
--
-- Paired bundle edit (applied via apply_fn_anchor_bundle.py): dropped bare
-- 'demarcation' phrases (would leak South Asia LAC demarcation now that
-- ASIA-SOUTHASIA is in scope) and 'Hun Sen' (leaked Cambodia-China Beijing
-- visits); added en-dash pair-compound variants.

BEGIN;

UPDATE friction_nodes
SET centroid_ids = ARRAY['ASIA-SOUTHEAST', 'ASIA-SOUTHASIA', 'ASIA-CHINA', 'ASIA-PACIFIC-THAILAND'],
    updated_at = NOW()
WHERE id = 'thailand_cambodia_border';

COMMIT;
