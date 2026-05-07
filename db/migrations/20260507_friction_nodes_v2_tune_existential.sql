-- Calibrate west_iran_nuclear_threat against Israeli + Saudi + Fox News
-- coverage. Add nuclear-specific recurring vocabulary, REMOVE IRGC/Mossad
-- from topic_keywords (those belong to a future Iran-proxy FN, not the
-- nuclear-program FN).
-- 2026-05-07

BEGIN;

UPDATE narratives_v2
SET framing_keywords = ARRAY[
    -- Original (kept):
    'existential threat',
    'preemptive strike',
    'maximum pressure',
    'breakout time',
    'weapons-grade',
    'Begin doctrine',
    'prevention not deterrence',
    'all options on table',
    'weapons program',
    'denial of capability',
    'Natanz strike',
    -- Added from calibration (nuclear-specific only):
    'uranium enrichment',
    'nuclear talks',
    'US-Iran nuclear',
    'US-Iran nuclear talks',
    'natanz nuclear',
    'nuclear chief',
    'nuclear deal',
    'Iranian nuclear',
    'Iran nuclear chief',
    'US-Israeli strikes',
    'strikes on nuclear',
    'strike on Natanz',
    'military strikes',
    -- Added from domain knowledge of the existential-threat lexicon:
    'nuclear ambition',
    'nuclear ambitions',
    'nuclear weapon program',
    'breakout capability',
    'breakout window',
    'enrichment cascade',
    'clandestine enrichment',
    'nuclear facility strike',
    'military option',
    'nuclear weapons capability',
    'denuclearization',
    'rollback',
    'Stuxnet'
],
topic_keywords = ARRAY[
    -- Original (kept, REMOVED IRGC + Mossad — those belong to the
    -- forthcoming Iran-proxy FN, not the nuclear-program FN):
    'Iran nuclear',
    'Natanz',
    'Fordow',
    'enrichment',
    'IAEA Iran',
    'centrifuge',
    'sanctions Iran',
    -- Added nuclear-specific named entities + venues:
    'Bushehr',
    'Arak',
    'uranium',
    'NPT',
    'JCPOA',
    'IAEA',
    'Grossi',
    'Witkoff',
    'Vienna talks',
    'Geneva talks',
    'Iran atomic',
    'enrichment program',
    'Tehran nuclear'
],
updated_at = now()
WHERE id = 'west_iran_nuclear_threat';

COMMIT;
