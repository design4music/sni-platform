-- Seed batch 2: ~35 additional strategic assets closing out ports, energy
-- facilities, critical minerals clusters, and agricultural belts. See
-- 20260703_strategic_assets.sql for schema, 20260703_seed_strategic_assets.sql
-- for the first 39 rows. Idempotent: safe to re-run.

-- =========================================================================
-- PORTS (Point)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('ningbo_zhoushan_port', 'Port of Ningbo-Zhoushan', 'Hafen Ningbo-Zhoushan', 'port',
 '{"type":"Point","coordinates":[121.85,29.87]}'::jsonb,
 ARRAY['containers','oil'], ARRAY['ASIA-CHINA'], 4,
 '{"share_note": "the worlds largest port by cargo tonnage"}'::jsonb,
 'The worlds busiest port by cargo tonnage, a critical node for Chinese export manufacturing and bulk commodity imports.',
 'Der nach Frachttonnage verkehrsreichste Hafen der Welt, ein zentraler Knotenpunkt fuer die chinesische Exportfertigung und Massengutimporte.'),

('shenzhen_port', 'Port of Shenzhen', 'Hafen Shenzhen', 'port',
 '{"type":"Point","coordinates":[114.05,22.55]}'::jsonb,
 ARRAY['containers'], ARRAY['ASIA-CHINA'], 4,
 '{"share_note": "one of the worlds busiest container ports, anchoring the Pearl River Delta"}'::jsonb,
 'The maritime gateway for the Pearl River Delta manufacturing belt, among the busiest container ports on earth.',
 'Das maritime Tor fuer den Fertigungsguertel des Perlflussdeltas, einer der verkehrsreichsten Containerhaefen der Welt.'),

('busan_port', 'Port of Busan', 'Hafen Busan', 'port',
 '{"type":"Point","coordinates":[129.08,35.10]}'::jsonb,
 ARRAY['containers'], ARRAY['ASIA-SOUTHKOREA'], 4,
 '{"share_note": "South Koreas largest port and a major Northeast Asia transshipment hub"}'::jsonb,
 'South Korea principal container port and a key transshipment hub linking Northeast Asia to global shipping lanes.',
 'Suedkoreas wichtigster Containerhafen und ein zentraler Umschlagknotenpunkt zwischen Nordostasien und den globalen Schifffahrtsrouten.'),

('qingdao_port', 'Port of Qingdao', 'Hafen Qingdao', 'port',
 '{"type":"Point","coordinates":[120.30,36.07]}'::jsonb,
 ARRAY['containers','oil'], ARRAY['ASIA-CHINA'], 3,
 '{"share_note": "a top-five Chinese port handling crude imports and containers"}'::jsonb,
 'A major northern Chinese port combining crude oil import terminals with large-scale container throughput.',
 'Ein bedeutender nordchinesischer Hafen, der Rohoel-Importterminals mit hohem Containerumschlag verbindet.'),

('tianjin_port', 'Port of Tianjin', 'Hafen Tianjin', 'port',
 '{"type":"Point","coordinates":[117.72,38.98]}'::jsonb,
 ARRAY['containers'], ARRAY['ASIA-CHINA'], 3,
 '{"share_note": "the main maritime gateway for Beijing and northern China"}'::jsonb,
 'The principal seaport serving Beijing and the Bohai Bay industrial region.',
 'Der wichtigste Seehafen fuer Peking und die Industrieregion Bohai-Bucht.'),

('kaohsiung_port', 'Port of Kaohsiung', 'Hafen Kaohsiung', 'port',
 '{"type":"Point","coordinates":[120.28,22.58]}'::jsonb,
 ARRAY['containers','semiconductors'], ARRAY['ASIA-TAIWAN'], 3,
 '{"share_note": "Taiwans largest port and main container gateway"}'::jsonb,
 'Taiwan largest port, handling the bulk of the islands container trade including semiconductor-linked cargo.',
 'Taiwans groesster Hafen, wickelt den Grossteil des Containerhandels der Insel ab, einschliesslich halbleiterbezogener Fracht.'),

('port_klang', 'Port Klang', 'Hafen Klang', 'port',
 '{"type":"Point","coordinates":[101.38,3.00]}'::jsonb,
 ARRAY['containers','oil'], ARRAY['ASIA-SINGAPORE'], 3,
 '{"share_note": "Malaysias busiest port, positioned at the Strait of Malacca"}'::jsonb,
 'Malaysia principal port, positioned along the Strait of Malacca and competing with Singapore for regional transshipment.',
 'Malaysias wichtigster Hafen an der Strasse von Malakka, im Wettbewerb mit Singapur um den regionalen Umschlag.'),

('colombo_port', 'Port of Colombo', 'Hafen Colombo', 'port',
 '{"type":"Point","coordinates":[79.85,6.95]}'::jsonb,
 ARRAY['containers'], ARRAY['ASIA-INDIA'], 3,
 '{"share_note": "a key Indian Ocean transshipment hub with significant Chinese port investment"}'::jsonb,
 'A central Indian Ocean transshipment hub whose Chinese-financed terminal has been a recurring flashpoint in Sri Lanka debt and strategic alignment debates.',
 'Ein zentraler Umschlagknotenpunkt im Indischen Ozean, dessen chinesisch finanziertes Terminal wiederholt Streitpunkt in Sri Lankas Schulden- und Ausrichtungsdebatten war.'),

('jawaharlal_nehru_port', 'Jawaharlal Nehru Port (Mumbai)', 'Jawaharlal-Nehru-Hafen (Mumbai)', 'port',
 '{"type":"Point","coordinates":[72.95,18.95]}'::jsonb,
 ARRAY['containers'], ARRAY['ASIA-INDIA'], 3,
 '{"share_note": "Indias largest container port"}'::jsonb,
 'India largest container port, handling a large share of the countries containerized trade with the rest of the world.',
 'Indiens groesster Containerhafen, wickelt einen Grossteil des containerisierten Handels des Landes mit der restlichen Welt ab.'),

('antwerp_bruges_port', 'Port of Antwerp-Bruges', 'Hafen Antwerpen-Bruegge', 'port',
 '{"type":"Point","coordinates":[4.40,51.30]}'::jsonb,
 ARRAY['containers','chemicals','oil'], ARRAY['EUROPE-NETHERLANDS'], 4,
 '{"share_note": "Europes second-largest port and its largest integrated chemical hub"}'::jsonb,
 'Europe second-largest port by tonnage and the continents largest integrated chemical cluster, tightly coupled with Rotterdam.',
 'Europas nach Tonnage zweitgroesster Hafen und der groesste integrierte Chemiecluster des Kontinents, eng verflochten mit Rotterdam.'),

('gdansk_port', 'Port of Gdansk', 'Hafen Danzig', 'port',
 '{"type":"Point","coordinates":[18.65,54.37]}'::jsonb,
 ARRAY['containers','oil','grain'], ARRAY['EUROPE-POLAND'], 3,
 '{"share_note": "Polands largest deepwater port and a growing LNG and grain gateway"}'::jsonb,
 'Poland principal deepwater port, increasingly important as a non-Russian energy import gateway and grain export outlet for the region.',
 'Polens wichtigster Tiefwasserhafen, zunehmend bedeutsam als nicht-russisches Energie-Importtor und Getreideexport-Ausgang fuer die Region.'),

('constanta_port', 'Port of Constanta', 'Hafen Konstanza', 'port',
 '{"type":"Point","coordinates":[28.65,44.17]}'::jsonb,
 ARRAY['grain','containers'], ARRAY['EUROPE-UKRAINE'], 4,
 '{"share_note": "the largest Black Sea port and the main alternate route for Ukrainian grain exports"}'::jsonb,
 'Romania Black Sea port that became the primary overland-and-sea alternate route for Ukrainian grain exports after the Odesa blockade.',
 'Rumaeniens Schwarzmeerhafen, der nach der Blockade Odessas zur wichtigsten Land-See-Alternativroute fuer ukrainische Getreideexporte wurde.'),

('houston_port', 'Port of Houston', 'Hafen Houston', 'port',
 '{"type":"Point","coordinates":[-95.15,29.73]}'::jsonb,
 ARRAY['oil','lng','chemicals'], ARRAY['AMERICAS-USA'], 4,
 '{"share_note": "the largest US port by foreign waterborne tonnage and the heart of the Gulf refining complex"}'::jsonb,
 'The hub of the US Gulf Coast refining and petrochemical complex, and the countrys leading energy-export port.',
 'Das Zentrum des US-Golfkuesten-Raffinerie- und Petrochemiekomplexes und der fuehrende Energie-Exporthafen des Landes.'),

('new_york_nj_port', 'Port of New York-New Jersey', 'Hafen New York-New Jersey', 'port',
 '{"type":"Point","coordinates":[-74.05,40.67]}'::jsonb,
 ARRAY['containers'], ARRAY['AMERICAS-USA'], 3,
 '{"share_note": "the largest port complex on the US East Coast"}'::jsonb,
 'The busiest container gateway on the US East Coast, critical for transatlantic trade and northeastern US supply chains.',
 'Das verkehrsreichste Container-Tor an der US-Ostkueste, entscheidend fuer den transatlantischen Handel und die Lieferketten im Nordosten der USA.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- ENERGY FACILITIES / CLUSTERS (Point or Polygon)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('sabine_pass_lng', 'Sabine Pass LNG Cluster', 'Sabine-Pass-LNG-Cluster', 'facility',
 '{"type":"Point","coordinates":[-93.87,29.74]}'::jsonb,
 ARRAY['lng'], ARRAY['AMERICAS-USA'], 4,
 '{"share_note": "one of the largest LNG export terminals in the United States"}'::jsonb,
 'A flagship US Gulf Coast LNG export terminal underpinning Americas rise as a swing gas supplier to Europe and Asia.',
 'Ein Flaggschiff-LNG-Exportterminal an der US-Golfkueste, Grundlage fuer Amerikas Aufstieg als Swing-Gaslieferant fuer Europa und Asien.'),

('yamal_lng', 'Yamal LNG (Sabetta)', 'Yamal-LNG (Sabetta)', 'facility',
 '{"type":"Point","coordinates":[72.05,71.27]}'::jsonb,
 ARRAY['lng','gas'], ARRAY['EUROPE-RUSSIA'], 4,
 '{"share_note": "Russias flagship Arctic LNG export project"}'::jsonb,
 'Russia flagship Arctic LNG terminal, exporting via the Northern Sea Route and remaining a target of Western sanctions debate.',
 'Russlands arktisches Vorzeige-LNG-Terminal, exportiert ueber die Nordostpassage und bleibt Gegenstand westlicher Sanktionsdebatten.'),

('ras_laffan_lng', 'Ras Laffan LNG Terminal', 'Ras-Laffan-LNG-Terminal', 'facility',
 '{"type":"Point","coordinates":[51.55,25.90]}'::jsonb,
 ARRAY['lng','gas'], ARRAY['MIDEAST-GULF'], 5,
 '{"share_note": "the worlds largest single LNG export complex"}'::jsonb,
 'Qatar principal LNG export complex and one of the largest in the world, a critical alternative gas supplier for both Europe and Asia.',
 'Katars wichtigster LNG-Exportkomplex und einer der groessten der Welt, ein kritischer alternativer Gaslieferant sowohl fuer Europa als auch Asien.'),

('gorgon_nws_lng', 'Gorgon-North West Shelf LNG', 'Gorgon-North-West-Shelf-LNG', 'facility',
 '{"type":"Point","coordinates":[115.40,-20.63]}'::jsonb,
 ARRAY['lng','gas'], ARRAY['ASIA-AUSTRALIA'], 4,
 '{"share_note": "anchors Australias position as a top global LNG exporter"}'::jsonb,
 'Australia largest LNG export complex, supplying long-term contracted gas to Japan, South Korea and China.',
 'Australiens groesster LNG-Exportkomplex, beliefert Japan, Suedkorea und China mit langfristig kontrahiertem Gas.'),

('jamnagar_refinery', 'Jamnagar Refining Complex', 'Raffineriekomplex Jamnagar', 'facility',
 '{"type":"Point","coordinates":[69.90,22.35]}'::jsonb,
 ARRAY['oil','refined_products'], ARRAY['ASIA-INDIA'], 4,
 '{"share_note": "the worlds largest single-site oil refining complex"}'::jsonb,
 'The worlds largest refinery complex, processing discounted Russian and Gulf crude into fuel exported worldwide, including to Europe.',
 'Der groesste Raffineriekomplex der Welt, verarbeitet verguenstigtes russisches und Golf-Rohoel zu weltweit exportiertem Treibstoff, auch nach Europa.'),

('ulsan_industrial', 'Ulsan Industrial-Refining Complex', 'Industrie- und Raffineriekomplex Ulsan', 'facility',
 '{"type":"Point","coordinates":[129.37,35.55]}'::jsonb,
 ARRAY['oil','refined_products','chemicals'], ARRAY['ASIA-SOUTHKOREA'], 3,
 '{"share_note": "South Koreas largest industrial and refining hub"}'::jsonb,
 'South Korea largest industrial complex, combining refining, petrochemicals and shipbuilding on the countrys southeast coast.',
 'Suedkoreas groesster Industriekomplex, verbindet Raffinerie, Petrochemie und Schiffbau an der Suedostkueste des Landes.'),

('norwegian_shelf_gas', 'Norwegian Continental Shelf Gas Fields', 'Gasfelder auf dem norwegischen Festlandsockel', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[1.5,58.5],[3.5,61.5],[2.0,64.5],[-1.0,65.5],[-3.0,62.0],[-1.0,59.0],[1.5,58.5]]]}'::jsonb,
 ARRAY['gas'], ARRAY['EUROPE-UK'], 5,
 '{"share_note": "became Europes largest single source of pipeline gas after the loss of Russian supply"}'::jsonb,
 'The North Sea gas fields that became Europe single most important gas source after Russian pipeline supply collapsed in 2022.',
 'Die Nordsee-Gasfelder, die nach dem Zusammenbruch der russischen Pipelinelieferungen 2022 zu Europas wichtigster einzelner Gasquelle wurden.'),

('orinoco_heavy_oil_belt', 'Orinoco Heavy Oil Belt', 'Orinoco-Schweroelguertel', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-66.5,8.7],[-62.5,8.7],[-62.5,7.5],[-66.5,7.5],[-66.5,8.7]]]}'::jsonb,
 ARRAY['oil'], ARRAY['AMERICAS-VENEZUELA'], 3,
 '{"share_note": "holds one of the largest heavy crude oil reserves in the world"}'::jsonb,
 'One of the worlds largest heavy-crude reserves, its output throttled for years by US sanctions and chronic underinvestment.',
 'Eine der weltweit groessten Schweroel-Reserven, deren Foerderung jahrelang durch US-Sanktionen und chronische Unterinvestition gedrosselt wurde.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- CRITICAL MINERALS CLUSTERS (Polygon, coarse hull)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('indonesian_nickel_belt', 'Indonesian Nickel Belt (Morowali/Sulawesi)', 'Indonesischer Nickelguertel (Morowali/Sulawesi)', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[121.0,-1.0],[123.5,-1.0],[123.5,-3.5],[121.0,-3.5],[121.0,-1.0]]]}'::jsonb,
 ARRAY['nickel'], ARRAY['ASIA-INDONESIA'], 4,
 '{"share_note": "supplies the large majority of the worlds mined and processed nickel"}'::jsonb,
 'Indonesia nickel mining and smelting belt, now the dominant global source feeding battery and stainless-steel supply chains.',
 'Indonesiens Nickel-Abbau- und Schmelzguertel, heute die dominante globale Quelle fuer Batterie- und Edelstahl-Lieferketten.'),

('bayan_obo_rare_earths', 'Bayan Obo Rare Earths Complex', 'Bayan-Obo-Seltene-Erden-Komplex', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[109.5,41.5],[110.3,41.5],[110.3,40.9],[109.5,40.9],[109.5,41.5]]]}'::jsonb,
 ARRAY['rare_earths'], ARRAY['ASIA-CHINA'], 5,
 '{"share_note": "the largest rare earth deposit and processing complex in the world"}'::jsonb,
 'The worlds largest rare-earth mining and processing complex, underpinning Chinas dominance over magnets and advanced electronics supply chains.',
 'Der groesste Seltene-Erden-Abbau- und Verarbeitungskomplex der Welt, Grundlage fuer Chinas Dominanz bei Magneten und Lieferketten fuer moderne Elektronik.'),

('norilsk_nickel_palladium', 'Norilsk Nickel-Palladium Complex', 'Norilsk-Nickel-Palladium-Komplex', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[87.8,69.0],[88.6,69.0],[88.6,69.6],[87.8,69.6],[87.8,69.0]]]}'::jsonb,
 ARRAY['nickel','palladium'], ARRAY['EUROPE-RUSSIA'], 4,
 '{"share_note": "the largest single source of mined palladium and a major nickel producer"}'::jsonb,
 'The worlds largest palladium producer and a major nickel source, giving Russia outsized leverage over catalytic-converter and battery supply chains.',
 'Der weltweit groesste Palladiumproduzent und eine bedeutende Nickelquelle, verschafft Russland ueberproportionalen Einfluss auf Lieferketten fuer Katalysatoren und Batterien.'),

('bushveld_platinum_complex', 'Bushveld Platinum Complex', 'Bushveld-Platin-Komplex', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[26.5,-24.0],[30.5,-24.0],[30.5,-25.8],[26.5,-25.8],[26.5,-24.0]]]}'::jsonb,
 ARRAY['platinum'], ARRAY['AFRICA-SOUTHAFRICA'], 4,
 '{"share_note": "holds the large majority of the worlds known platinum group metal reserves"}'::jsonb,
 'South Africa vast platinum-group-metal reserves, essential to catalytic converters and the emerging hydrogen fuel cell industry.',
 'Suedafrikas riesige Platingruppenmetall-Reserven, unverzichtbar fuer Katalysatoren und die aufstrebende Wasserstoff-Brennstoffzellenindustrie.'),

('oyu_tolgoi_copper_gold', 'Oyu Tolgoi Copper-Gold Complex', 'Oyu-Tolgoi-Kupfer-Gold-Komplex', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[106.6,43.0],[107.2,43.0],[107.2,42.6],[106.6,42.6],[106.6,43.0]]]}'::jsonb,
 ARRAY['copper'], ARRAY[]::text[], 3,
 '{"share_note": "one of the largest copper-gold deposits developed in recent decades"}'::jsonb,
 'A major new copper-gold mine in the Gobi Desert, positioning Mongolia as an emerging supplier for the global energy-transition copper market.',
 'Eine bedeutende neue Kupfer-Gold-Mine in der Wueste Gobi, positioniert die Mongolei als aufstrebenden Lieferanten fuer den globalen Kupfermarkt der Energiewende.'),

('kazakh_uranium_belt', 'Kazakh Uranium Belt', 'Kasachischer Uranguertel', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[63.0,42.5],[68.5,42.5],[68.5,46.5],[63.0,46.5],[63.0,42.5]]]}'::jsonb,
 ARRAY['uranium'], ARRAY[]::text[], 4,
 '{"share_note": "produces the largest share of the worlds mined uranium"}'::jsonb,
 'Kazakhstan in-situ leach uranium mines supply the largest share of the worlds mined uranium, feeding nuclear fuel cycles worldwide.',
 'Kasachstans In-situ-Auslaugungs-Uranminen liefern den groessten Anteil des weltweit geforderten Urans und versorgen Kernbrennstoffkreislaeufe weltweit.'),

('saskatchewan_potash_belt', 'Saskatchewan Potash Belt', 'Saskatchewan-Kaliguertel', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-106.5,51.0],[-102.0,51.0],[-102.0,53.5],[-106.5,53.5],[-106.5,51.0]]]}'::jsonb,
 ARRAY['potash'], ARRAY[]::text[], 3,
 '{"share_note": "the largest potash reserves and export capacity in the world"}'::jsonb,
 'The worlds largest potash mining region, a critical fertilizer input whose supply security shapes global food-price stability.',
 'Die weltweit groesste Kali-Abbauregion, ein kritischer Duengemittel-Rohstoff, dessen Versorgungssicherheit die globale Preisstabilitaet bei Lebensmitteln mitbestimmt.'),

('moroccan_phosphate_plateau', 'Moroccan Phosphate Plateau (Khouribga)', 'Marokkanisches Phosphatplateau (Khouribga)', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-7.3,32.5],[-6.5,32.5],[-6.5,32.9],[-7.3,32.9],[-7.3,32.5]]]}'::jsonb,
 ARRAY['phosphate'], ARRAY[]::text[], 4,
 '{"share_note": "holds the large majority of the worlds known phosphate rock reserves"}'::jsonb,
 'Morocco holds most of the worlds known phosphate reserves, the essential input for phosphate fertilizer underpinning global food production.',
 'Marokko haelt den Grossteil der weltweit bekannten Phosphatreserven, den essenziellen Rohstoff fuer Phosphatduenger, der die globale Nahrungsmittelproduktion stuetzt.'),

('chilean_copper_belt', 'Chilean Copper Belt (Escondida/Antofagasta)', 'Chilenischer Kupferguertel (Escondida/Antofagasta)', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-70.0,-22.0],[-68.5,-22.0],[-68.5,-24.5],[-70.0,-24.5],[-70.0,-22.0]]]}'::jsonb,
 ARRAY['copper'], ARRAY['AMERICAS-CHILE'], 4,
 '{"share_note": "the largest concentration of copper mines in the worlds top copper-producing country"}'::jsonb,
 'The core of Chile position as the worlds largest copper producer, a supply base central to global electrification and grid-buildout demand.',
 'Der Kern von Chiles Position als weltweit groesster Kupferproduzent, eine Versorgungsbasis, die zentral fuer die globale Elektrifizierung und den Netzausbau ist.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- AGRICULTURAL BELTS (Polygon, coarse hull)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('us_corn_soy_belt', 'US Corn-Soy Belt (Iowa/Illinois Core)', 'US-Mais-Soja-Guertel (Kernzone Iowa/Illinois)', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-96.5,43.5],[-88.0,43.5],[-88.0,38.5],[-96.5,38.5],[-96.5,43.5]]]}'::jsonb,
 ARRAY['corn','soy'], ARRAY['AMERICAS-USA'], 4,
 '{"share_note": "the core of the worlds largest corn and soybean producing region"}'::jsonb,
 'The heart of US grain production, whose harvest and export volumes are a primary driver of global corn and soybean prices.',
 'Das Herz der US-Getreideproduktion, deren Ernte- und Exportvolumen ein Hauptfaktor fuer die globalen Mais- und Sojapreise sind.'),

('mato_grosso_soy_belt', 'Mato Grosso Soy Belt', 'Mato-Grosso-Sojaguertel', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-58.5,-9.0],[-52.5,-9.0],[-52.5,-16.0],[-58.5,-16.0],[-58.5,-9.0]]]}'::jsonb,
 ARRAY['soy'], ARRAY['AMERICAS-BRAZIL'], 4,
 '{"share_note": "Brazils largest soybean-producing state and a top global soy source"}'::jsonb,
 'Brazil largest soybean-producing state, whose expansion has made the country the worlds leading soy exporter, largely to China.',
 'Brasiliens groesster sojaproduzierender Bundesstaat, dessen Expansion das Land zum weltweit fuehrenden Sojaexporteur gemacht hat, vor allem nach China.'),

('pampas_grain_belt', 'Pampas Grain Belt', 'Pampas-Getreideguertel', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-64.5,-31.0],[-58.5,-31.0],[-58.5,-38.5],[-64.5,-38.5],[-64.5,-31.0]]]}'::jsonb,
 ARRAY['grain','soy'], ARRAY[]::text[], 3,
 '{"share_note": "Argentinas fertile core producing the bulk of its grain and soy exports"}'::jsonb,
 'Argentina fertile agricultural core, producing the bulk of the countrys wheat, corn and soybean exports and highly sensitive to export-tax policy shifts.',
 'Argentiniens fruchtbarer landwirtschaftlicher Kern, produziert den Grossteil der Weizen-, Mais- und Sojaexporte des Landes und ist stark sensibel gegenueber Aenderungen der Exportsteuerpolitik.'),

('indonesia_malaysia_palm_oil_belt', 'Indonesian-Malaysian Palm Oil Belt', 'Indonesisch-malaysischer Palmoelguertel', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[97.5,5.5],[118.0,5.5],[118.0,-4.5],[97.5,-4.5],[97.5,5.5]]]}'::jsonb,
 ARRAY['palm_oil'], ARRAY['ASIA-INDONESIA'], 3,
 '{"share_note": "supplies the large majority of the worlds palm oil"}'::jsonb,
 'The Sumatra-Borneo-Peninsular Malaysia plantation belt supplying most of the worlds palm oil, a key vegetable-oil and biodiesel feedstock.',
 'Der Plantagenguertel Sumatra-Borneo-Malaiische Halbinsel liefert den Grossteil des weltweiten Palmoels, ein wichtiger Rohstoff fuer Pflanzenoel und Biodiesel.')

ON CONFLICT (id) DO NOTHING;
