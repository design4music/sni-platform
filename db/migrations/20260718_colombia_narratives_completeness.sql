-- colombia_theater: atomic narratives, theater cards, completeness fields
-- (FN_THEATER_BUILD_SPEC 0a, steps 6-8).
--
-- Publisher pools are measured, not assumed. Three real blocs cover Colombia:
--   MAINSTREAM: El País (173, the dominant source), Reuters, BBC, DW, AP, CNN,
--     Guardian, France 24, NYT, Le Monde, NPR, Euronews, Bloomberg, FT
--   LATAM/SPANISH RIGHT-LEANING: El Mundo, Reforma, El Universal, Clarín,
--     La Nación, Infobae
--   STATE / GLOBAL SOUTH: CGTN, RT, Al Jazeera, Anadolu, Al-Ahram, Press TV
-- There is NO US conservative bloc in this corpus at all (same finding as the
-- LatAm theater), so no card is authored for one.
--
-- Every atomic narrative whose publisher pool overlaps another of the same sign
-- carries framing_required=true with disjoint keywords -- the three-stance
-- pattern (section 5). This is the failure mode that produced the
-- mercosur_market_opportunity firehose earlier today.
--
-- On labelling: the incoming president's politics are contested. Following
-- 0a step 6, no contested label is stated as fact in FN prose; the critical
-- narrative carries the democratic-backsliding reading and the sympathetic one
-- carries the mandate reading, and neither is presented as the neutral truth.

BEGIN;

-- ---------------------------------------------------------------- completeness
UPDATE friction_nodes SET
    name_de = 'Kolumbien',
    description_en = 'Colombia''s external alignment, its contested presidential transition, and the negotiations with armed groups and drug cartels.',
    description_de = 'Kolumbiens außenpolitische Ausrichtung, der umstrittene Präsidentschaftswechsel und die Verhandlungen mit bewaffneten Gruppen und Drogenkartellen.',
    editorial_summary_en = 'Relations with Washington moved from a threatened military operation and a formal Colombian complaint to a White House meeting within weeks, and the resulting understanding disrupted the government''s negotiations with armed groups. A presidential election then produced a winner endorsed by the US president, while the outgoing president alleged foreign interference in the vote. Colombia has no centroid of its own and is covered under AMERICAS-ANDEAN.',
    editorial_summary_de = 'Die Beziehungen zu Washington entwickelten sich binnen Wochen von einer angedrohten Militäroperation und einer förmlichen kolumbianischen Beschwerde hin zu einem Treffen im Weißen Haus; die daraus folgende Verständigung störte die Verhandlungen der Regierung mit bewaffneten Gruppen. Eine Präsidentschaftswahl brachte anschließend einen vom US-Präsidenten unterstützten Sieger hervor, während der scheidende Präsident ausländische Einflussnahme auf die Wahl behauptete. Kolumbien hat keinen eigenen Zentroid und wird unter AMERICAS-ANDEAN geführt.',
    updated_at = now()
WHERE id = 'colombia_theater';

UPDATE friction_nodes SET
    name_de = 'Ausrichtung gegenüber Washington',
    description_en = 'Colombia''s relations with the United States, spanning coercive measures, tariffs, sanctions designations and negotiated rapprochement.',
    description_de = 'Kolumbiens Beziehungen zu den Vereinigten Staaten, von Zwangsmaßnahmen, Zöllen und Sanktionslistungen bis zur ausgehandelten Annäherung.',
    editorial_summary_en = 'In January the US president threatened a military operation against Colombia following a raid in Venezuela; Bogotá lodged a formal complaint. Within weeks the two presidents met at the White House. The episode combined tariff threats, visa measures and sanctions designations with a rapid diplomatic reversal, and the resulting understanding carried directly into Colombia''s talks with armed groups.',
    editorial_summary_de = 'Im Januar drohte der US-Präsident nach einem Einsatz in Venezuela mit einer Militäroperation gegen Kolumbien; Bogotá legte förmlich Beschwerde ein. Wenige Wochen später trafen sich beide Präsidenten im Weißen Haus. Die Episode verband Zolldrohungen, Visamaßnahmen und Sanktionslistungen mit einer raschen diplomatischen Kehrtwende; die daraus folgende Verständigung wirkte unmittelbar auf Kolumbiens Gespräche mit bewaffneten Gruppen.',
    updated_at = now()
WHERE id = 'colombia_us_alignment';

UPDATE friction_nodes SET
    name_de = 'Präsidentschaftswechsel und institutioneller Streit',
    description_en = 'The Colombian presidential succession, the contested result and the institutional disputes around it.',
    description_de = 'Die kolumbianische Präsidentschaftsnachfolge, das umstrittene Ergebnis und die damit verbundenen institutionellen Auseinandersetzungen.',
    editorial_summary_en = 'The presidential race concluded in a narrow runoff win for Abelardo de la Espriella over Iván Cepeda. The US president publicly endorsed the winner before the vote, and the outgoing president alleged foreign interference in the result. The losing camp pursued a legal challenge. Coverage divides between readings of the outcome as a security mandate and as a risk to institutional norms.',
    editorial_summary_de = 'Das Präsidentschaftsrennen endete mit einem knappen Stichwahlsieg von Abelardo de la Espriella über Iván Cepeda. Der US-Präsident hatte den Sieger vor der Wahl öffentlich unterstützt, und der scheidende Präsident behauptete ausländische Einflussnahme auf das Ergebnis. Das unterlegene Lager ging juristisch dagegen vor. Die Berichterstattung teilt sich in Deutungen des Ausgangs als Sicherheitsmandat und als Risiko für institutionelle Normen.',
    updated_at = now()
WHERE id = 'colombia_political_transition';

UPDATE friction_nodes SET
    name_de = 'Bewaffnete Gruppen und der Friedensprozess',
    description_en = 'Negotiations with guerrilla groups and drug cartels under the "total peace" policy, and the armed and narcotics economy they operate in.',
    description_de = 'Verhandlungen mit Guerillagruppen und Drogenkartellen im Rahmen der Politik des "totalen Friedens" sowie die bewaffnete Ökonomie und Drogenwirtschaft, in der sie agieren.',
    editorial_summary_en = 'The "total peace" policy opened parallel negotiations with the ELN, FARC dissident factions and the Gulf Clan. A tribunal charged former FARC members with war crimes, and the largest cartel suspended talks after the understanding reached between the Colombian and US presidents. Coca cultivation and gold trafficking fund several of the groups involved.',
    editorial_summary_de = 'Die Politik des "totalen Friedens" eröffnete parallele Verhandlungen mit der ELN, FARC-Dissidentengruppen und dem Clan del Golfo. Ein Tribunal klagte frühere FARC-Mitglieder wegen Kriegsverbrechen an, und das größte Kartell setzte die Gespräche aus, nachdem sich der kolumbianische und der US-Präsident verständigt hatten. Kokaanbau und Goldschmuggel finanzieren mehrere der beteiligten Gruppen.',
    updated_at = now()
WHERE id = 'colombia_armed_groups_peace';

-- ------------------------------------------------------ atomic: US alignment
INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES
(
 'colombia_us_rapprochement', 'colombia_us_alignment', 1,
 'Negotiated rapprochement', 'Ausgehandelte Annäherung',
 'The channel was repaired', 'Der Gesprächskanal wurde repariert',
 'Coverage of the reversal treats the White House meeting as evidence that the relationship remains negotiable: threats gave way to an invitation, both governments claimed a working understanding, and cooperation on security and trade resumed.',
 'Die Berichterstattung über die Kehrtwende wertet das Treffen im Weißen Haus als Beleg dafür, dass die Beziehung verhandelbar bleibt: Auf Drohungen folgte eine Einladung, beide Regierungen reklamierten eine Arbeitsverständigung, und die Zusammenarbeit bei Sicherheit und Handel wurde wieder aufgenommen.',
 ARRAY['Reuters','Associated Press','BBC World','Deutsche Welle','CNN','The Guardian','New York Times','France 24','France 24 (EN)','Le Monde','NPR','Euronews','Bloomberg','Financial Times','El País'],
 ARRAY['détente','detente','amends','meeting','reunión','encuentro','invit','pacto','acuerdo','visita','recibe','host','talks','deal'],
 true, ARRAY['AMERICAS-USA'], true, 1
),
(
 'colombia_us_coercion', 'colombia_us_alignment', -1,
 'Coercion against a partner', 'Zwang gegen einen Partner',
 'Threats replaced diplomacy', 'Drohungen ersetzten Diplomatie',
 'The critical reading holds that an allied government was subjected to a threatened military operation, tariff pressure and sanctions designations over a policy dispute, and that Bogotá''s formal complaint marked a durable shift in what the relationship can be assumed to guarantee.',
 'Die kritische Lesart hält fest, dass eine verbündete Regierung wegen eines politischen Streits mit einer angedrohten Militäroperation, Zolldruck und Sanktionslistungen überzogen wurde und dass Bogotás förmliche Beschwerde eine dauerhafte Verschiebung dessen markiert, was die Beziehung noch garantiert.',
 ARRAY['Reuters','Associated Press','BBC World','Deutsche Welle','CNN','The Guardian','New York Times','France 24','France 24 (EN)','Le Monde','NPR','Euronews','Bloomberg','Financial Times','El País'],
 ARRAY['threat','amenaza','military operation','operación militar','military action','tariff','arancel','sanction','sanción','sovereignty','soberan','complaint','queja','insult','slander'],
 true, ARRAY['AMERICAS-USA'], true, 2
),
(
 'colombia_us_imperial_overreach', 'colombia_us_alignment', -2,
 'Hegemonic imposition', 'Hegemoniale Anmaßung',
 'A sovereign state treated as a subordinate', 'Ein souveräner Staat als Untergebener behandelt',
 'State and non-Western outlets present the episode as an assertion of hemispheric domination rather than a bilateral dispute: military threats against a sovereign government, coupled with strikes in neighbouring Venezuela, are framed as the working method of US regional primacy.',
 'Staatliche und außerwestliche Medien stellen die Episode als Behauptung hemisphärischer Vorherrschaft dar und nicht als bilateralen Streit: Militärdrohungen gegen eine souveräne Regierung, verbunden mit Angriffen im benachbarten Venezuela, gelten als Arbeitsmethode US-amerikanischer Regionalvormacht.',
 ARRAY['CGTN','China Daily','Global Times','Xinhua','RT','TASS','TASS (EN)','Sputnik','RIA Novosti','Press TV','Al Jazeera','Anadolu Agency','Al-Ahram'],
 ARRAY['hegemon','imperial','sovereignty','soberan','interference','injerencia','domination','bullying','unilateral'],
 false, ARRAY['AMERICAS-USA'], true, 3
);

-- ----------------------------------------------- atomic: political transition
INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES
(
 'colombia_transition_mandate', 'colombia_political_transition', 2,
 'A mandate for security', 'Ein Mandat für Sicherheit',
 'Voters chose a harder line', 'Die Wähler wählten eine härtere Linie',
 'The sympathetic reading treats the result as a decisive verdict on the outgoing government''s security record: an electorate exhausted by cartel violence and stalled negotiations voted for confrontation with armed groups and closer working relations with Washington.',
 'Die wohlwollende Lesart wertet das Ergebnis als deutliches Urteil über die Sicherheitsbilanz der scheidenden Regierung: Eine von Kartellgewalt und stockenden Verhandlungen erschöpfte Wählerschaft stimmte für die Konfrontation mit bewaffneten Gruppen und engere Arbeitsbeziehungen zu Washington.',
 ARRAY['El Mundo','Reforma','El Universal','Clarín','La Nación','Infobae'],
 ARRAY['mandato','victoria','triunfo','ganó','seguridad','mano dura','cartel','respaldo','apoyo','elegido','contundente'],
 true, ARRAY['AMERICAS-ANDEAN'], true, 1
),
(
 'colombia_transition_institutional_concern', 'colombia_political_transition', -1,
 'Concern for institutional norms', 'Sorge um institutionelle Normen',
 'The result strains the guardrails', 'Das Ergebnis belastet die Schutzmechanismen',
 'The critical reading raises the endorsement of a candidate by a foreign head of state before the vote, the outgoing president''s allegation of foreign interference, and the losing camp''s legal challenge as pressures on Colombian institutional norms, independent of the winner''s programme.',
 'Die kritische Lesart benennt die Unterstützung eines Kandidaten durch ein ausländisches Staatsoberhaupt vor der Wahl, den Vorwurf ausländischer Einflussnahme durch den scheidenden Präsidenten und die Klage des unterlegenen Lagers als Belastungen kolumbianischer institutioneller Normen -- unabhängig vom Programm des Siegers.',
 ARRAY['El País','The Guardian','Deutsche Welle','France 24','France 24 (EN)','Le Monde','BBC World','New York Times','CNN','Euronews','Reuters','Associated Press'],
 ARRAY['institucional','institutional','democracia','democracy','injerencia','interference','fraude','impugna','legal challenge','norms','autoritari','riesgo','concern','fears'],
 true, ARRAY['AMERICAS-ANDEAN'], true, 2
);

-- ------------------------------------------- atomic: armed groups and peace
INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES
(
 'colombia_peace_negotiation_defense', 'colombia_armed_groups_peace', 1,
 'Negotiation is the workable route', 'Verhandlung ist der gangbare Weg',
 'Talks are how the war ends', 'Gespräche beenden den Krieg',
 'The supportive reading holds that negotiated demobilisation, transitional justice and rural investment are the only instruments that have historically reduced Colombia''s armed conflict, and that suspending talks under external pressure forfeits the mechanism without offering a replacement.',
 'Die unterstützende Lesart hält fest, dass ausgehandelte Demobilisierung, Übergangsjustiz und Investitionen im ländlichen Raum die einzigen Instrumente sind, die Kolumbiens bewaffneten Konflikt historisch verringert haben, und dass die Aussetzung der Gespräche unter äußerem Druck diesen Mechanismus preisgibt, ohne Ersatz zu bieten.',
 ARRAY['El País','Deutsche Welle','Al Jazeera','Anadolu Agency','UN News','The Guardian','France 24','France 24 (EN)','BBC World'],
 ARRAY['paz total','proceso de paz','negociac','peace talks','peace process','desmoviliz','transitional justice','justicia transicional','diálogo','acuerdo'],
 true, ARRAY['AMERICAS-ANDEAN'], true, 1
),
(
 'colombia_peace_process_failure', 'colombia_armed_groups_peace', -1,
 'Negotiation emboldened the groups', 'Verhandlungen bestärkten die Gruppen',
 'Talks bought the cartels time', 'Gespräche verschafften den Kartellen Zeit',
 'The critical reading holds that open-ended negotiations let guerrilla factions and cartels consolidate territory, recruit and expand coca and gold revenues while nominally at the table, and that violence rose over the period the policy was in force.',
 'Die kritische Lesart hält fest, dass ergebnisoffene Verhandlungen es Guerillafraktionen und Kartellen erlaubten, Gebiete zu festigen, zu rekrutieren sowie Koka- und Goldeinnahmen auszuweiten, während sie nominell am Tisch saßen, und dass die Gewalt im Geltungszeitraum der Politik zunahm.',
 ARRAY['El Mundo','Reforma','El Universal','Clarín','La Nación','Infobae'],
 ARRAY['violencia','fracaso','enseñorea','dispara','control territorial','reclutamiento','impunidad','failed','emboldened','expansión'],
 true, ARRAY['AMERICAS-ANDEAN'], true, 2
);

-- --------------------------------------------------------- theater roll-up cards
-- Publisher pools disjoint WITHIN each sign bucket:
--   positive: [LatAm/Spanish right] [mainstream + global south]
--   negative: [mainstream] [state/global south] [LatAm/Spanish right]
INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES
(
 'colombia_theater_hard_turn', 'colombia_theater', 2,
 'A country turning hard', 'Ein Land im harten Kurswechsel',
 'The electorate chose confrontation', 'Die Wählerschaft wählte Konfrontation',
 'One reading runs through every arena at once: voters rejected negotiation with armed groups, elected a government promising confrontation and closer alignment with Washington, and treated the outgoing security policy as the thing that failed.',
 'Eine Lesart durchzieht alle Bereiche zugleich: Die Wähler lehnten Verhandlungen mit bewaffneten Gruppen ab, wählten eine Regierung, die Konfrontation und engere Anlehnung an Washington verspricht, und werteten die scheidende Sicherheitspolitik als das Gescheiterte.',
 ARRAY['El Mundo','Reforma','El Universal','Clarín','La Nación','Infobae'],
 ARRAY['mandato','seguridad','mano dura','cartel','violencia','victoria','contundente'],
 false, ARRAY['AMERICAS-ANDEAN'], true, 1
),
(
 'colombia_theater_negotiated_path', 'colombia_theater', 1,
 'The negotiated path holds', 'Der Verhandlungsweg trägt',
 'Bargaining still works, at home and abroad', 'Verhandeln funktioniert weiter, innen wie außen',
 'A second reading emphasises that both the confrontation with Washington and the conflict with armed groups were managed through bargaining rather than force: the military threat ended in a White House meeting, and negotiation remains the only instrument that has historically shrunk the armed conflict.',
 'Eine zweite Lesart betont, dass sowohl die Konfrontation mit Washington als auch der Konflikt mit bewaffneten Gruppen durch Verhandlung statt Gewalt bearbeitet wurden: Die Militärdrohung endete in einem Treffen im Weißen Haus, und Verhandlung bleibt das einzige Instrument, das den bewaffneten Konflikt historisch verkleinert hat.',
 ARRAY['Reuters','Associated Press','BBC World','Deutsche Welle','CNN','The Guardian','New York Times','France 24','France 24 (EN)','Le Monde','NPR','Euronews','Bloomberg','Financial Times','El País','Al Jazeera','Anadolu Agency','UN News'],
 ARRAY['détente','acuerdo','negociac','peace process','paz total','diálogo','meeting'],
 false, ARRAY['AMERICAS-ANDEAN'], true, 2
),
(
 'colombia_theater_external_pressure', 'colombia_theater', -1,
 'Sovereignty under external pressure', 'Souveränität unter äußerem Druck',
 'Decisions shaped from outside', 'Von außen geformte Entscheidungen',
 'Mainstream coverage across the arenas describes a state whose room for manoeuvre narrowed from outside: a threatened military operation, tariff and sanctions pressure, a foreign endorsement in a national election, and an understanding with Washington that reshaped domestic negotiations with armed groups.',
 'Etablierte Berichterstattung beschreibt über alle Bereiche hinweg einen Staat, dessen Handlungsspielraum von außen verengt wurde: eine angedrohte Militäroperation, Zoll- und Sanktionsdruck, eine ausländische Wahlempfehlung im nationalen Wahlkampf und eine Verständigung mit Washington, die die inneren Verhandlungen mit bewaffneten Gruppen umformte.',
 ARRAY['Reuters','Associated Press','BBC World','Deutsche Welle','CNN','The Guardian','New York Times','France 24','France 24 (EN)','Le Monde','NPR','Euronews','Bloomberg','Financial Times','El País'],
 ARRAY['threat','amenaza','sovereignty','soberan','injerencia','interference','institutional','democracia','tariff','sanction'],
 false, ARRAY['AMERICAS-ANDEAN'], true, 3
),
(
 'colombia_theater_hegemonic_critique', 'colombia_theater', -2,
 'Hemispheric domination critique', 'Kritik hemisphärischer Vorherrschaft',
 'The region as a sphere of influence', 'Die Region als Einflusssphäre',
 'State and non-Western outlets read the same events as a single demonstration of US primacy in the hemisphere -- military threats, strikes in neighbouring Venezuela and open intervention in an allied democracy''s election -- rather than as separate bilateral disputes.',
 'Staatliche und außerwestliche Medien lesen dieselben Ereignisse als eine einzige Demonstration US-amerikanischer Vormacht in der Hemisphäre -- Militärdrohungen, Angriffe im benachbarten Venezuela und offene Einmischung in die Wahl einer verbündeten Demokratie -- und nicht als getrennte bilaterale Streitfälle.',
 ARRAY['CGTN','China Daily','Global Times','Xinhua','RT','TASS','TASS (EN)','Sputnik','RIA Novosti','Press TV','Al-Ahram'],
 ARRAY['hegemon','imperial','soberan','injerencia','domination','unilateral','sphere of influence'],
 false, ARRAY['AMERICAS-USA'], true, 4
);

COMMIT;
