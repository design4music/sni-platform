-- eu_cohesion_theater — theater-level narrative cards (FN_THEATER_BUILD_SPEC §5.5).
-- The theater carries no fn_anchor bundle; these cards' sample headlines + counts
-- roll up from the member atomics' title_narratives, matched by stance-SIGN +
-- publisher (THEATER_ROLLUP_SQL in apps/frontend/lib/friction-nodes.ts).
-- Cohesion axis: +2 defends the EU's cohesion / liberal-institutional order;
-- -1 the sovereigntist revolt against Brussels (from within the West); -2 the
-- Russian/Chinese rift-exploitation. Within the NEGATIVE sign bucket the -1 and -2
-- cards are publisher-DISJOINT (broad Western vs Russian/Chinese state) so their
-- uncapped counts partition cleanly. The +2 card shares Western publishers with the
-- -1 card but is the opposite sign, so no title double-counts.
-- Idempotent: ON CONFLICT (id) DO NOTHING.
SET client_encoding TO 'UTF8';

INSERT INTO narratives_v2
  (id, name_en, name_de, claim_en, claim_de, actor_centroids, framing_keywords,
   is_active, publishers, fn_id, display_order, stance_label_en, stance_label_de,
   stance, framing_required)
VALUES
(
 'eu_cohesion_hold',
 'European cohesion and the rule of law must hold against centrifugal forces',
 'Europäischer Zusammenhalt und Rechtsstaatlichkeit müssen den Fliehkräften standhalten',
 'Pro-cohesion framing (Western mainstream and pro-integration press) treats the Union''s shared rules as worth defending: rule-of-law conditionality and anti-corruption standards, a democratic order guarded against the radical right, solidarity on migration and budget, and a firewall against normalising forces hostile to the European project. It reads the disputes as tests the Union must pass to hold together. Vocabulary: rule of law, solidarity, firewall, democracy, standards.',
 'Die Zusammenhalts-Rahmung (westlicher Mainstream und integrationsfreundliche Presse) sieht die gemeinsamen Regeln der Union als verteidigenswert: Rechtsstaats-Konditionalität und Antikorruptionsstandards, eine gegen die radikale Rechte geschützte demokratische Ordnung, Solidarität bei Migration und Haushalt und eine Brandmauer gegen die Normalisierung projektfeindlicher Kräfte. Sie deutet die Konflikte als Prüfungen, die die Union bestehen muss.',
 ARRAY['NON-STATE-EU','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-SOUTH','EUROPE-VISEGRAD'],
 ARRAY['rule of law','Rechtsstaatlichkeit','solidarity','Solidarität','firewall','Brandmauer','democracy','Demokratie','far-right','rechtsextrem','standards','cohesion','Zusammenhalt'],
 true,
 ARRAY['Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Sky News','Handelsblatt','Frankfurter Allgemeine','Le Figaro','Corriere della Sera','El Mundo','The Telegraph','Wall Street Journal','Bloomberg','Die Presse','Der Standard','Kurier','eKathimerini'],
 'eu_cohesion_theater', 1,
 'European cohesion must hold', 'Europäischer Zusammenhalt muss halten',
 2, false
),
(
 'eu_sovereigntist_revolt',
 'Nations and voters are resisting an overreaching Brussels',
 'Nationen und Wähler wehren sich gegen ein übergriffiges Brüssel',
 'Sovereigntist framing (national-conservative governments and sympathetic voices across member states) holds that Brussels overreaches into national competences, budgets and identity, that mainstream parties wrongly exclude movements millions vote for, and that member states should reclaim control over migration, money and the rule of their own institutions. It runs from within the Union, not against its existence. Vocabulary: sovereignty, overreach, net contributor, will of voters, national control.',
 'Die souveränistische Rahmung (nationalkonservative Regierungen und wohlwollende Stimmen in den Mitgliedstaaten) sieht Brüssel als übergriffig gegenüber nationalen Zuständigkeiten, Haushalten und Identität, den Ausschluss von Bewegungen, die Millionen wählen, als falsch und fordert, dass die Mitgliedstaaten die Kontrolle über Migration, Geld und ihre Institutionen zurückgewinnen. Sie wirkt aus der Union heraus, nicht gegen deren Bestand.',
 ARRAY['EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-SOUTH','EUROPE-VISEGRAD'],
 ARRAY['sovereignty','Souveränität','overreach','Bevormundung','net contributor','Nettozahler','will of the people','Millionen Wähler','national control','unaffordable','establishment','crackdown','Grenzen schützen'],
 true,
 ARRAY['Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Sky News','Handelsblatt','Frankfurter Allgemeine','Le Figaro','Corriere della Sera','El Mundo','The Telegraph','Wall Street Journal','Bloomberg','Die Presse','Der Standard','Kurier','eKathimerini'],
 'eu_cohesion_theater', 2,
 'Sovereigntist revolt against Brussels', 'Souveränistische Revolte gegen Brüssel',
 -1, false
),
(
 'eu_fracture_rift_exploitation',
 'A divided EU is proof of Western decline and hypocrisy',
 'Eine gespaltene EU beweist westlichen Niedergang und westliche Heuchelei',
 'Rift-exploitation framing (Russian and Chinese state media) amplifies every internal European dispute as evidence that the Union coerces its members, is fiscally and politically overstretched, and is fracturing under the weight of migration, budget fights and a collapsing liberal centre. It is adversarial to European cohesion as a whole and takes no genuine side in the internal disputes it magnifies. Vocabulary: coercion, decline, hypocrisy, chaos, collapse.',
 'Die Riss-Ausnutzungs-Rahmung (russische und chinesische Staatsmedien) verstärkt jeden inneren europäischen Streit als Beleg, dass die Union ihre Mitglieder zwingt, finanziell und politisch überfordert ist und unter Migration, Haushaltsstreit und einer zusammenbrechenden liberalen Mitte zerfällt. Sie ist der europäischen Kohäsion insgesamt feindlich gesinnt und ergreift in den vergrößerten Konflikten keine echte Partei.',
 ARRAY['EUROPE-RUSSIA','ASIA-CHINA'],
 ARRAY['coercion','decline','hypocrisy','chaos','collapse','crisis','disunity','persecution','failing'],
 true,
 ARRAY['RT','TASS (EN)','TASS','Lenta.ru','Gazeta.ru','Izvestia','RIA Novosti','BelTA Russian','CGTN','China Daily','Global Times','Xinhua'],
 'eu_cohesion_theater', 3,
 'Russian & Chinese rift-exploitation', 'Russische & chinesische Riss-Ausnutzung',
 -2, false
)
ON CONFLICT (id) DO NOTHING;
