-- eu_cohesion_theater — atomic narratives (FN_THEATER_BUILD_SPEC §5).
-- Model per atomic (friendly-critic, §5): the two Western narratives SHARE a broad
-- Western coalition and compete on stance, so both framing_required=true with
-- DISJOINT framing keywords (publisher alone can't disambiguate an intra-Western
-- dispute). The pro-Kremlin/China narrative has a DISJOINT coalition, so
-- framing_required=false (publisher suffices) — and it sits on the rift-exploitation
-- axis (§5 caveat): schadenfreude at EU disunity, NOT endorsement of either side.
-- Cohesion-axis sign convention: +2 pro-EU-cohesion/liberal-institutional;
-- -1 sovereigntist/anti-Brussels-from-within; -2 pro-Kremlin centrifugal.
-- Idempotent: ON CONFLICT (id) DO NOTHING.
SET client_encoding TO 'UTF8';

INSERT INTO narratives_v2
  (id, name_en, name_de, claim_en, claim_de, actor_centroids, framing_keywords,
   is_active, publishers, fn_id, display_order, stance_label_en, stance_label_de,
   stance, framing_required)
VALUES

-- =================== hungary_rule_of_law ===================
(
 'hungary_eu_standards',
 'Rule of law and EU standards must be upheld in Hungary',
 'Rechtsstaatlichkeit und EU-Standards müssen in Ungarn gelten',
 'Standards-defense framing (Western mainstream) holds that judicial independence, media freedom, anti-corruption and the conditionality mechanism are non-negotiable European commitments, that the frozen funds were a justified response to backsliding, and that the post-transition clean-up of captured institutions is democratic renewal. Vocabulary: rule of law, conditionality, corruption, media freedom, democratic renewal.',
 'Die Standards-Rahmung (westlicher Mainstream) sieht richterliche Unabhängigkeit, Medienfreiheit, Korruptionsbekämpfung und den Konditionalitätsmechanismus als nicht verhandelbare europäische Verpflichtungen, die eingefrorenen Mittel als gerechtfertigte Antwort auf den Abbau des Rechtsstaats und die Aufarbeitung vereinnahmter Institutionen nach dem Machtwechsel als demokratische Erneuerung.',
 ARRAY['NON-STATE-EU','EUROPE-VISEGRAD'],
 ARRAY['rule of law','Rechtsstaatlichkeit','état de droit','stato di diritto','conditionality','Konditionalität','judicial independence','richterliche Unabhängigkeit','media freedom','Pressefreiheit','corruption','Korruption','anti-corruption','backsliding','captured state','democratic renewal','frozen funds','eingefrorene'],
 true,
 ARRAY['Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Sky News','Handelsblatt','Frankfurter Allgemeine','Le Figaro','Corriere della Sera','El Mundo','The Telegraph','Wall Street Journal','Bloomberg','Die Presse','Der Standard','Kurier','eKathimerini'],
 'hungary_rule_of_law', 1,
 'EU rule-of-law standards', 'EU-Rechtsstaatsstandards',
 2, true
),
(
 'hungary_sovereignty_interference',
 'Brussels interferes in a sovereign nation''s democracy',
 'Brüssel mischt sich in die Demokratie eines souveränen Landes ein',
 'Sovereignty framing (national-conservative sympathisers and the ousted camp''s own voice) holds that the conditionality fight was Brussels punishing a democratically elected government and infringing national sovereignty, and reads the domestic reckoning that followed the change of government as political revenge against opponents. Vocabulary: sovereignty, interference, Brussels overreach, double standard, political persecution, revenge.',
 'Die Souveränitäts-Rahmung (nationalkonservative Sympathisanten und die Stimme des abgewählten Lagers) sieht im Konditionalitätsstreit eine Bestrafung einer demokratisch gewählten Regierung durch Brüssel und einen Eingriff in die nationale Souveränität und deutet die innenpolitische Abrechnung nach dem Regierungswechsel als politische Rache an Gegnern.',
 ARRAY['EUROPE-VISEGRAD'],
 ARRAY['sovereignty','Souveränität','souveraineté','interference','Einmischung','ingérence','Brussels overreach','Bevormundung','blackmail','Erpressung','double standard','doppelte Standards','witch hunt','Hexenjagd','political persecution','politische Verfolgung','revenge','Rache','purge','settle scores','national identity','will of voters'],
 true,
 ARRAY['Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Sky News','Handelsblatt','Frankfurter Allgemeine','Le Figaro','Corriere della Sera','El Mundo','The Telegraph','Wall Street Journal','Bloomberg','Die Presse','Der Standard','Kurier','eKathimerini'],
 'hungary_rule_of_law', 2,
 'National sovereignty vs Brussels', 'Nationale Souveränität gegen Brüssel',
 -1, true
),
(
 'hungary_brussels_coercion',
 'The EU coerces its members, as the campaign over Budapest shows',
 'Die EU zwingt ihre Mitglieder, wie die Kampagne um Budapest zeigt',
 'Rift-exploitation framing (Russian state press) presents the whole episode as proof that Brussels coerces member states and engineers the fall of governments it dislikes, amplifying the EU''s internal division as evidence of Western hypocrisy and decline rather than endorsing any Hungarian faction. Vocabulary: coercion, diktat, Brussels bureaucrats, engineered, sovereignty trampled.',
 'Die Riss-Ausnutzungs-Rahmung (russische Staatspresse) deutet die Episode als Beleg dafür, dass Brüssel die Mitgliedstaaten zwingt und den Sturz missliebiger Regierungen betreibt, und verstärkt die interne Spaltung der EU als Zeichen westlicher Heuchelei und westlichen Niedergangs, ohne eine ungarische Seite zu unterstützen.',
 ARRAY['EUROPE-RUSSIA'],
 ARRAY['coercion','diktat','Brussels bureaucrats','sovereignty','hypocrisy','decline','engineered','puppet','vassal'],
 true,
 ARRAY['RT','TASS (EN)','TASS','Lenta.ru','Gazeta.ru','Izvestia','RIA Novosti','BelTA Russian'],
 'hungary_rule_of_law', 3,
 'Russian rift-exploitation', 'Russische Riss-Ausnutzung',
 -2, false
),

-- =================== afd_and_german_polarisation ===================
(
 'afd_democratic_defense',
 'The AfD is a threat to the democratic order that must be contained',
 'Die AfD ist eine Gefahr für die demokratische Ordnung, die eingedämmt werden muss',
 'Democratic-defense framing (German and Western mainstream) treats the AfD as a radical or extremist force whose classification by the domestic-intelligence service, the "Brandmauer" against cooperation, scrutiny of its access to office and state secrets and a possible ban are legitimate defences of the constitutional order. Vocabulary: rechtsextrem, extremist, threat to democracy, firewall, Verfassungsschutz, ban.',
 'Die Demokratie-Verteidigungs-Rahmung (deutscher und westlicher Mainstream) sieht die AfD als radikale oder extremistische Kraft, deren Einstufung durch den Verfassungsschutz, die „Brandmauer" gegen Zusammenarbeit, die Prüfung ihres Zugangs zu Ämtern und Staatsgeheimnissen und ein mögliches Verbot legitime Verteidigungen der verfassungsmäßigen Ordnung seien.',
 ARRAY['EUROPE-GERMANY'],
 ARRAY['rechtsextrem','far-right','extremist','extremism','threat to democracy','Bedrohung','Demokratie','firewall','Brandmauer','Verfassungsschutz','ban','Verbot','verfassungsfeindlich','wehrhafte Demokratie','hate','Hetze','isolate','ausgrenzen'],
 true,
 ARRAY['Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Sky News','Handelsblatt','Frankfurter Allgemeine','Le Figaro','Corriere della Sera','El Mundo','The Telegraph','Wall Street Journal','Bloomberg','Die Presse','Der Standard','Kurier'],
 'afd_and_german_polarisation', 1,
 'Defence of the democratic order', 'Verteidigung der demokratischen Ordnung',
 2, true
),
(
 'afd_exclusion_undemocratic',
 'Excluding a party millions vote for is itself undemocratic',
 'Eine Partei auszuschließen, die Millionen wählen, ist selbst undemokratisch',
 'Exclusion-critique framing (voiced by the party and by sympathetic commentary) holds that the firewall, the intelligence classification and moves toward a ban disenfranchise millions of voters, amount to establishment overreach and threaten free speech, and that the party should be treated as a normal democratic actor. Vocabulary: millions of voters, undemocratic, establishment, free speech, exclusion, censorship.',
 'Die Ausschluss-Kritik-Rahmung (von der Partei und von wohlwollenden Kommentaren vertreten) sieht in Brandmauer, Geheimdiensteinstufung und Verbotsüberlegungen eine Entrechtung von Millionen Wählern, einen Übergriff des Establishments und eine Gefahr für die Meinungsfreiheit und fordert, die Partei als normalen demokratischen Akteur zu behandeln.',
 ARRAY['EUROPE-GERMANY'],
 ARRAY['millions of voters','Millionen Wähler','undemocratic','undemokratisch','establishment','elite','free speech','Meinungsfreiheit','censorship','Zensur','witch hunt','Gesinnung','disenfranchise','stigmatis','normal party','second-class','double standard'],
 true,
 ARRAY['Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Sky News','Handelsblatt','Frankfurter Allgemeine','Le Figaro','Corriere della Sera','El Mundo','The Telegraph','Wall Street Journal','Bloomberg','Die Presse','Der Standard','Kurier'],
 'afd_and_german_polarisation', 2,
 'Exclusion as anti-democratic', 'Ausgrenzung als undemokratisch',
 -1, true
),
(
 'afd_persecution_kremlin',
 'Germany persecutes its opposition and silences dissent',
 'Deutschland verfolgt seine Opposition und unterdrückt abweichende Meinungen',
 'Rift-exploitation framing (Russian state press) presents German measures against the AfD as political persecution, censorship and the hypocrisy of a state that lectures others on democracy, amplifying the polarisation as evidence of Western decline rather than endorsing the party''s programme. Vocabulary: persecution, censorship, crackdown, hypocrisy, dictatorship of opinion.',
 'Die Riss-Ausnutzungs-Rahmung (russische Staatspresse) stellt die deutschen Maßnahmen gegen die AfD als politische Verfolgung, Zensur und Heuchelei eines Staates dar, der andere über Demokratie belehrt, und verstärkt die Polarisierung als Beleg westlichen Niedergangs, ohne das Programm der Partei zu unterstützen.',
 ARRAY['EUROPE-RUSSIA'],
 ARRAY['persecution','censorship','crackdown','opposition','hypocrisy','dictatorship','silence','ban','repression'],
 true,
 ARRAY['RT','TASS (EN)','TASS','Lenta.ru','Gazeta.ru','Izvestia','RIA Novosti','BelTA Russian'],
 'afd_and_german_polarisation', 3,
 'Russian rift-exploitation', 'Russische Riss-Ausnutzung',
 -2, false
),

-- =================== french_nationalist_challenge ===================
(
 'france_republican_defense',
 'The rule of law and republican norms must apply to the RN',
 'Rechtsstaat und republikanische Normen müssen auch für das RN gelten',
 'Republican-defense framing (French and Western mainstream) treats the Rassemblement National as a challenge to republican norms and the embezzlement case and any resulting ineligibility as the ordinary application of the law, and views the governing instability as the price of the party''s rise. Vocabulary: far-right, rule of law, embezzlement, convicted, republican, ineligibility.',
 'Die republikanische Verteidigungs-Rahmung (französischer und westlicher Mainstream) sieht das Rassemblement National als Herausforderung republikanischer Normen und den Veruntreuungsprozess sowie eine mögliche Unwählbarkeit als normale Anwendung des Rechts und deutet die Regierungsinstabilität als Preis des Aufstiegs der Partei.',
 ARRAY['EUROPE-FRANCE'],
 ARRAY['far-right','extrême droite','estrema destra','rechtsextrem','rule of law','état de droit','embezzlement','détournement','convicted','condamn','ineligibility','inéligibilité','republican','républicain','threat','justice','trial'],
 true,
 ARRAY['Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Sky News','Handelsblatt','Frankfurter Allgemeine','Le Figaro','Corriere della Sera','El Mundo','The Telegraph','Wall Street Journal','Bloomberg'],
 'french_nationalist_challenge', 1,
 'Republican norms and rule of law', 'Republikanische Normen und Rechtsstaat',
 2, true
),
(
 'france_popular_will',
 'The establishment and the courts are blocking the popular will',
 'Establishment und Justiz blockieren den Volkswillen',
 'Popular-will framing (voiced by the party and sympathetic commentary) holds that the judicial cases against Marine Le Pen and the marginalisation of the movement are an establishment and judicial effort to deny voters the leader they prefer ahead of 2027. Vocabulary: will of the people, establishment, witch hunt, judicial coup, denial of democracy.',
 'Die Volkswillen-Rahmung (von der Partei und wohlwollenden Kommentaren vertreten) sieht in den Gerichtsverfahren gegen Marine Le Pen und der Marginalisierung der Bewegung den Versuch von Establishment und Justiz, den Wählern die bevorzugte Anführerin vor 2027 zu verwehren.',
 ARRAY['EUROPE-FRANCE'],
 ARRAY['will of the people','volonté populaire','popular will','establishment','elite','witch hunt','acharnement','judicial coup','déni de démocratie','anti-democratic','muzzle','museler','disqualify','persecution','favourite'],
 true,
 ARRAY['Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Sky News','Handelsblatt','Frankfurter Allgemeine','Le Figaro','Corriere della Sera','El Mundo','The Telegraph','Wall Street Journal','Bloomberg'],
 'french_nationalist_challenge', 2,
 'Popular will vs the establishment', 'Volkswille gegen das Establishment',
 -1, true
),
(
 'france_decline_kremlin',
 'France''s model is failing amid chaos and instability',
 'Frankreichs Modell scheitert in Chaos und Instabilität',
 'Rift-exploitation framing (Russian state press) presents French political turmoil, government collapses and street unrest as proof of a failing Western model and elite disconnect, amplifying the instability rather than endorsing any French party. Vocabulary: chaos, collapse, crisis, decline, ungovernable.',
 'Die Riss-Ausnutzungs-Rahmung (russische Staatspresse) deutet die französischen Turbulenzen, Regierungsstürze und Unruhen als Beleg eines scheiternden westlichen Modells und abgehobener Eliten und verstärkt die Instabilität, ohne eine französische Partei zu unterstützen.',
 ARRAY['EUROPE-RUSSIA'],
 ARRAY['chaos','collapse','crisis','decline','ungovernable','turmoil','failing','elite'],
 true,
 ARRAY['RT','TASS (EN)','TASS','Lenta.ru','Gazeta.ru','Izvestia','RIA Novosti','BelTA Russian'],
 'french_nationalist_challenge', 3,
 'Russian rift-exploitation', 'Russische Riss-Ausnutzung',
 -2, false
),

-- =================== eu_migration_burden_sharing ===================
(
 'migration_solidarity_rights',
 'Migration requires European solidarity and respect for rights and law',
 'Migration erfordert europäische Solidarität und die Achtung von Rechten und Recht',
 'Solidarity-and-rights framing (Western mainstream and pro-integration voices) holds that asylum is a legal obligation, that the Pact''s burden-sharing must be honoured, that detention and pushbacks that courts find unlawful are unacceptable, and that regularisation and integration are legitimate answers. Vocabulary: solidarity, human rights, asylum right, unlawful, integration, shared responsibility.',
 'Die Solidaritäts- und Rechte-Rahmung (westlicher Mainstream und integrationsfreundliche Stimmen) sieht Asyl als rechtliche Pflicht, die Lastenteilung des Pakts als einzuhaltende Verpflichtung, gerichtlich für rechtswidrig erklärte Inhaftierung und Zurückweisung als inakzeptabel und Regularisierung und Integration als legitime Antworten.',
 ARRAY['NON-STATE-EU'],
 ARRAY['solidarity','Solidarität','solidarité','human rights','Menschenrechte','asylum right','Asylrecht','unlawful','illegal ruling','ruled illegal','rechtswidrig','integration','shared responsibility','humanitarian','welcome','court','protect refugees'],
 true,
 ARRAY['Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Sky News'],
 'eu_migration_burden_sharing', 1,
 'Solidarity and rights', 'Solidarität und Rechte',
 2, true
),
(
 'migration_national_control',
 'Member states must control borders and curb irregular migration',
 'Mitgliedstaaten müssen Grenzen kontrollieren und irreguläre Migration eindämmen',
 'Control framing (national governments and centre-right and sovereigntist voices) holds that irregular migration must be curbed through tougher borders, faster returns, offshore processing and restriction, that generous regularisation sets the wrong incentives, and that member states, not Brussels, should decide. Vocabulary: control, crackdown, returns, irregular, offshore, restrict, pull factor.',
 'Die Kontroll-Rahmung (nationale Regierungen sowie Mitte-rechts- und souveränistische Stimmen) sieht irreguläre Migration durch härtere Grenzen, schnellere Rückführungen, ausgelagerte Verfahren und Restriktion einzudämmen, großzügige Regularisierung als falschen Anreiz und die Entscheidung bei den Mitgliedstaaten, nicht bei Brüssel.',
 ARRAY['EUROPE-SOUTH','EUROPE-GERMANY','NON-STATE-EU'],
 ARRAY['control','Kontrolle','crackdown','tougher','deport','Abschiebung','irregular','illegal migration','offshore','Albania','remigration','pull factor','restrict','clampdown','overwhelmed','Grenzen schützen','secure border','national'],
 true,
 ARRAY['Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Sky News','Handelsblatt','Frankfurter Allgemeine','Le Figaro','Corriere della Sera','El Mundo','The Telegraph'],
 'eu_migration_burden_sharing', 2,
 'National border control', 'Nationale Grenzkontrolle',
 -1, true
),
(
 'migration_eu_failure_kremlin',
 'EU migration policy is chaos and a failure of the European project',
 'Die EU-Migrationspolitik ist Chaos und ein Scheitern des europäischen Projekts',
 'Rift-exploitation framing (Russian state press) presents EU migration as chaos, division and the failure of a hypocritical Europe, amplifying the disputes between member states as evidence of decline rather than taking a side on asylum policy. Vocabulary: chaos, crisis, invasion, failure, hypocrisy, collapse of Schengen.',
 'Die Riss-Ausnutzungs-Rahmung (russische Staatspresse) stellt die EU-Migration als Chaos, Spaltung und Scheitern eines heuchlerischen Europas dar und verstärkt die Streitigkeiten zwischen den Mitgliedstaaten als Zeichen des Niedergangs, ohne in der Asylpolitik Partei zu ergreifen.',
 ARRAY['EUROPE-RUSSIA'],
 ARRAY['chaos','crisis','invasion','failure','hypocrisy','collapse','uncontrolled','flood','decline'],
 true,
 ARRAY['RT','TASS (EN)','TASS','Lenta.ru','Gazeta.ru','Izvestia','RIA Novosti','BelTA Russian'],
 'eu_migration_burden_sharing', 3,
 'Russian rift-exploitation', 'Russische Riss-Ausnutzung',
 -2, false
),

-- =================== eu_budget_sovereignty ===================
(
 'budget_more_europe',
 'A capable Union needs stronger common financing',
 'Eine handlungsfähige Union braucht eine stärkere gemeinsame Finanzierung',
 'Integration framing (the Commission and pro-integration mainstream) holds that new own resources and a larger budget are needed for competitiveness, defence and shared priorities, that rule-of-law conditionality is legitimate, and that reform of cohesion and agricultural spending should serve common European goals. Vocabulary: own resources, common, invest, competitiveness, ambitious, more Europe.',
 'Die Integrations-Rahmung (Kommission und integrationsfreundlicher Mainstream) sieht neue Eigenmittel und einen größeren Haushalt als notwendig für Wettbewerbsfähigkeit, Verteidigung und gemeinsame Prioritäten, die Rechtsstaats-Konditionalität als legitim und die Reform der Kohäsions- und Agrarausgaben als Dienst an gemeinsamen europäischen Zielen.',
 ARRAY['NON-STATE-EU'],
 ARRAY['own resources','Eigenmittel','common','gemeinsam','invest','competitiveness','Wettbewerbsfähigkeit','ambitious','more Europe','solidarity','joint','strategic','strengthen','stärken','capacity'],
 true,
 ARRAY['Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Bloomberg'],
 'eu_budget_sovereignty', 1,
 'Stronger common financing', 'Stärkere gemeinsame Finanzierung',
 2, true
),
(
 'budget_national_sovereignty',
 'Brussels wants more money and power at the expense of nations and taxpayers',
 'Brüssel will mehr Geld und Macht auf Kosten der Nationen und Steuerzahler',
 'Sovereignty framing (net-contributor governments, centre-right and sovereigntist voices, farm and business lobbies) holds that the proposed budget is unaffordable, that new EU taxes and own resources are a power grab into national competences and taxpayers'' money, and that Green Deal and agricultural rules are overreach to be resisted. Vocabulary: net contributor, unaffordable, taxpayer, cut, overreach, red tape, reject.',
 'Die Souveränitäts-Rahmung (Nettozahler-Regierungen, Mitte-rechts- und souveränistische Stimmen, Agrar- und Wirtschaftsverbände) sieht den vorgeschlagenen Haushalt als unbezahlbar, neue EU-Steuern und Eigenmittel als Griff nach nationalen Zuständigkeiten und Steuergeldern und Green-Deal- und Agrarregeln als abzuwehrende Übergriffe.',
 ARRAY['EUROPE-GERMANY','EUROPE-SOUTH','EUROPE-VISEGRAD'],
 ARRAY['net contributor','Nettozahler','too high','unaffordable','unbezahlbar','taxpayer','Steuerzahler','cut','Kürzung','overreach','power grab','red tape','Bürokratie','reject','ablehnen','burden','rebate','sovereignty','no-go','frugal'],
 true,
 ARRAY['Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Handelsblatt','Frankfurter Allgemeine','Le Figaro','Corriere della Sera','El Mundo','The Telegraph','Wall Street Journal','Bloomberg','Die Presse'],
 'eu_budget_sovereignty', 2,
 'National sovereignty and taxpayers', 'Nationale Souveränität und Steuerzahler',
 -1, true
),
(
 'budget_eu_decline_kremlin',
 'The EU is fiscally overstretched and in decline',
 'Die EU ist finanziell überfordert und im Niedergang',
 'Rift-exploitation framing (Russian state press) presents the budget disputes as proof that the EU is broke, overstretched by rearmament and Ukraine, and fracturing between paymasters and dependants, amplifying the division rather than taking a side. Vocabulary: broke, insolvent, overstretched, decline, disunity, paymaster.',
 'Die Riss-Ausnutzungs-Rahmung (russische Staatspresse) deutet die Haushaltsstreitigkeiten als Beleg, dass die EU pleite, durch Aufrüstung und Ukraine überfordert und zwischen Zahlmeistern und Empfängern zerrissen sei, und verstärkt die Spaltung, ohne Partei zu ergreifen.',
 ARRAY['EUROPE-RUSSIA'],
 ARRAY['broke','insolvent','overstretched','decline','disunity','paymaster','collapse','bankrupt','crisis'],
 true,
 ARRAY['RT','TASS (EN)','TASS','Lenta.ru','Gazeta.ru','Izvestia','RIA Novosti','BelTA Russian'],
 'eu_budget_sovereignty', 3,
 'Russian rift-exploitation', 'Russische Riss-Ausnutzung',
 -2, false
),

-- =================== eu_right_realignment ===================
(
 'realignment_firewall_defense',
 'The mainstream must not normalise the radical right',
 'Der Mainstream darf die radikale Rechte nicht normalisieren',
 'Firewall-defense framing (centre-left, greens and pro-cordon voices) holds that mainstream parties, above all the EPP, must not legitimise or govern with national-conservative and radical-right forces, that the cordon sanitaire protects liberal democracy, and that its erosion is dangerous. Vocabulary: firewall, cordon sanitaire, normalisation, far-right, taboo, must not, legitimise.',
 'Die Brandmauer-Verteidigungs-Rahmung (Mitte-links, Grüne und Befürworter des Cordon sanitaire) sieht, dass Mainstream-Parteien, allen voran die EVP, nationalkonservative und rechtsradikale Kräfte nicht legitimieren oder mit ihnen regieren dürfen, dass der Cordon sanitaire die liberale Demokratie schützt und seine Aufweichung gefährlich ist.',
 ARRAY['NON-STATE-EU','EUROPE-GERMANY'],
 ARRAY['firewall','Brandmauer','cordon sanitaire','normalis','normalisierung','far-right','rechtsextrem','taboo','Tabu','must not','legitimis','legitimieren','dangerous','erosion','pact with','shift right','Dammbruch'],
 true,
 ARRAY['Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv'],
 'eu_right_realignment', 1,
 'Defence of the cordon sanitaire', 'Verteidigung des Cordon sanitaire',
 2, true
),
(
 'realignment_new_majority',
 'The right has a democratic mandate to govern and to cooperate',
 'Die Rechte hat ein demokratisches Mandat zu regieren und zusammenzuarbeiten',
 'Realignment framing (centre-right and national-conservative voices) holds that parties representing a large share of voters have a democratic mandate, that cooperation across the old cordon is legitimate and overdue, and that a new centre-right-to-national-conservative majority is a normal democratic outcome. Vocabulary: mandate, majority, legitimate, voters, normalise cooperation, new majority, represent.',
 'Die Neuordnungs-Rahmung (Mitte-rechts- und nationalkonservative Stimmen) sieht Parteien, die einen großen Wähleranteil vertreten, mit einem demokratischen Mandat, die Zusammenarbeit über den alten Cordon hinweg als legitim und überfällig und eine neue Mehrheit von der Mitte-rechten bis zur nationalkonservativen Seite als normales demokratisches Ergebnis.',
 ARRAY['NON-STATE-EU','EUROPE-SOUTH'],
 ARRAY['mandate','Mandat','majority','Mehrheit','legitimate','legitim','voters','Wähler','normal','pragmatic','new majority','represent','realign','cooperation legitimate','overdue','listen to voters'],
 true,
 ARRAY['Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Handelsblatt','Frankfurter Allgemeine','Le Figaro','Corriere della Sera','El Mundo','The Telegraph'],
 'eu_right_realignment', 2,
 'A new democratic majority', 'Eine neue demokratische Mehrheit',
 -1, true
),
(
 'realignment_center_decline_kremlin',
 'Europe''s liberal centre is collapsing',
 'Europas liberale Mitte bricht zusammen',
 'Rift-exploitation framing (Russian and Chinese state media) presents the realignment as the collapse of a discredited European liberal centre and the vindication of forces opposed to Brussels and to support for Ukraine, amplifying the shift as Western decline rather than endorsing a specific party. Vocabulary: collapse, decline, discredited, liberal elite, sweeping, end of an era.',
 'Die Riss-Ausnutzungs-Rahmung (russische und chinesische Staatsmedien) deutet die Neuordnung als Zusammenbruch einer diskreditierten europäischen liberalen Mitte und als Bestätigung der Kräfte gegen Brüssel und gegen die Ukraine-Unterstützung und verstärkt den Wandel als westlichen Niedergang, ohne eine bestimmte Partei zu unterstützen.',
 ARRAY['EUROPE-RUSSIA','ASIA-CHINA'],
 ARRAY['collapse','decline','discredited','liberal elite','sweeping','end of an era','crumbling','rejected','establishment fails'],
 true,
 ARRAY['RT','TASS (EN)','TASS','Lenta.ru','Gazeta.ru','Izvestia','RIA Novosti','BelTA Russian','CGTN','China Daily','Global Times','Xinhua'],
 'eu_right_realignment', 3,
 'Russian & Chinese rift-exploitation', 'Russische & chinesische Riss-Ausnutzung',
 -2, false
)

ON CONFLICT (id) DO NOTHING;
