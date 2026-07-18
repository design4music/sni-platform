-- latam_hemispheric_theater: atomic + theater narratives and completeness fields
-- (FN_THEATER_BUILD_SPEC 0a, steps 6-8).
--
-- Coalition design is grounded in the measured publisher distribution, not
-- assumed:
--   * Chinese/Russian state media carry real volume in these centroids
--     (CGTN 84, China Daily 38, Global Times 32, RT 24, TASS 33) AND push an
--     actual line -- "Chinese Embassy in Peru firmly opposes and strongly
--     condemns US spread of false claims smearing Chancay Port project". They
--     earn a card on latam_resource_access.
--   * On latam_us_trade_pressure the same bloc is near-absent (CGTN 2), so no
--     state-media card is authored there. Presence is not a line (the
--     us_china_theater lesson).
--   * Mining.com alone is 60 of ~110 resource titles. It is trade press with no
--     stance, so it is deliberately in NO coalition -- those titles attribute to
--     the FN but to no narrative, which is the honest outcome.
--
-- Where two narratives of the same sign share a publisher pool (the two
-- European positions on Mercosur) BOTH carry framing_required=true with
-- disjoint keywords, per the three-stance pattern in section 5. Publisher alone
-- cannot disambiguate them.
--
-- FN description/editorial text is neutral, fact-based and evergreen; all
-- framing lives in narratives_v2.

BEGIN;

-- ---------------------------------------------------------------- completeness
UPDATE friction_nodes SET
    name_de = 'Externe Mächte in Lateinamerika',
    description_en = 'Competition among external powers -- the United States, China and the European Union -- for trade terms, resource access and infrastructure contracts in South America.',
    description_de = 'Wettbewerb externer Mächte -- der Vereinigten Staaten, Chinas und der Europäischen Union -- um Handelsbedingungen, Rohstoffzugang und Infrastrukturaufträge in Südamerika.',
    editorial_summary_en = 'Brazil, the Southern Cone and the Andean states are courted and pressured by three external blocs at once. The European Union negotiates market access through the Mercosur agreement, the United States applies tariffs and sanctions, and China finances ports, rail and mineral supply. Scope is South America; Mexico, Central America and the Caribbean are covered by their own theaters.',
    editorial_summary_de = 'Brasilien, der Südkegel und die Andenstaaten werden zugleich von drei externen Blöcken umworben und unter Druck gesetzt. Die Europäische Union verhandelt über das Mercosur-Abkommen den Marktzugang, die Vereinigten Staaten setzen Zölle und Sanktionen ein, und China finanziert Häfen, Bahnstrecken und Mineralienlieferungen. Der Zuschnitt umfasst Südamerika; Mexiko, Mittelamerika und die Karibik werden von eigenen Schauplätzen abgedeckt.',
    updated_at = now()
WHERE id = 'latam_hemispheric_theater';

UPDATE friction_nodes SET
    name_de = 'Zugang zu kritischen Rohstoffen und Infrastruktur',
    description_en = 'External competition for South American critical minerals, mining concessions and transport infrastructure, including lithium, copper and rare earths.',
    description_de = 'Externer Wettbewerb um südamerikanische kritische Rohstoffe, Bergbaukonzessionen und Verkehrsinfrastruktur, darunter Lithium, Kupfer und Seltene Erden.',
    editorial_summary_en = 'The United States, China, the European Union and India all pursue supply agreements and mining stakes across Brazil, Chile, Argentina, Peru and Bolivia. Chinese operators additionally finance and build physical infrastructure, including the Chancay deep-water terminal in Peru and river and rail projects in the Southern Cone.',
    editorial_summary_de = 'Die Vereinigten Staaten, China, die Europäische Union und Indien verfolgen alle Lieferabkommen und Bergbaubeteiligungen in Brasilien, Chile, Argentinien, Peru und Bolivien. Chinesische Akteure finanzieren und bauen zusätzlich physische Infrastruktur, darunter das Tiefwasserterminal Chancay in Peru sowie Fluss- und Bahnprojekte im Südkegel.',
    updated_at = now()
WHERE id = 'latam_resource_access';

UPDATE friction_nodes SET
    name_de = 'US-Zoll- und Sanktionsdruck',
    description_en = 'United States tariffs, sanctions designations and trade-enforcement measures applied to South American states.',
    description_de = 'Zölle, Sanktionslistungen und handelspolitische Zwangsmaßnahmen der Vereinigten Staaten gegenüber südamerikanischen Staaten.',
    editorial_summary_en = 'Washington has proposed or imposed tariffs on Brazilian goods and issued sanctions designations touching Brazilian and Colombian officials and networks. Affected governments respond through negotiation, retaliation or appeals to the domestic electorate, and the measures intersect with election cycles in the targeted states.',
    editorial_summary_de = 'Washington hat Zölle auf brasilianische Waren vorgeschlagen oder verhängt und Sanktionslistungen gegen brasilianische und kolumbianische Amtsträger und Netzwerke ausgesprochen. Betroffene Regierungen reagieren mit Verhandlungen, Gegenmaßnahmen oder der Ansprache der eigenen Wählerschaft; die Maßnahmen überschneiden sich mit Wahlzyklen in den betroffenen Staaten.',
    updated_at = now()
WHERE id = 'latam_us_trade_pressure';

UPDATE friction_nodes SET
    name_de = 'EU-Mercosur-Marktzugang',
    description_en = 'Ratification and implementation of the trade agreement between the European Union and Mercosur, including quota allocation, import standards and related EFTA talks.',
    description_de = 'Ratifizierung und Umsetzung des Handelsabkommens zwischen der Europäischen Union und dem Mercosur, einschließlich Quotenverteilung, Einfuhrstandards und damit verbundener EFTA-Gespräche.',
    editorial_summary_en = 'The agreement concluded between the two blocs requires ratification across European institutions and member states. France, Poland and Switzerland have registered formal opposition, Poland has filed a challenge at the EU Court of Justice, and the European Union has restricted certain Brazilian meat imports. Uruguay and Argentina have ratified. The EU deforestation regulation applies to several covered commodities.',
    editorial_summary_de = 'Das zwischen den beiden Blöcken geschlossene Abkommen bedarf der Ratifizierung durch die europäischen Institutionen und Mitgliedstaaten. Frankreich, Polen und die Schweiz haben förmlichen Widerstand angemeldet, Polen hat Klage beim Gerichtshof der EU eingereicht, und die Europäische Union hat bestimmte brasilianische Fleischeinfuhren beschränkt. Uruguay und Argentinien haben ratifiziert. Die EU-Entwaldungsverordnung gilt für mehrere erfasste Rohstoffe.',
    updated_at = now()
WHERE id = 'latam_eu_market_access';

-- ------------------------------------------------------- atomic: resource access
INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES
(
 'resource_south_south_partnership', 'latam_resource_access', 2,
 'South-South development partnership', 'Süd-Süd-Entwicklungspartnerschaft',
 'Cooperation brings development', 'Kooperation bringt Entwicklung',
 'Chinese and Russian state media frame mineral purchases, port finance and rail construction as mutually beneficial South-South cooperation that delivers infrastructure Western lenders declined to fund, and cast US warnings about those projects as smear campaigns intended to deny the region a second partner.',
 'Chinesische und russische Staatsmedien stellen Mineralienkäufe, Hafenfinanzierung und Bahnbau als beiderseits vorteilhafte Süd-Süd-Kooperation dar, die Infrastruktur liefert, deren Finanzierung westliche Kreditgeber ablehnten, und werten US-Warnungen vor diesen Projekten als Verleumdungskampagnen, die der Region einen zweiten Partner verwehren sollen.',
 ARRAY['CGTN','China Daily','Global Times','Xinhua','People''s Daily','RT','TASS','TASS (EN)','tass.com','Sputnik','RIA Novosti','Izvestia','Kommersant','BelTA'],
 ARRAY['cooperation','win-win','partnership','development','mutual benefit','Zusammenarbeit','cooperación','beneficio mutuo','合作','共赢'],
 false, ARRAY['ASIA-CHINA'], true, 1
),
(
 'resource_sovereign_development', 'latam_resource_access', 1,
 'Sovereign resource strategy', 'Souveräne Rohstoffstrategie',
 'The region sets its own terms', 'Die Region setzt eigene Bedingungen',
 'South American outlets present their governments as active agents rather than objects of competition: courting several buyers at once, legislating national minerals policy and pressing to capture processing and value-added stages domestically instead of exporting raw ore.',
 'Südamerikanische Medien stellen ihre Regierungen als handelnde Akteure statt als Objekte des Wettbewerbs dar: Sie umwerben mehrere Abnehmer zugleich, verankern eine nationale Rohstoffpolitik gesetzlich und drängen darauf, Verarbeitung und Wertschöpfung im Land zu halten, statt Roherz auszuführen.',
 ARRAY['Clarín','La Nación','O Globo','Folha de S.Paulo','O Estado de S. Paulo','Infobae','Brazil Reports','El Mercurio','La Tercera'],
 ARRAY['soberan','estratégic','agregar valor','valor agregado','política nacional','industrializ','negociar','acordo','acuerdo'],
 true, ARRAY['AMERICAS-BRAZIL'], true, 2
),
(
 'resource_extractivism_critique', 'latam_resource_access', -1,
 'Extractivism and local cost', 'Extraktivismus und lokale Kosten',
 'Extraction externalises its costs', 'Die Förderung lagert ihre Kosten aus',
 'Critical regional coverage holds that whichever external buyer prevails, the extraction model itself transfers water, land and environmental burdens onto local and indigenous communities while the processed value accrues abroad.',
 'Kritische regionale Berichterstattung hält fest, dass unabhängig davon, welcher externe Abnehmer sich durchsetzt, das Fördermodell selbst Wasser-, Land- und Umweltlasten auf lokale und indigene Gemeinschaften abwälzt, während die verarbeitete Wertschöpfung im Ausland anfällt.',
 ARRAY['Clarín','La Nación','O Globo','Folha de S.Paulo','O Estado de S. Paulo','Infobae','Brazil Reports','El Mercurio','La Tercera','Página 12'],
 ARRAY['extractivis','contaminac','contaminaç','comunidades','indígena','saqueo','socioambiental','medio ambiente','meio ambiente','agua','água','protesta','protesto'],
 true, ARRAY['AMERICAS-BRAZIL'], true, 3
),
(
 'resource_strategic_penetration', 'latam_resource_access', -2,
 'Strategic penetration warning', 'Warnung vor strategischer Durchdringung',
 'Beijing is buying strategic depth', 'Peking kauft strategische Tiefe',
 'US security-oriented commentary treats Chinese port, rail and mineral holdings in the region as dual-use strategic positioning in the Western hemisphere rather than ordinary commerce, and urges Washington to contest those contracts.',
 'US-sicherheitspolitische Kommentare werten chinesische Hafen-, Bahn- und Mineralienbeteiligungen in der Region als militärisch mitnutzbare strategische Positionierung in der westlichen Hemisphäre statt als gewöhnlichen Handel und drängen Washington, diese Aufträge zu bestreiten.',
 ARRAY['Fox News','New York Post','Washington Examiner','Breitbart','Newsmax','The National Interest','The Federalist','Daily Caller','Washington Times','National Review','Atlantic Council'],
 ARRAY['dual-use','strategic','military','backyard','hemisphere','influence','threat','Beijing'],
 false, ARRAY['AMERICAS-USA'], true, 4
);

-- --------------------------------------------------- atomic: US trade pressure
INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES
(
 'trade_pressure_enforcement_justified', 'latam_us_trade_pressure', 2,
 'Legitimate trade enforcement', 'Legitime Handelsdurchsetzung',
 'Tariffs answer unfair practice', 'Zölle antworten auf unfaire Praktiken',
 'America-First commentary holds that tariffs and designations are proportionate responses to trade practices, judicial overreach and criminal networks in the targeted states, and that leverage is the only instrument that has produced concessions.',
 'America-First-Kommentare halten Zölle und Listungen für verhältnismäßige Antworten auf Handelspraktiken, justizielle Übergriffe und kriminelle Netzwerke in den betroffenen Staaten und sehen Druckmittel als einziges Instrument, das Zugeständnisse bewirkt hat.',
 ARRAY['Fox News','New York Post','Washington Examiner','Breitbart','Newsmax','The National Interest','The Federalist','Daily Caller','Washington Times','National Review'],
 ARRAY['unfair','reciprocal','leverage','deal','concession','enforcement'],
 false, ARRAY['AMERICAS-USA'], true, 1
),
(
 'trade_pressure_sovereignty_defense', 'latam_us_trade_pressure', -1,
 'Coercion against a sovereign partner', 'Zwang gegen einen souveränen Partner',
 'Tariffs punish a trade partner', 'Zölle bestrafen einen Handelspartner',
 'Mainstream and regional coverage treats the measures as economic coercion applied to states that run trade deficits with the United States, notes their entanglement with domestic election cycles, and reports the targeted governments seeking negotiated relief or alternative markets.',
 'Etablierte und regionale Berichterstattung wertet die Maßnahmen als wirtschaftlichen Zwang gegen Staaten, die gegenüber den Vereinigten Staaten Handelsdefizite aufweisen, verweist auf ihre Verflechtung mit innenpolitischen Wahlzyklen und berichtet, dass die betroffenen Regierungen Verhandlungslösungen oder Alternativmärkte suchen.',
 ARRAY['Reuters','Associated Press','Bloomberg','Financial Times','The Guardian','Deutsche Welle','El País','Clarín','La Nación','O Globo','Folha de S.Paulo','O Estado de S. Paulo','Al Jazeera','The Hindu','NPR','S&P Global'],
 ARRAY['coercion','retaliation','sovereignty','soberan','represalia','negotiat','punish','threat'],
 false, ARRAY['AMERICAS-BRAZIL'], true, 2
);

-- ------------------------------------------------- atomic: EU market access
INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES
(
 'mercosur_market_opportunity', 'latam_eu_market_access', 2,
 'Market opening for the bloc', 'Marktöffnung für den Block',
 'The agreement opens a large market', 'Das Abkommen öffnet einen großen Markt',
 'South American coverage presents the agreement as long-delayed access to a high-value market, a diversification away from dependence on any single buyer, and a test of whether the bloc can conclude and hold a major external deal.',
 'Südamerikanische Berichterstattung stellt das Abkommen als lange verzögerten Zugang zu einem hochwertigen Markt dar, als Diversifizierung weg von der Abhängigkeit von einem einzelnen Abnehmer und als Prüfstein dafür, ob der Block ein großes Außenabkommen abschließen und halten kann.',
 ARRAY['Clarín','La Nación','O Globo','Folha de S.Paulo','O Estado de S. Paulo','Infobae','Brazil Reports','El Observador','La Tercera'],
 ARRAY['acordo','acuerdo','oportunidad','oportunidade','exporta','mercado','ratific','cotas','cuotas'],
 false, ARRAY['AMERICAS-BRAZIL'], true, 1
),
(
 'mercosur_farm_protection', 'latam_eu_market_access', -2,
 'European farm protection', 'Europäischer Agrarschutz',
 'The deal undercuts European farmers', 'Das Abkommen unterbietet Europas Bauern',
 'Opposition framing in European coverage holds that imported beef, poultry, sugar and ethanol produced under different cost and regulatory conditions will undercut domestic producers, and that quota concessions were granted without adequate safeguards.',
 'Die Oppositionsdarstellung in europäischen Medien hält fest, dass eingeführtes Rind-, Geflügelfleisch, Zucker und Ethanol, die unter anderen Kosten- und Regulierungsbedingungen erzeugt werden, heimische Produzenten unterbieten und dass Quotenzugeständnisse ohne ausreichende Schutzklauseln gewährt wurden.',
 ARRAY['Le Figaro','Le Monde','Frankfurter Allgemeine','Süddeutsche Zeitung','Die Zeit','Tagesschau','Corriere della Sera','ANSA','NZZ','Swissinfo','EurActiv','Euronews','France 24','France 24 (EN)','Boulevard Voltaire'],
 ARRAY['agriculteur','Bauern','Landwirt','farmer','éleveur','viande','Rindfleisch','Fleisch','volaille','poultry','concurrence','Wettbewerbs','Standards','Schutzklausel','clause de sauvegarde','protest','manifestation','quota','Quote'],
 true, ARRAY['NON-STATE-EU'], true, 2
),
(
 'mercosur_environmental_critique', 'latam_eu_market_access', -1,
 'Deforestation and climate objection', 'Entwaldungs- und Klimaeinwand',
 'The deal rewards forest clearance', 'Das Abkommen belohnt Waldrodung',
 'A separate European objection holds that expanding agricultural exports raises pressure on the Amazon and Cerrado, and that the agreement sits awkwardly beside the European Union''s own deforestation regulation and climate commitments.',
 'Ein gesonderter europäischer Einwand hält fest, dass ausgeweitete Agrarexporte den Druck auf Amazonas und Cerrado erhöhen und dass das Abkommen im Widerspruch zur eigenen Entwaldungsverordnung und zu den Klimaverpflichtungen der Europäischen Union steht.',
 ARRAY['Le Figaro','Le Monde','Frankfurter Allgemeine','Süddeutsche Zeitung','Die Zeit','Tagesschau','Corriere della Sera','ANSA','NZZ','Swissinfo','EurActiv','Euronews','France 24','France 24 (EN)','The Guardian'],
 ARRAY['déforestation','Entwaldung','Abholzung','deforestation','Amazon','Amazonas','Amazonie','Regenwald','climat','Klima','climate','Umwelt','environnement','EUDR'],
 true, ARRAY['NON-STATE-EU'], true, 3
);

COMMIT;
