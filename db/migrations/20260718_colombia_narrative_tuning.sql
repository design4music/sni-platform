-- colombia_theater: narrative tuning after reading unnarrated samples (0a step 9).
--
-- colombia_political_transition attributed 76 events but only 9 titles reached a
-- narrative. Reading the unnarrated set showed two distinct causes:
--   (a) MOST of it is genuinely neutral process reporting ("Cepeda, de la
--       Espriella advance in Colombia's presidential election"). Correctly
--       excluded -- precision over recall. Not a bug.
--   (b) But real stance signals were missed because the keywords were
--       Spanish-heavy while much of the coverage is English and Italian:
--       "promise of crime crackdown", "proposes mega-prisons", "el ULTRA De la
--       Espriella", "estrema destra ... Cepeda non riconosce il risultato",
--       "cements Latin America's rightward shift".
--   (c) Three covering publishers were in no pool at all: La Repubblica,
--       Japan Times, Atlantic Council.
--
-- On the contested labels: 'ultraderech' / 'far-right' / 'estrema destra' are
-- added ONLY as framing keywords on the CRITICAL narrative, never to FN prose,
-- per 0a step 6 -- they are terms the subject rejects, so they identify a
-- framing rather than state a fact. The sympathetic narrative gets the
-- self-description terms (crackdown, mano dura, security) in the same way.
-- 'ultraderech' is used rather than bare 'ultra' because framing_keywords match
-- by ILIKE substring and 'ultra' is inside ultramarino, ultimátum, etc.
--
-- colombia_armed_groups_peace is deliberately NOT force-fixed. It has 50
-- attributed events and 2 narrated titles because the coverage is neutral wire
-- reporting of charges, seizures and suspended talks. Broadening its framing
-- keywords into topic words would turn the publisher pools into a firehose --
-- the exact failure repaired on mercosur_market_opportunity earlier. Only
-- genuinely stance-bearing terms are added.

BEGIN;

UPDATE narratives_v2 SET
    publishers = ARRAY['El Mundo','Reforma','El Universal','Clarín','La Nación','Infobae','Associated Press','Reuters','Bloomberg','Japan Times','Atlantic Council'],
    framing_keywords = ARRAY[
        'mandato','victoria','triunfo','ganó','seguridad','mano dura','cartel','respaldo',
        'apoyo','elegido','contundente','crackdown','mega-prison','megacárcel','crime',
        'rightward','giro a la derecha','ciclo de Petro','presidente electo','tough on'
    ],
    updated_at = now()
WHERE id = 'colombia_transition_mandate';

UPDATE narratives_v2 SET
    publishers = ARRAY['El País','The Guardian','Deutsche Welle','France 24','France 24 (EN)','Le Monde','BBC World','New York Times','CNN','Euronews','La Repubblica','Al Jazeera','Anadolu Agency'],
    framing_keywords = ARRAY[
        'institucional','institutional','democracia','democracy','injerencia','interference',
        'fraude','impugna','legal challenge','norms','autoritari','riesgo','concern','fears',
        'ultraderech','far-right','extrema derecha','estrema destra','no reconoce','non riconosce',
        'threat to','amenaza para','backsliding'
    ],
    updated_at = now()
WHERE id = 'colombia_transition_institutional_concern';

-- Keep the theater -1 card publisher-disjoint from the -2 card after adding
-- Al Jazeera / Anadolu above, so those titles are not homeless at theater level.
UPDATE narratives_v2 SET
    publishers = ARRAY['Reuters','Associated Press','BBC World','Deutsche Welle','CNN','The Guardian','New York Times','France 24','France 24 (EN)','Le Monde','NPR','Euronews','Bloomberg','Financial Times','El País','La Repubblica','Al Jazeera','Anadolu Agency'],
    updated_at = now()
WHERE id = 'colombia_theater_external_pressure';

UPDATE narratives_v2 SET
    framing_keywords = ARRAY[
        'paz total','proceso de paz','negociac','peace talks','peace process','desmoviliz',
        'transitional justice','justicia transicional','diálogo','acuerdo','resume','reanuda','ceasefire','cese'
    ],
    updated_at = now()
WHERE id = 'colombia_peace_negotiation_defense';

UPDATE narratives_v2 SET
    framing_keywords = ARRAY[
        'violencia','fracaso','enseñorea','dispara','control territorial','reclutamiento',
        'impunidad','failed','emboldened','expansión','suspend','war crimes','crímenes de guerra','extorsión'
    ],
    updated_at = now()
WHERE id = 'colombia_peace_process_failure';

COMMIT;
