-- Add publisher-stance bucketing to narratives_v2.
-- 2026-05-07
--
-- Architecture shift: title-narrative attribution moves from text-only
-- (topic + framing + centroid) to publisher-stance bucketing.
-- See concept doc section 7.5 (calibration) and the discussion below.
--
-- Why: framing_keyword text matching undercatches real coverage because
-- headlines are short and use neutral descriptors more than loaded
-- vocabulary. But publisher editorial stance IS stable and editorially
-- established. Press TV always frames Iran nuclear from Iran's POV;
-- Fox News always frames it from the existential-threat POV. Bucketing
-- by publisher is more accurate than guessing the frame from headline text.
--
-- Membership becomes: FN-topic-match (tight) AND publisher-in-narrative-list.
-- framing_keywords stay in the schema but are repurposed as a SAMPLE-
-- QUALITY RANKER for picking representative headlines per card, not as
-- a membership filter.

BEGIN;

ALTER TABLE narratives_v2
    ADD COLUMN IF NOT EXISTS publishers text[];

CREATE INDEX IF NOT EXISTS idx_narratives_v2_publishers
    ON narratives_v2 USING gin (publishers);

COMMENT ON COLUMN narratives_v2.publishers IS
    'Publishers whose editorial stance maps to this narrative. Used as the primary membership filter for title attribution; FN topic_keywords gate FN-relevance, this list determines which narrative bucket a title falls in.';

COMMIT;
