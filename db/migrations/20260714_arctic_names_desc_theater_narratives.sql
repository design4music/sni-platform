-- (A) Fill friction_nodes.name_de + description_en/_de for arctic_theater and
--     its 4 atomics (were null).
-- (B) Add 3 theater-level narratives_v2 for arctic_theater so the theater page
--     renders narrative cards (like ukraine_war_theater). Theater cards carry no
--     bundle of their own -- their sample headlines + counts roll up from the
--     member atomics' title_narratives, matched by stance-sign + publisher
--     (see THEATER_ROLLUP_SQL in apps/frontend/lib/friction-nodes.ts). The two
--     negative cards are publisher-DISJOINT (Russian/Chinese vs Western/green)
--     so their counts don't collide; the positive card takes the +sign atomics.
SET client_encoding TO 'UTF8';

-- ========================= (A) names + descriptions =========================
UPDATE friction_nodes SET
  name_de = 'Strategischer Wettbewerb in der Arktis',
  description_en = 'The contest over the Arctic as retreating sea ice opens once-inaccessible waters, seabed and sea lanes to competition among the eight Arctic states and China. Four axes run through it: the militarization of the High North and NATO''s northern expansion, the race for Arctic hydrocarbons and critical minerals, control of the emerging shipping routes, and the confrontation over Greenland that has strained transatlantic relations. Coverage is sharply divided — Western outlets frame Russian and Chinese activity as encroachment requiring deterrence, while Moscow and Beijing frame NATO''s build-up and the US Greenland push as the destabilizing provocation.',
  description_de = 'Der Wettstreit um die Arktis, während das zurückweichende Meereis einst unzugängliche Gewässer, Meeresböden und Seewege dem Wettbewerb zwischen den acht Arktis-Staaten und China öffnet. Vier Achsen durchziehen ihn: die Militarisierung des hohen Nordens und die Nordausdehnung der NATO, das Rennen um arktische Kohlenwasserstoffe und kritische Rohstoffe, die Kontrolle über die entstehenden Schifffahrtsrouten und die Konfrontation um Grönland, die die transatlantischen Beziehungen belastet hat. Die Berichterstattung ist tief gespalten — westliche Medien deuten russische und chinesische Aktivitäten als Vordringen, das Abschreckung erfordert, während Moskau und Peking den NATO-Aufbau und den US-Vorstoß in Grönland als destabilisierende Provokation darstellen.',
  updated_at = NOW()
WHERE id = 'arctic_theater';

UPDATE friction_nodes SET
  name_de = 'Strategische Kontrolle über Grönland und Arktis-Geopolitik',
  description_en = 'The confrontation over Greenland after Washington escalated a long-standing interest into an open push for control, backed by tariff threats against objecting European allies. The island''s Arctic bases, rare-earth minerals and opening sea lanes make it strategically pivotal, but the fight runs along a transatlantic axis — the United States against Denmark, the EU and NATO partners — with Greenlanders'' own claim to self-determination cutting across both. Framings range from a US strategic claim to a European defense of sovereignty to a pro-Kremlin reading that treats the episode as proof of Western imperialism and hypocrisy.',
  description_de = 'Die Konfrontation um Grönland, nachdem Washington ein langjähriges Interesse zu einem offenen Vorstoß zur Kontrolle eskaliert hat, untermauert durch Zolldrohungen gegen widersprechende europäische Verbündete. Die arktischen Stützpunkte der Insel, ihre Seltenen Erden und die sich öffnenden Seewege machen sie strategisch entscheidend, doch der Konflikt verläuft transatlantisch — die USA gegen Dänemark, die EU und NATO-Partner — mit dem grönländischen Anspruch auf Selbstbestimmung quer dazu. Die Deutungen reichen von einem strategischen US-Anspruch über eine europäische Verteidigung der Souveränität bis zu einer pro-Kreml-Lesart, die die Episode als Beweis westlicher Heuchelei und Imperialismus behandelt.',
  updated_at = NOW()
WHERE id = 'greenland_control';

UPDATE friction_nodes SET
  name_de = 'Militärischer Aufbau in der Arktis und NATO-Erweiterung',
  description_en = 'The re-militarization of the High North: Russia''s rebuilt bases and Northern Fleet along the Kola Peninsula and Barents Sea, and NATO''s answer — enlarged by Finnish and Swedish accession — through exercises, reinforcement and new basing, increasingly shadowed by Sino-Russian cooperation. The contest is over who is the provocateur. Western and Nordic coverage frames the build-up as necessary deterrence; Russian and Chinese state media cast NATO expansion as the destabilizing militarization of a once-low-tension zone.',
  description_de = 'Die erneute Militarisierung des hohen Nordens: Russlands wiederaufgebaute Stützpunkte und Nordflotte entlang der Kola-Halbinsel und der Barentssee sowie die Antwort der durch den finnischen und schwedischen Beitritt vergrößerten NATO durch Übungen, Verstärkung und neue Stützpunkte, zunehmend begleitet von russisch-chinesischer Kooperation. Umstritten ist, wer der Provokateur ist. Westliche und nordische Berichterstattung sieht den Aufbau als notwendige Abschreckung; russische und chinesische Staatsmedien stellen die NATO-Erweiterung als destabilisierende Militarisierung einer einst spannungsarmen Zone dar.',
  updated_at = NOW()
WHERE id = 'arctic_military_presence';

UPDATE friction_nodes SET
  name_de = 'Wettbewerb um arktische Rohstoffe und Klimazugang',
  description_en = 'The race for Arctic hydrocarbons and critical minerals as retreating ice opens access — Russia''s Yamal gas and Vostok oil, Norway''s Barents fields, Alaska''s Willow project, Greenland''s rare earths — contested by Arctic states and China. It sets a development camp that treats extraction as a legitimate sovereign right against its own critics, who warn that the same warming which opens the region — record-low sea ice, thawing permafrost, black carbon — is a climate emergency that drilling and mining only deepen.',
  description_de = 'Das Rennen um arktische Kohlenwasserstoffe und kritische Rohstoffe, während das zurückweichende Eis den Zugang öffnet — Russlands Jamal-Gas und Wostok-Öl, Norwegens Barents-Felder, Alaskas Willow-Projekt, Grönlands Seltene Erden — umkämpft von Arktis-Staaten und China. Es stellt ein Entwicklungslager, das die Förderung als legitimes souveränes Recht betrachtet, gegen dessen eigene Kritiker, die warnen, dass dieselbe Erwärmung, die die Region öffnet — Rekordtief beim Meereis, tauender Permafrost, Ruß — ein Klimanotstand ist, den Bohrungen und Bergbau nur vertiefen.',
  updated_at = NOW()
WHERE id = 'arctic_resources_competition';

UPDATE friction_nodes SET
  name_de = 'Arktische Schifffahrtsrouten und Passagenwettbewerb',
  description_en = 'The competition over the sea routes that Arctic warming is opening — the Northern Sea Route along Russia''s coast, the Northwest Passage through Canada''s archipelago, and a future transpolar route — which could cut weeks off Asia-Europe voyages. Russia is developing the Northern Sea Route with nuclear icebreakers and the port of Sabetta, and China has folded it into a "Polar Silk Road". Coverage divides between an opportunity framing and a Western security framing that sees Russian control and Chinese encroachment as a strategic threat.',
  description_de = 'Der Wettbewerb um die Seewege, welche die arktische Erwärmung öffnet — die Nordostpassage entlang der russischen Küste, die Nordwestpassage durch den kanadischen Archipel und eine künftige transpolare Route — die Asien-Europa-Fahrten um Wochen verkürzen könnten. Russland entwickelt die Nordostpassage mit nuklearen Eisbrechern und dem Hafen Sabetta, und China hat sie in eine "polare Seidenstraße" eingebettet. Die Berichterstattung teilt sich zwischen einer Chancen-Rahmung und einer westlichen Sicherheits-Rahmung, welche die russische Kontrolle und chinesisches Vordringen als strategische Bedrohung sieht.',
  updated_at = NOW()
WHERE id = 'arctic_shipping_routes';

-- ========================= (B) theater narratives =========================
INSERT INTO narratives_v2
  (id, name_en, name_de, claim_en, claim_de, actor_centroids, framing_keywords,
   is_active, publishers, fn_id, display_order, stance_label_en, stance_label_de,
   stance, framing_required)
VALUES
(
  'arctic_western_security_consensus',
  'The Arctic must be secured against Russian militarization and Sino-Russian encroachment',
  'Die Arktis muss gegen russische Militarisierung und russisch-chinesisches Vordringen gesichert werden',
  'Western security-consensus framing (NATO, Nordic and US mainstream plus Western business press) holds that the Arctic is becoming a zone of strategic vulnerability that must be secured: Russian rearmament in the High North and deepening Sino-Russian cooperation require NATO deterrence, resource and shipping-route access must be protected, and allied sovereignty defended. Vocabulary: deter, Russian threat, encroachment, defend the north, freedom of navigation, security.',
  'Die westliche Sicherheitskonsens-Rahmung (NATO, nordischer und US-Mainstream sowie westliche Wirtschaftspresse) sieht die Arktis als eine Zone strategischer Verwundbarkeit, die gesichert werden muss: russische Aufrüstung im hohen Norden und vertiefte russisch-chinesische Kooperation erfordern NATO-Abschreckung, der Zugang zu Rohstoffen und Schifffahrtsrouten muss geschützt und die Souveränität der Verbündeten verteidigt werden.',
  ARRAY['NON-STATE-NATO','EUROPE-NORDIC','AMERICAS-USA','AMERICAS-CANADA','NON-STATE-EU'],
  ARRAY['deter','deterrence','Russian threat','encroachment','defend','defend the north','security','build-up','freedom of navigation','reinforce','high north'],
  true,
  ARRAY['Reuters','BBC World','Financial Times','Associated Press','The Guardian','Deutsche Welle','Euronews','France 24 (EN)','Wall Street Journal','New York Times','Washington Post','NPR','CNN','ABC News','Military Times','Defense News','ERR News','LRT English','Atlantic Council','Politico','Bloomberg','OilPrice','Globe and Mail','CNBC','Fox News'],
  'arctic_theater', 1,
  'Western Arctic security consensus',
  'Westlicher Sicherheitskonsens in der Arktis',
  2, false
),
(
  'arctic_russia_china_counter',
  'NATO expansion and the US Greenland grab are the real provocation and Western hypocrisy',
  'NATO-Erweiterung und der US-Griff nach Grönland sind die eigentliche Provokation und westliche Heuchelei',
  'Russian and Chinese counter-framing (Russian state press and Chinese state media) reverses the Western account: NATO''s northern expansion is the destabilizing militarization of a once-low-tension zone and an encirclement of Russia, and the US push on Greenland is imperialist overreach that exposes Western hypocrisy -- not a threat Moscow or Beijing pose but a pretext. It is adversarial to the Western Arctic posture as a whole. Vocabulary: militarization, provocation, encirclement, imperialism, hypocrisy, pretext.',
  'Die russische und chinesische Gegen-Rahmung (russische Staatspresse und chinesische Staatsmedien) kehrt die westliche Darstellung um: Die Nordausdehnung der NATO sei die destabilisierende Militarisierung einer einst spannungsarmen Zone und eine Einkreisung Russlands, und der US-Vorstoß in Grönland sei imperialistische Überheblichkeit, die westliche Heuchelei entlarvt -- keine Bedrohung durch Moskau oder Peking, sondern ein Vorwand.',
  ARRAY['EUROPE-RUSSIA','ASIA-CHINA'],
  ARRAY['militariz','provocation','encirclement','imperialism','imperialist','hypocrisy','pretext','land grab','destabiliz','bloc confrontation','double standard'],
  true,
  ARRAY['RT','TASS','TASS (EN)','tass.com','Sputnik','RIA Novosti','Lenta.ru','Gazeta.ru','Izvestia','Kommersant','BelTA','Press TV','CGTN','Global Times','China Daily','Xinhua'],
  'arctic_theater', 2,
  'Russian & Chinese counter-framing',
  'Russische & chinesische Gegen-Rahmung',
  -2, false
),
(
  'arctic_western_sovereignty_stewardship',
  'Coercion and reckless exploitation of the Arctic must be resisted — for allied sovereignty and the climate',
  'Zwang und rücksichtslose Ausbeutung der Arktis müssen abgewehrt werden — für die Souveränität der Verbündeten und das Klima',
  'Western sovereignty-and-stewardship framing (European and Western mainstream plus green press) resists the Arctic being carved up by coercion or reckless exploitation: it defends Danish and allied sovereignty and international law against the US Greenland push, is wary of Russian control of the sea routes, and treats the warming Arctic as a fragile climate system that drilling, mining and militarization endanger. Distinct from the security-consensus card, it is critical rather than martial. Vocabulary: sovereignty, coercion, international law, not for sale, warming, black carbon, fragile, climate.',
  'Die westliche Souveränitäts- und Stewardship-Rahmung (europäischer und westlicher Mainstream sowie grüne Presse) wehrt sich gegen eine Aufteilung der Arktis durch Zwang oder rücksichtslose Ausbeutung: sie verteidigt die dänische und verbündete Souveränität und das Völkerrecht gegen den US-Vorstoß in Grönland, ist misstrauisch gegenüber russischer Kontrolle der Seewege und betrachtet die sich erwärmende Arktis als fragiles Klimasystem, das Bohrungen, Bergbau und Militarisierung gefährden.',
  ARRAY['NON-STATE-EU','EUROPE-NORDIC','EUROPE-GERMANY','EUROPE-FRANCE','AMERICAS-USA','AMERICAS-CANADA'],
  ARRAY['sovereignty','coercion','not for sale','international law','hands off','fragile','warming','black carbon','climate','environmental','self-determination','melting'],
  true,
  ARRAY['El País','Le Monde','The Independent','Channel NewsAsia','ANSA','EurActiv','Der Spiegel','Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','Al Jazeera','Anadolu Agency','The Guardian','Deutsche Welle','Euronews','France 24 (EN)','BBC World','New York Times','Reuters','Associated Press'],
  'arctic_theater', 3,
  'European sovereignty & environmental stewardship',
  'Europäische Souveränität & Umweltverantwortung',
  -1, false
)
ON CONFLICT (id) DO NOTHING;
