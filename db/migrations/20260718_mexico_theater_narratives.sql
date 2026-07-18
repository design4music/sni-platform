-- Mexico theater: re-scope us_mexico_military_pressure + author all narratives
-- (10 atomic + 4 theater cards). LOCAL build 2026-07-18. Idempotent.
-- No DELETE/TRUNCATE/DROP: pure UPSERT.

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. Re-scope + rename us_mexico_military_pressure (approved Phase 1 change):
--    broaden from narrow "military-action pressure" to cover the dominant
--    covert (CIA) + political/electoral interference dimension. Neutral,
--    evergreen description (framing lives in narratives_v2).
-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET
  name_en = 'US intervention pressure and Mexican sovereignty',
  name_de = 'US-Interventionsdruck und mexikanische Souveränität',
  description_en = 'Friction over US covert operations (CIA), proposals for military action against cartels on Mexican soil, indictments of Mexican officials, and disputes over political interference, set against Mexico''s sovereignty position.',
  description_de = 'Spannungen über verdeckte US-Operationen (CIA), Vorschläge für Militäraktionen gegen Kartelle auf mexikanischem Boden, Anklagen gegen mexikanische Amtsträger und Auseinandersetzungen über politische Einmischung, gegenüber Mexikos Souveränitätsposition.'
WHERE id = 'us_mexico_military_pressure';

-- ===========================================================================
-- ATOMIC NARRATIVES
-- ===========================================================================

INSERT INTO narratives_v2
  (id, fn_id, display_order, stance, framing_required,
   name_en, name_de, stance_label_en, stance_label_de,
   claim_en, claim_de, actor_centroids, publishers, framing_keywords)
VALUES

-- --- mexico_cartel_war (own-goal topic: three-stance gradient) ---------------
(
  'cartel_offensive_progress', 'mexico_cartel_war', 1, 2, true,
  'The militarised offensive is working: captures and takedowns weaken the cartels',
  'Die militarisierte Offensive wirkt: Festnahmen und Schläge schwächen die Kartelle',
  'Security-offensive progress', 'Fortschritt der Sicherheitsoffensive',
  'Offensive-progress framing (Mexican establishment and wire coverage, plus US enforcement voices) presents cartel-leader captures, extraditions and army operations against CJNG and Sinaloa as concrete security gains: the state is degrading the cartels'' command. Shares a publisher pool with the narco-state critique, so it is separated by framing (capture/arrest/takedown vocabulary).',
  'Das Offensiv-Fortschritts-Framing (mexikanische Establishment- und Agenturberichterstattung sowie US-Strafverfolgungsstimmen) stellt Festnahmen von Kartellführern, Auslieferungen und Armeeoperationen gegen CJNG und Sinaloa als konkrete Sicherheitsgewinne dar: Der Staat schwächt die Führung der Kartelle. Teilt den Publisher-Pool mit der Narco-Staat-Kritik und wird über das Framing getrennt (Vokabular von Festnahme/Verhaftung/Schlag).',
  ARRAY['AMERICAS-MEXICO','AMERICAS-USA'],
  ARRAY['El Universal','Reforma','Mexico News Daily','El País','EL PAÍS','Reuters','Associated Press','CNN','New York Times','Washington Post','BBC World','The Guardian','Deutsche Welle','France 24 (EN)','Al Jazeera','Fox News','NPR','Bloomberg'],
  ARRAY['capture','captured','arrest','arrested','detained','dismantle','seized','extradited','extradition','kingpin','takedown','blow to','operation','killed','handed over','captura','capturado','detención','detenido','arresto','desmantel','incautación','extraditado','abatido','golpe al','operativo','Festnahme','festgenommen','Schlag gegen','zerschlagen']
),
(
  'cartel_narco_state_critique', 'mexico_cartel_war', 2, -1, true,
  'Militarisation is failing and the state is compromised: collusion, corruption and impunity',
  'Die Militarisierung scheitert und der Staat ist kompromittiert: Kollusion, Korruption und Straflosigkeit',
  'Narco-state / militarisation critique', 'Narco-Staat-/Militarisierungskritik',
  'Friendly-critic framing (Mexican watchdog outlets and Western investigative coverage) treats the drug war as an own-goal: officials colluding with cartels (the Sinaloa-governor indictment, the arrested security chief), a militarisation strategy that has not lowered violence, and entrenched corruption and impunity. Same publisher pool as offensive-progress; separated by collusion/failure vocabulary.',
  'Das Framing des wohlwollenden Kritikers (mexikanische Watchdog-Medien und westliche Investigativberichterstattung) behandelt den Drogenkrieg als Eigentor: Amtsträger, die mit Kartellen kolludieren (die Anklage gegen den Sinaloa-Gouverneur, der festgenommene Sicherheitschef), eine Militarisierungsstrategie, die die Gewalt nicht gesenkt hat, sowie verfestigte Korruption und Straflosigkeit. Gleicher Publisher-Pool wie Offensiv-Fortschritt; getrennt über Kollusions-/Versagensvokabular.',
  ARRAY['AMERICAS-MEXICO','AMERICAS-USA'],
  ARRAY['El Universal','Reforma','Mexico News Daily','El País','EL PAÍS','Reuters','Associated Press','CNN','New York Times','Washington Post','BBC World','The Guardian','Deutsche Welle','France 24 (EN)','Al Jazeera','Fox News','NPR','Bloomberg'],
  ARRAY['collusion','complicity','complicit','narco-state','corruption','protection','impunity','militarization','militarisation','violence surges','failed','embedded','ties to cartel','cover-up','disappeared','colusión','complicidad','narcoestado','corrupción','impunidad','militarización','vínculos','nexos','desaparecidos','encubrimiento','connivencia','Kollusion','Komplizenschaft','Korruption','Straflosigkeit']
),
(
  'cartel_us_culpability_rift', 'mexico_cartel_war', 3, -2, true,
  'The cartel crisis is made in America: US drug demand and US guns fuel it, and Washington exploits it',
  'Die Kartellkrise ist hausgemacht in Amerika: US-Drogennachfrage und US-Waffen befeuern sie, und Washington nutzt sie aus',
  'US-culpability / rift-exploitation', 'US-Schuld / Rift-Ausnutzung',
  'Rift-exploitation framing (Russian and Chinese state media) shifts blame to the United States: American drug consumption and the southward flow of US firearms drive the violence, and Washington weaponises the cartel threat as a pretext to pressure and intervene in its neighbour. It is adversarial to the US, not an endorsement of the cartels.',
  'Das Rift-Ausnutzungs-Framing (russische und chinesische Staatsmedien) verlagert die Schuld auf die USA: Amerikanischer Drogenkonsum und der Zustrom von US-Schusswaffen nach Süden treiben die Gewalt an, und Washington instrumentalisiert die Kartellbedrohung als Vorwand, um seinen Nachbarn unter Druck zu setzen und zu intervenieren. Es ist gegen die USA gerichtet, keine Billigung der Kartelle.',
  ARRAY['EUROPE-RUSSIA','ASIA-CHINA'],
  ARRAY['RT','TASS','TASS (EN)','tass.com','Sputnik','RIA Novosti','CGTN','Global Times','China Daily','Xinhua','Press TV'],
  ARRAY['US demand','American demand','US guns','American weapons','arms flow','iron river','pretext','hypocrisy','Monroe','root cause','consumers','blame Washington','drug consumption','double standard','armas estadounidenses','consumo','pretexto','hipocresía']
),

-- --- us_mexico_military_pressure (intervention vs sovereignty) ----------------
(
  'intervention_necessity', 'us_mexico_military_pressure', 1, 2, false,
  'US action against the cartels is necessary because Mexico cannot or will not stop them',
  'US-Maßnahmen gegen die Kartelle sind notwendig, weil Mexiko sie nicht stoppen kann oder will',
  'US-intervention necessity', 'Notwendigkeit der US-Intervention',
  'Intervention-necessity framing (US conservative press) holds that the cartels are terrorist organisations threatening Americans, that the Mexican state is unwilling or unable to defeat them, and that Washington is therefore justified in covert action, designations, indictments and even unilateral strikes on Mexican soil.',
  'Das Interventions-Notwendigkeits-Framing (US-konservative Presse) besagt, dass die Kartelle terroristische Organisationen sind, die Amerikaner bedrohen, dass der mexikanische Staat sie nicht besiegen will oder kann und dass Washington daher zu verdeckten Aktionen, Einstufungen, Anklagen und sogar einseitigen Schlägen auf mexikanischem Boden berechtigt ist.',
  ARRAY['AMERICAS-USA'],
  ARRAY['Fox News','New York Post','Washington Examiner','Breitbart','Newsmax','The National Interest','Washington Times','Daily Caller'],
  ARRAY['terrorist','FTO','must act','unilateral','take out','decisive','cartel terrorists','national security','strike the cartels','failed state','designation']
),
(
  'mexican_sovereignty_defense', 'us_mexico_military_pressure', 2, -2, false,
  'US pressure violates Mexican sovereignty; non-intervention is the red line',
  'US-Druck verletzt Mexikos Souveränität; Nichteinmischung ist die rote Linie',
  'Mexican sovereignty defense', 'Verteidigung der mexikanischen Souveränität',
  'Sovereignty-defense framing (Mexican and Hispanic-American outlets) treats US covert operations, intervention threats and indictments of Mexican officials as violations of sovereignty and unacceptable interference in internal affairs. It centres Mexico''s constitutional non-intervention doctrine and Sheinbaum''s insistence on cooperation without subordination.',
  'Das Souveränitätsverteidigungs-Framing (mexikanische und hispanoamerikanische Medien) behandelt verdeckte US-Operationen, Interventionsdrohungen und Anklagen gegen mexikanische Amtsträger als Verletzungen der Souveränität und inakzeptable Einmischung in innere Angelegenheiten. Es stellt Mexikos verfassungsmäßige Nichtinterventionsdoktrin und Sheinbaums Beharren auf Kooperation ohne Unterordnung in den Mittelpunkt.',
  ARRAY['AMERICAS-MEXICO'],
  ARRAY['El Universal','Reforma','Mexico News Daily','El País','EL PAÍS','El Mundo','Clarín','La Nación','O Globo','Folha de S.Paulo','O Estado de S. Paulo'],
  ARRAY['sovereignty','interference','non-intervention','red line','will not accept','internal affairs','subordination','soberanía','injerencia','intervención','no subordinación','respeto','dignidad','asuntos internos','Souveränität','Einmischung','Nichteinmischung']
),
(
  'western_intervention_scrutiny', 'us_mexico_military_pressure', 3, -1, false,
  'US pressure is straining the relationship and inviting scandal',
  'Der US-Druck belastet die Beziehung und lädt zu Skandalen ein',
  'Western institutional scrutiny', 'Westliche institutionelle Prüfung',
  'Institutional-scrutiny framing (US mainstream and European coverage) reports the pressure campaign critically but from a governance angle rather than a nationalist one: the CIA-officers-in-Chihuahua affair, diplomatic strains, questions over whether Sheinbaum is appeasing Trump, and the escalation risk of covert operations in an allied country.',
  'Das Framing der institutionellen Prüfung (US-amerikanische Mainstream- und europäische Berichterstattung) berichtet über die Druckkampagne kritisch, aber aus einer Governance-Perspektive statt einer nationalistischen: die Affäre um die CIA-Beamten in Chihuahua, diplomatische Spannungen, Fragen, ob Sheinbaum Trump beschwichtigt, und das Eskalationsrisiko verdeckter Operationen in einem verbündeten Land.',
  ARRAY['AMERICAS-USA','AMERICAS-MEXICO'],
  ARRAY['Reuters','Associated Press','CNN','New York Times','Washington Post','NPR','MSNBC','ABC News','BBC World','The Guardian','Financial Times','Deutsche Welle','Euronews','France 24 (EN)','France 24','Le Monde','Le Figaro','Der Spiegel','Die Zeit','Süddeutsche Zeitung','Sky News','The Telegraph'],
  ARRAY['escalate','tensions','strains','scandal','CIA','deaths','appeasing','pressure','alarm','diplomatic crisis','fraught','covert','Spannungen','Skandal','Eskalation','verdeckt']
),
(
  'anti_hegemony_rift', 'us_mexico_military_pressure', 4, -2, false,
  'US pressure on Mexico is imperial overreach in Washington''s backyard',
  'Der US-Druck auf Mexiko ist imperiale Anmaßung in Washingtons Hinterhof',
  'Anti-hegemony rift-exploitation', 'Anti-Hegemonie-Rift-Ausnutzung',
  'Rift-exploitation framing (Russian and Chinese state media) casts the pressure campaign as 21st-century Monroe-Doctrine imperialism: Washington bullies a neighbour, treats Latin America as its backyard, and reveals the hypocrisy of a rules-based order. It amplifies the US-Mexico rift with schadenfreude and is adversarial to US hegemony, not supportive of either government.',
  'Das Rift-Ausnutzungs-Framing (russische und chinesische Staatsmedien) stellt die Druckkampagne als Monroe-Doktrin-Imperialismus des 21. Jahrhunderts dar: Washington drangsaliert einen Nachbarn, behandelt Lateinamerika als seinen Hinterhof und offenbart die Heuchelei einer regelbasierten Ordnung. Es verstärkt den US-mexikanischen Riss mit Schadenfreude und richtet sich gegen die US-Hegemonie, ohne eine der Regierungen zu unterstützen.',
  ARRAY['EUROPE-RUSSIA','ASIA-CHINA'],
  ARRAY['RT','TASS','TASS (EN)','tass.com','Sputnik','RIA Novosti','CGTN','Global Times','China Daily','Xinhua','Press TV'],
  ARRAY['imperialism','imperialist','backyard','Monroe','bullying','hegemony','gunboat','neo-colonial','double standard','pretext','sphere of influence','Imperialismus','Hinterhof','Hegemonie','Doppelmoral']
),

-- --- us_mexico_trade_border (leverage vs coercion) ---------------------------
(
  'leverage_justified', 'us_mexico_trade_border', 1, 2, false,
  'Tariff and border pressure are legitimate leverage that forces Mexican cooperation',
  'Zoll- und Grenzdruck sind legitime Druckmittel, die Mexiko zur Kooperation zwingen',
  'Leverage justified (America first)', 'Druckmittel gerechtfertigt (America First)',
  'Leverage-justified framing (US conservative press) holds that tariff threats and border enforcement are effective tools that have already extracted Mexican concessions on migration, fentanyl and troop deployments, and that Washington should keep using economic pressure to secure results.',
  'Das Framing des gerechtfertigten Druckmittels (US-konservative Presse) besagt, dass Zolldrohungen und Grenzsicherung wirksame Instrumente sind, die Mexiko bereits Zugeständnisse bei Migration, Fentanyl und Truppenentsendungen abgerungen haben, und dass Washington weiter wirtschaftlichen Druck einsetzen sollte, um Ergebnisse zu erzielen.',
  ARRAY['AMERICAS-USA'],
  ARRAY['Fox News','New York Post','Washington Examiner','Breitbart','Newsmax','The National Interest','Washington Times','Daily Caller'],
  ARRAY['leverage','tough','America first','secure the border','force Mexico','cooperation','results','concession','deport','fentanyl','crackdown']
),
(
  'trade_economic_disruption', 'us_mexico_trade_border', 2, -1, false,
  'Tariff brinkmanship disrupts an integrated economy and rattles markets',
  'Zoll-Brinkmanship stört eine integrierte Wirtschaft und verunsichert die Märkte',
  'Economic-disruption analysis', 'Analyse der wirtschaftlichen Störung',
  'Economic-disruption framing (business and wire coverage) reports the tariff and USMCA fights through their market and supply-chain effects: threatened auto, steel and aluminium duties, cross-border supply-chain risk, nearshoring, currency and growth impacts, and the uncertainty of on-again-off-again deadlines.',
  'Das Framing der wirtschaftlichen Störung (Wirtschafts- und Agenturberichterstattung) berichtet über die Zoll- und USMCA-Auseinandersetzungen anhand ihrer Markt- und Lieferkettenwirkungen: angedrohte Zölle auf Autos, Stahl und Aluminium, grenzüberschreitendes Lieferkettenrisiko, Nearshoring, Währungs- und Wachstumseffekte sowie die Unsicherheit ständig verschobener Fristen.',
  ARRAY['AMERICAS-USA','AMERICAS-MEXICO'],
  ARRAY['Reuters','Associated Press','Bloomberg','Financial Times','Wall Street Journal','S&P Global','The Economist','Globe and Mail','Mining.com','OilPrice'],
  ARRAY['supply chain','markets','autos','disruption','uncertainty','GDP','recession','nearshoring','integrated','costs','tariff hit','peso','investment','Lieferkette','Märkte','Unsicherheit']
),
(
  'trade_coercion_pushback', 'us_mexico_trade_border', 3, -2, false,
  'US tariff threats are economic coercion that violate USMCA and Mexican dignity',
  'US-Zolldrohungen sind wirtschaftlicher Zwang, der das USMCA und Mexikos Würde verletzt',
  'Mexican coercion pushback', 'Mexikanischer Widerstand gegen Zwang',
  'Coercion-pushback framing (Mexican and Hispanic-American outlets) treats tariff threats and migration demands as economic blackmail that breaches the USMCA/T-MEC and Mexico''s dignity, met with counter-measures, diversification toward the EU and other partners, and insistence that cooperation cannot be coerced.',
  'Das Framing des Widerstands gegen Zwang (mexikanische und hispanoamerikanische Medien) behandelt Zolldrohungen und Migrationsforderungen als wirtschaftliche Erpressung, die das USMCA/T-MEC und Mexikos Würde verletzt, beantwortet mit Gegenmaßnahmen, Diversifizierung hin zur EU und anderen Partnern sowie dem Beharren, dass Kooperation nicht erzwungen werden kann.',
  ARRAY['AMERICAS-MEXICO'],
  ARRAY['El Universal','Reforma','Mexico News Daily','El País','EL PAÍS','El Mundo','Clarín','La Nación','O Globo','Folha de S.Paulo','O Estado de S. Paulo'],
  ARRAY['coercion','blackmail','USMCA','T-MEC','retaliation','unfair','bullying','dignity','diversif','aranceles','chantaje','coerción','soberanía','represalia','dignidad','Zwang','Erpressung','Vergeltung']
)
ON CONFLICT (id) DO UPDATE SET
  fn_id = EXCLUDED.fn_id, display_order = EXCLUDED.display_order,
  stance = EXCLUDED.stance, framing_required = EXCLUDED.framing_required,
  name_en = EXCLUDED.name_en, name_de = EXCLUDED.name_de,
  stance_label_en = EXCLUDED.stance_label_en, stance_label_de = EXCLUDED.stance_label_de,
  claim_en = EXCLUDED.claim_en, claim_de = EXCLUDED.claim_de,
  actor_centroids = EXCLUDED.actor_centroids, publishers = EXCLUDED.publishers,
  framing_keywords = EXCLUDED.framing_keywords, is_active = true, updated_at = now();

-- ===========================================================================
-- THEATER-LEVEL NARRATIVE CARDS (fn_id = mexico_theater). Publisher-DISJOINT
-- within each sign bucket: -1 (Western/business), -2a (Mexican), -2b (Ru/Cn).
-- ===========================================================================

INSERT INTO narratives_v2
  (id, fn_id, display_order, stance, framing_required,
   name_en, name_de, stance_label_en, stance_label_de,
   claim_en, claim_de, actor_centroids, publishers, framing_keywords)
VALUES
(
  'mexth_us_pressure_justified', 'mexico_theater', 1, 2, false,
  'US pressure on Mexico is justified and is producing results',
  'Der US-Druck auf Mexiko ist gerechtfertigt und bringt Ergebnisse',
  'US pressure justified', 'US-Druck gerechtfertigt',
  'The America-first framing across the theater (US conservative press): cartels are terrorists, Mexico is an unreliable partner, and covert action, indictments, tariff threats and border enforcement are legitimate leverage that has already forced concessions.',
  'Das America-First-Framing über das gesamte Theater (US-konservative Presse): Kartelle sind Terroristen, Mexiko ist ein unzuverlässiger Partner, und verdeckte Aktionen, Anklagen, Zolldrohungen und Grenzsicherung sind legitime Druckmittel, die bereits Zugeständnisse erzwungen haben.',
  ARRAY['AMERICAS-USA'],
  ARRAY['Fox News','New York Post','Washington Examiner','Breitbart','Newsmax','The National Interest','Washington Times','Daily Caller'],
  ARRAY['terrorist','leverage','tough','America first','necessary','results','failed state']
),
(
  'mexth_western_scrutiny', 'mexico_theater', 2, -1, false,
  'US pressure strains the relationship and carries scandal and economic risk',
  'Der US-Druck belastet die Beziehung und birgt Skandal- und Wirtschaftsrisiken',
  'Western institutional scrutiny', 'Westliche institutionelle Prüfung',
  'The Western mainstream and business framing: reports the confrontation critically through governance and market lenses, the CIA-in-Chihuahua scandal, diplomatic strain, supply-chain and tariff disruption, and doubts about whether Mexico''s concessions are working, rather than through nationalism or America-first triumphalism.',
  'Das westliche Mainstream- und Wirtschaftsframing: berichtet über die Konfrontation kritisch durch Governance- und Marktlinsen, den CIA-in-Chihuahua-Skandal, diplomatische Spannungen, Lieferketten- und Zollstörungen sowie Zweifel, ob Mexikos Zugeständnisse wirken, statt durch Nationalismus oder America-First-Triumphalismus.',
  ARRAY['AMERICAS-USA','AMERICAS-MEXICO'],
  ARRAY['Reuters','Associated Press','CNN','New York Times','Washington Post','NPR','MSNBC','ABC News','BBC World','The Guardian','Financial Times','Deutsche Welle','Euronews','France 24 (EN)','France 24','Le Monde','Le Figaro','Der Spiegel','Die Zeit','Süddeutsche Zeitung','Sky News','The Telegraph','Bloomberg','Wall Street Journal','S&P Global','The Economist','Globe and Mail'],
  ARRAY['tensions','strains','scandal','CIA','disruption','supply chain','markets','diplomatic','escalation','uncertainty']
),
(
  'mexth_mexican_sovereignty', 'mexico_theater', 3, -2, false,
  'US pressure violates Mexican sovereignty and dignity',
  'Der US-Druck verletzt Mexikos Souveränität und Würde',
  'Mexican sovereignty and anti-coercion', 'Mexikanische Souveränität und Anti-Zwang',
  'The Mexican and Hispanic-American framing across the theater: covert operations, intervention threats, official indictments and tariff blackmail are violations of sovereignty and dignity, met by insistence on non-intervention, cooperation without subordination, counter-measures and diversification away from dependence on Washington.',
  'Das mexikanische und hispanoamerikanische Framing über das gesamte Theater: verdeckte Operationen, Interventionsdrohungen, Anklagen gegen Amtsträger und Zoll-Erpressung sind Verletzungen der Souveränität und Würde, beantwortet mit dem Beharren auf Nichtintervention, Kooperation ohne Unterordnung, Gegenmaßnahmen und Diversifizierung weg von der Abhängigkeit von Washington.',
  ARRAY['AMERICAS-MEXICO'],
  ARRAY['El Universal','Reforma','Mexico News Daily','El País','EL PAÍS','El Mundo','Clarín','La Nación','O Globo','Folha de S.Paulo','O Estado de S. Paulo'],
  ARRAY['soberanía','sovereignty','injerencia','interference','dignidad','no subordinación','aranceles','coerción','represalia','non-intervention']
),
(
  'mexth_anti_hegemony_rift', 'mexico_theater', 4, -2, false,
  'US pressure on Mexico exposes American imperialism in its own backyard',
  'Der US-Druck auf Mexiko entlarvt den amerikanischen Imperialismus im eigenen Hinterhof',
  'Russia/China rift-exploitation', 'Russland/China-Rift-Ausnutzung',
  'The Russian and Chinese state-media framing: not support for either government but exploitation of the rift, US pressure on Mexico is Monroe-Doctrine imperialism, Washington bullies its neighbour and treats Latin America as its backyard, the cartel and migration threats are pretexts, and the episode proves the hypocrisy of the US-led order.',
  'Das Framing der russischen und chinesischen Staatsmedien: keine Unterstützung für eine der Regierungen, sondern Ausnutzung des Risses, der US-Druck auf Mexiko ist Monroe-Doktrin-Imperialismus, Washington drangsaliert seinen Nachbarn und behandelt Lateinamerika als seinen Hinterhof, die Kartell- und Migrationsbedrohungen sind Vorwände, und der Vorfall beweist die Heuchelei der US-geführten Ordnung.',
  ARRAY['EUROPE-RUSSIA','ASIA-CHINA'],
  ARRAY['RT','TASS','TASS (EN)','tass.com','Sputnik','RIA Novosti','CGTN','Global Times','China Daily','Xinhua','Press TV'],
  ARRAY['imperialism','backyard','Monroe','bullying','hegemony','pretext','double standard','neo-colonial','sphere of influence']
)
ON CONFLICT (id) DO UPDATE SET
  fn_id = EXCLUDED.fn_id, display_order = EXCLUDED.display_order,
  stance = EXCLUDED.stance, framing_required = EXCLUDED.framing_required,
  name_en = EXCLUDED.name_en, name_de = EXCLUDED.name_de,
  stance_label_en = EXCLUDED.stance_label_en, stance_label_de = EXCLUDED.stance_label_de,
  claim_en = EXCLUDED.claim_en, claim_de = EXCLUDED.claim_de,
  actor_centroids = EXCLUDED.actor_centroids, publishers = EXCLUDED.publishers,
  framing_keywords = EXCLUDED.framing_keywords, is_active = true, updated_at = now();

COMMIT;
