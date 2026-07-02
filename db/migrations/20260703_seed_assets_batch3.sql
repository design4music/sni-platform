-- Seed batch 3: ~26 additional strategic assets completing global port and
-- export-hub coverage (bulk commodity ports, container ports across Africa,
-- Middle East, South/Southeast Asia, East Asia, and Latin America) plus two
-- strategic pipelines (SUMED crude bypass, Nord Stream). See
-- 20260703_strategic_assets.sql for schema, 20260703_seed_strategic_assets.sql
-- and 20260703_seed_assets_batch2.sql for prior rows. Idempotent: safe to
-- re-run.

-- =========================================================================
-- COMMODITY EXPORT PORTS (Point, criticality 4)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('port_hedland', 'Port Hedland', 'Hafen Hedland', 'port',
 '{"type":"Point","coordinates":[118.60,-20.31]}'::jsonb,
 ARRAY['iron_ore'], ARRAY['ASIA-AUSTRALIA'], 4,
 '{"share_note": "the worlds largest iron ore export port"}'::jsonb,
 'The worlds largest iron ore export port, moving the bulk of Australias Pilbara output mostly to Chinese steelmakers.',
 'Der weltweit groesste Eisenerz-Exporthafen, transportiert den Grossteil der Pilbara-Foerderung Australiens vor allem zu chinesischen Stahlherstellern.'),

('newcastle_au_port', 'Port of Newcastle', 'Hafen Newcastle', 'port',
 '{"type":"Point","coordinates":[151.78,-32.92]}'::jsonb,
 ARRAY['coal'], ARRAY['ASIA-AUSTRALIA'], 4,
 '{"share_note": "the worlds largest coal export port"}'::jsonb,
 'The worlds largest coal export port, a key supply line for thermal coal into Asian power generation markets.',
 'Der weltweit groesste Kohle-Exporthafen, eine wichtige Versorgungslinie fuer Kesselkohle in asiatische Stromerzeugungsmaerkte.'),

('richards_bay_port', 'Richards Bay Coal Terminal', 'Kohleterminal Richards Bay', 'port',
 '{"type":"Point","coordinates":[32.10,-28.78]}'::jsonb,
 ARRAY['coal'], ARRAY['AFRICA-SOUTHAFRICA'], 4,
 '{"share_note": "one of the worlds largest dedicated coal export terminals"}'::jsonb,
 'South Africa principal coal export terminal, a major thermal coal supply route to Europe and Asia and a bellwether for the countrys rail-logistics troubles.',
 'Suedafrikas wichtigstes Kohle-Exportterminal, eine bedeutende Kesselkohle-Lieferroute nach Europa und Asien und ein Fruehindikator fuer die Eisenbahn-Logistikprobleme des Landes.'),

('rosario_grain_hub', 'Rosario Grain Hub', 'Getreideknotenpunkt Rosario', 'port',
 '{"type":"Point","coordinates":[-60.65,-32.95]}'::jsonb,
 ARRAY['grain','soy'], ARRAY[]::text[], 4,
 '{"share_note": "handles the large majority of Argentinas grain and soy exports via the Parana river"}'::jsonb,
 'The Parana river grain-export complex handling most of Argentinas soybean and grain shipments, highly exposed to river water levels and export-tax policy.',
 'Der Getreide-Exportkomplex am Parana-Fluss, wickelt den Grossteil der argentinischen Soja- und Getreideexporte ab, stark abhaengig von Flusswasserstaenden und Exportsteuerpolitik.'),

('tubarao_vitoria_port', 'Tubarao Port (Vitoria)', 'Hafen Tubarao (Vitoria)', 'port',
 '{"type":"Point","coordinates":[-40.25,-20.28]}'::jsonb,
 ARRAY['iron_ore'], ARRAY['AMERICAS-BRAZIL'], 4,
 '{"share_note": "one of the worlds largest iron ore export terminals"}'::jsonb,
 'One of the worlds largest iron ore export terminals, the main outlet for Vale shipments to Chinese and European steel mills.',
 'Eines der weltweit groessten Eisenerz-Exportterminals, der Hauptausgang fuer Vale-Lieferungen an chinesische und europaeische Stahlwerke.'),

('djibouti_port', 'Port of Djibouti', 'Hafen Dschibuti', 'port',
 '{"type":"Point","coordinates":[43.145,11.60]}'::jsonb,
 ARRAY['containers','oil'], ARRAY['MIDEAST-YEMEN'], 4,
 '{"share_note": "the primary logistics gateway for Ethiopia and host to multiple foreign military bases"}'::jsonb,
 'The key Red Sea logistics hub serving landlocked Ethiopia and host to competing Chinese, American, French and Japanese military bases at the mouth of Bab-el-Mandeb.',
 'Der zentrale Rotmeer-Logistikknotenpunkt fuer das Binnenland Aethiopien und Standort konkurrierender chinesischer, amerikanischer, franzoesischer und japanischer Militaerbasen am Bab-el-Mandeb.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- CONTAINER / GENERAL PORTS (Point, criticality 3 unless noted)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('tanger_med_port', 'Tanger Med Port', 'Hafen Tanger Med', 'port',
 '{"type":"Point","coordinates":[-5.50,35.89]}'::jsonb,
 ARRAY['containers'], ARRAY[]::text[], 4,
 '{"share_note": "the largest port in Africa and the Mediterranean by container throughput"}'::jsonb,
 'Africas largest port by container throughput, positioned directly opposite Gibraltar and a fast-growing transshipment rival to Spanish ports.',
 'Afrikas nach Containerumschlag groesster Hafen, direkt gegenueber Gibraltar gelegen und ein schnell wachsender Umschlag-Rivale zu spanischen Haefen.'),

('algeciras_port', 'Port of Algeciras', 'Hafen Algeciras', 'port',
 '{"type":"Point","coordinates":[-5.45,36.13]}'::jsonb,
 ARRAY['containers','oil'], ARRAY[]::text[], 3,
 '{"share_note": "Spains busiest port and a major Strait of Gibraltar transshipment hub"}'::jsonb,
 'Spain busiest port, a major bunkering and transshipment hub sitting directly on the Strait of Gibraltar shipping lane.',
 'Spaniens verkehrsreichster Hafen, ein bedeutender Bunker- und Umschlagknotenpunkt direkt an der Schifffahrtsroute der Strasse von Gibraltar.'),

('valencia_port', 'Port of Valencia', 'Hafen Valencia', 'port',
 '{"type":"Point","coordinates":[-0.325,39.44]}'::jsonb,
 ARRAY['containers'], ARRAY[]::text[], 3,
 '{"share_note": "Spains largest container port on the Mediterranean"}'::jsonb,
 'Spain largest Mediterranean container port, a key gateway for Iberian trade with Asia and the Americas.',
 'Spaniens groesster Mittelmeer-Containerhafen, ein wichtiges Tor fuer den iberischen Handel mit Asien und Amerika.'),

('le_havre_port', 'Port of Le Havre', 'Hafen Le Havre', 'port',
 '{"type":"Point","coordinates":[0.10,49.48]}'::jsonb,
 ARRAY['containers','oil'], ARRAY['EUROPE-FRANCE'], 3,
 '{"share_note": "Frances largest container port"}'::jsonb,
 'France largest container port, the maritime gateway for the greater Paris region and northern French industry.',
 'Frankreichs groesster Containerhafen, das maritime Tor fuer den Grossraum Paris und die nordfranzoesische Industrie.'),

('felixstowe_port', 'Port of Felixstowe', 'Hafen Felixstowe', 'port',
 '{"type":"Point","coordinates":[1.32,51.96]}'::jsonb,
 ARRAY['containers'], ARRAY['EUROPE-UK'], 3,
 '{"share_note": "the United Kingdoms busiest container port"}'::jsonb,
 'The UK busiest container port, handling a large share of the countrys containerized trade with continental Europe and Asia.',
 'Grossbritanniens verkehrsreichster Containerhafen, wickelt einen Grossteil des containerisierten Handels des Landes mit Kontinentaleuropa und Asien ab.'),

('marseille_fos_port', 'Port of Marseille-Fos', 'Hafen Marseille-Fos', 'port',
 '{"type":"Point","coordinates":[4.85,43.40]}'::jsonb,
 ARRAY['containers','oil','lng'], ARRAY['EUROPE-FRANCE'], 3,
 '{"share_note": "Frances largest port, combining container, oil and LNG terminals"}'::jsonb,
 'France largest port, combining container terminals with major oil refining and LNG import capacity on the Mediterranean coast.',
 'Frankreichs groesster Hafen, verbindet Containerterminals mit bedeutender Oelraffinerie- und LNG-Importkapazitaet an der Mittelmeerkueste.'),

('genoa_port', 'Port of Genoa', 'Hafen Genua', 'port',
 '{"type":"Point","coordinates":[8.90,44.40]}'::jsonb,
 ARRAY['containers'], ARRAY[]::text[], 3,
 '{"share_note": "Italys busiest port by cargo throughput"}'::jsonb,
 'Italy busiest seaport, the principal gateway for containerized trade into northern Italy and the Po valley industrial belt.',
 'Italiens verkehrsreichster Seehafen, das wichtigste Tor fuer containerisierten Handel nach Norditalien und den industriellen Po-Guertel.'),

('trieste_port', 'Port of Trieste', 'Hafen Triest', 'port',
 '{"type":"Point","coordinates":[13.75,45.65]}'::jsonb,
 ARRAY['containers','oil'], ARRAY[]::text[], 3,
 '{"share_note": "the Adriatics deepest port and a key pipeline oil-import terminal for central Europe"}'::jsonb,
 'The Adriatics deepest port, combining a growing container business with the TAL pipeline oil terminal supplying refineries across central Europe.',
 'Der tiefste Hafen der Adria, verbindet ein wachsendes Containergeschaeft mit dem TAL-Pipeline-Oelterminal, das Raffinerien in ganz Mitteleuropa versorgt.'),

('durban_port', 'Port of Durban', 'Hafen Durban', 'port',
 '{"type":"Point","coordinates":[31.05,-29.87]}'::jsonb,
 ARRAY['containers','oil'], ARRAY['AFRICA-SOUTHAFRICA'], 3,
 '{"share_note": "the busiest container port in Sub-Saharan Africa"}'::jsonb,
 'Sub-Saharan Africas busiest container port, the principal maritime gateway for South Africas industrial heartland.',
 'Der verkehrsreichste Containerhafen im subsaharischen Afrika, das wichtigste maritime Tor fuer Suedafrikas industrielles Kernland.'),

('lagos_lekki_port', 'Lagos-Lekki Deep Sea Port', 'Tiefwasserhafen Lagos-Lekki', 'port',
 '{"type":"Point","coordinates":[3.57,6.43]}'::jsonb,
 ARRAY['containers','oil'], ARRAY[]::text[], 3,
 '{"share_note": "Nigerias newest deep-water port, aimed at easing chronic Lagos port congestion"}'::jsonb,
 'A new deep-water port east of Lagos built to relieve chronic congestion and give Nigeria, Africas largest crude producer, greater container capacity.',
 'Ein neuer Tiefwasserhafen oestlich von Lagos, gebaut zur Entlastung chronischer Staus und zur Staerkung der Containerkapazitaet Nigerias, Afrikas groesstem Rohoelproduzenten.'),

('mombasa_port', 'Port of Mombasa', 'Hafen Mombasa', 'port',
 '{"type":"Point","coordinates":[39.65,-4.05]}'::jsonb,
 ARRAY['containers'], ARRAY[]::text[], 3,
 '{"share_note": "East Africas primary gateway port serving Kenya and landlocked neighbors"}'::jsonb,
 'East Africas primary gateway port, serving Kenya, Uganda, Rwanda and South Sudan through the Northern Corridor trade route.',
 'Ostafrikas wichtigster Tor-Hafen, versorgt Kenia, Uganda, Ruanda und Suedsudan ueber die Handelsroute des Northern Corridor.'),

('jeddah_port', 'Jeddah Islamic Port', 'Islamischer Hafen Jeddah', 'port',
 '{"type":"Point","coordinates":[39.17,21.48]}'::jsonb,
 ARRAY['containers','oil'], ARRAY['MIDEAST-SAUDI'], 4,
 '{"share_note": "Saudi Arabias main Red Sea port and container gateway"}'::jsonb,
 'Saudi Arabias principal Red Sea port, the kingdoms main container gateway and a logistics hub for Hajj and Umrah traffic.',
 'Saudi-Arabiens wichtigster Rotmeer-Hafen, das Haupttor des Koenigreichs fuer Container und ein Logistikknotenpunkt fuer Hadsch- und Umrah-Verkehr.'),

('salalah_port', 'Port of Salalah', 'Hafen Salalah', 'port',
 '{"type":"Point","coordinates":[54.02,16.93]}'::jsonb,
 ARRAY['containers','oil'], ARRAY[]::text[], 3,
 '{"share_note": "a major Indian Ocean transshipment hub outside the Strait of Hormuz"}'::jsonb,
 'Omans deep-water transshipment hub on the Arabian Sea, valued as a major container port that lies outside the Strait of Hormuz chokepoint.',
 'Omans Tiefwasser-Umschlaghafen am Arabischen Meer, geschaetzt als bedeutender Containerhafen ausserhalb des Engpasses der Strasse von Hormus.'),

('haifa_port', 'Port of Haifa', 'Hafen Haifa', 'port',
 '{"type":"Point","coordinates":[35.00,32.83]}'::jsonb,
 ARRAY['containers'], ARRAY['MIDEAST-ISRAEL'], 3,
 '{"share_note": "Israels largest port and a hub for its growing regional trade links"}'::jsonb,
 'Israels largest port, central to the countrys Mediterranean trade and a strategic node in evolving regional shipping partnerships.',
 'Israels groesster Hafen, zentral fuer den Mittelmeerhandel des Landes und ein strategischer Knotenpunkt in sich entwickelnden regionalen Schifffahrtspartnerschaften.'),

('port_said_east', 'Port Said East Port', 'Ostafen Port Said', 'port',
 '{"type":"Point","coordinates":[32.35,31.32]}'::jsonb,
 ARRAY['containers','oil'], ARRAY['MIDEAST-EGYPT'], 4,
 '{"share_note": "the main container transshipment hub at the Mediterranean entrance to the Suez Canal"}'::jsonb,
 'Egypts main transshipment port at the Mediterranean mouth of the Suez Canal, capturing container traffic feeding the canal corridor.',
 'Aegyptens wichtigster Umschlaghafen am Mittelmeer-Eingang des Suezkanals, erfasst Containerverkehr, der den Kanalkorridor speist.'),

('mundra_port', 'Port of Mundra', 'Hafen Mundra', 'port',
 '{"type":"Point","coordinates":[69.72,22.84]}'::jsonb,
 ARRAY['containers','coal','oil'], ARRAY['ASIA-INDIA'], 3,
 '{"share_note": "Indias largest private port and container terminal"}'::jsonb,
 'Indias largest private port, a fast-growing Gujarat coast gateway handling containers, coal and crude for the countrys west-coast industry.',
 'Indiens groesster privater Hafen, ein schnell wachsendes Tor an der Kueste Gujarats fuer Container, Kohle und Rohoel fuer die Industrie an der Westkueste des Landes.'),

('karachi_port', 'Port of Karachi', 'Hafen Karatschi', 'port',
 '{"type":"Point","coordinates":[66.98,24.82]}'::jsonb,
 ARRAY['containers','oil'], ARRAY['ASIA-PAKISTAN'], 3,
 '{"share_note": "Pakistans largest and busiest port"}'::jsonb,
 'Pakistans largest and busiest seaport, handling the majority of the countrys foreign trade and energy imports.',
 'Pakistans groesster und verkehrsreichster Seehafen, wickelt den Grossteil des Aussenhandels und der Energieimporte des Landes ab.'),

('chittagong_port', 'Port of Chittagong', 'Hafen Chittagong', 'port',
 '{"type":"Point","coordinates":[91.83,22.33]}'::jsonb,
 ARRAY['containers'], ARRAY[]::text[], 3,
 '{"share_note": "Bangladeshs primary seaport handling the large majority of its foreign trade"}'::jsonb,
 'Bangladeshs primary seaport, the entry and exit point for the large majority of the countrys garment-export-driven trade.',
 'Bangladeschs wichtigster Seehafen, Ein- und Ausgangspunkt fuer den Grossteil des von Bekleidungsexporten getriebenen Handels des Landes.'),

('laem_chabang_port', 'Laem Chabang Port', 'Hafen Laem Chabang', 'port',
 '{"type":"Point","coordinates":[100.89,13.08]}'::jsonb,
 ARRAY['containers','autos'], ARRAY[]::text[], 3,
 '{"share_note": "Thailands largest port and a major regional auto-export hub"}'::jsonb,
 'Thailands largest deep-sea port and a major automobile export hub anchoring the countrys Eastern Economic Corridor.',
 'Thailands groesster Tiefseehafen und ein bedeutender Autoexport-Knotenpunkt, Ankerpunkt des oestlichen Wirtschaftskorridors des Landes.'),

('cai_mep_port', 'Cai Mep Port', 'Hafen Cai Mep', 'port',
 '{"type":"Point","coordinates":[107.02,10.57]}'::jsonb,
 ARRAY['containers'], ARRAY[]::text[], 3,
 '{"share_note": "Vietnams principal deep-water port for direct services to the US and Europe"}'::jsonb,
 'Vietnams principal deep-water container port near Ho Chi Minh City, a key outlet for the countrys expanding manufacturing exports.',
 'Vietnams wichtigster Tiefwasser-Containerhafen nahe Ho-Chi-Minh-Stadt, ein zentraler Ausgang fuer die wachsenden Fertigungsexporte des Landes.'),

('tanjung_priok_port', 'Tanjung Priok Port (Jakarta)', 'Hafen Tanjung Priok (Jakarta)', 'port',
 '{"type":"Point","coordinates":[106.88,-6.10]}'::jsonb,
 ARRAY['containers'], ARRAY['ASIA-INDONESIA'], 3,
 '{"share_note": "Indonesias busiest port, serving the greater Jakarta metropolitan economy"}'::jsonb,
 'Indonesias busiest port, the principal maritime gateway for the greater Jakarta metropolitan region and national consumer imports.',
 'Indonesiens verkehrsreichster Hafen, das wichtigste maritime Tor fuer den Grossraum Jakarta und nationale Konsumgueterimporte.'),

('manila_port', 'Port of Manila', 'Hafen Manila', 'port',
 '{"type":"Point","coordinates":[120.95,14.58]}'::jsonb,
 ARRAY['containers'], ARRAY[]::text[], 3,
 '{"share_note": "the Philippines busiest port and premier international gateway"}'::jsonb,
 'The Philippines busiest seaport, the primary international gateway for the countrys imports and manufacturing exports.',
 'Der verkehrsreichste Seehafen der Philippinen, das wichtigste internationale Tor fuer die Importe und Fertigungsexporte des Landes.'),

('yokohama_tokyo_bay_port', 'Yokohama-Tokyo Bay Port', 'Hafen Yokohama-Tokio-Bucht', 'port',
 '{"type":"Point","coordinates":[139.65,35.45]}'::jsonb,
 ARRAY['containers','autos'], ARRAY['ASIA-JAPAN'], 4,
 '{"share_note": "the core port complex of the Tokyo-Yokohama industrial and consumer megaregion"}'::jsonb,
 'The core port complex of the Tokyo Bay megaregion, Japans busiest gateway for containerized trade and auto exports.',
 'Der zentrale Hafenkomplex der Tokio-Bucht-Megaregion, Japans verkehrsreichstes Tor fuer containerisierten Handel und Autoexporte.'),

('nagoya_port', 'Port of Nagoya', 'Hafen Nagoya', 'port',
 '{"type":"Point","coordinates":[136.88,35.05]}'::jsonb,
 ARRAY['autos','containers'], ARRAY['ASIA-JAPAN'], 3,
 '{"share_note": "Japans largest port by trade value, dominated by automobile exports"}'::jsonb,
 'Japans largest port by trade value, the principal export outlet for the Toyota-centered Chubu region automobile industry.',
 'Japans nach Handelswert groesster Hafen, der wichtigste Exportausgang fuer die auf Toyota zentrierte Automobilindustrie der Region Chubu.'),

('callao_port', 'Port of Callao', 'Hafen Callao', 'port',
 '{"type":"Point","coordinates":[-77.15,-12.05]}'::jsonb,
 ARRAY['containers','copper'], ARRAY[]::text[], 3,
 '{"share_note": "Perus main port, handling most of the countrys copper and container trade"}'::jsonb,
 'Perus principal port, the main export outlet for the countrys copper mining sector and its largest container gateway.',
 'Perus wichtigster Hafen, der Haupt-Exportausgang fuer den Kupferbergbausektor des Landes und sein groesstes Container-Tor.'),

('manzanillo_mx_port', 'Port of Manzanillo', 'Hafen Manzanillo', 'port',
 '{"type":"Point","coordinates":[-104.32,19.05]}'::jsonb,
 ARRAY['containers'], ARRAY[]::text[], 3,
 '{"share_note": "Mexicos busiest port and principal Pacific gateway"}'::jsonb,
 'Mexicos busiest seaport, the principal Pacific coast gateway for trade with Asia and a key node in North American supply chains.',
 'Mexikos verkehrsreichster Seehafen, das wichtigste Pazifik-Tor fuer den Handel mit Asien und ein zentraler Knotenpunkt in nordamerikanischen Lieferketten.'),

('cartagena_co_port', 'Port of Cartagena', 'Hafen Cartagena', 'port',
 '{"type":"Point","coordinates":[-75.53,10.40]}'::jsonb,
 ARRAY['containers','oil'], ARRAY[]::text[], 3,
 '{"share_note": "Colombias leading container port on the Caribbean coast"}'::jsonb,
 'Colombias leading Caribbean container port, a key regional transshipment point linking the country to North American and European trade.',
 'Kolumbiens fuehrender Karibik-Containerhafen, ein wichtiger regionaler Umschlagpunkt, der das Land mit dem nordamerikanischen und europaeischen Handel verbindet.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- PIPELINES (LineString)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('sumed_pipeline', 'SUMED Pipeline', 'SUMED-Pipeline', 'pipeline',
 '{"type":"LineString","coordinates":[[32.35,29.60],[32.10,29.75],[31.60,30.05],[31.05,30.35],[30.55,30.65],[30.10,30.85],[29.85,30.95],[29.60,31.05]]}'::jsonb,
 ARRAY['oil'], ARRAY['MIDEAST-EGYPT'], 4,
 '{"share_note": "carries roughly the same crude volumes as the Suez Canal itself, giving Egypt a bypass route"}'::jsonb,
 'The overland crude pipeline from Ain Sukhna to Sidi Kerir that lets tankers too large for the Suez Canal move oil between the Red Sea and Mediterranean, making it a critical redundancy for the canal chokepoint.',
 'Die Ueberland-Rohoelpipeline von Ain Sukhna nach Sidi Kerir, die es fuer den Suezkanal zu grossen Tankern erlaubt, Oel zwischen Rotem Meer und Mittelmeer zu transportieren, eine kritische Redundanz zum Engpass des Kanals.'),

('nord_stream_pipeline', 'Nord Stream Pipeline', 'Nord-Stream-Pipeline', 'pipeline',
 '{"type":"LineString","coordinates":[[28.70,60.70],[27.00,60.20],[24.50,59.60],[21.50,58.80],[19.00,57.80],[16.50,56.20],[15.00,55.20],[14.30,54.60],[13.65,54.15]]}'::jsonb,
 ARRAY['gas'], ARRAY['EUROPE-RUSSIA', 'EUROPE-GERMANY'], 2,
 '{"share_note": "three of four lines destroyed in the September 2022 seabed sabotage; remains strategically significant as a dormant asset", "status": "damaged, largely non-operational since 2022"}'::jsonb,
 'The Baltic seabed gas pipeline linking Vyborg to Greifswald, sabotaged in September 2022; though largely inoperative, its fate remains a live strategic and diplomatic question over any future Russia-Germany gas relationship.',
 'Die Ostsee-Gaspipeline von Wyborg nach Greifswald, im September 2022 sabotiert; obwohl weitgehend ausser Betrieb, bleibt ihr Schicksal eine offene strategische und diplomatische Frage fuer jede kuenftige Gasbeziehung zwischen Russland und Deutschland.')

ON CONFLICT (id) DO NOTHING;
