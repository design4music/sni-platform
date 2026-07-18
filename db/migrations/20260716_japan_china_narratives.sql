-- japan_china_theater: atomic + theater narratives (FN_THEATER_BUILD_SPEC 0a steps 6-7)
--
-- Coalition design, grounded in measured publisher counts per atomic (180d):
--   Chinese state : Global Times / CGTN / China Daily / People's Daily / Xinhua
--   Japanese      : Japan Times / Nikkei Asia / Asahi Shimbun / Kyodo News / NHK World
--   Western wire  : Reuters / Bloomberg / FT / WSJ / Straits Times / CNA / Guardian / DW
-- Fully disjoint on every atomic.
--
-- NO own-goal / friendly-critic split (spec 5): checked and rejected against the corpus.
-- Japanese and Western press are uniformly aligned with the government framing
-- ("China squeezes Japan over rare earths", "Takaichi warns of China 'coercion'",
-- "Landslide election victory lets Takaichi confront China on her terms"). Takaichi won
-- a landslide; there is no cross-camp critical strand as there is on Ukraine corruption.
-- Publisher alone therefore disambiguates stance -> framing_required=false throughout.
--
-- NO rift-exploitation card (spec 5, rift caveat): that caveat is for INTRA-WESTERN
-- disputes where Russia/China are bystanders amplifying a split. China is a PRINCIPAL
-- PARTY here, so its coverage belongs on the dispute's own pro/con axis (the SCS lesson).
-- Russian outlets genuinely push the Japanese-militarism line (a longstanding line tied to
-- WWII/Kurils), so they fold INTO that narrative rather than getting one of their own --
-- and only where evidenced, per the us_china lesson that Russian wires are not
-- stance-saturated.
--
-- Stance axis is theater-consistent (following us_china_theater, the closest analogue):
-- Japanese/Western framing = POSITIVE, Chinese state framing = NEGATIVE. This must hold
-- across all five atomics or the theater roll-up (spec 5.5) would pull Chinese-state
-- titles into both sign buckets and double-count them.

BEGIN;

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, framing_required, is_active,
                           name_en, name_de, stance_label_en, stance_label_de,
                           actor_centroids, publishers, framing_keywords, claim_en, claim_de)
VALUES

-- ============ senkaku_diaoyu_islands ============
('senkaku_japanese_administration', 'senkaku_diaoyu_islands', 1, 2, false, true,
 'The Senkakus are Japanese-administered territory and Chinese vessel entries are grey-zone pressure',
 'Die Senkaku-Inseln stehen unter japanischer Verwaltung, und das Eindringen chinesischer Schiffe ist Grauzonen-Druck',
 'Japanese administration / grey-zone pressure',
 'Japanische Verwaltung / Grauzonen-Druck',
 ARRAY['ASIA-JAPAN'],
 ARRAY['Japan Times','Nikkei Asia','Asahi Shimbun','Kyodo News','NHK World','Japan Wire by KYODO NEWS','Reuters','Bloomberg','Financial Times','Wall Street Journal','Straits Times','Channel NewsAsia','The Telegraph','The Economist','CSIS','Philippine Daily Inquirer','Times of India','NDTV'],
 ARRAY['territorial waters','intrusion','incursion','grey zone','gray zone','unacceptable','repeated','unilateral','protest','disputed','administration','escalation','Hoheitsgewässer','Eindringen','Grauzone'],
 'Administration framing (Japanese and Western press) treats the Senkakus as territory under Japanese administrative control and reads China Coast Guard entries into the surrounding territorial waters and contiguous zone -- along with survey ships, buoys and drilling structures placed near the median line -- as sustained grey-zone pressure intended to normalise a Chinese presence and erode that control without triggering armed conflict. Incidents are counted and protested rather than escalated. Vocabulary: territorial waters, intrusion, grey zone, unacceptable, repeated entry, protest, unilateral development.',
 'Die Verwaltungs-Rahmung (japanische und westliche Presse) betrachtet die Senkaku-Inseln als Gebiet unter japanischer Verwaltungshoheit und deutet das Einlaufen der chinesischen Küstenwache in die umliegenden Hoheitsgewässer und die Anschlusszone -- samt Forschungsschiffen, Bojen und Bohrstrukturen nahe der Mittellinie -- als anhaltenden Grauzonen-Druck, der eine chinesische Präsenz normalisieren und diese Kontrolle aushöhlen soll, ohne einen bewaffneten Konflikt auszulösen. Vorfälle werden gezählt und mit Protesten beantwortet, nicht eskaliert.'),

('senkaku_chinese_rights_protection', 'senkaku_diaoyu_islands', 2, -2, false, true,
 'Diaoyu Dao is inherent Chinese territory and coast guard patrols are lawful rights protection',
 'Diaoyu Dao ist chinesisches Hoheitsgebiet, und die Patrouillen der Küstenwache sind rechtmäßiger Rechtsschutz',
 'Chinese rights-protection claim',
 'Chinesischer Rechtsschutz-Anspruch',
 ARRAY['ASIA-CHINA'],
 ARRAY['Global Times','CGTN','China Daily','People''s Daily','Xinhua','Xinhuanet Deutsch'],
 ARRAY['rights protection','law enforcement','inherent territory','sacred territory','expel','illegally intruding','intrusion into China','routine','since ancient times','provocation','remilitarization','Rechtsdurchsetzung','Hoheitsgebiet'],
 'Rights-protection framing (Chinese state media) holds that Diaoyu Dao and its affiliated islets have been Chinese territory since ancient times, that China Coast Guard patrols in the surrounding waters are routine and lawful rights-protection law enforcement in Chinese jurisdiction, and that Japanese vessels entering those waters are the intruders being lawfully expelled. Japanese protests are cast as provocation, and the friction is tied to Tokyo''s accelerating remilitarisation rather than to Chinese activity. Vocabulary: rights protection, law enforcement, inherent territory, expel, illegal intrusion, routine patrol, provocation.',
 'Die Rechtsschutz-Rahmung (chinesische Staatsmedien) sieht Diaoyu Dao und die zugehörigen Inseln seit jeher als chinesisches Hoheitsgebiet an. Patrouillen der chinesischen Küstenwache gelten als routinemäßige und rechtmäßige Rechtsdurchsetzung in chinesischem Hoheitsbereich; japanische Schiffe in diesen Gewässern seien die Eindringlinge, die rechtmäßig vertrieben würden. Japanische Proteste werden als Provokation dargestellt und die Reibung der beschleunigten Wiederbewaffnung Tokios zugeschrieben.'),

-- ============ japan_china_taiwan_question ============
('jc_taiwan_japan_security_stake', 'japan_china_taiwan_question', 1, 2, false, true,
 'A Taiwan contingency directly threatens Japan''s security and Japan is entitled to say so',
 'Ein Taiwan-Konflikt bedroht Japans Sicherheit unmittelbar, und Japan darf dies aussprechen',
 'Japanese security stake',
 'Japanisches Sicherheitsinteresse',
 ARRAY['ASIA-JAPAN','ASIA-TAIWAN'],
 ARRAY['Japan Times','Nikkei Asia','Asahi Shimbun','Kyodo News','NHK World','Japan Wire by KYODO NEWS','朝日新聞','Reuters','Bloomberg','Financial Times','Wall Street Journal','New York Times','The Economist','The Telegraph','The Guardian','Straits Times','Channel NewsAsia','Deutsche Welle','Al Jazeera','Philippine Daily Inquirer','The Hindu'],
 ARRAY['contingency','survival-threatening','collective self-defense','collective self-defence','security','coercion','pressure','rebuts','retract','deterrence','southwest islands','free and open','stands firm','Sicherheit','Nötigung'],
 'Security-stake framing (Japanese and Western press) holds that Taiwan''s proximity to Japan''s southwestern islands makes a Taiwan contingency a direct question of Japanese national survival, that a prime minister may say so openly, and that Beijing''s response -- demands for retraction, blacklists, mineral restrictions and pressure on tourism -- is coercion aimed at silencing legitimate security debate in a democracy. It reads Japan''s destroyer transits of the Taiwan Strait and its deepening ties with Washington, Manila and G7 partners as lawful and defensive. Vocabulary: contingency, survival-threatening situation, collective self-defence, coercion, rebut, deterrence, free and open Indo-Pacific.',
 'Die Sicherheits-Rahmung (japanische und westliche Presse) sieht in der Nähe Taiwans zu Japans Südwest-Inseln eine unmittelbare Frage des nationalen Überlebens Japans; eine Regierungschefin dürfe dies offen aussprechen. Pekings Reaktion -- Rücknahmeforderungen, schwarze Listen, Rohstoffbeschränkungen und Druck auf den Tourismus -- gilt als Nötigung, die eine legitime sicherheitspolitische Debatte in einer Demokratie zum Schweigen bringen soll. Durchfahrten japanischer Zerstörer durch die Taiwanstraße und engere Bindungen an Washington, Manila und die G7 erscheinen als rechtmäßig und defensiv.'),

('jc_taiwan_interference_charge', 'japan_china_taiwan_question', 2, -2, false, true,
 'Japan''s Taiwan remarks are interference in China''s internal affairs and breach the postwar understanding',
 'Japans Taiwan-Äußerungen sind Einmischung in Chinas innere Angelegenheiten und brechen die Nachkriegsverständigung',
 'Chinese interference charge',
 'Chinesischer Einmischungsvorwurf',
 ARRAY['ASIA-CHINA'],
 ARRAY['Global Times','CGTN','China Daily','People''s Daily','Xinhua','Xinhuanet Deutsch'],
 ARRAY['interference','internal affairs','erroneous remarks','fallacious','red line','one-China','Taiwan question','four political documents','1972','reflect','correct','retract','no right','pretext','bloc confrontation','stoking','Einmischung','innere Angelegenheiten'],
 'Interference framing (Chinese state media) holds that Taiwan is an internal Chinese affair on which Japan has no standing to comment, that the prime minister''s remarks were erroneous and unlawful, crossed a red line and violated the one-China principle and the four political documents that underpin postwar China-Japan relations, and that they -- not any Chinese response -- are the root cause of the current state of ties. Japan is called on to reflect, correct and retract, and its invocation of collective self-defence is cast as a pretext for intervention and bloc confrontation given its wartime record. Vocabulary: interference, internal affairs, erroneous remarks, red line, one-China principle, four political documents, reflect and correct, pretext, bloc confrontation.',
 'Die Einmischungs-Rahmung (chinesische Staatsmedien) sieht Taiwan als innere Angelegenheit Chinas, zu der Japan kein Mitspracherecht habe. Die Äußerungen der Regierungschefin seien falsch und unrechtmäßig, hätten eine rote Linie überschritten und verstießen gegen das Ein-China-Prinzip sowie die vier politischen Dokumente, auf denen die Nachkriegsbeziehungen beruhen; sie seien -- und nicht etwaige chinesische Reaktionen -- die Ursache des derzeitigen Zustands der Beziehungen. Japan solle sich besinnen, korrigieren und widerrufen; die Berufung auf kollektive Selbstverteidigung gelte angesichts der Kriegsvergangenheit als Vorwand für Intervention und Blockkonfrontation.'),

-- ============ japan_defense_expansion ============
('jde_deterrence_response', 'japan_defense_expansion', 1, 2, false, true,
 'Japan''s defense build-up is a proportionate response to China''s military expansion',
 'Japans Verteidigungsaufbau ist eine verhältnismäßige Antwort auf Chinas militärische Expansion',
 'Deterrence response',
 'Abschreckungs-Antwort',
 ARRAY['ASIA-JAPAN'],
 ARRAY['Japan Times','Nikkei Asia','Asahi Shimbun','Kyodo News','NHK World','Japan Wire by KYODO NEWS','朝日新聞','Reuters','Bloomberg','Financial Times','Wall Street Journal','New York Times','The Economist','The Telegraph','The Guardian','Straits Times','Channel NewsAsia','Deutsche Welle','Al Jazeera'],
 ARRAY['deterrence','defense-oriented','defence-oriented','response','counter','rebuff','rebuts','proportionate','exclusively defensive','security environment','severe','concern','buildup','capability','Abschreckung','Verteidigung'],
 'Deterrence framing (Japanese and Western press) presents Japan''s counter-strike capability, higher defense spending, eased equipment-transfer rules and closer alignment with the United States, NATO and regional partners as a proportionate and exclusively defence-oriented answer to a deteriorating security environment -- Chinese naval and air activity around the southwestern islands, missile growth, and the Taiwan contingency. It records Tokyo''s rejection of the militarism charge and names China as the principal concern in its own doctrine documents. Vocabulary: deterrence, exclusively defence-oriented, severe security environment, response, capability, rebuff.',
 'Die Abschreckungs-Rahmung (japanische und westliche Presse) stellt Japans Gegenschlagfähigkeit, höhere Verteidigungsausgaben, gelockerte Regeln für Rüstungstransfers und die engere Anbindung an die USA, die NATO und regionale Partner als verhältnismäßige und ausschließlich verteidigungsorientierte Antwort auf ein sich verschlechterndes Sicherheitsumfeld dar -- chinesische Marine- und Luftaktivitäten um die Südwest-Inseln, wachsende Raketenarsenale und einen möglichen Taiwan-Konflikt. Sie hält Tokios Zurückweisung des Militarismus-Vorwurfs fest.'),

('jde_militarism_revival', 'japan_defense_expansion', 2, -2, false, true,
 'Japan is hollowing out its pacifist constitution and reviving militarism',
 'Japan höhlt seine Friedensverfassung aus und belebt den Militarismus wieder',
 'Militarism-revival charge',
 'Militarismus-Vorwurf',
 ARRAY['ASIA-CHINA','EUROPE-RUSSIA'],
 ARRAY['Global Times','CGTN','China Daily','People''s Daily','Xinhua','Xinhuanet Deutsch','RT','TASS','TASS (EN)','Sputnik','Press TV'],
 ARRAY['militaris','militariz','neo-militaris','remilitariz','revival','ghosts of militarism','pacifist mask','hollow','whitewash','postwar order','vigilance','dangerous path','clean break','crushing defeat','peaceful nation','Militarismus','Wiederbewaffnung'],
 'Militarism-revival framing (Chinese state media, echoed by Russian outlets) holds that Japan''s counter-strike missiles, rising defense budget, scrapped arms-export limits, renamed ranks and constitutional-revision push together hollow out the pacifist constitution and dismantle the postwar order imposed after 1945, revealing a state reverting to its militarist past behind a "peaceful nation" disguise. The China threat is cast as fearmongering manufactured to justify the build-up, and the international community is urged to stay vigilant and coordinate export controls in response. Vocabulary: neo-militarism, remilitarisation, revival, ghosts of militarism, pacifist mask, whitewash, postwar order, vigilance, dangerous path.',
 'Die Militarismus-Rahmung (chinesische Staatsmedien, aufgegriffen von russischen Medien) sieht in Japans Gegenschlagraketen, steigendem Verteidigungshaushalt, gestrichenen Rüstungsexportgrenzen, umbenannten Dienstgraden und dem Vorstoß zur Verfassungsänderung eine Aushöhlung der Friedensverfassung und eine Demontage der Nachkriegsordnung von 1945: ein Staat kehre hinter der Maske einer "friedlichen Nation" zu seiner militaristischen Vergangenheit zurück. Die China-Bedrohung gilt als Angstmacherei zur Rechtfertigung der Aufrüstung.'),

-- ============ china_japan_economic_restrictions ============
('cjer_economic_coercion', 'china_japan_economic_restrictions', 1, 2, false, true,
 'China is weaponizing trade, minerals and tourism to punish Japanese political speech',
 'China instrumentalisiert Handel, Rohstoffe und Tourismus, um japanische politische Äußerungen zu bestrafen',
 'Economic coercion',
 'Wirtschaftliche Nötigung',
 ARRAY['ASIA-JAPAN'],
 ARRAY['Japan Times','Nikkei Asia','Asahi Shimbun','Kyodo News','NHK World','Japan Wire by KYODO NEWS','朝日新聞','Reuters','Bloomberg','Financial Times','Wall Street Journal','New York Times','The Economist','The Telegraph','The Guardian','Straits Times','Channel NewsAsia','Deutsche Welle','Mining.com','OilPrice','Wired','Al Jazeera','VN Express'],
 ARRAY['coercion','squeeze','chokehold','pressure','weaponiz','retaliation','punish','throttling','blacklist','curbs','showdown','de-risk','diversify','stockpiling','alternatives','non-China','Nötigung','Druck','Vergeltung'],
 'Coercion framing (Japanese and Western press) reads China''s rare-earth and dual-use export controls, entity blacklists, travel advisories, the collapse in Chinese tourism and the detention of Japanese nationals as a coordinated economic punishment for a political statement -- a repeat of the 2010 rare-earth showdown -- and treats supply concentration in Chinese hands as a strategic vulnerability. The response it presents is diversification: seabed mining, recycling, and joint stockpiling with Canada, France and G7 partners to find non-Chinese sources. Vocabulary: coercion, squeeze, chokehold, throttling exports, blacklist, retaliation, de-risking, diversify, non-China sources.',
 'Die Nötigungs-Rahmung (japanische und westliche Presse) deutet Chinas Exportkontrollen für Seltene Erden und Güter mit doppeltem Verwendungszweck, schwarze Listen für Unternehmen, Reisewarnungen, den Einbruch des chinesischen Tourismus und die Festnahme japanischer Staatsbürger als koordinierte wirtschaftliche Bestrafung einer politischen Äußerung -- eine Wiederholung des Seltene-Erden-Konflikts von 2010 -- und sieht in der Lieferkonzentration eine strategische Verwundbarkeit. Als Antwort erscheint Diversifizierung: Tiefseeabbau, Recycling und gemeinsame Vorratshaltung mit Kanada, Frankreich und G7-Partnern.'),

('cjer_lawful_regulation', 'china_japan_economic_restrictions', 2, -2, false, true,
 'China''s export controls are lawful regulation and Japan''s own conduct caused the downturn',
 'Chinas Exportkontrollen sind rechtmäßige Regulierung, und Japans eigenes Verhalten hat den Einbruch verursacht',
 'Lawful regulation claim',
 'Anspruch rechtmäßiger Regulierung',
 ARRAY['ASIA-CHINA'],
 ARRAY['Global Times','CGTN','China Daily','People''s Daily','Xinhua','Xinhuanet Deutsch'],
 ARRAY['in accordance with law','lawful','dual-use','military end-user','non-proliferation','international obligations','watch list','erosion of mutual trust','harms business','root cause','self-inflicted','outlier','curb','neo-militaris','in accordance with Chinese laws','rechtmäßig','Gesetz'],
 'Lawful-regulation framing (Chinese state media) presents the export controls as ordinary licensing of dual-use items to military end-users, applied in accordance with Chinese law and international non-proliferation obligations and aimed at curbing Japan''s military build-up rather than at trade. It attributes the fall in tourism and business confidence to Japanese conduct -- an erosion of mutual trust caused by the prime minister''s remarks -- and casts detentions as ordinary law enforcement against violations of Chinese law, while presenting Japanese firms and G7 partners as unconvinced by Tokyo''s hardline stance. Vocabulary: in accordance with law, dual-use, military end-user, watch list, erosion of mutual trust, root cause, outlier.',
 'Die Regulierungs-Rahmung (chinesische Staatsmedien) stellt die Exportkontrollen als gewöhnliche Lizenzierung von Gütern mit doppeltem Verwendungszweck für militärische Endnutzer dar -- angewandt nach chinesischem Recht und internationalen Nichtverbreitungspflichten und gerichtet auf die Eindämmung von Japans Aufrüstung, nicht auf den Handel. Den Rückgang von Tourismus und Geschäftsvertrauen führt sie auf japanisches Verhalten zurück: eine durch die Äußerungen der Regierungschefin verursachte Erosion des gegenseitigen Vertrauens. Festnahmen gelten als normale Strafverfolgung.'),

-- ============ japan_china_memory_wars ============
('memory_political_leverage', 'japan_china_memory_wars', 1, 2, false, true,
 'Historical grievances are raised as political leverage in a deteriorating relationship',
 'Historische Vorwürfe werden als politisches Druckmittel in einer sich verschlechternden Beziehung eingesetzt',
 'History as leverage',
 'Geschichte als Druckmittel',
 ARRAY['ASIA-JAPAN'],
 ARRAY['Japan Times','Nikkei Asia','Asahi Shimbun','Kyodo News','NHK World','Japan Wire by KYODO NEWS','朝日新聞','Reuters','Bloomberg','Financial Times','Wall Street Journal','The Telegraph','The Economist','The Guardian','Straits Times','Channel NewsAsia','Deutsche Welle'],
 ARRAY['risks','wrath','anger','backlash','rebuff','rebuts','tribute','offering','private capacity','personal','tensions','row','amid','deteriorating','Zorn','Empörung'],
 'Leverage framing (Japanese and Western press) reports historical disputes primarily as a barometer of the wider political relationship: a ritual offering to Yasukuni or a rank-renaming is noted for the reaction it will provoke in Beijing rather than adjudicated, prime-ministerial observances are described as made in a private capacity, and the timing of archive openings, relic-restitution campaigns and anniversary commemorations is read against the state of bilateral ties. It neither endorses nor rebuts the historical charges, and records Tokyo''s rejection of the militarism framing attached to them. Vocabulary: risks China''s wrath, backlash, tribute, ritual offering, private capacity, amid tensions, row.',
 'Die Druckmittel-Rahmung (japanische und westliche Presse) berichtet historische Streitfragen vor allem als Barometer des politischen Verhältnisses: Eine rituelle Opfergabe an den Yasukuni-Schrein oder eine Umbenennung von Dienstgraden wird wegen der zu erwartenden Reaktion in Peking vermerkt, nicht inhaltlich entschieden; Besuche von Regierungschefs werden als in privater Eigenschaft erfolgt beschrieben; der Zeitpunkt von Archivöffnungen, Restitutionskampagnen und Gedenktagen wird am Zustand der bilateralen Beziehungen gelesen. Die historischen Vorwürfe werden weder bestätigt noch zurückgewiesen.'),

('memory_historical_accountability', 'japan_china_memory_wars', 2, -2, false, true,
 'Japan has never reckoned with its wartime aggression and continues to honour war criminals',
 'Japan hat seine Kriegsaggression nie aufgearbeitet und ehrt weiterhin Kriegsverbrecher',
 'Historical accountability demand',
 'Forderung nach historischer Verantwortung',
 ARRAY['ASIA-CHINA','EUROPE-RUSSIA'],
 ARRAY['Global Times','CGTN','China Daily','People''s Daily','Xinhua','Xinhuanet Deutsch','RT','TASS','TASS (EN)','Sputnik'],
 ARRAY['reflect on history','face history','aggression','war criminal','notorious','worship','glorif','denial','deny','undeniable','painful lessons','not forget','looted','return','restitution','rubbing salt','victimized','right-wing','revisionis','postwar norms','Geschichte','Aggression'],
 'Accountability framing (Chinese state media, echoed by Russian outlets) holds that Japan has never genuinely reckoned with its war of aggression: offerings to Yasukuni honour convicted war criminals, denial of the Nanjing Massacre and of the coercion of "comfort women" persists among right-wing figures, wartime rank titles are being restored, abandoned chemical weapons remain undestroyed, and looted cultural relics remain unreturned. Newly opened archives and scholar campaigns are presented as undeniable evidence, and the historical record is explicitly linked to a present-day militarist drift that the victimized countries are urged not to forget. Vocabulary: reflect on history, face history of aggression, war criminals, notorious shrine, denial, painful lessons, looted relics, restitution, revisionism.',
 'Die Verantwortungs-Rahmung (chinesische Staatsmedien, aufgegriffen von russischen Medien) sieht Japans Aufarbeitung seines Angriffskriegs als nie erfolgt an: Opfergaben am Yasukuni-Schrein ehrten verurteilte Kriegsverbrecher, die Leugnung des Massakers von Nanking und der Zwangsrekrutierung von "Trostfrauen" halte im rechten Spektrum an, Dienstgrade aus der Kriegszeit würden wiedereingeführt, zurückgelassene Chemiewaffen seien unvernichtet und geraubte Kulturgüter unzurückgegeben. Neu geöffnete Archive gelten als unwiderlegbarer Beleg; die historische Bilanz wird ausdrücklich mit einer gegenwärtigen militaristischen Tendenz verknüpft.'),

-- ============ THEATER-LEVEL cards (spec 5.5) ============
-- Publisher-DISJOINT within each sign bucket. Two buckets only: the corpus does not
-- support a third (Western-critical) card -- Guardian/DW/Al Jazeera coverage here is
-- neutral reporting, not a coherent critical bloc. Two honest cards beat three invented.
('jc_theater_japanese_western_consensus', 'japan_china_theater', 1, 2, false, true,
 'China''s pressure on Japan is coercion that hardens Japanese resolve rather than changing it',
 'Chinas Druck auf Japan ist Nötigung, die Japans Entschlossenheit eher verhärtet als verändert',
 'Japanese/Western consensus',
 'Japanisch-westlicher Konsens',
 ARRAY['ASIA-JAPAN'],
 ARRAY['Japan Times','Nikkei Asia','Asahi Shimbun','Kyodo News','NHK World','Japan Wire by KYODO NEWS','朝日新聞','Reuters','Bloomberg','Financial Times','Wall Street Journal','New York Times','The Economist','The Telegraph','The Guardian','Straits Times','Channel NewsAsia','Deutsche Welle','Al Jazeera','Mining.com','OilPrice','Wired','CSIS','Philippine Daily Inquirer','Times of India','NDTV','VN Express'],
 ARRAY['coercion','pressure','squeeze','deterrence','security','counter','rebuff','diversify','resolve','tensions','Nötigung','Abschreckung'],
 'The Japanese and Western consensus reads the rupture as one initiated by Beijing''s reaction rather than by Tokyo''s words: a prime minister stated a security interest, and China answered with mineral controls, blacklists, a tourism collapse and detentions. Across the theater it treats Chinese pressure -- at sea around the Senkakus, in export licensing, and in the historical register -- as a single coercive repertoire that has hardened Japanese resolve, strengthened the government''s mandate, and accelerated both the defense build-up and the search for supply chains outside China.',
 'Der japanisch-westliche Konsens deutet den Bruch als von Pekings Reaktion ausgelöst, nicht von Tokios Worten: Eine Regierungschefin benannte ein Sicherheitsinteresse, und China antwortete mit Rohstoffkontrollen, schwarzen Listen, einem Einbruch des Tourismus und Festnahmen. Über das gesamte Theater hinweg gilt chinesischer Druck -- zur See um die Senkaku-Inseln, bei Exportlizenzen und im historischen Register -- als ein einziges Nötigungsrepertoire, das Japans Entschlossenheit verhärtet, das Mandat der Regierung gestärkt und sowohl die Aufrüstung als auch die Suche nach Lieferketten außerhalb Chinas beschleunigt hat.'),

('jc_theater_chinese_state_counter', 'japan_china_theater', 2, -2, false, true,
 'Japan is breaking the postwar settlement and reviving militarism behind a pacifist facade',
 'Japan bricht die Nachkriegsordnung und belebt hinter einer pazifistischen Fassade den Militarismus',
 'Chinese state counter-framing',
 'Chinesische staatliche Gegen-Rahmung',
 ARRAY['ASIA-CHINA','EUROPE-RUSSIA'],
 ARRAY['Global Times','CGTN','China Daily','People''s Daily','Xinhua','Xinhuanet Deutsch','RT','TASS','TASS (EN)','Sputnik','Press TV'],
 ARRAY['militaris','neo-militaris','remilitariz','interference','internal affairs','erroneous remarks','reflect','correct','postwar order','historical','aggression','rights protection','in accordance with law','vigilance','Militarismus','Einmischung'],
 'The Chinese state counter-framing binds every strand of the theater into one account: a Japan that never atoned for its war of aggression is now hollowing out its pacifist constitution, arming for strike, and asserting a right to intervene over Taiwan that it does not possess. On this reading the prime minister''s Taiwan remarks are the root cause of the rupture, export licensing and coast guard patrols are lawful acts within Chinese jurisdiction rather than retaliation, and the historical record -- Yasukuni, Nanjing, the comfort women, looted relics -- is not a separate grievance but the evidence that the present drift is a return rather than a departure.',
 'Die chinesische staatliche Gegen-Rahmung verbindet alle Stränge des Theaters zu einer Darstellung: Ein Japan, das seinen Angriffskrieg nie gesühnt habe, höhle nun seine Friedensverfassung aus, rüste zum Erstschlag und beanspruche ein Interventionsrecht in der Taiwan-Frage, das ihm nicht zustehe. Die Taiwan-Äußerungen der Regierungschefin gelten als Ursache des Bruchs, Exportlizenzen und Küstenwachpatrouillen als rechtmäßige Handlungen in chinesischer Zuständigkeit statt als Vergeltung, und die historische Bilanz -- Yasukuni, Nanking, die "Trostfrauen", geraubte Kulturgüter -- als Beleg dafür, dass die gegenwärtige Entwicklung eine Rückkehr und kein Aufbruch ist.')

ON CONFLICT (id) DO UPDATE
   SET fn_id = EXCLUDED.fn_id, display_order = EXCLUDED.display_order, stance = EXCLUDED.stance,
       framing_required = EXCLUDED.framing_required, is_active = EXCLUDED.is_active,
       name_en = EXCLUDED.name_en, name_de = EXCLUDED.name_de,
       stance_label_en = EXCLUDED.stance_label_en, stance_label_de = EXCLUDED.stance_label_de,
       actor_centroids = EXCLUDED.actor_centroids, publishers = EXCLUDED.publishers,
       framing_keywords = EXCLUDED.framing_keywords,
       claim_en = EXCLUDED.claim_en, claim_de = EXCLUDED.claim_de,
       updated_at = now();

COMMIT;
