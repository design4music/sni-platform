-- Sahel: second precision pass on sahel_counterinsurgency_abuses (2026-07-20).
--
-- The previous fix kept 'airstrike' / 'air strike' / 'frappes' as
-- state-perpetration markers. Reading the result showed they imply a
-- PERPETRATOR but not a HARM, so successful counterterror strikes were being
-- filed as abuses -- the exact inversion the stance is supposed to prevent:
--   "Des frappes aériennes menées par le Nigeria avec les États-Unis tuent
--    175 membres de l'EI"                                        (France 24)
--   "Le Nigeria mène de nouvelles frappes avec les États-Unis contre le
--    groupe État islamique"                                      (France 24)
--   "Mali : la force unifiée antidjihadiste a mené des frappes après les
--    attaques du week-end"                                       (Le Figaro)
-- Six of twenty titles were operations reporting, not abuse reporting.
--
-- Fix: the framing must require a harm or documentation marker, never a bare
-- military-action noun. Dropped airstrike/air strike/frappes; added the
-- outcome markers that actually distinguish the two registers ('feared dead',
-- 'market'/'marché' -- both Borno market strikes are in this class).
-- The action nouns stay in the fn_anchor bundle, where they belong: they are
-- correct as a TOPIC gate and wrong as a STANCE gate.

BEGIN;

UPDATE narratives_v2
SET framing_keywords = ARRAY[
        -- independent documentation
        'exaction','atrocit','abuses','human rights','Human Rights Watch','HRW',
        'Amnesty','impunity','impunité','droits de l''homme','Menschenrechte',
        'Übergriffe','Gräueltaten','derechos humanos',
        -- unlawful-killing markers
        'summary execution','extrajudicial','mass grave','charnier',
        'disappearance','misfire',
        -- civilian-harm outcomes
        'civilian deaths','killed civilians','civils tués','morts civils',
        'victimes civiles','feared dead','wedding','mariage','market','marché',
        -- explicit state attribution
        'crimes de l''armée','army behind','par l''armée'
    ],
    updated_at = NOW()
WHERE id = 'sahel_counterinsurgency_abuses';

COMMIT;
