-- Arctic theater narrative layer (§5 of FN_THEATER_BUILD_SPEC).
-- Authors narratives_v2 for the 4 atomics of arctic_theater:
--   greenland_control, arctic_military_presence,
--   arctic_resources_competition, arctic_shipping_routes.
--
-- Design notes:
--  * greenland_control is a 4-stance set. The pro-Kremlin/Beijing narrative
--    (greenland_western_hypocrisy) is NOT on the "should the US take Greenland"
--    axis -- it is rift-exploitation on the WESTERN-COHESION axis (US-imperialism
--    critique + EU-hypocrisy schadenfreude + Russia-threat-pretext denial). It is
--    publisher-disjoint (RT/TASS/CGTN/GT) so framing_required=false routes it
--    correctly. The two Western-camp narratives (sovereignty-defense vs
--    Greenlandic self-determination) SHARE Western/Nordic publishers, so both are
--    framing_required=true with disjoint framing keywords.
--  * arctic_resources_competition: the environmental-critic narrative is an
--    own-goal (the pro-development camp's own green critics) -> framing_required=true.
-- Idempotent: ON CONFLICT (id) DO NOTHING.
SET client_encoding TO 'UTF8';

INSERT INTO narratives_v2
  (id, name_en, name_de, claim_en, claim_de, actor_centroids, framing_keywords,
   is_active, publishers, fn_id, display_order, stance_label_en, stance_label_de,
   stance, framing_required)
VALUES

-- ============ greenland_control ============
(
  'greenland_us_strategic_claim',
  'US control of Greenland is a strategic and national-security necessity',
  'Die US-Kontrolle über Grönland ist eine strategische und sicherheitspolitische Notwendigkeit',
  'US-manifest-destiny framing (Trump-aligned American press) holds that acquiring or controlling Greenland is a core national-security interest -- for Arctic bases, rare-earth minerals and sea lanes -- justified by Russian and Chinese encroachment, and that Washington should secure it "one way or the other". Genuine advocacy is thin relative to overall coverage. Vocabulary: core national security, strategic necessity, acquire Greenland, Arctic security, deal on the table.',
  'Die Manifest-Destiny-Rahmung (Trump-nahe US-Presse) sieht die Übernahme oder Kontrolle Grönlands als zentrales nationales Sicherheitsinteresse -- für arktische Stützpunkte, Seltene Erden und Seewege -- gerechtfertigt durch russisches und chinesisches Vordringen.',
  ARRAY['AMERICAS-USA'],
  ARRAY['core national security','national security interest','strategic necessity','acquire Greenland','buy Greenland','get Greenland','take Greenland','one way or the other','won''t rule out','will not rule out','deal on the table','Arctic security','American Greenland','national sicherheit','Grönland kaufen','Grönland erwerben'],
  true,
  ARRAY['Fox News','New York Post','Washington Examiner','Breitbart','The National Interest','Newsmax'],
  'greenland_control', 1,
  'US strategic claim (manifest destiny)',
  'US-Machtanspruch (Manifest Destiny)',
  2, true
),
(
  'greenland_sovereignty_defense',
  'Coercion over Greenland is unacceptable; Danish/European sovereignty must be defended',
  'Zwang gegen Grönland ist inakzeptabel; die dänische/europäische Souveränität muss verteidigt werden',
  'Sovereignty-defense framing (Western mainstream) treats US pressure on Greenland as an unacceptable coercion of an ally, a violation of territorial integrity and international law, and a test of European unity -- met with condemnation, protests, counter-tariffs and troop deployments. It defends Denmark''s and the EU''s position against Washington. Vocabulary: hands off, not for sale, sovereignty, coercion, condemn, retaliate, allies, international law.',
  'Die Souveränitäts-Rahmung (westlicher Mainstream) sieht den US-Druck auf Grönland als inakzeptablen Zwang gegen einen Verbündeten, als Verletzung der territorialen Integrität und des Völkerrechts und als Test der europäischen Einigkeit -- beantwortet mit Verurteilung, Protesten und Gegenzöllen.',
  ARRAY['NON-STATE-EU','EUROPE-NORDIC','EUROPE-GERMANY','EUROPE-FRANCE','AMERICAS-USA','AMERICAS-CANADA'],
  ARRAY['hands off','not for sale','sovereignty','territorial integrity','coercion','coerce','condemn','pushback','unacceptable','retaliate','counter-tariff','allies','international law','defend Greenland','rally','protest','red line','Souveränität','unverkäuflich','Hände weg','Völkerrecht','Vergeltung','Verbündete','inakzeptabel'],
  true,
  ARRAY['Reuters','BBC World','Financial Times','Associated Press','The Guardian','Deutsche Welle','Euronews','France 24 (EN)','Wall Street Journal','Washington Post','New York Times','ABC News','NPR','El País','Le Monde','ANSA','EurActiv','Politico','Der Spiegel','Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','CNN'],
  'greenland_control', 2,
  'European/Danish sovereignty defense',
  'Verteidigung europäischer/dänischer Souveränität',
  -1, true
),
(
  'greenland_self_determination',
  'Greenland''s future is for Greenlanders to decide -- not Washington or Copenhagen',
  'Über Grönlands Zukunft entscheiden die Grönländer -- nicht Washington oder Kopenhagen',
  'Self-determination framing (Greenlandic/Nordic voices) centres Greenland''s own agency: the island is not for sale, its people decide their future, and the crisis accelerates the independence debate vis-à-vis both Denmark and the United States. Distinct from EU sovereignty-defense, which speaks for Denmark/Brussels. Vocabulary: self-determination, Greenlanders decide, our future, not for sale, independence, Inuit, referendum.',
  'Die Selbstbestimmungs-Rahmung (grönländische/nordische Stimmen) stellt Grönlands eigene Handlungsmacht in den Mittelpunkt: die Insel ist nicht verkäuflich, ihr Volk entscheidet über seine Zukunft, und die Krise beschleunigt die Unabhängigkeitsdebatte gegenüber Dänemark und den USA.',
  ARRAY['EUROPE-GREENLAND','EUROPE-NORDIC'],
  ARRAY['self-determination','Greenlanders decide','our future','our country','right to decide','independence','Inuit','referendum','Naleraq','Egede','decide our','Selbstbestimmung','Unabhängigkeit','Grönländer'],
  true,
  ARRAY['Reuters','BBC World','Deutsche Welle','France 24 (EN)','Euronews','Associated Press','The Guardian','ERR News','LRT English','Anadolu Agency','Al Jazeera'],
  'greenland_control', 3,
  'Greenlandic self-determination',
  'Grönländische Selbstbestimmung',
  0, true
),
(
  'greenland_western_hypocrisy',
  'US imperialism over Greenland exposes Western hypocrisy and disunity',
  'Der US-Imperialismus um Grönland entlarvt westliche Heuchelei und Uneinigkeit',
  'Rift-exploitation framing (Russian state press + Chinese state media) frames the episode not as support for a US takeover but as proof of Western hypocrisy and imperialism: Washington behaves as a 21st-century coloniser toward an ally, the "Russian/Chinese threat" to Greenland is a manufactured pretext (which even Western officials deny), and the transatlantic rift it opens is amplified with schadenfreude. It is adversarial to the US and to Western cohesion, NOT an endorsement of annexation. Vocabulary: imperialism, land grab, double standard, manufactured threat, northern outpost, ups ante, colonialism.',
  'Die Riss-Ausnutzungs-Rahmung (russische und chinesische Staatsmedien) deutet die Episode nicht als Zustimmung zu einer US-Übernahme, sondern als Beweis westlicher Heuchelei und Imperialismus: Washington verhält sich wie ein Kolonialherr des 21. Jahrhunderts, die "russisch-chinesische Bedrohung" Grönlands sei ein Vorwand, und der transatlantische Riss wird mit Schadenfreude verstärkt. Gegnerisch zu den USA und zur westlichen Geschlossenheit -- keine Zustimmung zur Annexion.',
  ARRAY['EUROPE-RUSSIA','ASIA-CHINA'],
  ARRAY['imperialism','imperialist','land grab','takeover','double standard','hypocrisy','pretext','manufactured threat','inflating','so-called threat','colonial','colonialism','northern outpost','ups ante','21st century','coloniser'],
  true,
  ARRAY['RT','TASS','TASS (EN)','tass.com','Sputnik','RIA Novosti','Lenta.ru','Gazeta.ru','Izvestia','Kommersant','BelTA','Press TV','CGTN','Global Times','China Daily','Xinhua'],
  'greenland_control', 4,
  'Anti-Western rift-exploitation',
  'Anti-westliche Riss-Ausnutzung',
  -2, false
),

-- ============ arctic_military_presence ============
(
  'arctic_nato_deterrence',
  'NATO must reinforce the Arctic to deter a growing Russian (and Chinese) threat',
  'Die NATO muss die Arktis verstärken, um eine wachsende russische (und chinesische) Bedrohung abzuschrecken',
  'Deterrence framing (Western/NATO/Nordic mainstream) holds that Russian rearmament in the High North and growing Sino-Russian Arctic cooperation require NATO reinforcement -- exercises, bases, icebreakers and readiness -- to defend allied territory and close a capability gap. Vocabulary: deter, defend the north, Russian threat, build-up, readiness, Arctic Sentry, Cold Response.',
  'Die Abschreckungs-Rahmung (westlicher/NATO/nordischer Mainstream) sieht die russische Aufrüstung im hohen Norden und die wachsende russisch-chinesische Arktis-Kooperation als Grund für eine NATO-Verstärkung -- Übungen, Stützpunkte, Eisbrecher und Einsatzbereitschaft.',
  ARRAY['NON-STATE-NATO','EUROPE-NORDIC','AMERICAS-USA','AMERICAS-CANADA','NON-STATE-EU'],
  ARRAY['deter','deterrence','defend the north','Russian threat','build-up','readiness','reinforce','vulnerability','capability gap','exercise','Arctic Sentry','Cold Response','high north','protect','Abschreckung','russische Bedrohung'],
  true,
  ARRAY['Reuters','BBC World','Financial Times','Associated Press','The Guardian','Deutsche Welle','Euronews','France 24 (EN)','Wall Street Journal','New York Times','Washington Post','NPR','Military Times','Defense News','ERR News','LRT English','Atlantic Council','Politico','Kyiv Post'],
  'arctic_military_presence', 1,
  'NATO Arctic deterrence necessary',
  'NATO-Abschreckung in der Arktis notwendig',
  1, false
),
(
  'arctic_nato_militarization',
  'NATO is militarising the Arctic and provoking a dangerous new confrontation',
  'Die NATO militarisiert die Arktis und provoziert eine gefährliche neue Konfrontation',
  'Militarisation framing (Russian + Chinese state press) reverses the causality: NATO expansion, exercises and basing are the destabilising provocation that turns a zone of low tension into an arena of bloc confrontation and an arms race, encircling Russia. Vocabulary: militarisation, provocation, encirclement, destabilise, arms race, bloc confrontation.',
  'Die Militarisierungs-Rahmung (russische und chinesische Staatspresse) kehrt die Kausalität um: NATO-Erweiterung, Übungen und Stützpunkte seien die destabilisierende Provokation, die eine Zone geringer Spannung in eine Arena der Blockkonfrontation und ein Wettrüsten verwandelt.',
  ARRAY['EUROPE-RUSSIA','ASIA-CHINA'],
  ARRAY['militariz','militarisation','provocation','encirclement','encircl','destabiliz','arms race','bloc confrontation','aggressive','escalat','Cold War','buildup','Militarisierung','Provokation','Einkreisung','Wettrüsten'],
  true,
  ARRAY['RT','TASS','TASS (EN)','Sputnik','RIA Novosti','Global Times','CGTN','China Daily','Xinhua','Press TV'],
  'arctic_military_presence', 2,
  'NATO militarising the Arctic',
  'NATO militarisiert die Arktis',
  -1, false
),

-- ============ arctic_resources_competition ============
(
  'arctic_resource_development',
  'Arctic energy and minerals are a legitimate sovereign development opportunity',
  'Arktische Energie und Rohstoffe sind eine legitime souveräne Entwicklungschance',
  'Development framing (Russian state + Western energy/business press) treats Arctic hydrocarbons and critical minerals as a legitimate, economically vital resource to be developed -- new discoveries, investment, production and jobs -- as retreating ice opens access. Vocabulary: discovery, reserves, investment, production, energy security, billion barrels.',
  'Die Entwicklungs-Rahmung (russische Staats- und westliche Wirtschaftspresse) sieht arktische Kohlenwasserstoffe und kritische Rohstoffe als legitime, wirtschaftlich wichtige Ressource -- neue Funde, Investitionen, Förderung und Arbeitsplätze -- während das zurückweichende Eis den Zugang öffnet.',
  ARRAY['EUROPE-RUSSIA','EUROPE-NORDIC','AMERICAS-USA','AMERICAS-CANADA','ASIA-CHINA'],
  ARRAY['discovery','reserves','investment','production','energy security','billion barrels','boom','extract','output','field','jobs','develop'],
  true,
  ARRAY['Bloomberg','OilPrice','Wall Street Journal','Financial Times','TASS (EN)','RT','RIA Novosti','Globe and Mail','CNBC','Reuters'],
  'arctic_resources_competition', 1,
  'Sovereign resource development',
  'Souveräne Rohstoffentwicklung',
  1, false
),
(
  'arctic_drilling_environmental_alarm',
  'Drilling and mining in the fragile Arctic is environmentally reckless',
  'Bohrungen und Bergbau in der fragilen Arktis sind ökologisch rücksichtslos',
  'Environmental-critic framing (Western/green press -- the pro-development camp''s own critics) treats Arctic extraction as a reckless assault on a fragile, warming ecosystem: oil-spill risk, black carbon, biodiversity loss and accelerated melt. Shares publishers with development coverage, so framing keywords separate the stances. Vocabulary: fragile ecosystem, climate, pollution, black carbon, pristine, ban drilling, reckless.',
  'Die Umwelt-kritische Rahmung (westliche/grüne Presse -- die eigenen Kritiker des Entwicklungslagers) sieht die arktische Förderung als rücksichtslosen Angriff auf ein fragiles, sich erwärmendes Ökosystem: Ölpest-Risiko, Ruß, Biodiversitätsverlust und beschleunigte Schmelze.',
  ARRAY['NON-STATE-EU','EUROPE-NORDIC','AMERICAS-USA'],
  ARRAY['fragile','ecosystem','climate','environmental','pollution','black carbon','warming','melting','pristine','biodiversity','ban drilling','reckless','oil spill','protect the Arctic','fragiles Ökosystem','Umwelt','Klimaschutz','Ölpest'],
  true,
  ARRAY['The Guardian','BBC World','Deutsche Welle','Euronews','France 24 (EN)','New York Times','El País','Le Monde','The Independent','Reuters'],
  'arctic_resources_competition', 2,
  'Environmental alarm at Arctic extraction',
  'Umweltalarm über arktische Förderung',
  -1, true
),

-- ============ arctic_shipping_routes ============
(
  'arctic_route_opportunity',
  'Melting ice opens Arctic sea routes as a shared economic opportunity',
  'Das schmelzende Eis öffnet arktische Seewege als gemeinsame wirtschaftliche Chance',
  'Opportunity framing (Russian + Chinese + commercial press) presents the Northern Sea Route, Northwest Passage and Polar Silk Road as shorter, developable trade corridors and a legitimate economic prospect, with icebreaker fleets and Arctic ports as investment. Vocabulary: shorter route, trade route, transit, Northern Sea Route, Polar Silk Road, cargo, icebreaker fleet.',
  'Die Chancen-Rahmung (russische, chinesische und kommerzielle Presse) präsentiert die Nordostpassage, die Nordwestpassage und die polare Seidenstraße als kürzere, entwickelbare Handelskorridore und legitime Wirtschaftsperspektive -- mit Eisbrecherflotten und arktischen Häfen als Investition.',
  ARRAY['EUROPE-RUSSIA','ASIA-CHINA','EUROPE-NORDIC'],
  ARRAY['shorter route','trade route','transit','opportunity','cargo','shipping boom','Polar Silk Road','develop','commercial','icebreaker fleet','Seidenstraße','Handelsroute'],
  true,
  ARRAY['TASS (EN)','RT','RIA Novosti','CGTN','Global Times','China Daily','Xinhua','Bloomberg','OilPrice'],
  'arctic_shipping_routes', 1,
  'Arctic routes as economic opportunity',
  'Arktische Routen als wirtschaftliche Chance',
  1, false
),
(
  'arctic_route_strategic_threat',
  'Russian and Chinese control of Arctic routes is a strategic threat',
  'Die russische und chinesische Kontrolle arktischer Routen ist eine strategische Bedrohung',
  'Strategic-threat framing (Western security press) treats Russian dominance of the Northern Sea Route and China''s Polar Silk Road ambitions as a chokepoint risk requiring monitoring, freedom-of-navigation assertion and sanctions -- including the "shadow fleet" and dual-use shipping. Vocabulary: control, chokepoint, dominance, Chinese encroachment, dual-use, shadow fleet, freedom of navigation.',
  'Die Bedrohungs-Rahmung (westliche Sicherheitspresse) sieht die russische Dominanz über die Nordostpassage und Chinas Ambitionen der polaren Seidenstraße als Nadelöhr-Risiko, das Überwachung, die Durchsetzung der Navigationsfreiheit und Sanktionen erfordert -- einschließlich der "Schattenflotte".',
  ARRAY['NON-STATE-NATO','AMERICAS-USA','EUROPE-NORDIC','NON-STATE-EU'],
  ARRAY['control','chokepoint','dominance','Russian control','Chinese encroachment','dual-use','shadow fleet','monitor','contest','freedom of navigation','strategic threat','militariz','sanctions','Bedrohung','Schattenflotte'],
  true,
  ARRAY['Reuters','BBC World','Financial Times','Wall Street Journal','New York Times','Military Times','Defense News','France 24 (EN)','Deutsche Welle','Euronews','Atlantic Council'],
  'arctic_shipping_routes', 2,
  'Russian/Chinese route control as threat',
  'Russische/chinesische Routenkontrolle als Bedrohung',
  -1, false
)

ON CONFLICT (id) DO NOTHING;
