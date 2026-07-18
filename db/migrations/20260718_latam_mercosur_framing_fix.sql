-- Fix: mercosur_market_opportunity was a publisher-only firehose.
--
-- Found by reading samples, not counts (spec 0a step 9). With
-- framing_required=false the card claimed every South American Mercosur
-- headline for a "market opens" label, including its direct opposite:
--   "En un golpe al acuerdo con el Mercosur, la UE prohíbe las importaciones
--    de carne desde Brasil"
--   "El Parlamento Europeo paraliza el acuerdo y lo envía a la Justicia"
--   "Argentina e Uruguai esgotam cotas de arroz e ovos e acendem alerta"
-- Same publisher pool, opposite stance -- publisher alone cannot disambiguate,
-- so the three-stance pattern (section 5) applies: both South-American cards
-- get framing_required=true with disjoint keywords.
--
-- The setback coverage is not merely "less positive"; it is the regional
-- reading of European obstruction, which had no card at all. Adding it.

BEGIN;

UPDATE narratives_v2 SET
    framing_required = true,
    framing_keywords = ARRAY[
        'oportunidad','oportunidade','se firmó','firmaron','assinatura','assinado',
        'histórico','histórica','entra en vigor','entrará en vigor','vigência',
        'apertura','abre','ganan','ganha','beneficia','exportadores','exportação',
        'integra','multilateralismo','ratificado','ratificação','avanza','avança'
    ],
    updated_at = now()
WHERE id = 'mercosur_market_opportunity';

INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES
(
 'mercosur_european_obstruction', 'latam_eu_market_access', -1,
 'European obstruction of the deal', 'Europäische Blockade des Abkommens',
 'Europe signs, then restricts', 'Europa unterzeichnet und beschränkt dann',
 'South American coverage of the agreement''s implementation phase reports a pattern of European restriction after signature: import bans on specific products, quota exhaustion, parliamentary and judicial challenges to ratification, and standards applied as barriers, read regionally as the terms being narrowed after the deal was concluded.',
 'Südamerikanische Berichterstattung über die Umsetzungsphase des Abkommens beschreibt ein Muster europäischer Beschränkungen nach der Unterzeichnung: Einfuhrverbote für einzelne Erzeugnisse, ausgeschöpfte Quoten, parlamentarische und gerichtliche Anfechtungen der Ratifizierung sowie als Handelshemmnis wirkende Standards -- regional gelesen als nachträgliche Verengung der vereinbarten Bedingungen.',
 ARRAY['Clarín','La Nación','O Globo','Folha de S.Paulo','O Estado de S. Paulo','Infobae','Brazil Reports','El Observador','La Tercera'],
 ARRAY[
    'golpe','prohíbe','prohibe','proíbe','proibiç','bloqueo','bloquea','bloqueia',
    'paraliza','paralisa','veto','freno','frena','trava','barreira','barreras',
    'obstácul','alerta','restric','restriç','suspende','impugna','acciona','Justiça','Justicia'
 ],
 true, ARRAY['AMERICAS-BRAZIL'], true, 4
);

COMMIT;
