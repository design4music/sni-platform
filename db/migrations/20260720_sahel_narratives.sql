-- Sahel theater: atomic + theater narratives (greenfield, 2026-07-20).
--
-- SIGN CONVENTION (theater-wide -- must be consistent or the §5.5 roll-up
-- mixes axes). This theater has no single dyad, so the axis is the CAMP, not
-- the country:
--   +  the sovereigntist / counterterror-partnership camp's framing
--      (Russian and Chinese state media; Nigerian state-security reporting)
--   -  the critical framing
--      (Western mainstream; Arab/Turkish humanitarian)
--
-- Publisher blocs, and the §5.5 disjointness they buy:
--   POSITIVE bucket:  Russian+Chinese state  |  Nigerian    -- disjoint
--   NEGATIVE bucket:  Western mainstream     |  Arab/Turkish -- disjoint
-- Atomic narratives may mix blocs freely; the constraint that actually matters
-- is that each THEATER card's publisher list is disjoint within its sign
-- bucket, because the card pulls on (sign, publisher) and counts distinct
-- titles. Verified after apply.
--
-- WHY sahel_jihadist_insurgency GETS THREE STANCES (spec §5, own-goal rule).
-- Counterinsurgency abuses are covered critically by the SAME Western outlets
-- that report the insurgent advance: Le Monde on Africa Corps "atrocités",
-- France 24 on the HRW report into army exactions since April, Al Jazeera on
-- the drone strike that killed civilians at a wedding. Publisher alignment
-- therefore cannot separate "the state is losing" from "the state is
-- committing abuses" -- both are Western, and collapsing them would file
-- atrocity coverage as battlefield reporting. So -2 and -1 share the Western
-- coalition with framing_required=true and disjoint keywords; only the +2
-- partnership stance is publisher-disjoint and needs no framing gate.
--
-- NO RIFT-EXPLOITATION CARD (spec §5, contrast Arctic). That caveat is for
-- INTRA-WESTERN disputes where Russia is a bystander amplifying a split. Here
-- France vs Burkina/Mali is not intra-Western, and Russia is a PRINCIPAL -- it
-- supplies the Africa Corps, Moscow issues statements as a party, and its
-- withdrawal from Kidal is itself the story. Russian coverage belongs on each
-- dispute's own axis, as it did for China in the SCS build.
--
-- STANCE-AMBIGUOUS KEYWORDS DELIBERATELY EXCLUDED:
--   'retrait' / 'withdrawal' -- appears in the Russian-partnership frame
--      ("Moscou rejette l'appel au retrait") and the Russian-failure frame
--      ("Africa Corps confirms withdrawal from Kidal"). Neutral; cut.
--   'terroriste' / 'terrorist' -- this is the JUNTA's label for the FLA and
--      JNIM alike. On a critical stance it would invert the title's meaning.
--      Confined to the +2 counterterror stances where it IS the speaker's frame.
--   'offensive' / 'attaque' -- pure event description, both camps.
--
-- Counts are expected to be small on sahel_security_patron_contest (19 titles)
-- and sahel_france_rupture (24). Recorded as measured, not padded.
--
-- No DELETE; INSERT ... ON CONFLICT. Reversible.

BEGIN;

-- ===========================================================================
-- A. sahel_jihadist_insurgency -- three-stance (own-goal topic)
-- ===========================================================================
INSERT INTO narratives_v2 (id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de, publishers, framing_keywords,
    framing_required, actor_centroids, display_order, is_active) VALUES

('sahel_counterterror_necessity', 'sahel_jihadist_insurgency',
 'A legitimate war against armed extremist groups',
 'Ein legitimer Krieg gegen bewaffnete extremistische Gruppen',
 'Sahelian and Nigerian armies, with the partners they have chosen, are fighting internationally designated armed groups that kill civilians, abduct schoolchildren and blockade cities -- and operations that degrade those groups deserve support rather than second-guessing.',
 'Die Armeen der Sahelzone und Nigerias kämpfen gemeinsam mit den von ihnen gewählten Partnern gegen international gelistete bewaffnete Gruppen, die Zivilisten töten, Schulkinder entführen und Städte blockieren -- Operationen, die diese Gruppen schwächen, verdienen Unterstützung statt Zweifel.',
 2, 'Counterterror necessity', 'Notwendige Terrorbekämpfung',
 ARRAY['RT','rt.com','TASS','TASS (EN)','tass.com','tass.ru','RIA Novosti','ria.ru','Kommersant','kommersant.ru','BelTA','BelTA Russian','CGTN','news.cgtn.com','newsaf.cgtn.com','Global Times','China Daily','People''s Daily','Xinhua','Vanguard','Vanguard News','Punch','Punch Newspapers','The Nation Newspaper','Premium Times Nigeria'],
 ARRAY[]::text[], false,
 ARRAY['AFRICA-SAHEL','AFRICA-NIGERIA','EUROPE-RUSSIA'], 1, true),

('sahel_state_losing_ground', 'sahel_jihadist_insurgency',
 'The state is losing territory it cannot recover',
 'Der Staat verliert Gebiet, das er nicht zurückgewinnen kann',
 'Coordinated assaults on Bamako, the fuel blockade of the capital and the fall of garrison towns show armies that no longer control their own terrain, and a military government whose core promise -- security -- has failed.',
 'Koordinierte Angriffe auf Bamako, die Treibstoffblockade der Hauptstadt und der Fall von Garnisonsstädten zeigen Armeen, die ihr eigenes Terrain nicht mehr kontrollieren, und eine Militärregierung, deren Kernversprechen -- Sicherheit -- gescheitert ist.',
 -2, 'State losing ground', 'Staat verliert Boden',
 ARRAY['France 24','France 24 (EN)','Le Monde','Le Figaro','Reuters','Associated Press','BBC World','Deutsche Welle','Die Zeit','Der Spiegel','Der Standard','Tagesschau','Süddeutsche Zeitung','Frankfurter Allgemeine','The Guardian','Washington Post','New York Times','The Telegraph','Sky News','Euronews','El País','El Mundo','La Repubblica','Corriere della Sera','Straits Times','Bangkok Post','WION','NDTV','The Hindu','Times of India','Janes','Kyiv Post','Novinite','News24','Daily Nation','Council on Foreign Relations','War on the Rocks','Military Times','Defense News','Financial Times','iROZHLAS','Republic TV','The National'],
 ARRAY['losing','lost control','seize','seized','captured','advance','advancing','blockade','siege','encircl','expand','spread','unprecedented','fragilis','vacille','recule','étouffer','emprise','progression','s''empare','sans précédent','inédit','verliert','Vormarsch','beispiellos','pierde','avanza','asedio'],
 true, ARRAY['AFRICA-SAHEL','AFRICA-NIGERIA'], 2, true),

('sahel_counterinsurgency_abuses', 'sahel_jihadist_insurgency',
 'The counterinsurgency is killing the civilians it claims to protect',
 'Die Aufstandsbekämpfung tötet die Zivilisten, die sie zu schützen vorgibt',
 'Drone strikes on weddings, mass executions documented by rights monitors, and the abuses of foreign auxiliaries mean the campaign against the armed groups is itself a major source of civilian death -- and impunity is fuelling recruitment.',
 'Drohnenangriffe auf Hochzeiten, von Menschenrechtsbeobachtern dokumentierte Massenexekutionen und die Übergriffe ausländischer Hilfstruppen machen den Feldzug gegen die bewaffneten Gruppen selbst zu einer Hauptursache ziviler Todesfälle -- und die Straflosigkeit befeuert die Rekrutierung.',
 -1, 'Civilian cost of the campaign', 'Ziviler Preis des Feldzugs',
 ARRAY['Al Jazeera','Al-Ahram','Ahram Online','Al Arabiya','Al Arabiya English','Anadolu Agency','Anadolu Ajansı','TRT World','Daily Sabah','Gulf News','Gulf Times','Arab News','UN News','France 24','France 24 (EN)','Le Monde','Le Figaro','Deutsche Welle','The Guardian','Der Spiegel','Die Zeit','BBC World','Washington Post'],
 ARRAY['civilian','civilians','civils','exactions','atrocit','massacre','abuses','human rights','Human Rights Watch','HRW','executions','wedding','mariage','impunity','impunité','disappearance','Zivilisten','Menschenrechte','Übergriffe','Gräueltaten','civiles','derechos humanos'],
 true, ARRAY['AFRICA-SAHEL','AFRICA-NIGERIA'], 3, true),

-- ===========================================================================
-- B. sahel_tuareg_separatism
-- ===========================================================================
('sahel_northern_autonomy_claim', 'sahel_tuareg_separatism',
 'Northern Mali is a political question, not only a military one',
 'Nordmali ist eine politische Frage, nicht nur eine militärische',
 'The Tuareg movements hold Kidal and press a decades-old claim over the north that no government has settled by force; treating an unresolved territorial dispute purely as terrorism forecloses the negotiation that any durable outcome requires.',
 'Die Tuareg-Bewegungen halten Kidal und verfolgen einen jahrzehntealten Anspruch auf den Norden, den keine Regierung militärisch gelöst hat; einen ungelösten Territorialkonflikt allein als Terrorismus zu behandeln, verbaut die Verhandlung, die jede dauerhafte Lösung braucht.',
 -2, 'Unresolved territorial claim', 'Ungelöster Gebietsanspruch',
 ARRAY['France 24','France 24 (EN)','Le Monde','Le Figaro','Reuters','Associated Press','BBC World','Deutsche Welle','Die Zeit','Der Spiegel','Euronews','The Guardian','El País','Straits Times','Bangkok Post','NDTV','The Hindu','Kyiv Post','Janes','Al Jazeera','Al-Ahram','Al Arabiya','Anadolu Agency','Gulf News','Republic TV','The National'],
 ARRAY[]::text[], false,
 ARRAY['AFRICA-SAHEL'], 1, true),

('sahel_separatism_as_jihadist_alliance', 'sahel_tuareg_separatism',
 'The separatists are a front for the armed extremists',
 'Die Separatisten sind ein Vorwand für die bewaffneten Extremisten',
 'The northern armed groups now attack alongside al-Qaeda-linked fighters and coordinate their claims with them; that alliance disqualifies any presentation of them as a national-liberation movement with a case to negotiate.',
 'Die bewaffneten Gruppen im Norden greifen inzwischen gemeinsam mit al-Qaida-nahen Kämpfern an und stimmen ihre Erklärungen mit ihnen ab; dieses Bündnis widerlegt jede Darstellung als nationale Befreiungsbewegung mit Verhandlungsanspruch.',
 2, 'A front for the extremists', 'Vorwand für die Extremisten',
 ARRAY['RT','rt.com','TASS','TASS (EN)','tass.com','tass.ru','RIA Novosti','ria.ru','Kommersant','kommersant.ru','BelTA','BelTA Russian','CGTN','news.cgtn.com','newsaf.cgtn.com','Global Times','China Daily','Xinhua','Vanguard','Vanguard News','Punch','Punch Newspapers'],
 ARRAY[]::text[], false,
 ARRAY['AFRICA-SAHEL','EUROPE-RUSSIA'], 2, true),

-- ===========================================================================
-- C. sahel_junta_consolidation
-- ===========================================================================
('sahel_sovereigntist_self_reliance', 'sahel_junta_consolidation',
 'Reclaiming sovereignty after decades of external tutelage',
 'Rückgewinnung der Souveränität nach Jahrzehnten äußerer Bevormundung',
 'The Sahel governments are choosing their own partners, leaving institutions they judge to serve others'' interests, and refusing the conditionality that came with Western support -- an assertion of independence that the states which lost influence naturally portray as decline.',
 'Die Sahel-Regierungen wählen ihre eigenen Partner, verlassen Institutionen, die aus ihrer Sicht fremden Interessen dienen, und weisen die Auflagen westlicher Unterstützung zurück -- eine Behauptung von Unabhängigkeit, die jene Staaten, die an Einfluss verloren, erwartungsgemäß als Niedergang darstellen.',
 2, 'Sovereigntist realignment', 'Souveränistische Neuausrichtung',
 ARRAY['RT','rt.com','TASS','TASS (EN)','tass.com','tass.ru','RIA Novosti','ria.ru','Kommersant','kommersant.ru','BelTA','BelTA Russian','CGTN','news.cgtn.com','newsaf.cgtn.com','Global Times','China Daily','People''s Daily','Xinhua','Vanguard','Vanguard News','Punch','Punch Newspapers'],
 ARRAY[]::text[], false,
 ARRAY['AFRICA-SAHEL','EUROPE-RUSSIA'], 1, true),

('sahel_democratic_closure', 'sahel_junta_consolidation',
 'Military rule is closing the last civic space',
 'Die Militärherrschaft schließt den letzten zivilgesellschaftlichen Raum',
 'Dissolving every political party, suspending foreign media, forcing out the UN human-rights office and abandoning international courts are not sovereignty measures but the removal of every remaining check -- and the transitions promised at each coup keep receding.',
 'Die Auflösung sämtlicher Parteien, die Suspendierung ausländischer Medien, die Vertreibung des UN-Menschenrechtsbüros und der Austritt aus internationalen Gerichten sind keine Souveränitätsmaßnahmen, sondern die Beseitigung jeder verbliebenen Kontrolle -- und die bei jedem Putsch versprochenen Übergänge rücken immer weiter weg.',
 -2, 'Democratic closure', 'Demokratische Schließung',
 ARRAY['France 24','France 24 (EN)','Le Monde','Le Figaro','Reuters','Associated Press','BBC World','Deutsche Welle','Die Zeit','Der Spiegel','Der Standard','Tagesschau','Süddeutsche Zeitung','Frankfurter Allgemeine','The Guardian','Washington Post','New York Times','Euronews','El País','El Mundo','Straits Times','Novinite','News24','Daily Nation','The Standard','Kyiv Post','UN News','Al Jazeera','Al-Ahram','Al Arabiya','Anadolu Agency','Gulf News'],
 ARRAY[]::text[], false,
 ARRAY['AFRICA-SAHEL'], 2, true),

-- ===========================================================================
-- D. sahel_security_patron_contest
-- ===========================================================================
('sahel_russian_partnership_delivers', 'sahel_security_patron_contest',
 'The new partnership delivers what the old one did not',
 'Die neue Partnerschaft liefert, was die alte nicht leistete',
 'Russian forces fight alongside Sahelian armies without demanding governance conditions, intervened to stop an attempted coup and struck the armed groups directly -- results that a decade of Western deployments never produced.',
 'Russische Kräfte kämpfen an der Seite der Sahel-Armeen, ohne Regierungsauflagen zu stellen, griffen ein, um einen Putschversuch zu stoppen, und trafen die bewaffneten Gruppen direkt -- Ergebnisse, die ein Jahrzehnt westlicher Einsätze nie erbrachte.',
 2, 'Partnership delivers', 'Partnerschaft liefert',
 ARRAY['RT','rt.com','TASS','TASS (EN)','tass.com','tass.ru','RIA Novosti','ria.ru','Kommersant','kommersant.ru','BelTA','BelTA Russian','CGTN','news.cgtn.com','newsaf.cgtn.com','Global Times','China Daily','Xinhua'],
 ARRAY[]::text[], false,
 ARRAY['AFRICA-SAHEL','EUROPE-RUSSIA'], 1, true),

('sahel_patron_model_failing', 'sahel_security_patron_contest',
 'The replacement security model is buckling',
 'Das neue Sicherheitsmodell gerät ins Wanken',
 'Africa Corps pulled out of Kidal, lost personnel to rebel attacks and is retreating under jihadist pressure, while Türkiye''s drones and training offer capability without the mass required -- the states that expelled their old partners have not found one that can hold the terrain.',
 'Das Africa Corps zog sich aus Kidal zurück, verlor Personal bei Rebellenangriffen und weicht unter dschihadistischem Druck zurück, während die Drohnen und Ausbildung der Türkei Fähigkeiten ohne die nötige Masse bieten -- die Staaten, die ihre alten Partner vertrieben, haben keinen gefunden, der das Terrain halten kann.',
 -2, 'Replacement model failing', 'Neues Modell scheitert',
 ARRAY['France 24','France 24 (EN)','Le Monde','Le Figaro','Reuters','Associated Press','BBC World','Deutsche Welle','Die Zeit','Der Spiegel','The Guardian','Washington Post','Euronews','El País','Straits Times','Kyiv Post','Janes','Military Times','Defense News','Financial Times','Council on Foreign Relations','War on the Rocks','Al Jazeera','Al-Ahram','Al Arabiya','Anadolu Agency','TRT World','Daily Sabah','Gulf News'],
 ARRAY[]::text[], false,
 ARRAY['AFRICA-SAHEL','EUROPE-RUSSIA'], 2, true),

-- ===========================================================================
-- E. sahel_france_rupture
-- ===========================================================================
('sahel_break_with_paris_justified', 'sahel_france_rupture',
 'Cutting ties ends a relationship that never became equal',
 'Der Bruch beendet eine Beziehung, die nie gleichberechtigt wurde',
 'Severing relations, expelling diplomats and prosecuting intelligence officers close a colonial-era arrangement in which the former ruler kept bases, currency influence and a veto on security policy long after formal independence.',
 'Der Abbruch der Beziehungen, die Ausweisung von Diplomaten und die Verfolgung von Nachrichtendienstoffizieren beenden ein koloniales Arrangement, in dem die frühere Kolonialmacht noch lange nach der formalen Unabhängigkeit Stützpunkte, Währungseinfluss und ein Veto in der Sicherheitspolitik behielt.',
 2, 'Ending the colonial relationship', 'Ende der kolonialen Beziehung',
 ARRAY['RT','rt.com','TASS','TASS (EN)','tass.com','tass.ru','RIA Novosti','ria.ru','Kommersant','kommersant.ru','BelTA','BelTA Russian','CGTN','news.cgtn.com','newsaf.cgtn.com','Global Times','China Daily','Xinhua','Vanguard','Vanguard News','Punch','Punch Newspapers'],
 ARRAY[]::text[], false,
 ARRAY['AFRICA-SAHEL','EUROPE-FRANCE'], 1, true),

('sahel_rupture_deepens_isolation', 'sahel_france_rupture',
 'The break leaves the Sahel with fewer options, not more',
 'Der Bruch lässt der Sahelzone weniger Optionen, nicht mehr',
 'Jailing a diplomat for twenty years, blaming Paris for jihadist attacks and cutting the last diplomatic channels remove partners and aid at the moment the security situation is deteriorating fastest -- and the sovereignty gained is largely rhetorical.',
 'Einen Diplomaten zu zwanzig Jahren Haft zu verurteilen, Paris für dschihadistische Anschläge verantwortlich zu machen und die letzten diplomatischen Kanäle zu kappen, entzieht Partner und Hilfe genau dann, wenn sich die Sicherheitslage am schnellsten verschlechtert -- und die gewonnene Souveränität bleibt weitgehend rhetorisch.',
 -2, 'Isolation, not sovereignty', 'Isolation statt Souveränität',
 ARRAY['France 24','France 24 (EN)','Le Monde','Le Figaro','Reuters','Associated Press','BBC World','Deutsche Welle','Die Zeit','Der Spiegel','Euronews','The Guardian','El País','Straits Times','Daily Nation','News24','Novinite','Kyiv Post','Al Jazeera','Al-Ahram','Al Arabiya','Anadolu Agency','Gulf News'],
 ARRAY[]::text[], false,
 ARRAY['AFRICA-SAHEL','EUROPE-FRANCE'], 2, true)

ON CONFLICT (id) DO UPDATE SET
    fn_id = EXCLUDED.fn_id, name_en = EXCLUDED.name_en, name_de = EXCLUDED.name_de,
    claim_en = EXCLUDED.claim_en, claim_de = EXCLUDED.claim_de,
    stance = EXCLUDED.stance, stance_label_en = EXCLUDED.stance_label_en,
    stance_label_de = EXCLUDED.stance_label_de, publishers = EXCLUDED.publishers,
    framing_keywords = EXCLUDED.framing_keywords,
    framing_required = EXCLUDED.framing_required,
    actor_centroids = EXCLUDED.actor_centroids,
    display_order = EXCLUDED.display_order, is_active = true, updated_at = NOW();

COMMIT;
