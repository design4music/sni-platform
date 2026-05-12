-- Surgical prune of framing_keywords for FN3's two stand-by narratives + FN3's
-- regime-change all-in narrative. Removes entity names (which belong in
-- fn_anchor, not framing) and event-specific noise that pollutes ranking +
-- attribution.
-- 2026-05-12.

BEGIN;

-- west_iran_regime_change_doctrine: drop entity names. Frontend ranks sample
-- titles by framing_keyword match count, so having "Pahlavi" / "MEK" /
-- "Mahsa Amini" as framing keywords causes Pahlavi headlines to monopolise the
-- top 6. Entities live in fn_anchor; framing should be rhetorical phrases only.
UPDATE narratives_v2
SET framing_keywords = ARRAY[
    'the regime', 'Iranian regime', 'Tehran regime', 'mullah regime',
    'tyrannical regime', 'brutal regime', 'oppressive regime',
    'Islamic Republic',
    'regime change', 'topple', 'overthrow',
    'fall of the regime', 'fall of the Islamic Republic', 'collapse of the regime',
    'democratic transition', 'post-regime Iran',
    'free Iran', 'liberate Iran', 'free the Iranian people',
    'Iranian people deserve freedom', 'people vs the regime',
    'Iranian opposition', 'opposition leaders', 'opposition figures',
    'oppressed by the regime',
    'morality police', 'hijab protest', 'protests in Iran crushed',
    'crackdown on protesters',
    'monarchist', 'monarchist opposition',
    'decapitation strike', 'regime decapitated', 'regime collapse imminent'
]
WHERE id = 'west_iran_regime_change_doctrine';

-- multipolar_systemic_alternative: drop the Russia/Ukraine sanctions noise and
-- generic sanctions phrases that catch unrelated stories. Keep anti-hegemonic
-- vocabulary that genuinely identifies the multipolar stance.
UPDATE narratives_v2
SET framing_keywords = ARRAY[
    'US hegemony', 'Western hegemony', 'unilateralism', 'imperialism',
    'Cold War mentality', 'collective punishment', 'foreign occupation',
    'multipolar', 'multipolar world', 'multipolar order',
    'BRICS', 'Global South',
    'sovereign right', 'inalienable right',
    'anti-sanctions',
    'dollar de-dependence', 'dollar hegemony', 'US dollar hegemony',
    'de-dollarisation', 'de-dollarization',
    'encirclement',
    'US bases', 'US bases in Middle East', 'US bases in region',
    'imperial overreach', 'imperial pressure',
    'double standards', 'second-class nation',
    'economic terrorism'
]
WHERE id = 'multipolar_systemic_alternative';

COMMIT;
