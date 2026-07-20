-- Sahel: framing-keyword recall fix on sahel_jihadist_insurgency (2026-07-20).
--
-- First measured pass gave sahel_state_losing_ground 16 titles and
-- sahel_counterinsurgency_abuses 1, against 290 titles on the atomic where
-- Western outlets are the largest bloc (France 24 alone has 37). Reading the
-- dropped titles showed the framing keywords, not the coalitions, were wrong:
--
--   "Percée jihadiste, blocus de Bamako, affaiblissement russe : le point de
--    bascule au Mali ?"                                          (France 24)
--   "Au Mali, djihadistes et indépendantistes accentuent la pression sur la
--    junte : « A partir d'aujourd'hui, nous bloquons Bamako »"    (Le Monde)
--   "Mali at risk of splintering after jihadi and separatist attacks" (Reuters)
--   "Journal de l'Afrique - Niger : la violence jihadiste se propage dans la
--    région de Tahoua"                                            (France 24)
--
-- Every one of these is squarely the "state losing ground" stance and every one
-- was dropped. The original keyword set was drafted in the ENGLISH register
-- (losing / seize / advance) while a third of this theater's corpus is French
-- and uses percée / pression / se propage / bousculent / point de bascule.
-- I had also cut 'offensive' and 'attaque' as stance-ambiguous -- correct
-- reasoning for a pair separated BY framing, wrong here: the +2 stance on this
-- atomic is publisher-disjoint (Russian/Chinese/Nigerian), so framing's only
-- job is to separate -2 from -1, and those two are separated by REGISTER
-- (advance/pressure vs civilian-harm), which 'offensive' does not blur.
--
-- The companion bundle change (20260720_sahel_bundles.sql, re-emitted) adds
-- airstrike / air strike / civilian + translations, because most civilian-harm
-- coverage never names an armed group and so was outside the atomic entirely.

BEGIN;

UPDATE narratives_v2
SET framing_keywords = ARRAY[
        -- EN advance / pressure register
        'losing','lost control','loses','seize','seized','capture','captured',
        'advance','advancing','offensive','coordinated','simultaneous',
        'blockade','siege','encircl','expand','spread','spreading','sweeping',
        'unprecedented','splinter','press attacks','under pressure','overrun',
        'no longer control','tipping point','crisis',
        -- FR
        'percée','pression','se propage','propagation','bousculent','bascule',
        'blocus','offensive','coordonnées','coordonnée','sans précédent',
        'inédit','fragilis','vacille','recule','étouffer','emprise',
        's''empare','ampleur','assaut','enlisement',
        -- DE
        'verliert','Vormarsch','beispiellos','Druck','Belagerung','erobert',
        -- ES / IT
        'pierde','avanza','asedio','ofensiva','sin precedentes',
        'perde','avanzata','assedio'
    ],
    updated_at = NOW()
WHERE id = 'sahel_state_losing_ground';

-- Civilian-harm register. Kept framing_required=true and deliberately DISJOINT
-- from the advance register above, so the two Western stances still separate.
UPDATE narratives_v2
SET framing_keywords = ARRAY[
        'civilian','civilians','civils','civiles','civili','Zivilisten',
        'exaction','atrocit','massacre','abuses','abuse','human rights',
        'Human Rights Watch','HRW','execution','summary killing','wedding',
        'mariage','impunity','impunité','disappearance','misfire','market',
        'marché','Menschenrechte','Übergriffe','Gräueltaten','derechos humanos',
        'diritti umani','droits de l''homme','victimes civiles','toll',
        'killed civilians','civilian deaths','morts civils'
    ],
    updated_at = NOW()
WHERE id = 'sahel_counterinsurgency_abuses';

COMMIT;
