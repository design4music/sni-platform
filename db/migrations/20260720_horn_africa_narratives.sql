-- Horn of Africa: atomic narratives (greenfield, 2026-07-20).
--
-- All coalitions are grounded in measured publisher distributions over 180d,
-- not assumed. framing_required stays FALSE everywhere: every pair below is
-- publisher-DISJOINT, so the publisher alone disambiguates stance and no
-- framing gate is needed (spec §5).
--
-- OWN-GOAL CHECK (spec §5): none of the three atomics is an own-goal topic.
-- The critical coverage here does NOT span a camp that otherwise supports the
-- actor -- Western outlets are not an Abiy-supportive bloc that turned critic,
-- they are critical throughout. So the three-stance framing_required model is
-- not needed.
--
-- RIFT-EXPLOITATION CHECK (spec §5): deliberately NOT used on
-- somaliland_recognition_contest. That caveat is for INTRA-WESTERN disputes
-- where Russia/China are bystanders amplifying a split. Israel is a PRINCIPAL
-- PARTY to the Somaliland recognition, exactly like China in the South China
-- Sea, so pro-Kremlin and Iranian coverage belongs on the dispute's own
-- sovereignty axis, not a separate hypocrisy axis. RT's actual Somaliland
-- output ("Somalia condemns Somaliland push for embassy in Jerusalem",
-- "Israel's recognition 'null and void' - African Union") is straightforwardly
-- the sovereignty claim, so it is filed there.
--
-- NO PRO-ADDIS NARRATIVE (Cuba lesson: a stance can have NO constituency --
-- retire it, don't keyword-stuff it). A "+2 Addis defends national unity"
-- narrative was drafted and dropped: the feed has no Ethiopian-government
-- advocacy bloc. CGTN/China Daily/Global Times cover Ethiopia as a DEVELOPMENT
-- partner (Chinese-built wind farm, buses converted to gas, zero-tariff policy)
-- and RT as an ARMS and trade customer (Russian drones, trade tripled) -- none
-- of it takes a side on Tigray or Eritrea. What they do carry is a
-- tensions-are-overstated / normalisation frame ("Tigray denies 'totally
-- untrue' claims of planning war", "Ethiopian Airlines resume flights to
-- Tigray"), which is what ethiopia_partnership_normalisation encodes at +1 --
-- an honest reading of that bloc rather than a manufactured +2.

BEGIN;

-- ===========================================================================
-- A. somaliland_recognition_contest
--    Israeli bloc (JPost 15 / ToI 15 / i24 10 / Haaretz 3) vs the Arab-Turkish-
--    Iranian-Russian sovereignty bloc (Egypt Today 7 / Al Jazeera 7 / RT 7 /
--    Daily Sabah 6 / Al-Ahram 5 / Anadolu 4) vs Western analytic (FT / Le Monde
--    / DW / IISS / Reuters / BBC). Fully disjoint.
-- ===========================================================================

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required,
    display_order, is_active
) VALUES
(
 'somaliland_statehood_earned', 'somaliland_recognition_contest',
 'Recognition of an earned statehood',
 'Anerkennung einer erarbeiteten Staatlichkeit',
 'Somaliland has governed itself peacefully and held competitive elections for over three decades, and recognition simply acknowledges a reality the world has ignored; the partnership with Israel opens trade, minerals and security cooperation for a state long locked out of them.',
 'Somaliland regiert sich seit über drei Jahrzehnten friedlich selbst und hält kompetitive Wahlen ab; die Anerkennung bestätigt lediglich eine Realität, die die Welt ignoriert hat. Die Partnerschaft mit Israel eröffnet einem lange ausgeschlossenen Staat Handel, Rohstoffe und Sicherheitskooperation.',
 2, 'Recognition is deserved', 'Die Anerkennung ist verdient',
 ARRAY['AFRICA-HORN','MIDEAST-ISRAEL'],
 ARRAY['Jerusalem Post','Times of Israel','i24NEWS','Haaretz','News24'],
 ARRAY['recognition','recognise','recognize','ambassador','embassy','historic','self-determination','democratic','Anerkennung','Botschaft','Selbstbestimmung'],
 false, 1, true
),
(
 'somali_territorial_integrity', 'somaliland_recognition_contest',
 'A violation of Somalia''s territorial integrity',
 'Ein Verstoß gegen Somalias territoriale Integrität',
 'Somaliland is part of Somalia under international law and the African Union''s founding principle of inherited borders; a unilateral recognition traded for minerals and a military base is an illegal act that rewards secession and invites external powers to redraw the Horn.',
 'Somaliland ist völkerrechtlich Teil Somalias und unterliegt dem Gründungsprinzip der Afrikanischen Union von der Unverletzlichkeit der ererbten Grenzen. Eine einseitige, gegen Rohstoffe und einen Militärstützpunkt eingetauschte Anerkennung ist ein illegaler Akt, der Sezession belohnt und fremde Mächte einlädt, das Horn neu zu ordnen.',
 -2, 'The recognition is illegitimate', 'Die Anerkennung ist unrechtmäßig',
 ARRAY['AFRICA-HORN','MIDEAST-EGYPT','MIDEAST-TURKEY'],
 ARRAY['Al Jazeera','Egypt Today','Al-Ahram','Daily Sabah','Anadolu Agency','Al Arabiya','Arab News','TRT World','Press TV','RT','TASS (EN)','Dawn'],
 ARRAY['sovereignty','territorial integrity','illegal','null and void','condemn','reject','violation','interference','Souveränität','territoriale Integrität','verurteilen','völkerrechtswidrig'],
 false, 2, true
),
(
 'somaliland_transactional_scramble', 'somaliland_recognition_contest',
 'Statehood traded for bases and minerals',
 'Staatlichkeit im Tausch gegen Stützpunkte und Rohstoffe',
 'Recognition is being priced rather than judged: Somaliland has offered critical minerals and basing rights in exchange for diplomatic status, and the result pulls a stable territory into a Red Sea military scramble it has no capacity to control.',
 'Die Anerkennung wird nicht beurteilt, sondern verhandelt: Somaliland bietet kritische Rohstoffe und Stützpunktrechte im Tausch gegen diplomatischen Status an. Das Ergebnis zieht ein bislang stabiles Gebiet in ein militärisches Wettrennen am Roten Meer, das es nicht kontrollieren kann.',
 -1, 'A transactional great-power bargain', 'Ein transaktionaler Großmachthandel',
 ARRAY['AFRICA-HORN','AMERICAS-USA'],
 ARRAY['Financial Times','Le Monde','Deutsche Welle','IISS','Reuters','BBC World','France 24','France 24 (EN)','Die Zeit','Der Standard','Daily Nation','The Standard'],
 ARRAY['minerals','critical mineral','military base','basing','port','leverage','scramble','strategic','maelstrom','Bodenschätze','Stützpunkt','Militärbasis'],
 false, 3, true
);

-- ===========================================================================
-- B. ethiopia_regional_confrontation
--    Egyptian state bloc (Al-Ahram 19 / Egypt Today 5) vs Western alarm
--    (Reuters 6 / BBC 5 / AFP 5 / DW 5 / France 24 3 / Economist 3) vs the
--    Chinese-Russian partnership frame (CGTN 3 + China Daily + GT + RT).
-- ===========================================================================

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required,
    display_order, is_active
) VALUES
(
 'ethiopia_partnership_normalisation', 'ethiopia_regional_confrontation',
 'Tensions overstated, partnership continues',
 'Überzeichnete Spannungen, fortgesetzte Partnerschaft',
 'Reports of an imminent northern war are exaggerated and often denied by the parties themselves; flights and administration are being restored, and Ethiopia remains a functioning partner for investment, infrastructure and trade regardless of the diplomatic noise around it.',
 'Berichte über einen unmittelbar bevorstehenden Krieg im Norden sind übertrieben und werden von den Beteiligten selbst dementiert. Flugverbindungen und Verwaltung werden wiederhergestellt, und Äthiopien bleibt ungeachtet des diplomatischen Lärms ein funktionierender Partner für Investitionen, Infrastruktur und Handel.',
 1, 'Tensions are overstated', 'Die Spannungen sind überzeichnet',
 ARRAY['AFRICA-HORN','ASIA-CHINA'],
 ARRAY['CGTN','China Daily','Global Times','RT','TASS (EN)','Xinhua','ANSA'],
 ARRAY['denies','untrue','resume','restore','cooperation','investment','partnership','development','dementiert','Zusammenarbeit','Wiederaufnahme'],
 false, 1, true
),
(
 'ethiopia_renewed_war_alarm', 'ethiopia_regional_confrontation',
 'A second northern war in the making',
 'Ein zweiter Krieg im Norden bahnt sich an',
 'The Pretoria settlement is unravelling: the Tigrayan party has restored its pre-war administration, drones are striking again, Eritrean troops are accused of crossing the border, and an election that excluded Tigray has removed the last political off-ramp.',
 'Das Abkommen von Pretoria zerfällt: Die tigrayische Partei hat ihre Vorkriegsverwaltung wiederhergestellt, es fliegen wieder Drohnenangriffe, eritreischen Truppen wird ein Grenzübertritt vorgeworfen, und eine Wahl unter Ausschluss Tigrays hat den letzten politischen Ausweg beseitigt.',
 -1, 'Alarm at a returning war', 'Alarm vor einem wiederkehrenden Krieg',
 ARRAY['AFRICA-HORN'],
 ARRAY['Reuters','BBC World','BBC','AFP','AFP Fact Check','Deutsche Welle','France 24','France 24 (EN)','The Economist','Associated Press','The Guardian','Le Monde','Atlantic Council','Daily Nation','News24','UN News','Bloomberg','CNN','Al Jazeera','Anadolu Agency','TRT World','Japan Times','Straits Times','The Standard'],
 ARRAY['brink','war','fears','renewed','clashes','drone','atrocities','massacre','accountability','excluded','withdrawal','incursion','Krieg','Eskalation','Gräueltaten','Rechenschaft'],
 false, 2, true
),
(
 'ethiopia_regional_revisionism', 'ethiopia_regional_confrontation',
 'A revisionist power destabilising the region',
 'Eine revisionistische Macht destabilisiert die Region',
 'Addis Ababa''s pursuit of a seaport and its unilateral control of the Nile dam are expansionist demands on its neighbours'' sovereignty, and the deepening Egyptian partnerships with Eritrea, Djibouti and Somalia are a legitimate defensive response to them.',
 'Addis Abebas Streben nach einem Seehafen und seine einseitige Kontrolle über den Nilstaudamm sind expansionistische Ansprüche gegenüber der Souveränität seiner Nachbarn. Die vertieften ägyptischen Partnerschaften mit Eritrea, Dschibuti und Somalia sind eine legitime Antwort darauf.',
 -2, 'Ethiopia is the destabiliser', 'Äthiopien ist der Destabilisator',
 ARRAY['AFRICA-HORN','MIDEAST-EGYPT'],
 ARRAY['Al-Ahram','Egypt Today','The National'],
 ARRAY['expansionist','sovereignty','water','dam','GERD','Nile','isolate','parallel entities','littoral','Souveränität','Nil','Staudamm','expansionistisch'],
 false, 3, true
);

-- ===========================================================================
-- C. somalia_state_security
--    Turkish-Kenyan constructive bloc (Anadolu 17 / Daily Sabah 16 / Daily
--    Nation 15 / The Standard 12) vs Western fragility/humanitarian reporting
--    (UN News 10 / BBC 9 / Guardian 5 / DW 4 / Reuters 3) vs the anti-US
--    intervention critique (RT 6 / Press TV 3).
--    NOTE Al Jazeera and Anadolu sit on DIFFERENT atomics' blocs here than in
--    (A) -- that is intentional and measured per atomic, not an inconsistency.
-- ===========================================================================

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required,
    display_order, is_active
) VALUES
(
 'somali_state_rebuilding', 'somalia_state_security',
 'A state rebuilding with regional partners',
 'Ein Staat im Wiederaufbau mit regionalen Partnern',
 'The federal government is steadily recovering ground and capacity: offensives are pushing al-Shabaab out of districts, offshore energy exploration and Turkish training are building genuine state institutions, and neighbours increasingly treat Mogadishu as a partner rather than a problem.',
 'Die Bundesregierung gewinnt stetig Gebiete und Handlungsfähigkeit zurück: Offensiven drängen al-Shabaab aus Distrikten, Offshore-Energieerkundung und türkische Ausbildung schaffen echte staatliche Institutionen, und die Nachbarn behandeln Mogadischu zunehmend als Partner statt als Problem.',
 2, 'The state is being rebuilt', 'Der Staat wird wiederaufgebaut',
 ARRAY['AFRICA-HORN','MIDEAST-TURKEY'],
 ARRAY['Anadolu Agency','Daily Sabah','TRT World','Daily Nation','The Standard','Egypt Today','Al-Ahram','ANSA'],
 ARRAY['transformation','renewal','institutions','cooperation','partnership','drilling','energy','training','offensive','recaptured','Wiederaufbau','Partnerschaft','Institutionen'],
 false, 1, true
),
(
 'somali_fragility_and_harm', 'somalia_state_security',
 'A fragile state and an abandoned population',
 'Ein fragiler Staat und eine im Stich gelassene Bevölkerung',
 'The recovery is thinner than claimed: famine is returning as aid funding collapses, the capital saw armed clashes over a delayed election, piracy has resumed off the coast, and the counter-terror campaign is inflicting civilian casualties with little accountability.',
 'Die Erholung ist dünner als behauptet: Mit dem Wegbrechen der Hilfsgelder kehrt die Hungersnot zurück, in der Hauptstadt kam es wegen einer verschobenen Wahl zu bewaffneten Zusammenstößen, vor der Küste ist die Piraterie zurück, und der Anti-Terror-Einsatz fordert zivile Opfer ohne nennenswerte Rechenschaft.',
 -1, 'Fragility and humanitarian failure', 'Fragilität und humanitäres Versagen',
 ARRAY['AFRICA-HORN'],
 ARRAY['UN News','The Guardian','BBC World','BBC','Reuters','Deutsche Welle','Associated Press','Financial Times','Kurier','France 24','France 24 (EN)','Al Jazeera','The Telegraph','Der Spiegel','Die Zeit','Der Standard','DR','Military Times','Defense News'],
 ARRAY['famine','hunger','malnutrition','drought','aid','clashes','protest','election delay','piracy','pirates','civilian','casualties','Hungersnot','Dürre','Piraterie','Zusammenstöße'],
 false, 2, true
),
(
 'somali_foreign_militarisation_critique', 'somalia_state_security',
 'Foreign militarisation is the destabiliser',
 'Ausländische Militarisierung ist der Destabilisator',
 'Somalia''s insecurity is being deepened from outside: American airstrikes kill civilians while Washington blocks UN support for the African Union mission, and an Israeli military foothold on the coast would turn Somali waters into another front in someone else''s war.',
 'Somalias Unsicherheit wird von außen verschärft: Amerikanische Luftangriffe töten Zivilisten, während Washington die UN-Unterstützung für die Mission der Afrikanischen Union blockiert; ein israelischer Militärstützpunkt an der Küste würde somalische Gewässer zu einer weiteren Front in einem fremden Krieg machen.',
 -2, 'Outside intervention is to blame', 'Die Einmischung von außen ist schuld',
 ARRAY['AFRICA-HORN','AMERICAS-USA'],
 ARRAY['RT','Press TV','TASS (EN)','Sputnik'],
 ARRAY['airstrike','strikes','blocks','blockade','foreign','intervention','base','legitimate target','sovereignty','imperial','Luftangriff','Einmischung','Stützpunkt'],
 false, 3, true
);

COMMIT;
