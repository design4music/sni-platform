-- Israel theater fn_anchor tightening.
-- Root cause of the Iran-war bleed into israel_theater narratives: the
-- German anchor list included the standalone token 'Iran'. ILIKE matching
-- is language-agnostic, so that single alias matched every 'Iran' substring
-- in any-language title text — pulling in pure-Iran coverage that never
-- mentioned Israel.
--
-- Fix: replace standalone 'Iran' with compound Iran<->Israel terms. Also
-- drop a couple of standalone aliases that had similar over-match risk
-- on atomic FNs.
-- 2026-05-12

BEGIN;

-- israel_theater: replace 'Iran' single token in German bundle with compounds.
UPDATE taxonomy_v3
SET aliases = jsonb_set(
    aliases,
    '{de}',
    jsonb_build_array(
        'Israel','Tel Aviv','Netanjahu','Netanyahu','israelische Armee','IDF',
        'Gaza','Hamas','Hisbollah','Westjordanland','Krieg in Gaza','Geiseln','Siedlungen',
        'Iran-Israel','Israel-Iran','Iran Israel','israelische Schläge gegen Iran',
        'iranische Angriffe auf Israel','Iran-Israel-Konflikt','Israel-Iran-Krieg'
    )
)
WHERE taxonomy_function = 'fn_anchor' AND linked_id = 'israel_theater';

-- israel_iran_strikes: drop standalone 'Pezeshkian' (Iranian president —
-- matches Iran-internal titles unrelated to Israel exchange). Keep all
-- compound Iran-Israel terms.
UPDATE taxonomy_v3
SET aliases = jsonb_set(
    aliases,
    '{en}',
    jsonb_build_array(
        'Iran Israel','Iranian strikes on Israel','Israeli strikes on Iran',
        'IRGC','Revolutionary Guard','Operation True Promise',
        'ballistic missiles Iran','Iranian drones','Iran retaliation',
        'Israeli retaliation','Natanz','Fordow','Iranian air defense',
        'Israeli air force Iran','Khamenei response','direct war Iran Israel'
    )
)
WHERE taxonomy_function = 'fn_anchor' AND linked_id = 'israel_iran_strikes';

-- west_bank_settlements: drop standalone 'PA' (matches countless unrelated
-- acronyms — DPA, AP, PA-system, etc.). Keep 'Palestinian Authority' as the
-- full form alongside.
UPDATE taxonomy_v3
SET aliases = jsonb_set(
    aliases,
    '{en}',
    jsonb_build_array(
        'West Bank','settlements','settler violence','Jenin','Nablus','Hebron',
        'outposts','occupation','Palestinian Authority','two-state',
        'Judea Samaria','E1','Area C','annexation','settler attack',
        'settler raid','Mahmoud Abbas'
    )
)
WHERE taxonomy_function = 'fn_anchor' AND linked_id = 'west_bank_settlements';

COMMIT;
