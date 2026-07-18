-- Atomic narratives for australia_theater's 4 atomics (spec 5).
--
-- Coalition design, from measured publisher distributions:
--   * Chinese state bloc (Global Times / CGTN / news.cgtn.com / China Daily /
--     People's Daily / Xinhua) is well represented on every China-facing atomic
--     (69 titles in the AUS-CHINA dyad alone) and is DISJOINT from the Western
--     bloc, so publisher alone disambiguates stance -- framing_required=false.
--   * China is a PRINCIPAL PARTY here, not a bystander amplifying someone else's
--     split, so its coverage belongs on each dispute's own pro/con axis. No
--     rift-exploitation card (that caveat is for intra-Western disputes; cf. the
--     SCS build, where the same reasoning applied).
--
-- aukus_alliance_reliability is the exception and gets the 3-stance own-goal
-- model (spec 5): AUKUS coverage is 96% China-free and dominated by Australian
-- outlets that are its harshest critics ("Aukus is among Australia's worst
-- foreign policy decisions", "Labor's AUKUS mess", the crowd-funded inquiry).
-- A publisher-only model would file all of that as supportive. So the +2 and -1
-- cards share the Australian/Western coalition and BOTH set framing_required,
-- with disjoint keywords.
--
-- Framing keywords were checked against real titles for stance-ambiguity
-- (eu_cohesion lesson). Deliberately EXCLUDED from the -1 AUKUS list:
--   `opponents` -- appears in the SUPPORTIVE "Conroy hits out at AUKUS opponents"
--   `doubt`     -- appears in the SUPPORTIVE "urges Australia not to surrender to doubt"
--   `sink`      -- appears in the SUPPORTIVE "Why Labor won't sink AUKUS"
--   `cost`      -- "Marles points to savings" is supportive; bare cost is ambiguous
--
-- NOT modelled (volume too thin, revisit if it grows): a Pacific island-agency
-- stance. "Vanuatu warns Australia it will not be 'dictated to'", "Vanuatu
-- suggests Australia and China are 'undermining' it" and "Vanuatu takes swipe at
-- Australia" are only ~3 ABC titles -- real, but not the systemic both-camps
-- pattern that justifies framing_required overhead on a 28-event atomic.
SET client_encoding TO 'UTF8';

INSERT INTO narratives_v2
  (id, name_en, name_de, claim_en, claim_de, actor_centroids, framing_keywords,
   is_active, publishers, fn_id, display_order, stance_label_en, stance_label_de,
   stance, framing_required)
VALUES

-- ===================== pacific_island_contest =====================
(
  'pacific_western_partnership',
  'Pacific island states are choosing Australia and its partners as their security partner',
  'Pazifische Inselstaaten wählen Australien und seine Partner als Sicherheitspartner',
  'Australian and Western coverage frames the Pacific as a region where Australia is consolidating its position as security partner of choice: the Fiji mutual defence treaty, the Vanuatu pact barring foreign military bases, and the Solomon Islands review of its secret pact with Beijing are read as island states freely choosing transparent partnerships over Chinese basing and policing arrangements. Vocabulary: defence pact, mutual defence, counter China, security agreement, partner of choice, transparency.',
  'Die australische und westliche Berichterstattung stellt den Pazifik als Region dar, in der Australien seine Stellung als bevorzugter Sicherheitspartner festigt: der Verteidigungsvertrag mit Fidschi, der Pakt mit Vanuatu zum Verbot ausländischer Militärbasen und die Überprüfung des geheimen Pakts der Salomonen mit Peking gelten als freie Entscheidung der Inselstaaten für transparente Partnerschaften statt chinesischer Stützpunkte und Polizeiabkommen.',
  ARRAY['OCEANIA-AUSTRALIA','OCEANIA-MELANESIA','OCEANIA-POLYNESIA','OCEANIA-MICRONESIA','OCEANIA-PAPUANEWGUINEA'],
  ARRAY['defence pact','defense pact','mutual defence','mutual defense','security agreement','security pact','counter China','containment','partner of choice','transparency','foreign military base','ban','review','secretive','treaty','alliance'],
  true,
  ARRAY['ABC News','Australian Broadcasting Corporation','ABC Pacific','Sydney Morning Herald','The Sydney Morning Herald','SMH.com.au','The Australian','The Guardian','Sky News','News24','Reuters','Associated Press','BBC World','Bloomberg','Financial Times','Nikkei Asia','Straits Times','The Straits Times','Deutsche Welle','Euronews','France 24 (EN)','Wall Street Journal','New York Times','Channel NewsAsia','The Hindu','Times of India','Philippine Daily Inquirer','CSIS','Lowy Institute'],
  'pacific_island_contest', 1,
  'Australian and Western partnership framing',
  'Australische und westliche Partnerschafts-Rahmung',
  2, false
),
(
  'pacific_china_cooperation',
  'Chinese engagement in the Pacific is ordinary development cooperation that no third party should constrain',
  'Chinas Engagement im Pazifik ist gewöhnliche Entwicklungszusammenarbeit, die kein Dritter beschränken sollte',
  'Chinese state framing presents Beijing''s Pacific presence as normal, mutually agreed cooperation — medical teams, infrastructure and policing assistance requested by sovereign governments — that "should not target any third party or be used for geopolitical contest". Australian and Western reporting on Chinese pacts is cast as hype driven by an exclusionary Cold War mindset that denies island states their own choices. Vocabulary: cooperation, mutual benefit, third party, geopolitical contest, hype, exclusionary, Cold War mentality.',
  'Die chinesische staatliche Rahmung stellt Pekings Präsenz im Pazifik als normale, einvernehmliche Zusammenarbeit dar — medizinische Teams, Infrastruktur und Polizeihilfe auf Wunsch souveräner Regierungen —, die "kein Drittland ins Visier nehmen oder für geopolitischen Wettbewerb genutzt werden sollte". Australische und westliche Berichte über chinesische Pakte werden als Panikmache eines ausgrenzenden Kalten-Kriegs-Denkens dargestellt, das den Inselstaaten eigene Entscheidungen abspricht.',
  ARRAY['ASIA-CHINA','OCEANIA-MELANESIA','OCEANIA-POLYNESIA','OCEANIA-MICRONESIA'],
  ARRAY['cooperation','co-op','mutual benefit','third party','geopolitical contest','hype','exclusionary','Cold War','mentality','sovereign','development','assistance','win-win','合作','互利'],
  true,
  ARRAY['Global Times','CGTN','news.cgtn.com','China Daily','People''s Daily','Xinhua'],
  'pacific_island_contest', 2,
  'Chinese state cooperation framing',
  'Chinesische staatliche Kooperations-Rahmung',
  -2, false
),

-- ===================== australia_china_trade_leverage =====================
(
  'trade_derisking_necessity',
  'Concentrated dependence on the Chinese market is a strategic vulnerability Australia must reduce',
  'Die konzentrierte Abhängigkeit vom chinesischen Markt ist eine strategische Verwundbarkeit, die Australien verringern muss',
  'Australian and Western business coverage reads Beijing''s commercial levers as strategic risk: the 55% tariff triggering at the beef quota threshold, the state buyer restricting Fortescue and BHP iron ore cargoes during price talks, and Chinese stakes in rare-earth projects forced into divestment. The conclusion drawn is that market concentration must be reduced through diversification, investment screening and alternative supply chains. Vocabulary: quota, tariff, restrictions, state buyer, divest, screening, diversify, supply chain, vulnerability.',
  'Die australische und westliche Wirtschaftsberichterstattung deutet Pekings kommerzielle Hebel als strategisches Risiko: der 55-Prozent-Zoll bei Erreichen der Rindfleischquote, der staatliche Käufer, der während der Preisverhandlungen Eisenerzladungen von Fortescue und BHP beschränkt, sowie chinesische Anteile an Seltene-Erden-Projekten, die zum Verkauf gezwungen werden. Daraus wird gefolgert, dass die Marktkonzentration durch Diversifizierung, Investitionsprüfung und alternative Lieferketten verringert werden muss.',
  ARRAY['OCEANIA-AUSTRALIA','ASIA-CHINA'],
  ARRAY['quota','tariff','restriction','state buyer','divest','screening','diversify','supply chain','vulnerability','dependence','leverage','pricing dispute','forced sale','rare earth','critical mineral'],
  true,
  ARRAY['ABC News','Australian Broadcasting Corporation','Sydney Morning Herald','The Sydney Morning Herald','SMH.com.au','The Australian','The Guardian','Sky News','News24','Reuters','Associated Press','BBC World','Bloomberg','Financial Times','Nikkei Asia','Straits Times','The Straits Times','Deutsche Welle','Euronews','Wall Street Journal','New York Times','Mining.com','S&P Global','OilPrice','CNBC','Channel NewsAsia'],
  'australia_china_trade_leverage', 1,
  'Australian and Western de-risking framing',
  'Australische und westliche Risikominderungs-Rahmung',
  2, false
),
(
  'trade_mutual_benefit',
  'Australia-China trade is complementary and growing, and quota mechanics are routine rather than coercive',
  'Der Handel zwischen Australien und China ist komplementär und wächst; Quotenmechanismen sind Routine, nicht Zwang',
  'Chinese state framing presents the commercial relationship as large, complementary and expanding — record Chinese vehicle sales in Australia, solar and energy-transition cooperation, growing beef and agricultural exports, rising Australian public opinion of China. Tariff steps are presented as the routine operation of agreed quota thresholds administered by MOFCOM rather than pressure, with strategic-rivalry politics cast as the thing putting the relationship at risk. Vocabulary: mutual benefit, complementary, growing market, quota threshold, cooperation, win-win.',
  'Die chinesische staatliche Rahmung stellt die Handelsbeziehung als groß, komplementär und wachsend dar — Rekordabsatz chinesischer Fahrzeuge in Australien, Zusammenarbeit bei Solar- und Energiewende, steigende Rindfleisch- und Agrarexporte, verbesserte australische Meinung über China. Zollschritte werden als routinemäßige Anwendung vereinbarter Quotenschwellen durch das Handelsministerium dargestellt, nicht als Druck; die Politik der strategischen Rivalität gilt als das eigentliche Risiko für die Beziehung.',
  ARRAY['ASIA-CHINA','OCEANIA-AUSTRALIA'],
  ARRAY['mutual benefit','complementary','growing market','quota','threshold','cooperation','win-win','record','success','opportunity','互利','合作'],
  true,
  ARRAY['Global Times','CGTN','news.cgtn.com','China Daily','People''s Daily','Xinhua'],
  'australia_china_trade_leverage', 2,
  'Chinese state mutual-benefit framing',
  'Chinesische staatliche Rahmung des gegenseitigen Nutzens',
  -2, false
),

-- ===================== china_threat_assessment =====================
(
  'china_threat_substantiated',
  'Chinese espionage and military reach against Australia are real and growing',
  'Chinesische Spionage und militärische Reichweite gegenüber Australien sind real und wachsen',
  'Australian and allied coverage treats the threat assessment as evidence-based: ASIO sparring with Beijing over foreign interference, prosecutions of Chinese nationals for interference in Canberra, a jury finding an Australian expat acted as a Chinese spy asset, Five Eyes warnings that Chinese services recruit through fake job ads on professional networks, and Lowy Institute analysis that China''s capacity to strike targets in Australia is "real and growing" — underlined by a nuclear-capable ballistic missile test into the South Pacific. Vocabulary: espionage, foreign interference, spy, Five Eyes, strike capacity, ballistic, assessment.',
  'Die australische und verbündete Berichterstattung behandelt die Bedrohungsanalyse als faktenbasiert: der Streit des Inlandsgeheimdienstes ASIO mit Peking über ausländische Einflussnahme, Anklagen gegen chinesische Staatsbürger wegen Einflussnahme in Canberra, ein Geschworenenurteil, wonach ein australischer Auswanderer als chinesischer Spionagehelfer handelte, Warnungen der Five Eyes vor Anwerbung über gefälschte Stellenanzeigen sowie die Analyse des Lowy Institute, Chinas Fähigkeit zu Angriffen auf Ziele in Australien sei "real und wachsend" — unterstrichen durch einen atomwaffenfähigen Raketentest im Südpazifik.',
  ARRAY['OCEANIA-AUSTRALIA','ASIA-CHINA'],
  ARRAY['espionage','foreign interference','spy','spies','Five Eyes','strike capacity','ballistic','missile','assessment','warns','charged','recruit','real and growing'],
  true,
  ARRAY['ABC News','Australian Broadcasting Corporation','Sydney Morning Herald','The Sydney Morning Herald','SMH.com.au','The Australian','The Guardian','Sky News','News24','Reuters','Associated Press','BBC World','Bloomberg','Financial Times','Nikkei Asia','Straits Times','The Straits Times','Deutsche Welle','Euronews','Wall Street Journal','New York Times','Jerusalem Post','Channel NewsAsia','Janes','Defense News','CSIS','Lowy Institute'],
  'china_threat_assessment', 1,
  'Australian and allied threat-assessment framing',
  'Australische und verbündete Bedrohungsanalyse-Rahmung',
  2, false
),
(
  'china_threat_fabricated',
  'The "China threat" is a fabricated narrative used to justify Australian alignment against Beijing',
  'Die "China-Bedrohung" ist ein konstruiertes Narrativ zur Rechtfertigung der australischen Ausrichtung gegen Peking',
  'Chinese state framing rejects the assessments as manufactured: the Five Eyes espionage warning is called a "crafted rhetorical trap" and "highly ironic" given the alliance''s own surveillance record, and Australian think-tank claims of a Chinese military threat are called a grave strategic miscalculation. The argument is that the threat narrative is hype that serves alignment politics and damages a functioning relationship. Vocabulary: fabricated, hype, rhetorical trap, ironic, miscalculation, smear, Cold War mentality.',
  'Die chinesische staatliche Rahmung weist die Einschätzungen als konstruiert zurück: die Five-Eyes-Warnung vor Spionage wird als "rhetorische Falle" und angesichts der eigenen Überwachungspraxis des Bündnisses als "höchst ironisch" bezeichnet, und Behauptungen australischer Denkfabriken über eine chinesische Militärbedrohung gelten als schwerer strategischer Fehlschluss. Das Narrativ der Bedrohung sei Panikmache, die der Bündnispolitik diene und eine funktionierende Beziehung beschädige.',
  ARRAY['ASIA-CHINA','OCEANIA-AUSTRALIA'],
  ARRAY['fabricated','hype','rhetorical trap','ironic','miscalculation','smear','Cold War','mentality','refutes','rejects','slams','so-called','alleged','炒作'],
  true,
  ARRAY['Global Times','CGTN','news.cgtn.com','China Daily','People''s Daily','Xinhua'],
  'china_threat_assessment', 2,
  'Chinese state rebuttal framing',
  'Chinesische staatliche Gegendarstellungs-Rahmung',
  -2, false
),

-- ===================== aukus_alliance_reliability (3-stance own-goal) =====================
(
  'aukus_strategic_necessity',
  'AUKUS is essential to Australian deterrence and is progressing',
  'AUKUS ist für die australische Abschreckung unerlässlich und kommt voran',
  'The supportive Australian framing holds that the submarine pact remains the cornerstone of Australian deterrence and is delivering: a $2.7bn pledge to accelerate the shipyard, the US Navy standing up Naval Support Activity Stirling in Western Australia, AUKUS partners advancing SSN and underwater-drone programmes, savings identified in the revised arrangement, and senior figures publicly backing the plan. Vocabulary: backs, advance, milestone, pledge, accelerate, savings, deterrence, cornerstone, sovereign capability.',
  'Die unterstützende australische Rahmung sieht den U-Boot-Pakt weiterhin als Eckpfeiler der australischen Abschreckung, der Ergebnisse liefert: eine Zusage von 2,7 Milliarden zur Beschleunigung der Werft, die Einrichtung der Naval Support Activity Stirling durch die US-Marine in Westaustralien, Fortschritte der AUKUS-Partner bei SSN- und Unterwasserdrohnen-Programmen, Einsparungen in der überarbeiteten Vereinbarung sowie führende Politiker, die sich öffentlich hinter den Plan stellen.',
  ARRAY['OCEANIA-AUSTRALIA','AMERICAS-USA','EUROPE-UK'],
  ARRAY['backs','back the','advance','advancing','milestone','pledge','pledges','accelerate','speed up','savings','deterrence','cornerstone','sovereign capability','strengthens','delivers','on track','progress','commitment','won''t sink','hits out at'],
  true,
  ARRAY['ABC News','Australian Broadcasting Corporation','Sydney Morning Herald','The Sydney Morning Herald','SMH.com.au','The Australian','The Guardian','Sky News','News24','Reuters','Associated Press','BBC World','Bloomberg','Financial Times','Nikkei Asia','Straits Times','The Straits Times','Deutsche Welle','Euronews','France 24','France 24 (EN)','Wall Street Journal','New York Times','Janes','Defense News','War on the Rocks','Chatham House','Anadolu Agency','Times of India','Express Tribune','Bangkok Post','The Star','CSIS','Lowy Institute'],
  'aukus_alliance_reliability', 1,
  'Australian supportive framing',
  'Australische unterstützende Rahmung',
  2, true
),
(
  'aukus_capability_doubt',
  'AUKUS is delivering less than promised and binds Australia to an unreliable partner',
  'AUKUS liefert weniger als versprochen und bindet Australien an einen unzuverlässigen Partner',
  'The critical Australian framing — carried by the same mainstream outlets — holds that the pact has been downgraded and politically strained: Australia will receive three second-hand submarines instead of new Virginia-class boats, a capability gap opens as the Collins-class fleet is downsized and enters a "high-risk" life extension, an inquiry has been warned of nuclear-disaster risk, an ex-minister crowd-funded his own inquiry, a former foreign minister called it among Australia''s worst foreign-policy decisions, and Labor is publicly split. Vocabulary: second-hand, used, downgrade, scrap, shake-up, mess, division, inquiry, risk, gap, delay, chaos, worst.',
  'Die kritische australische Rahmung — getragen von denselben Leitmedien — sieht den Pakt als herabgestuft und politisch belastet: Australien erhält drei gebrauchte U-Boote statt neuer Virginia-Klasse-Boote, eine Fähigkeitslücke entsteht, während die Collins-Klasse verkleinert wird und in eine "hochriskante" Laufzeitverlängerung geht, eine Untersuchung wurde vor nuklearem Katastrophenrisiko gewarnt, ein Ex-Minister finanzierte seine eigene Untersuchung per Crowdfunding, ein früherer Außenminister nannte ihn eine der schlechtesten außenpolitischen Entscheidungen Australiens, und Labor ist offen gespalten.',
  ARRAY['OCEANIA-AUSTRALIA','AMERICAS-USA','EUROPE-UK'],
  ARRAY['second-hand','secondhand','used nuclear','only three','downgrade','downgrades','scraps','shake-up','mess','division','divided','want out','inquiry','risk','high-risk','gap','delay','blowout','chaos','worst','spats','explaining','stood up','quit','fears','frog in a sock','sinking feeling','heroic','crowd-funded'],
  true,
  ARRAY['ABC News','Australian Broadcasting Corporation','Sydney Morning Herald','The Sydney Morning Herald','SMH.com.au','The Australian','The Guardian','Sky News','News24','Reuters','Associated Press','BBC World','Bloomberg','Financial Times','Nikkei Asia','Straits Times','The Straits Times','Deutsche Welle','Euronews','France 24','France 24 (EN)','Wall Street Journal','New York Times','Janes','Defense News','War on the Rocks','Chatham House','Anadolu Agency','Times of India','Express Tribune','Bangkok Post','The Star','CSIS','Lowy Institute'],
  'aukus_alliance_reliability', 2,
  'Australian critical framing',
  'Australische kritische Rahmung',
  -1, true
),
(
  'aukus_bloc_confrontation',
  'AUKUS is bloc confrontation that spreads nuclear submarine technology and fuels an arms race',
  'AUKUS ist Blockkonfrontation, die Nuklear-U-Boot-Technologie verbreitet und ein Wettrüsten anheizt',
  'Chinese and Russian state framing treats the pact as a Cold War bloc project: an Anglosphere grouping that transfers naval nuclear propulsion to a non-nuclear-weapon state, strains the non-proliferation regime, and drives regional militarisation under the banner of deterrence. US basing steps in Western Australia are reported as evidence of the build-up rather than as reassurance. Vocabulary: bloc confrontation, Cold War mentality, arms race, proliferation, militarisation, Anglo-Saxon.',
  'Die chinesische und russische staatliche Rahmung behandelt den Pakt als Blockprojekt des Kalten Krieges: eine angelsächsische Gruppierung, die nukleare Marineantriebstechnik an einen Nichtkernwaffenstaat weitergibt, das Nichtverbreitungsregime belastet und die Militarisierung der Region unter dem Vorwand der Abschreckung vorantreibt. US-Stützpunktschritte in Westaustralien werden als Beleg für den Aufbau dargestellt, nicht als Rückversicherung.',
  ARRAY['ASIA-CHINA','EUROPE-RUSSIA','OCEANIA-AUSTRALIA'],
  ARRAY['bloc confrontation','Cold War','mentality','arms race','proliferation','militarisation','militarization','Anglo-Saxon','hegemony','provocation'],
  true,
  ARRAY['Global Times','CGTN','news.cgtn.com','China Daily','People''s Daily','Xinhua','TASS','TASS (EN)','tass.com','RT'],
  'aukus_alliance_reliability', 3,
  'Chinese and Russian state framing',
  'Chinesische und russische staatliche Rahmung',
  -2, false
)
ON CONFLICT (id) DO NOTHING;
