-- Korea theater: strip the trailing "Vocabulary: ..." sentence from claim_en.
--
-- The sentence duplicated framing_keywords, which already render as their own
-- "Loaded vocabulary" pill block in FrictionNodeNarrativeCards.tsx. claim_de
-- was never given the sentence in the first place (translation omitted it),
-- so this only touches claim_en -- bringing it in line with claim_de and with
-- the separate-block design already used for the pill rendering.
--
-- Cosmetic content-only change. No structural, matching, or attribution
-- impact -- framing_keywords (the actual matching data) is untouched.

BEGIN;

UPDATE narratives_v2
SET claim_en = regexp_replace(claim_en, '\s*Vocabulary:.*$', ''),
    updated_at = NOW()
WHERE fn_id IN (
    'korea_theater',
    'north_korea_missile_program',
    'north_korea_china_patronage',
    'north_korea_russia_alignment',
    'korea_peninsula_deterrence',
    'inter_korean_relations'
)
AND claim_en ~ 'Vocabulary:';

COMMIT;
