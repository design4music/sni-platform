-- "Oil everything" batch: complete globally-significant oil infrastructure
-- coverage -- major production basins/fields not yet seeded, refining hubs,
-- and export/logistics terminals. See 20260703_strategic_assets.sql for
-- schema. Idempotent: safe to re-run.

-- =========================================================================
-- A. PRODUCTION BASINS / FIELDS (Polygon hulls)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES

('safaniya_field', 'Safaniya Offshore Field', 'Safaniya-Offshorefeld', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[48.55,28.3],[48.85,28.3],[48.85,27.75],[48.55,27.75],[48.55,28.3]]]}'::jsonb,
 ARRAY['oil'], ARRAY['MIDEAST-SAUDI'], 4,
 '{"share_note": "the worlds largest offshore oil field"}'::jsonb,
 'The worlds largest offshore oil field, a major pillar of Saudi Arabia spare production capacity in the northern Gulf.',
 'Das weltweit groesste Offshore-Oelfeld, eine wichtige Saeule der saudischen Foerderreserve im noerdlichen Golf.'),

('rumaila_basra_fields', 'Rumaila-Basra Fields', 'Rumaila-Basra-Felder', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[46.9,31.2],[47.9,31.2],[47.9,30.2],[46.9,30.2],[46.9,31.2]]]}'::jsonb,
 ARRAY['oil'], ARRAY['MIDEAST-IRAQ'], 4,
 '{"share_note": "the core cluster of fields underpinning most of Iraqs crude output"}'::jsonb,
 'The supergiant southern Iraq field cluster that generates the large majority of Baghdad oil revenue and export volume.',
 'Der suedirakische Superfeld-Cluster, der den Grossteil der Oeleinnahmen und Exportmenge Bagdads erzeugt.'),

('burgan_field', 'Burgan Field', 'Burgan-Feld', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[47.85,29.25],[48.15,29.25],[48.15,28.85],[47.85,28.85],[47.85,29.25]]]}'::jsonb,
 ARRAY['oil'], ARRAY[]::text[], 4,
 '{"share_note": "one of the largest conventional oil fields ever discovered"}'::jsonb,
 'The second-largest conventional oil field in the world, the backbone of Kuwaiti production and state revenue.',
 'Das zweitgroesste konventionelle Oelfeld der Welt, das Rueckgrat der kuwaitischen Foerderung und Staatseinnahmen.'),

('upper_zakum_field', 'Upper Zakum Field', 'Upper-Zakum-Feld', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[53.55,25.15],[53.85,25.15],[53.85,24.85],[53.55,24.85],[53.55,25.15]]]}'::jsonb,
 ARRAY['oil'], ARRAY['MIDEAST-GULF'], 3,
 '{"share_note": "one of the largest offshore oil fields in the world"}'::jsonb,
 'A major offshore field west of Abu Dhabi and a core source of UAE crude output and expansion capacity.',
 'Ein bedeutendes Offshore-Feld westlich von Abu Dhabi und eine zentrale Quelle der Foerderung und Ausbaukapazitaet der VAE.'),

('tengiz_kashagan_fields', 'Tengiz-Kashagan Fields', 'Tengiz-Kaschagan-Felder', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[50.0,46.9],[52.4,46.9],[52.4,45.6],[50.0,45.6],[50.0,46.9]]]}'::jsonb,
 ARRAY['oil'], ARRAY[]::text[], 4,
 '{"share_note": "together the largest oil development in Kazakhstan and one of the largest globally in recent decades"}'::jsonb,
 'Kazakhstan two supergiant Caspian fields, whose output depends heavily on the CPC pipeline route through Russian territory to reach world markets.',
 'Kasachstans zwei kaspische Superfelder, deren Foerderung stark von der CPC-Pipelineroute durch russisches Territorium abhaengt, um Weltmaerkte zu erreichen.'),

('santos_presalt_basin', 'Santos Pre-Salt Basin', 'Santos-Pre-Salt-Becken', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-44.5,-23.5],[-41.5,-23.5],[-41.5,-27.0],[-44.5,-27.0],[-44.5,-23.5]]]}'::jsonb,
 ARRAY['oil','gas'], ARRAY['AMERICAS-BRAZIL'], 4,
 '{"share_note": "the deepwater discovery that made Brazil a top-five global oil producer"}'::jsonb,
 'The offshore pre-salt fields that turned Brazil into a major oil exporter, underpinning Petrobras production growth for the next decade.',
 'Die Offshore-Pre-Salt-Felder, die Brasilien zu einem bedeutenden Oelexporteur gemacht haben, Grundlage fuer Petrobras Foerderwachstum im naechsten Jahrzehnt.'),

('stabroek_block', 'Stabroek Block', 'Stabroek-Block', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-58.2,8.3],[-56.4,8.3],[-56.4,6.6],[-58.2,6.6],[-58.2,8.3]]]}'::jsonb,
 ARRAY['oil'], ARRAY['AMERICAS-GUYANA'], 3,
 '{"share_note": "the fastest-growing major offshore oil discovery of the last decade"}'::jsonb,
 'The offshore discovery that turned Guyana into one of the fastest-growing oil producers on earth within a single decade.',
 'Die Offshore-Entdeckung, die Guyana innerhalb eines einzigen Jahrzehnts zu einem der am schnellsten wachsenden Oelproduzenten der Welt gemacht hat.'),

('niger_delta_basin', 'Niger Delta Basin', 'Niger-Delta-Becken', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[4.5,6.0],[8.5,6.0],[8.5,3.8],[4.5,3.8],[4.5,6.0]]]}'::jsonb,
 ARRAY['oil','gas'], ARRAY['AFRICA-NIGERIA'], 4,
 '{"share_note": "the source of nearly all Nigerian crude output, onshore and offshore"}'::jsonb,
 'Africa largest oil-producing region, chronically exposed to pipeline sabotage, artisanal theft and militant unrest that repeatedly cut Nigerian output.',
 'Afrikas groesste oelfoerdernde Region, chronisch anfaellig fuer Pipeline-Sabotage, informellen Oeldiebstahl und militante Unruhen, die die nigerianische Foerderung wiederholt gedrosselt haben.'),

('sirte_basin', 'Sirte Basin', 'Sirte-Becken', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[17.5,31.5],[21.5,31.5],[21.5,27.5],[17.5,27.5],[17.5,31.5]]]}'::jsonb,
 ARRAY['oil'], ARRAY[]::text[], 3,
 '{"share_note": "holds the large majority of Libyas proven oil reserves"}'::jsonb,
 'Libya principal oil-producing basin, where output has repeatedly been shut in or fought over amid the countrys ongoing civil conflict.',
 'Libyens wichtigstes Oelfoerderbecken, dessen Produktion inmitten des andauernden Buergerkriegs im Land wiederholt stillgelegt oder umkaempft war.'),

('athabasca_oil_sands', 'Athabasca Oil Sands', 'Athabasca-Oelsande', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-113.5,58.0],[-110.5,58.0],[-110.5,55.5],[-113.5,55.5],[-113.5,58.0]]]}'::jsonb,
 ARRAY['oil'], ARRAY['AMERICAS-CANADA'], 4,
 '{"share_note": "the largest oil sands deposit in the world and the core of Canadas oil exports"}'::jsonb,
 'The worlds largest oil sands deposit, the source of the large majority of Canadian crude exports, almost entirely to the United States.',
 'Die weltweit groesste Oelsand-Lagerstaette, Quelle des Grossteils der kanadischen Rohoelexporte, fast ausschliesslich in die USA.'),

('bakken_shale', 'Bakken Shale', 'Bakken-Schieferformation', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-104.0,48.9],[-101.5,48.9],[-101.5,46.8],[-104.0,46.8],[-104.0,48.9]]]}'::jsonb,
 ARRAY['oil','gas'], ARRAY['AMERICAS-USA'], 3,
 '{"share_note": "one of the largest US shale oil plays outside the Permian"}'::jsonb,
 'A major North Dakota shale play and one of the largest contributors to US oil output outside the Permian Basin.',
 'Ein bedeutendes Schieferoelgebiet in North Dakota und einer der groessten Beitraege zur US-Oelfoerderung ausserhalb des Perm-Beckens.'),

('daqing_field', 'Daqing Field', 'Daqing-Feld', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[124.6,46.9],[125.4,46.9],[125.4,46.2],[124.6,46.2],[124.6,46.9]]]}'::jsonb,
 ARRAY['oil'], ARRAY['ASIA-CHINA'], 3,
 '{"share_note": "historically Chinas largest and longest-producing onshore oil field"}'::jsonb,
 'Chinas largest and longest-producing onshore field, historically the backbone of domestic crude output and a symbol of state industrial policy.',
 'Chinas groesstes und am laengsten foerderndes Onshore-Feld, historisch das Rueckgrat der heimischen Oelfoerderung und Symbol staatlicher Industriepolitik.'),

('sakhalin_projects', 'Sakhalin Oil and Gas Projects', 'Sachalin-Oel-und-Gasprojekte', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[142.5,52.5],[144.5,52.5],[144.5,50.0],[142.5,50.0],[142.5,52.5]]]}'::jsonb,
 ARRAY['oil','gas'], ARRAY['EUROPE-RUSSIA'], 3,
 '{"share_note": "Russias main Pacific-facing offshore oil and gas production and LNG export base"}'::jsonb,
 'Russia Far East offshore oil and gas hub, its LNG and crude exports to Japan and China surviving despite Western sanctions on the Sakhalin ventures.',
 'Russlands fernoestlicher Offshore-Oel- und Gasknotenpunkt, dessen LNG- und Rohoelexporte nach Japan und China trotz westlicher Sanktionen gegen die Sachalin-Projekte fortbestehen.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- B. REFINING HUBS (Point, facility)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES

('jurong_island_refining', 'Jurong Island Refining-Petrochemical Complex', 'Raffinerie-Petrochemie-Komplex Jurong Island', 'facility',
 '{"type":"Point","coordinates":[103.71,1.27]}'::jsonb,
 ARRAY['oil','refined_products'], ARRAY['ASIA-SINGAPORE'], 4,
 '{"share_note": "one of the worlds largest integrated refining and petrochemical hubs"}'::jsonb,
 'Singapore reclaimed-island refining and petrochemical complex, a pricing and supply hub for Asian refined product markets.',
 'Singapurs aufgeschuetteter Raffinerie- und Petrochemiekomplex auf Jurong Island, ein Preis- und Versorgungsknotenpunkt fuer asiatische Mineraloelmaerkte.'),

('us_gulf_coast_refining_corridor', 'US Gulf Coast Refining Corridor', 'US-Golfkuesten-Raffineriekorridor', 'facility',
 '{"type":"Point","coordinates":[-94.0,29.9]}'::jsonb,
 ARRAY['oil','refined_products'], ARRAY['AMERICAS-USA'], 5,
 '{"share_note": "the worlds densest concentration of refining capacity, spanning Houston, Port Arthur and Lake Charles"}'::jsonb,
 'The Houston-Port Arthur-Lake Charles corridor, the worlds densest refining cluster and the backbone of US fuel supply and product exports.',
 'Der Korridor Houston-Port Arthur-Lake Charles, der weltweit dichteste Raffineriecluster und das Rueckgrat der US-Treibstoffversorgung und Produktexporte.'),

('ruwais_refinery', 'Ruwais Refinery', 'Raffinerie Ruwais', 'facility',
 '{"type":"Point","coordinates":[52.73,24.11]}'::jsonb,
 ARRAY['oil','refined_products'], ARRAY['MIDEAST-GULF'], 3,
 '{"share_note": "one of the largest single-site refining and petrochemical complexes in the Middle East"}'::jsonb,
 'Abu Dhabi flagship refining and petrochemical hub, central to the UAE downstream diversification strategy away from crude exports alone.',
 'Abu Dhabis Vorzeige-Raffinerie- und Petrochemiezentrum, zentral fuer die Downstream-Diversifizierungsstrategie der VAE weg vom reinen Rohoelexport.'),

('yanbu_refining_hub', 'Yanbu Refining Hub', 'Raffineriezentrum Yanbu', 'facility',
 '{"type":"Point","coordinates":[38.06,24.09]}'::jsonb,
 ARRAY['oil','refined_products'], ARRAY['MIDEAST-SAUDI'], 3,
 '{"share_note": "Saudi Arabias principal Red Sea refining and petrochemical export hub"}'::jsonb,
 'Saudi Arabia main Red Sea refining and export hub, fed by crude piped overland from the Eastern Province, bypassing the Strait of Hormuz.',
 'Saudi-Arabiens wichtigstes Rotmeer-Raffinerie- und Exportzentrum, versorgt mit per Pipeline aus der Ostprovinz transportiertem Rohoel unter Umgehung der Strasse von Hormus.'),

('zhenhai_zhoushan_refining', 'Zhenhai-Zhoushan Refining Complex', 'Raffineriekomplex Zhenhai-Zhoushan', 'facility',
 '{"type":"Point","coordinates":[121.9,29.95]}'::jsonb,
 ARRAY['oil','refined_products'], ARRAY['ASIA-CHINA'], 3,
 '{"share_note": "one of Chinas largest coastal refining and crude storage complexes"}'::jsonb,
 'A major eastern China refining and strategic crude storage complex, positioned to receive tanker imports feeding the Yangtze River Delta economy.',
 'Ein bedeutender ostchinesischer Raffinerie- und strategischer Rohoellagerkomplex, positioniert zum Empfang von Tankerimporten fuer die Wirtschaft des Jangtse-Deltas.'),

('paraguana_refining_center', 'Paraguana Refining Center', 'Raffineriezentrum Paraguana', 'facility',
 '{"type":"Point","coordinates":[-70.02,11.77]}'::jsonb,
 ARRAY['oil','refined_products'], ARRAY['AMERICAS-VENEZUELA'], 2,
 '{"share_note": "historically one of the largest refining complexes in the world, now running well below capacity"}'::jsonb,
 'Once one of the worlds largest refining complexes, now running far below capacity after years of underinvestment and US sanctions, yet still central to any Venezuelan oil recovery scenario.',
 'Einst einer der groessten Raffineriekomplexe der Welt, laeuft nach Jahren der Unterinvestition und US-Sanktionen heute weit unter Kapazitaet, bleibt aber zentral fuer jedes venezolanische Oel-Erholungsszenario.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- C. EXPORT / LOGISTICS TERMINALS (Point, port)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES

('kharg_island_terminal', 'Kharg Island Terminal', 'Terminal Khark-Insel', 'port',
 '{"type":"Point","coordinates":[50.31,29.23]}'::jsonb,
 ARRAY['oil'], ARRAY['MIDEAST-IRAN'], 4,
 '{"share_note": "loads the large majority of Irans crude oil exports"}'::jsonb,
 'Iran principal crude export terminal in the northern Gulf, loading nearly all of the countrys oil exports and a recurring target in escalation scenarios.',
 'Irans wichtigstes Rohoel-Exportterminal im noerdlichen Golf, verlaedt fast alle Oelexporte des Landes und ein wiederkehrendes Ziel in Eskalationsszenarien.'),

('basra_oil_terminal', 'Basra Oil Terminal (Al Basrah)', 'Oelterminal Basra (Al-Basra)', 'port',
 '{"type":"Point","coordinates":[48.8,29.68]}'::jsonb,
 ARRAY['oil'], ARRAY['MIDEAST-IRAQ'], 4,
 '{"share_note": "loads the large majority of Iraqs crude oil exports"}'::jsonb,
 'Iraq main offshore crude export terminal in the northern Gulf, the loading point for most of Baghdad oil revenue.',
 'Iraks wichtigstes Offshore-Rohoel-Exportterminal im noerdlichen Golf, der Verladepunkt fuer den Grossteil der Oeleinnahmen Bagdads.'),

('ceyhan_terminal', 'Ceyhan Terminal', 'Terminal Ceyhan', 'port',
 '{"type":"Point","coordinates":[35.95,36.87]}'::jsonb,
 ARRAY['oil'], ARRAY['MIDEAST-TURKEY'], 3,
 '{"share_note": "the Mediterranean terminus of the BTC pipeline and a key non-Hormuz export point"}'::jsonb,
 'The Mediterranean terminus of the Baku-Tbilisi-Ceyhan pipeline, giving Caspian crude a route to world markets that bypasses both Russia and the Strait of Hormuz.',
 'Der Mittelmeer-Endpunkt der Baku-Tiflis-Ceyhan-Pipeline, der kaspischem Rohoel einen Weg zu den Weltmaerkten unter Umgehung sowohl Russlands als auch der Strasse von Hormus verschafft.'),

('fujairah_hub', 'Fujairah Bunkering-Export Hub', 'Bunker- und Exportzentrum Fudschaira', 'port',
 '{"type":"Point","coordinates":[56.37,25.12]}'::jsonb,
 ARRAY['oil'], ARRAY['MIDEAST-GULF'], 4,
 '{"share_note": "a major bunkering hub and one of the few UAE export points that lies outside the Strait of Hormuz"}'::jsonb,
 'A UAE export and bunkering hub on the Gulf of Oman coast, valued precisely because it lies outside the Strait of Hormuz and can keep loading if the strait is closed.',
 'Ein Export- und Bunkerzentrum der VAE an der Kueste des Golfs von Oman, geschaetzt gerade weil es ausserhalb der Strasse von Hormus liegt und bei einer Sperrung weiter beladen werden kann.'),

('kozmino_terminal', 'Kozmino Terminal', 'Terminal Koszmino', 'port',
 '{"type":"Point","coordinates":[133.0,42.73]}'::jsonb,
 ARRAY['oil'], ARRAY['EUROPE-RUSSIA'], 3,
 '{"share_note": "the Pacific terminus of the ESPO pipeline and Russias main oil export gateway to Asia"}'::jsonb,
 'The Pacific terminus of the ESPO pipeline, Russia main oil export gateway to Asian buyers and a key outlet for crude that no longer flows to Europe.',
 'Der pazifische Endpunkt der ESPO-Pipeline, Russlands wichtigstes Oel-Exporttor zu asiatischen Abnehmern und ein zentraler Ausgang fuer Rohoel, das nicht mehr nach Europa fliesst.'),

('primorsk_ust_luga_terminals', 'Primorsk-Ust-Luga Terminals', 'Terminals Primorsk-Ust-Luga', 'port',
 '{"type":"Point","coordinates":[28.68,60.32]}'::jsonb,
 ARRAY['oil'], ARRAY['EUROPE-RUSSIA'], 4,
 '{"share_note": "Russias main Baltic Sea crude export terminals and the principal departure point for shadow-fleet tankers"}'::jsonb,
 'Russia primary Baltic Sea oil export terminals, the main departure point for the aging shadow-fleet tankers used to move sanctioned crude around the price cap.',
 'Russlands wichtigste Oel-Exportterminals an der Ostsee, der wichtigste Abfahrtspunkt fuer die alternde Schattenflotte, die sanktioniertes Rohoel am Preisdeckel vorbei transportiert.'),

('corpus_christi_export_hub', 'Corpus Christi Export Hub', 'Exportzentrum Corpus Christi', 'port',
 '{"type":"Point","coordinates":[-97.39,27.8]}'::jsonb,
 ARRAY['oil'], ARRAY['AMERICAS-USA'], 4,
 '{"share_note": "the largest US crude oil export port by volume"}'::jsonb,
 'The largest US crude export port, the main outlet through which Permian Basin output reaches international tanker markets.',
 'Der groesste US-Rohoel-Exporthafen, der Hauptausgang, ueber den die Foerderung des Perm-Beckens internationale Tankermaerkte erreicht.'),

('cushing_storage_hub', 'Cushing Storage Hub', 'Lagerzentrum Cushing', 'facility',
 '{"type":"Point","coordinates":[-96.77,35.98]}'::jsonb,
 ARRAY['oil'], ARRAY['AMERICAS-USA'], 3,
 '{"share_note": "the physical delivery point for the WTI crude oil futures contract"}'::jsonb,
 'The Oklahoma tank farm that serves as the physical delivery point for WTI futures, making its storage levels a closely watched signal for global oil pricing.',
 'Der Tanklager-Standort in Oklahoma, der als physischer Lieferpunkt fuer WTI-Futures dient, wodurch seine Lagerbestaende ein genau beobachtetes Signal fuer die globale Oelpreisbildung sind.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- SUGGESTED FN ASSIGNMENTS (review before trusting)
-- =========================================================================

UPDATE friction_nodes SET affected_asset_ids = (
  SELECT ARRAY(SELECT DISTINCT unnest(affected_asset_ids || ARRAY['kharg_island_terminal','fujairah_hub']))
) WHERE id = 'iran_theater';

UPDATE friction_nodes SET affected_asset_ids = (
  SELECT ARRAY(SELECT DISTINCT unnest(affected_asset_ids || ARRAY['paraguana_refining_center']))
) WHERE id = 'latam_theater';

UPDATE friction_nodes SET affected_asset_ids = (
  SELECT ARRAY(SELECT DISTINCT unnest(affected_asset_ids || ARRAY['primorsk_ust_luga_terminals']))
) WHERE id = 'russia_europe_theater';
