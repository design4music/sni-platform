-- Seed ~15 agriculture, food and fertilizer strategic assets: grain and
-- rice belts, offshore fisheries, and potash/phosphate fertilizer sites.
-- Static ground-truth layer that friction nodes press on (see
-- 20260703_strategic_assets.sql for schema). Idempotent: safe to re-run.

-- =========================================================================
-- GRAIN / RICE BELTS (Polygon, coarse hull)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES

('punjab_haryana_wheat_rice_belt', 'Punjab-Haryana Wheat-Rice Belt', 'Punjab-Haryana Weizen-Reis-Guertel', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[73.0,32.2],[77.0,32.2],[77.0,28.5],[73.0,28.5],[73.0,32.2]]]}'::jsonb,
 ARRAY['wheat','rice'], ARRAY['ASIA-INDIA','ASIA-PAKISTAN'], 4,
 '{"share_note": "the Green Revolution heartland straddling the India-Pakistan border, feeding both national food-grain reserves"}'::jsonb,
 'The irrigated breadbasket that anchors food security for roughly 1.5 billion people across South Asia, now straining under falling groundwater tables.',
 'Die bewaesserte Kornkammer, die die Ernaehrungssicherheit fuer rund 1,5 Milliarden Menschen in Suedasien sichert, nun unter sinkenden Grundwasserspiegeln leidend.'),

('north_china_plain', 'North China Plain', 'Nordchinesische Tiefebene', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[113.0,38.0],[118.0,38.0],[118.0,33.0],[113.0,33.0],[113.0,38.0]]]}'::jsonb,
 ARRAY['wheat','corn'], ARRAY['ASIA-CHINA'], 4,
 '{"share_note": "produces the majority of Chinas wheat and a large share of its corn"}'::jsonb,
 'Chinas largest wheat and corn producing region; any shortfall here forces Beijing onto world grain markets, moving global prices.',
 'Chinas groesste Weizen- und Maisanbauregion; jeder Ernteausfall zwingt Peking auf die Weltgetreidemaerkte und bewegt die globalen Preise.'),

('mekong_delta_rice', 'Mekong Delta Rice Belt', 'Mekong-Delta-Reisguertel', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[104.5,10.8],[106.8,10.8],[106.8,8.5],[104.5,8.5],[104.5,10.8]]]}'::jsonb,
 ARRAY['rice'], ARRAY['ASIA-SOUTHEAST'], 4,
 '{"share_note": "Vietnams principal rice-growing region and one of the worlds top rice export sources"}'::jsonb,
 'Vietnams rice export engine, increasingly threatened by saltwater intrusion and upstream Mekong dam operations that starve the delta of sediment and fresh water.',
 'Vietnams Reisexport-Motor, zunehmend bedroht durch Versalzung und stromaufwaerts gelegene Mekong-Staudaemme, die dem Delta Sediment und Suesswasser entziehen.'),

('chao_phraya_rice_basin', 'Chao Phraya Rice Basin', 'Chao-Phraya-Reisbecken', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[99.5,16.5],[101.2,16.5],[101.2,13.5],[99.5,13.5],[99.5,16.5]]]}'::jsonb,
 ARRAY['rice'], ARRAY['ASIA-SOUTHEAST'], 3,
 '{"share_note": "Thailands central rice bowl and a major global rice export base"}'::jsonb,
 'Thailands central river-basin rice bowl, historically one of the worlds largest rice exporters and a swing supplier when other exporters restrict shipments.',
 'Thailands zentrales Flussbecken-Reisgebiet, historisch einer der groessten Reisexporteure der Welt und Ersatzlieferant, wenn andere Exporteure Lieferungen einschraenken.'),

('canadian_prairies_wheat', 'Canadian Prairies Wheat Belt', 'Kanadischer Praerie-Weizenguertel', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-110.0,53.0],[-97.0,53.0],[-97.0,49.0],[-110.0,49.0],[-110.0,53.0]]]}'::jsonb,
 ARRAY['wheat'], ARRAY['AMERICAS-CANADA'], 3,
 '{"share_note": "the core of Canadas wheat production and one of the top wheat export sources globally"}'::jsonb,
 'Canadas prairie wheat belt is a top-five global wheat exporter, giving Ottawa outsized leverage in world grain markets whenever Black Sea supply is disrupted.',
 'Kanadas Praerie-Weizenguertel gehoert zu den fuenf groessten Weizenexporteuren der Welt und verschafft Ottawa erheblichen Einfluss auf die Weltgetreidemaerkte, sobald die Schwarzmeer-Versorgung gestoert ist.'),

('australian_wheat_belt', 'Australian Wheat Belt (WA-NSW)', 'Australischer Weizenguertel (WA-NSW)', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[115.5,-30.0],[149.0,-30.0],[149.0,-38.0],[115.5,-38.0],[115.5,-30.0]]]}'::jsonb,
 ARRAY['wheat'], ARRAY['OCEANIA-AUSTRALIA'], 3,
 '{"share_note": "spans Western Australia and New South Wales, together supplying most of Australias wheat exports"}'::jsonb,
 'Australias dryland wheat belt, spanning Western Australia to New South Wales, is a top global wheat exporter whose output swings sharply with El Nino drought cycles.',
 'Australiens Trockenland-Weizenguertel von Westaustralien bis New South Wales ist ein fuehrender Weizenexporteur, dessen Ertrag stark mit El-Nino-Duerrezyklen schwankt.'),

('kansas_oklahoma_winter_wheat', 'Kansas-Oklahoma Winter Wheat Belt', 'Kansas-Oklahoma Winterweizenguertel', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-102.0,40.0],[-95.0,40.0],[-95.0,34.0],[-102.0,34.0],[-102.0,40.0]]]}'::jsonb,
 ARRAY['wheat'], ARRAY['AMERICAS-USA'], 3,
 '{"share_note": "the historic core of US hard red winter wheat production"}'::jsonb,
 'The traditional heart of US hard red winter wheat, a benchmark grade for global wheat pricing and a bellwether for Great Plains drought stress.',
 'Das traditionelle Kernland des US-amerikanischen Hartweizens (Hard Red Winter Wheat), eine Referenzsorte fuer die globale Weizenpreisbildung und ein Fruehindikator fuer Duerrestress in den Great Plains.'),

('cerrado_expansion_zone', 'Cerrado Expansion Zone (MATOPIBA)', 'Cerrado-Expansionszone (MATOPIBA)', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-48.0,-6.0],[-42.0,-6.0],[-42.0,-14.0],[-48.0,-14.0],[-48.0,-6.0]]]}'::jsonb,
 ARRAY['soy','corn'], ARRAY['AMERICAS-BRAZIL'], 3,
 '{"share_note": "the Maranhao-Tocantins-Piaui-Bahia frontier, Brazils fastest-growing soy and corn frontier beyond Mato Grosso"}'::jsonb,
 'Brazils newest agricultural frontier beyond Mato Grosso, converting savanna into soy and corn cropland at a pace that draws mounting deforestation and land-rights scrutiny.',
 'Brasiliens neueste Agrarfront jenseits von Mato Grosso, die Savanne in rasantem Tempo in Soja- und Maisanbauflaeche umwandelt und zunehmend wegen Entwaldung und Landrechten kritisiert wird.'),

('nile_delta_agriculture', 'Nile Delta Agriculture', 'Nildelta-Landwirtschaft', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[30.0,31.7],[32.5,31.7],[32.5,30.0],[30.0,30.0],[30.0,31.7]]]}'::jsonb,
 ARRAY['wheat','rice'], ARRAY['MIDEAST-EGYPT','MIDEAST-EGYPT'], 3,
 '{"share_note": "Egypts most fertile and densely farmed region, almost entirely dependent on Nile floodwater and irrigation"}'::jsonb,
 'Egypts food-producing heartland, wholly dependent on Nile flow, making it acutely exposed to any reduction in upstream water from the Grand Ethiopian Renaissance Dam.',
 'Aegyptens landwirtschaftliches Kernland, vollstaendig abhaengig vom Nilwasser, und daher besonders anfaellig fuer jede Verringerung der Wasserzufuhr durch den Grand-Ethiopian-Renaissance-Staudamm.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- FISHERIES (Polygon, offshore grounds)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES

('peruvian_anchoveta_grounds', 'Peruvian Anchoveta Grounds', 'Peruanische Sardellen-Fanggruende', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-82.0,-4.0],[-76.0,-4.0],[-76.0,-18.0],[-82.0,-18.0],[-82.0,-4.0]]]}'::jsonb,
 ARRAY['fish'], ARRAY['AMERICAS-PERU'], 3,
 '{"share_note": "the worlds largest single-species fishery by tonnage, feeding the global fishmeal and fish oil market"}'::jsonb,
 'The worlds biggest single-species fishery, feeding global aquaculture and livestock feed through fishmeal exports, and one that collapses almost completely in strong El Nino years.',
 'Die weltweit groesste Einzelart-Fischerei, die ueber Fischmehlexporte die globale Aquakultur und Tierfutterproduktion versorgt und in starken El-Nino-Jahren fast vollstaendig zusammenbricht.'),

('west_african_fishing_grounds', 'West African Fishing Grounds', 'Westafrikanische Fanggruende', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-20.0,21.0],[-16.0,21.0],[-16.0,12.0],[-20.0,12.0],[-20.0,21.0]]]}'::jsonb,
 ARRAY['fish'], ARRAY['AFRICA-SAHEL'], 3,
 '{"share_note": "the Senegal-Mauritania upwelling zone, a key protein source under heavy pressure from foreign industrial fleets"}'::jsonb,
 'A rich upwelling fishery off Senegal and Mauritania that feeds local food security, now depleted by foreign industrial trawlers operating under opaque licensing deals.',
 'Eine ergiebige Auftriebsfischerei vor Senegal und Mauretanien, die die lokale Ernaehrungssicherung stuetzt, nun durch auslaendische Industrietrawler unter undurchsichtigen Lizenzvereinbarungen dezimiert.'),

('south_pacific_tuna_belt', 'South Pacific Tuna Belt', 'Suedpazifischer Thunfischguertel', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[160.0,5.0],[179.0,5.0],[179.0,-15.0],[160.0,-15.0],[160.0,5.0]]]}'::jsonb,
 ARRAY['fish'], ARRAY[]::text[], 2,
 '{"share_note": "one of the last large healthy tuna stocks, managed by Pacific Island states through the Nauru Agreement vessel-day scheme"}'::jsonb,
 'A vast tuna fishery that Pacific Island nations license through a shared vessel-day scheme, giving small states rare leverage over distant-water fishing fleets from China, the US and the EU.',
 'Eine riesige Thunfischfischerei, die pazifische Inselstaaten ueber ein gemeinsames Schiffstage-System lizenzieren, was kleinen Staaten seltenen Einfluss auf Fernfischereiflotten aus China, den USA und der EU verschafft.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- FERTILIZER (Point, mine/processing site)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES

('belarus_potash_soligorsk', 'Belarus Potash (Soligorsk)', 'Belarus-Kali (Salihorsk)', 'facility',
 '{"type":"Point","coordinates":[27.55,52.8]}'::jsonb,
 ARRAY['potash'], ARRAY['EUROPE-RUSSIA'], 4,
 '{"share_note": "Belaruskali Soligorsk complex, historically one of the worlds top three potash exporters", "sanctions_note": "under EU and US sanctions since 2021-2022, rerouting exports through Russian ports"}'::jsonb,
 'The Belaruskali potash complex at Soligorsk was a top global fertilizer exporter until Western sanctions over the Lukashenko regime forced a costly rerouting of trade through Russia.',
 'Der Belaruskali-Kalikomplex in Salihorsk war ein weltweit fuehrender Duengemittelexporteur, bis westliche Sanktionen gegen das Lukaschenko-Regime eine kostspielige Umleitung des Handels ueber Russland erzwangen.'),

('urals_potash_berezniki_solikamsk', 'Urals Potash (Berezniki-Solikamsk)', 'Ural-Kali (Beresniki-Solikamsk)', 'facility',
 '{"type":"Point","coordinates":[56.25,59.4]}'::jsonb,
 ARRAY['potash'], ARRAY['EUROPE-RUSSIA'], 4,
 '{"share_note": "Uralkali Berezniki-Solikamsk mines, one of the largest potash basins in the world"}'::jsonb,
 'Uralkalis potash mines feed a large share of world fertilizer supply; sinkhole collapses over old workings and sanctions exposure both threaten continuity of exports that Latin American and Asian farmers depend on.',
 'Uralkalis Kaliminen versorgen einen Grossteil der weltweiten Duengemittelnachfrage; Erdeinbrueche ueber alten Abbaufeldern und Sanktionsrisiken gefaehrden gleichermassen die Exporte, auf die Landwirte in Lateinamerika und Asien angewiesen sind.'),

('maaden_phosphate_ras_al_khair', 'Maaden Phosphate Complex (Ras Al Khair)', 'Maaden-Phosphatkomplex (Ras Al Khair)', 'facility',
 '{"type":"Point","coordinates":[48.15,27.5]}'::jsonb,
 ARRAY['phosphate'], ARRAY['MIDEAST-SAUDI'], 2,
 '{"share_note": "Saudi Arabias integrated phosphate and ammonia export hub, part of the Maaden state mining group"}'::jsonb,
 'Saudi Arabias Ras Al Khair complex processes phosphate rock into fertilizer for export, positioning the kingdom as a rising alternative to Moroccan and Chinese phosphate supply.',
 'Saudi-Arabiens Komplex in Ras Al Khair verarbeitet Phosphatgestein zu Duengemitteln fuer den Export und positioniert das Koenigreich als aufstrebende Alternative zur marokkanischen und chinesischen Phosphatversorgung.')

ON CONFLICT (id) DO NOTHING;
