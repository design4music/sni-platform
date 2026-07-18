-- Taiwan Strait theater: atomic + theater narratives (FN_THEATER_BUILD_SPEC §5 / §5.5)
--
-- Three design decisions worth recording:
--
-- 1. taiwan_us_security_commitment uses the THREE-STANCE own-goal model (§5). Western
--    mainstream is simultaneously pro-Taiwan and highly critical of Washington -- NYT
--    "Trump Uses Taiwan Arms Sales as Bargaining Chip With China, in a Risky Move" is
--    critical of the US, not pro-Beijing. A publisher-only model would misfile every
--    alarmed Western headline as "commitment firm". So us_commitment_firm (+1) and
--    us_commitment_doubted (-1) SHARE the Western coalition, both framing_required=true
--    with disjoint keywords; the Beijing/Moscow narrative (-2) keeps its own disjoint
--    coalition at framing_required=false.
--
-- 2. The other three atomics are plain pro/con: the publisher coalitions (Western vs
--    Chinese/Russian state) are genuinely disjoint and stance-predictive, so
--    framing_required stays false and keywords only rank samples.
--
-- 3. No rift-exploitation narrative is needed here. That pattern applies to INTRA-WESTERN
--    disputes, where Moscow/Beijing endorse neither side. In the Taiwan Strait, Beijing is
--    a principal, not a spectator, so its framing sits on the dispute's own axis.
--
-- Theater cards (§5.5): publisher-disjoint within each stance-sign bucket. The two
-- negatives (-2 Chinese/Russian, -1 Western) are publisher-disjoint so their uncapped
-- counts partition cleanly; the +2 Western card shares publishers with the -1 card but
-- opposite signs pull different-signed atomic titles, so no title double-counts. The -1
-- Western card exists specifically to give us_commitment_doubted (-1, Western publishers)
-- a home -- without it that narrative is homeless at theater level (Arctic lesson).

BEGIN;

-- Publisher coalitions, defined once and reused.
CREATE TEMP TABLE _blocs (name text PRIMARY KEY, pubs text[]) ON COMMIT DROP;

INSERT INTO _blocs VALUES
('western', ARRAY[
    'Reuters','Bloomberg','Nikkei Asia','Japan Times','Straits Times','Asahi Shimbun',
    'Wall Street Journal','Channel NewsAsia','NHK World','Associated Press','AFP',
    'Financial Times','Deutsche Welle','BBC World','CNN','New York Times','The Guardian',
    'France 24 (EN)','France 24','Euronews','The Telegraph','Der Spiegel',
    'Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','Der Standard','Die Presse',
    'Handelsblatt','Tagesschau','Kyodo News','Fox News','NPR','ABC News','Washington Post',
    'Politico','Defense News','Janes','The Economist','The Australian','Globe and Mail',
    'Al Jazeera','Al Arabiya','Anadolu Agency','TRT World','Jerusalem Post','Brookings',
    'Le Figaro','Le Monde','El País','El Mundo','Corriere della Sera','La Repubblica',
    'La Nación','Folha de S.Paulo','O Globo','O Estado de S. Paulo','KBS World',
    'Times of India','The Hindu','Indian Express','Philippine Daily Inquirer','Bangkok Post',
    'The Nation Thailand','VN Express','Dawn','Dhaka Tribune','New Straits Times',
    'LRT English','LRT','ERR News','The Independent','Daily Nation','The Verge','TechCrunch'
]),
('beijing_moscow', ARRAY[
    'Global Times','China Daily','China Daily - Global Edition','CGTN','news.cgtn.com',
    'newsus.cgtn.com','newsaf.cgtn.com','People''s Daily','People''s Daily Online','Xinhua',
    'Xinhuanet Deutsch','RT','rt.com','TASS','TASS (EN)','tass.com','tass.ru','Sputnik',
    'RIA Novosti','Lenta.ru','lenta.ru','Izvestia','Kommersant','kommersant.ru',
    'BelTA','BelTA – News','BelTA Russian','Press TV'
]);

INSERT INTO narratives_v2
 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de,
  actor_centroids, publishers, framing_keywords, framing_required, display_order, is_active,
  created_at, updated_at)
SELECT v.id, v.fn_id, v.stance, v.sl_en, v.sl_de, v.n_en, v.n_de, v.c_en, v.c_de,
       v.actors, b.pubs, v.fk, v.fr, v.ord, true, now(), now()
FROM (VALUES

-- ============================ taiwan_military_pressure ============================
('taiwan_coercion_deterrence', 'taiwan_military_pressure', 1::smallint,
 'Chinese coercion requiring deterrence',
 'Chinesischer Zwang, der Abschreckung erfordert',
 'Chinese military and coast guard pressure around Taiwan is coercion that must be deterred',
 'Der militärische und küstenwachliche Druck Chinas rund um Taiwan ist Zwang, der abgeschreckt werden muss',
 'Deterrence framing (Western, Japanese and regional mainstream) treats PLA sorties across the median line, coast guard "law enforcement" patrols east of the island, carrier transits and invasion-style drills as escalating coercion against a democracy -- a grey-zone campaign to normalise pressure and wear down Taiwan''s defences -- to be answered with readiness drills, allied Strait transits and deterrence. Vocabulary: incursion, provocative, pressure, grey zone, new normal, readiness, deterrence, squeeze.',
 'Die Abschreckungs-Rahmung (westlicher, japanischer und regionaler Mainstream) deutet Einsätze der Volksbefreiungsarmee über die Mittellinie, Küstenwach-"Rechtsdurchsetzungs"-Patrouillen östlich der Insel, Trägerdurchfahrten und invasionsähnliche Manöver als eskalierenden Zwang gegen eine Demokratie -- eine Grauzonen-Kampagne, die Druck normalisieren und Taiwans Verteidigung zermürben soll -- der mit Bereitschaftsübungen, alliierten Durchfahrten und Abschreckung zu begegnen ist.',
 ARRAY['ASIA-TAIWAN','AMERICAS-USA','ASIA-JAPAN'], 'western',
 ARRAY['incursion','provocative','provocation','pressure','grey zone','gray zone','new normal',
       'readiness','deterrence','squeeze','threat','coercion','intimidation','alert','noose',
       'Abschreckung','Provokation','Druck','Bedrohung','Einschüchterung','Grauzone'],
 false, 1),

('pla_sovereignty_enforcement', 'taiwan_military_pressure', -1::smallint,
 'Lawful sovereignty enforcement',
 'Rechtmäßige Durchsetzung der Souveränität',
 'Military and coast guard activity around Taiwan is routine, lawful enforcement of Chinese sovereignty',
 'Militär- und Küstenwachaktivitäten rund um Taiwan sind routinemäßige, rechtmäßige Durchsetzung chinesischer Souveränität',
 'Sovereignty-enforcement framing (Chinese and Russian state media) presents patrols and drills as routine law enforcement and legitimate defence of territorial integrity in China''s own waters, triggered by "Taiwan independence" provocation and foreign meddling, with responsibility for escalation placed on Taipei and Washington. Vocabulary: routine, law enforcement, legitimate, territorial integrity, provocation, external forces, meddling, red line, countermeasure.',
 'Die Souveränitäts-Rahmung (chinesische und russische Staatsmedien) stellt Patrouillen und Manöver als routinemäßige Rechtsdurchsetzung und legitime Verteidigung der territorialen Integrität in eigenen Gewässern dar, ausgelöst durch "Taiwan-Unabhängigkeits"-Provokation und ausländische Einmischung; die Verantwortung für die Eskalation wird Taipeh und Washington zugewiesen.',
 ARRAY['ASIA-CHINA'], 'beijing_moscow',
 ARRAY['routine','law enforcement','legitimate','territorial integrity','provocation',
       'external forces','meddling','red line','countermeasure','resolutely','safeguard',
       'sovereignty','interfere','one-China principle'],
 false, 2),

-- ========================= taiwan_us_security_commitment =========================
('us_commitment_firm', 'taiwan_us_security_commitment', 1::smallint,
 'US commitment holding firm',
 'US-Zusage bleibt belastbar',
 'US arms supply and the security commitment to Taiwan are holding and being strengthened',
 'Die US-Waffenlieferungen und die Sicherheitszusage an Taiwan halten und werden verstärkt',
 'Commitment-firm framing (Western and regional mainstream) reports approvals, deliveries and record arms-sale volumes, cleared backlogs and official reaffirmations that policy is unchanged, alongside Taiwan''s own budget increases and asymmetric build-up, as evidence that deterrence is being reinforced. Shares its publisher coalition with the commitment-doubt narrative, so framing keywords are required to separate the two. Vocabulary: approve, deliver, strengthen, reaffirm, unwavering, no change, record.',
 'Die Rahmung einer belastbaren Zusage (westlicher und regionaler Mainstream) berichtet Genehmigungen, Lieferungen und Rekordvolumina bei Rüstungsverkäufen, abgearbeitete Rückstände und offizielle Bekräftigungen unveränderter Politik -- samt Taiwans eigener Budgeterhöhungen und asymmetrischem Aufbau -- als Beleg dafür, dass die Abschreckung gestärkt wird.',
 ARRAY['AMERICAS-USA','ASIA-TAIWAN'], 'western',
 ARRAY['approve','approves','approved','deliver','delivery','strengthen','boost','reaffirm',
       'unwavering','rock-solid','no change','record','clears','cleared','greenlight',
       'authorise','authorize','ramp up','continued support','genehmigt','bekräftigt',
       'verstärkt','unerschütterlich','Rekord','Zusage'],
 true, 1),

('us_commitment_doubted', 'taiwan_us_security_commitment', -1::smallint,
 'Commitment in doubt (Western alarm)',
 'Zweifel an der Zusage (westliche Alarmierung)',
 'Washington''s commitment is wavering and Taiwan risks being traded away',
 'Washingtons Zusage wankt und Taiwan droht zur Verhandlungsmasse zu werden',
 'Commitment-doubt framing (the same Western and regional mainstream, in critical register) treats Taiwan as exposed by an administration that calls arms sales a negotiating chip, withholds or reviews packages, declines to state a commitment, and bargains over the island in summitry with Beijing. This is the own-goal register in which the normally supportive coalition is itself the critic -- it is criticism of Washington, not support for Beijing. Vocabulary: bargaining chip, no commitment, under review, withheld, delay, abandon, sacrificed, doubts, hedge.',
 'Die Zweifel-Rahmung (derselbe westliche und regionale Mainstream, in kritischem Register) sieht Taiwan durch eine Regierung exponiert, die Waffenverkäufe als Verhandlungsmasse bezeichnet, Pakete zurückhält oder überprüft, eine Zusage verweigert und bei Gipfeln mit Peking über die Insel verhandelt. Es ist Kritik an Washington, nicht Zustimmung zu Peking.',
 ARRAY['AMERICAS-USA','ASIA-TAIWAN'], 'western',
 ARRAY['bargaining chip','negotiating chip','no commitment','made no commitment','under review',
       'withhold','withholding','withheld','delay','jeopardi','abandon','sacrificed','sell out',
       'sells out','doubt','anxieties','anxiety','risky','wavering','hedge','concession',
       'falls short','stalling','uncertainty','questions','Verhandlungsmasse','Faustpfand',
       'infrage','Zweifel','Verzögerung','im Stich','geopfert'],
 true, 2),

('taiwan_us_pawn', 'taiwan_us_security_commitment', -2::smallint,
 'Taiwan as a US pawn',
 'Taiwan als Schachfigur der USA',
 'US arms sales violate the one-China principle and use Taiwan as a pawn Washington will discard',
 'US-Waffenverkäufe verletzen das Ein-China-Prinzip und benutzen Taiwan als Schachfigur, die Washington fallen lassen wird',
 'Pawn framing (Chinese and Russian state media) holds that American arms sales breach the one-China principle and the joint communiqués, that Washington milks Taiwan as a "cash machine" and will abandon it when convenient, and that the governing party''s reliance on external forces is doomed. Vocabulary: pawn, chess piece, cash machine, abandoned, one-China principle, communiqué, interference, doomed, chopping board.',
 'Die Schachfiguren-Rahmung (chinesische und russische Staatsmedien) hält amerikanische Waffenverkäufe für einen Bruch des Ein-China-Prinzips und der gemeinsamen Kommuniqués, sieht Washington Taiwan als "Geldautomat" ausnehmen und bei Gelegenheit fallen lassen, und erklärt das Vertrauen der Regierungspartei auf äußere Kräfte für zum Scheitern verurteilt.',
 ARRAY['ASIA-CHINA'], 'beijing_moscow',
 ARRAY['pawn','chess piece','cash machine','abandon','one-China principle','communiqué',
       'communique','interference','interfere','doomed','chopping board','sell out','hollow',
       'external forces','Taiwan region','arms sales'],
 false, 3),

-- =========================== taiwan_political_warfare ===========================
('united_front_subversion', 'taiwan_political_warfare', 1::smallint,
 'United front work as subversion',
 'Einheitsfrontarbeit als Unterwanderung',
 'Beijing''s united front work, infiltration and disinformation are subverting Taiwan''s democracy',
 'Pekings Einheitsfrontarbeit, Unterwanderung und Desinformation untergraben Taiwans Demokratie',
 'Subversion framing (Western, Japanese and regional mainstream) treats Beijing''s cultivation of the opposition, economic inducements, espionage inside the military, and cognitive-warfare and disinformation campaigns as an attempt to hollow out Taiwan''s democracy from within and secure annexation without fighting. Vocabulary: united front, infiltration, espionage, disinformation, cognitive warfare, influence, subvert, meddling, penetration.',
 'Die Unterwanderungs-Rahmung (westlicher, japanischer und regionaler Mainstream) deutet Pekings Umwerben der Opposition, wirtschaftliche Anreize, Spionage im Militär sowie Kognitions- und Desinformationskampagnen als Versuch, Taiwans Demokratie von innen auszuhöhlen und die Annexion ohne Kampf zu erreichen.',
 ARRAY['ASIA-TAIWAN','ASIA-CHINA'], 'western',
 ARRAY['united front','infiltration','infiltrate','espionage','spy','disinformation',
       'cognitive warfare','influence operation','subvert','subversion','meddling','penetration',
       'interference','Einheitsfront','Spionage','Desinformation','Unterwanderung','Einflussnahme'],
 false, 1),

('cross_strait_exchange_goodwill', 'taiwan_political_warfare', -1::smallint,
 'Exchanges as goodwill; governing party obstructs',
 'Austausch als Wohlwollen; Regierungspartei blockiert',
 'Cross-strait exchanges and dialogue build peace, and the governing party obstructs them',
 'Der Austausch über die Meerenge und der Dialog schaffen Frieden, und die Regierungspartei blockiert sie',
 'Exchange framing (Chinese and Russian state media) presents opposition-party visits, the Straits Forum, economic incentives and people-to-people contact as goodwill toward "Taiwan compatriots" and the path to peaceful reunification, while casting the governing party as the obstacle -- hyping threats, restricting exchanges and serving external forces. Vocabulary: compatriot, exchange, goodwill, peaceful reunification, family, integration, obstruct, hype, preferential policies.',
 'Die Austausch-Rahmung (chinesische und russische Staatsmedien) stellt Besuche der Oppositionspartei, das Straits-Forum, wirtschaftliche Anreize und zwischenmenschliche Kontakte als Wohlwollen gegenüber den "taiwanischen Landsleuten" und als Weg zur friedlichen Wiedervereinigung dar, während die Regierungspartei als Hindernis gezeichnet wird.',
 ARRAY['ASIA-CHINA'], 'beijing_moscow',
 ARRAY['compatriot','exchange','goodwill','peaceful reunification','family','integration',
       'obstruct','hype','preferential','benefit','welcome','one family','reunification',
       'Landsleute','Wiedervereinigung'],
 false, 2),

-- ======================== taiwan_international_recognition ========================
('taiwan_international_space', 'taiwan_international_recognition', 1::smallint,
 'Taiwan''s international space',
 'Taiwans internationaler Handlungsraum',
 'Taiwan''s international participation is legitimate and Beijing''s campaign to isolate it is coercive',
 'Taiwans internationale Teilhabe ist legitim, und Pekings Kampagne zu seiner Isolierung ist Zwang',
 'International-space framing (Western, Japanese and regional mainstream) treats Beijing''s pressure on Taiwan''s remaining diplomatic allies, the blocking of its leaders'' transits and overflight clearances, and its exclusion from the World Health Assembly and ICAO as coercive isolation of a functioning democracy, and defends parliamentary visits and representative offices against retaliation. Vocabulary: isolate, pressure, coercion, block, deny, exclude, meaningful participation, international space, retaliation.',
 'Die Handlungsraum-Rahmung (westlicher, japanischer und regionaler Mainstream) deutet Pekings Druck auf Taiwans verbliebene diplomatische Partner, die Blockade von Transitreisen und Überflugrechten seiner Führung sowie den Ausschluss von der Weltgesundheitsversammlung und der ICAO als erzwungene Isolierung einer funktionierenden Demokratie.',
 ARRAY['ASIA-TAIWAN'], 'western',
 ARRAY['isolate','isolation','pressure','coercion','block','blocked','deny','denied','exclude',
       'exclusion','meaningful participation','international space','retaliation','bully',
       'intimidation','ausgeschlossen','Isolierung','Druck','Einschüchterung'],
 false, 1),

('one_china_consensus', 'taiwan_international_recognition', -1::smallint,
 'One-China principle as international consensus',
 'Ein-China-Prinzip als internationaler Konsens',
 'The one-China principle is settled international consensus and Taiwan''s diplomacy is doomed to fail',
 'Das Ein-China-Prinzip ist gefestigter internationaler Konsens, und Taiwans Diplomatie ist zum Scheitern verurteilt',
 'One-China framing (Chinese and Russian state media) holds that UN Resolution 2758 settled the island''s status, that the one-China principle commands near-universal recognition, and that "dollar diplomacy" and attempts to expand international space breach other states'' commitments and will collapse. Vocabulary: one-China principle, Resolution 2758, international consensus, Taiwan region, dollar diplomacy, doomed, internal affairs, red line.',
 'Die Ein-China-Rahmung (chinesische und russische Staatsmedien) hält den Status der Insel durch die UN-Resolution 2758 für geklärt, das Ein-China-Prinzip für nahezu universell anerkannt und "Dollar-Diplomatie" sowie Versuche zur Ausweitung des internationalen Handlungsraums für einen Bruch der Zusagen anderer Staaten.',
 ARRAY['ASIA-CHINA'], 'beijing_moscow',
 ARRAY['one-China principle','Resolution 2758','international consensus','Taiwan region',
       'dollar diplomacy','doomed','internal affairs','red line','universally recognized',
       'adhere','Ein-China','innere Angelegenheiten'],
 false, 2),

-- ============================= theater-level cards (§5.5) =============================
('taiwan_strait_western_consensus', 'taiwan_strait_theater', 2::smallint,
 'Western and regional security consensus',
 'Westlicher und regionaler Sicherheitskonsens',
 'Taiwan is a democracy under escalating Chinese coercion and its deterrence must be reinforced',
 'Taiwan ist eine Demokratie unter eskalierendem chinesischem Zwang, und seine Abschreckung muss gestärkt werden',
 'The Western and regional security consensus reads the Strait as a democracy under sustained coercion -- military and grey-zone pressure, united front subversion and diplomatic isolation -- whose deterrence, arms supply and international space must be reinforced. It spans Western, Japanese and regional mainstream outlets and is the frame against which the other two cards define themselves.',
 'Der westliche und regionale Sicherheitskonsens liest die Meerenge als Demokratie unter anhaltendem Zwang -- militärischer und Grauzonen-Druck, Unterwanderung durch die Einheitsfront und diplomatische Isolierung --, deren Abschreckung, Waffenversorgung und internationaler Handlungsraum gestärkt werden müssen.',
 ARRAY['ASIA-TAIWAN','AMERICAS-USA','ASIA-JAPAN'], 'western',
 ARRAY['coercion','deterrence','pressure','democracy','grey zone','incursion','isolate',
       'united front','Abschreckung','Zwang','Druck'],
 false, 1),

('taiwan_strait_beijing_counter', 'taiwan_strait_theater', -2::smallint,
 'Beijing and Moscow counter-framing',
 'Gegenrahmung Pekings und Moskaus',
 'Taiwan is Chinese territory and foreign interference, not Chinese action, is the provocation',
 'Taiwan ist chinesisches Territorium, und die Provokation ist die ausländische Einmischung, nicht Chinas Handeln',
 'The Chinese and Russian state counter-framing treats the island as Chinese territory whose status was settled by UN Resolution 2758: military patrols are routine law enforcement, exchanges are goodwill toward compatriots, and the destabilising force is American arms sales and foreign meddling in an internal affair. Responsibility for escalation is placed on Taipei and Washington throughout.',
 'Die chinesisch-russische Gegenrahmung behandelt die Insel als chinesisches Territorium, dessen Status durch die UN-Resolution 2758 geklärt sei: Militärpatrouillen seien routinemäßige Rechtsdurchsetzung, Austausch sei Wohlwollen gegenüber Landsleuten, und die destabilisierende Kraft seien amerikanische Waffenverkäufe und ausländische Einmischung in eine innere Angelegenheit.',
 ARRAY['ASIA-CHINA'], 'beijing_moscow',
 ARRAY['one-China principle','territorial integrity','internal affairs','external forces',
       'interference','routine','law enforcement','separatist','reunification','Resolution 2758',
       'red line','Ein-China','Einmischung'],
 false, 2),

('taiwan_strait_western_doubt', 'taiwan_strait_theater', -1::smallint,
 'Western doubt over US resolve',
 'Westliche Zweifel an der US-Entschlossenheit',
 'Taiwan''s protection is not assured -- Washington may bargain the island away and its defences fall short',
 'Taiwans Schutz ist nicht gesichert -- Washington könnte die Insel verhandeln, und ihre Verteidigung bleibt hinter dem Bedarf zurück',
 'The Western critical register turns the same supportive coalition into a critic: it reports an American administration calling arms sales a negotiating chip, reviewing or withholding packages and declining to state a commitment, alongside Taiwan''s own stalled defence budget and contested readiness. It is criticism of Washington and of Taipei''s preparedness -- not support for Beijing''s claim -- and it carries the theater''s Western-published negative coverage, which would otherwise have no card.',
 'Das westliche kritische Register macht dieselbe unterstützende Koalition zur Kritikerin: Es berichtet von einer amerikanischen Regierung, die Waffenverkäufe als Verhandlungsmasse bezeichnet, Pakete überprüft oder zurückhält und eine Zusage verweigert -- neben Taiwans blockiertem Verteidigungshaushalt und umstrittener Einsatzbereitschaft. Es ist Kritik an Washington und an Taipehs Vorbereitung, keine Zustimmung zu Pekings Anspruch.',
 ARRAY['AMERICAS-USA','ASIA-TAIWAN'], 'western',
 ARRAY['bargaining chip','negotiating chip','no commitment','under review','withhold','delay',
       'abandon','sacrificed','doubt','anxieties','falls short','stalling','wavering',
       'Verhandlungsmasse','Zweifel','infrage'],
 false, 3)

) AS v(id, fn_id, stance, sl_en, sl_de, n_en, n_de, c_en, c_de, actors, bloc, fk, fr, ord)
JOIN _blocs b ON b.name = v.bloc
ON CONFLICT (id) DO UPDATE
   SET fn_id = EXCLUDED.fn_id, stance = EXCLUDED.stance,
       stance_label_en = EXCLUDED.stance_label_en, stance_label_de = EXCLUDED.stance_label_de,
       name_en = EXCLUDED.name_en, name_de = EXCLUDED.name_de,
       claim_en = EXCLUDED.claim_en, claim_de = EXCLUDED.claim_de,
       actor_centroids = EXCLUDED.actor_centroids, publishers = EXCLUDED.publishers,
       framing_keywords = EXCLUDED.framing_keywords,
       framing_required = EXCLUDED.framing_required,
       display_order = EXCLUDED.display_order, is_active = true, updated_at = now();

COMMIT;
