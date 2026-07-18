-- latam_hemispheric_theater: theater-level narrative cards (spec section 5.5).
--
-- THEATER_ROLLUP_SQL sources each card from member atomics' title_narratives
-- where sign(atomic.stance) = sign(theater.stance) AND publisher is in the
-- card's list. match_count is uncapped over that match, so two cards of the
-- SAME SIGN with overlapping publishers double-count the same titles.
--
-- Publisher pools are therefore disjoint WITHIN each sign bucket:
--   positive: [South American press] [Chinese/Russian state] [US conservative]
--   negative: [wires + South American press] [European press] [US conservative]
-- Across signs the pools may repeat -- US conservative outlets appear on both
-- the positive tariff card and the negative China card, which is the actual
-- position that bloc holds, and opposite signs pull different-signed atomic
-- titles so nothing double-counts.
--
-- Every atomic narrative's publisher pool has a same-sign theater card, so no
-- atomic narrative is left homeless at theater level (the Greenland -1 lesson).

BEGIN;

INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES
(
 'latam_theater_regional_agency', 'latam_hemispheric_theater', 2,
 'The region negotiates for itself', 'Die Region verhandelt für sich selbst',
 'Courted by all sides, committed to none', 'Von allen umworben, keinem verpflichtet',
 'South American coverage across all three arenas presents the region as an actor with leverage rather than a prize: playing buyers against each other, holding out for processing and value-added stages, and treating simultaneous deals with Washington, Brussels and Beijing as the point rather than a contradiction.',
 'Südamerikanische Berichterstattung stellt die Region in allen drei Arenen als Akteur mit Verhandlungsmacht dar und nicht als Beute: Sie spielt Abnehmer gegeneinander aus, besteht auf Verarbeitung und Wertschöpfung im Land und betrachtet gleichzeitige Abkommen mit Washington, Brüssel und Peking als das Ziel und nicht als Widerspruch.',
 ARRAY['Clarín','La Nación','O Globo','Folha de S.Paulo','O Estado de S. Paulo','Infobae','Brazil Reports','El Mercurio','La Tercera','El Observador'],
 ARRAY['soberan','estratégic','acordo','acuerdo','negociar','exporta','agregar valor','oportunidad','oportunidade'],
 false, ARRAY['AMERICAS-BRAZIL'], true, 1
),
(
 'latam_theater_eastern_partnership', 'latam_hemispheric_theater', 1,
 'Partnership beyond the West', 'Partnerschaft jenseits des Westens',
 'A second partner on offer', 'Ein zweiter Partner steht bereit',
 'Chinese and Russian state media present their engagement across minerals, finance and infrastructure as an alternative to Western conditionality, and frame US objections to those projects as an attempt to keep the region inside a single sphere of influence.',
 'Chinesische und russische Staatsmedien stellen ihr Engagement bei Rohstoffen, Finanzierung und Infrastruktur als Alternative zu westlicher Konditionalität dar und werten US-Einwände gegen diese Projekte als Versuch, die Region in einer einzigen Einflusssphäre zu halten.',
 ARRAY['CGTN','China Daily','Global Times','Xinhua','People''s Daily','RT','TASS','TASS (EN)','tass.com','Sputnik','RIA Novosti','Izvestia','Kommersant','BelTA'],
 ARRAY['cooperation','win-win','partnership','mutual benefit','sphere of influence','hegemon','合作','共赢'],
 false, ARRAY['ASIA-CHINA'], true, 2
),
(
 'latam_theater_leverage_works', 'latam_hemispheric_theater', 2,
 'Pressure is the working instrument', 'Druck ist das wirksame Instrument',
 'Leverage produced the concessions', 'Druckmittel haben die Zugeständnisse gebracht',
 'America-First commentary holds that tariffs, designations and contract challenges are what actually moved South American governments, and that declining to use that leverage would cede the hemisphere''s trade terms and resource contracts to Beijing by default.',
 'America-First-Kommentare halten fest, dass Zölle, Listungen und Auftragsanfechtungen es waren, die südamerikanische Regierungen tatsächlich bewegt haben, und dass ein Verzicht auf diese Druckmittel die Handelsbedingungen und Rohstoffverträge der Hemisphäre kampflos an Peking abträte.',
 ARRAY['Fox News','New York Post','Washington Examiner','Breitbart','Newsmax','The National Interest','The Federalist','Daily Caller','Washington Times','National Review','Atlantic Council'],
 ARRAY['leverage','reciprocal','unfair','deal','concession','enforcement','hemisphere'],
 false, ARRAY['AMERICAS-USA'], true, 3
),
(
 'latam_theater_terms_imposed', 'latam_hemispheric_theater', -1,
 'Terms set from outside', 'Von außen gesetzte Bedingungen',
 'The costs land locally', 'Die Kosten fallen vor Ort an',
 'Mainstream and regional reporting treats the three arenas as variations on one asymmetry: tariffs, quota allocations and extraction contracts are largely determined abroad, while the adjustment costs -- to exporters, to public budgets, to the communities around mine sites -- are absorbed within the region.',
 'Etablierte und regionale Berichterstattung behandelt die drei Arenen als Varianten derselben Asymmetrie: Zölle, Quotenzuteilungen und Förderverträge werden überwiegend im Ausland bestimmt, während die Anpassungskosten -- für Exporteure, öffentliche Haushalte und die Gemeinden rund um die Minen -- in der Region anfallen.',
 ARRAY['Reuters','Associated Press','Bloomberg','Financial Times','The Guardian','Deutsche Welle','El País','Al Jazeera','The Hindu','NPR','S&P Global','Página 12'],
 ARRAY['coercion','asymmetr','sovereignty','soberan','extractivis','comunidades','represalia','punish'],
 false, ARRAY['AMERICAS-BRAZIL'], true, 4
),
(
 'latam_theater_european_objection', 'latam_hemispheric_theater', -2,
 'European objection to the opening', 'Europäischer Einwand gegen die Öffnung',
 'Europe resists its own agreement', 'Europa wehrt sich gegen sein eigenes Abkommen',
 'European coverage carries the internal resistance to market opening: producer groups object to competition under different cost and regulatory conditions, environmental critics object to the pressure that expanded agricultural exports place on forest cover, and several member states and parliaments have moved to block or challenge ratification.',
 'Europäische Berichterstattung trägt den internen Widerstand gegen die Marktöffnung: Erzeugerverbände wenden sich gegen Konkurrenz unter anderen Kosten- und Regulierungsbedingungen, Umweltkritiker gegen den Druck ausgeweiteter Agrarexporte auf die Waldbestände, und mehrere Mitgliedstaaten und Parlamente haben die Ratifizierung blockiert oder angefochten.',
 ARRAY['Le Figaro','Le Monde','Frankfurter Allgemeine','Süddeutsche Zeitung','Die Zeit','Tagesschau','Corriere della Sera','ANSA','NZZ','Swissinfo','EurActiv','Euronews','France 24','France 24 (EN)','Boulevard Voltaire'],
 ARRAY['agriculteur','Bauern','Landwirt','farmer','viande','Rindfleisch','déforestation','Entwaldung','Abholzung','Amazonas','Klima','Schutzklausel','ratifi','Quote','quota'],
 false, ARRAY['NON-STATE-EU'], true, 5
),
(
 'latam_theater_strategic_warning', 'latam_hemispheric_theater', -2,
 'Strategic penetration warning', 'Warnung vor strategischer Durchdringung',
 'Commerce with a strategic tail', 'Handel mit strategischem Nachlauf',
 'US security-oriented commentary reads Chinese port, rail and mineral holdings in the hemisphere as dual-use positioning rather than ordinary commerce, and treats each concession awarded as a durable strategic loss rather than a single contract.',
 'US-sicherheitspolitische Kommentare deuten chinesische Hafen-, Bahn- und Mineralienbeteiligungen in der Hemisphäre als militärisch mitnutzbare Positionierung statt als gewöhnlichen Handel und werten jede vergebene Konzession als dauerhaften strategischen Verlust und nicht als einzelnen Auftrag.',
 ARRAY['Fox News','New York Post','Washington Examiner','Breitbart','Newsmax','The National Interest','The Federalist','Daily Caller','Washington Times','National Review','Atlantic Council'],
 ARRAY['dual-use','strategic','military','backyard','hemisphere','Beijing','threat','influence'],
 false, ARRAY['AMERICAS-USA'], true, 6
);

COMMIT;
