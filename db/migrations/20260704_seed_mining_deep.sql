-- Critical minerals deep-dive: ~18 additional mining assets closing gaps in
-- copper, iron ore, rare earths, uranium, nickel, lithium, bauxite, gold,
-- tin and graphite. See 20260703_strategic_assets.sql for schema.
-- Does not duplicate existing mining ids (pilbara_iron_belt,
-- australian_lithium_belt, atacama_lithium_triangle, chilean_copper_belt,
-- katanga_copper_belt, guinea_bauxite_belt, bayan_obo_rare_earths,
-- norilsk_nickel_palladium, bushveld_platinum_complex, oyu_tolgoi_copper_gold,
-- kazakh_uranium_belt, saskatchewan_potash_belt, moroccan_phosphate_plateau,
-- indonesian_nickel_belt). Idempotent: safe to re-run.

-- =========================================================================
-- COPPER
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('grasberg_mine', 'Grasberg Mine', 'Grasberg-Mine', 'facility',
 '{"type":"Point","coordinates":[137.11,-4.06]}'::jsonb,
 ARRAY['copper','gold'], ARRAY['ASIA-SOUTHEAST'], 4,
 '{"share_note": "one of the largest copper and gold mines in the world, operated by Freeport-McMoRan with Indonesian state co-ownership"}'::jsonb,
 'One of the largest copper and gold mines on earth, high in the Papuan highlands; Freeport-McMoRan operating rights and Jakarta growing ownership stake have repeatedly been renegotiated under political pressure.',
 'Eine der groessten Kupfer- und Goldminen der Welt, hoch im papuanischen Hochland; die Betriebsrechte von Freeport-McMoRan und Jakartas wachsender Eigentumsanteil wurden wiederholt unter politischem Druck neu verhandelt.'),

('cobre_panama', 'Cobre Panama Mine', 'Cobre-Panama-Mine', 'facility',
 '{"type":"Point","coordinates":[-80.62,9.07]}'::jsonb,
 ARRAY['copper'], ARRAY['AMERICAS-CENTRAL-AMERICA'], 3,
 '{"share_note": "one of the largest new copper mines built this century, idled since 2023"}'::jsonb,
 'A major First Quantum copper mine forced shut in late 2023 after Panama Supreme Court ruled its concession unconstitutional following mass protests; the site remains idle and contested, removing significant copper supply from the market.',
 'Eine bedeutende Kupfermine von First Quantum, die Ende 2023 nach einem Urteil des panamaischen Obersten Gerichts zur Verfassungswidrigkeit ihrer Konzession infolge Massenprotesten stillgelegt wurde; die Anlage bleibt ungenutzt und umstritten und entzieht dem Markt eine erhebliche Kupferversorgung.'),

('southern_peru_copper_belt', 'Southern Peru Copper Belt', 'Suedperuanischer Kupferguertel', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-72.3,-14.5],[-71.0,-14.5],[-71.0,-16.8],[-72.3,-16.8],[-72.3,-14.5]]]}'::jsonb,
 ARRAY['copper'], ARRAY['AMERICAS-PERU'], 4,
 '{"share_note": "hosts Cerro Verde and Las Bambas, among Perus largest copper mines"}'::jsonb,
 'The Arequipa-Apurimac mining corridor hosting Cerro Verde and Las Bambas, Peru top copper producers; chronic community blockades over water and land rights have repeatedly halted output and transport.',
 'Der Bergbaukorridor Arequipa-Apurimac mit Cerro Verde und Las Bambas, Perus fuehrenden Kupferproduzenten; chronische Blockaden lokaler Gemeinden wegen Wasser- und Landrechten haben Foerderung und Transport wiederholt lahmgelegt.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- IRON ORE
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('simandou_iron_ore', 'Simandou Iron Ore', 'Simandou-Eisenerz', 'facility',
 '{"type":"Point","coordinates":[-8.8,8.5]}'::jsonb,
 ARRAY['iron_ore'], ARRAY['AFRICA-WEST'], 4,
 '{"share_note": "the largest untapped high-grade iron ore deposit in the world"}'::jsonb,
 'The largest untapped high-grade iron ore deposit on earth, developed with heavy Chinese state financing and infrastructure; first exports are set to reshape the seaborne iron ore trade long dominated by Australia and Brazil.',
 'Die groesste unerschlossene hochgradige Eisenerzlagerstaette der Welt, mit massiver chinesischer Staatsfinanzierung und Infrastruktur entwickelt; erste Exporte duerften den seewaertigen Eisenerzhandel neu ordnen, der bisher von Australien und Brasilien dominiert wird.'),

('carajas_mine', 'Carajas Mine', 'Carajas-Mine', 'facility',
 '{"type":"Point","coordinates":[-50.35,-6.0]}'::jsonb,
 ARRAY['iron_ore'], ARRAY['AMERICAS-BRAZIL'], 4,
 '{"share_note": "the largest iron ore mine in the world, operated by Vale"}'::jsonb,
 'The worlds largest iron ore mine, operated by Vale in the Amazon interior; its output underpins Brazil position as the second-largest seaborne iron ore exporter after Australia.',
 'Die groesste Eisenerzmine der Welt, betrieben von Vale im Amazonas-Hinterland; ihre Foerderung untermauert Brasiliens Position als zweitgroesster seewaertiger Eisenerzexporteur nach Australien.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- RARE EARTHS
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('mountain_pass_mine', 'Mountain Pass Mine', 'Mountain-Pass-Mine', 'facility',
 '{"type":"Point","coordinates":[-115.53,35.48]}'::jsonb,
 ARRAY['rare_earths'], ARRAY['AMERICAS-USA'], 4,
 '{"share_note": "the only significant rare earth mining and processing site in the United States"}'::jsonb,
 'The only significant rare earth mine and processing site in the United States, operated by MP Materials; it anchors Washington push to reduce dependence on Chinese-controlled rare earth supply chains.',
 'Die einzige bedeutende Seltene-Erden-Mine und Verarbeitungsanlage in den Vereinigten Staaten, betrieben von MP Materials; sie ist die Grundlage von Washingtons Bemuehen, die Abhaengigkeit von chinesisch kontrollierten Seltene-Erden-Lieferketten zu verringern.'),

('mount_weld_mine', 'Mount Weld Mine', 'Mount-Weld-Mine', 'facility',
 '{"type":"Point","coordinates":[122.53,-28.87]}'::jsonb,
 ARRAY['rare_earths'], ARRAY['OCEANIA-AUSTRALIA'], 3,
 '{"share_note": "one of the highest-grade rare earth deposits outside China, operated by Lynas"}'::jsonb,
 'One of the highest-grade rare earth deposits outside China, operated by Lynas and feeding processing capacity in Malaysia and a new plant in Texas; a key node in allied efforts to build a non-Chinese rare earth supply chain.',
 'Eine der hochgradigsten Seltene-Erden-Lagerstaetten ausserhalb Chinas, betrieben von Lynas und Rohstoffquelle fuer Verarbeitungskapazitaeten in Malaysia sowie eine neue Anlage in Texas; ein zentraler Knotenpunkt in den Bemuehungen verbuendeter Staaten um eine chinaunabhaengige Seltene-Erden-Lieferkette.'),

('kachin_rare_earth_zone', 'Kachin Rare Earth Mining Zone', 'Kachin-Seltene-Erden-Abbauzone', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[97.5,26.0],[98.5,26.0],[98.5,25.0],[97.5,25.0],[97.5,26.0]]]}'::jsonb,
 ARRAY['rare_earths'], ARRAY[]::text[], 3,
 '{"share_note": "an unregulated heavy rare earth mining zone supplying most of Chinas heavy rare earth imports"}'::jsonb,
 'A largely unregulated heavy rare earth mining zone near the Chinese border, controlled by armed groups and supplying most of Chinas heavy rare earth ore imports; extraction revenue has become a direct source of conflict financing in Myanmar civil war.',
 'Eine weitgehend unregulierte Abbauzone fuer schwere Seltene Erden nahe der chinesischen Grenze, kontrolliert von bewaffneten Gruppen und Quelle des Grossteils der chinesischen Importe an schweren Seltene-Erden-Erzen; die Foerdererloese sind zu einer direkten Quelle der Konfliktfinanzierung im myanmarischen Buergerkrieg geworden.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- URANIUM
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('athabasca_basin_uranium', 'Athabasca Basin Uranium District', 'Athabasca-Becken-Uranrevier', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-108.5,58.5],[-104.5,58.5],[-104.5,56.5],[-108.5,56.5],[-108.5,58.5]]]}'::jsonb,
 ARRAY['uranium'], ARRAY['AMERICAS-CANADA'], 4,
 '{"share_note": "hosts Cigar Lake and McArthur River, the worlds highest-grade uranium mines"}'::jsonb,
 'Home to Cigar Lake and McArthur River, the worlds highest-grade uranium mines, making Canada a top global producer and a critical Western alternative to Kazakh and Russian-linked uranium supply.',
 'Heimat von Cigar Lake und McArthur River, den hochgradigsten Uranminen der Welt; sie machen Kanada zu einem der weltweit fuehrenden Produzenten und einer wichtigen westlichen Alternative zu kasachischer und russisch verbundener Uranversorgung.'),

('husab_rossing_uranium', 'Husab-Rossing Uranium District', 'Husab-Rossing-Uranrevier', 'facility',
 '{"type":"Point","coordinates":[15.24,-22.98]}'::jsonb,
 ARRAY['uranium'], ARRAY[]::text[], 3,
 '{"share_note": "hosts two of the largest uranium mines in Africa, both majority Chinese-owned"}'::jsonb,
 'Namibia desert uranium district hosting the Husab and Roessing mines, both majority owned by Chinese state firms, giving Beijing direct control over a significant share of Western-reactor-grade uranium supply.',
 'Namibias Wuesten-Uranrevier mit den Minen Husab und Roessing, beide mehrheitlich im Besitz chinesischer Staatsunternehmen, was Peking direkte Kontrolle ueber einen erheblichen Teil der Uranversorgung fuer westliche Reaktoren verschafft.'),

('olympic_dam_mine', 'Olympic Dam Mine', 'Olympic-Dam-Mine', 'facility',
 '{"type":"Point","coordinates":[136.88,-30.44]}'::jsonb,
 ARRAY['uranium','copper'], ARRAY['OCEANIA-AUSTRALIA'], 3,
 '{"share_note": "holds the largest known single uranium deposit in the world, also a major copper source"}'::jsonb,
 'Home to the largest known single uranium deposit on the planet alongside substantial copper reserves, operated by BHP; its scale underpins Australia role as a top uranium exporter to allied nuclear power markets.',
 'Beheimatet die groesste bekannte einzelne Uranlagerstaette der Welt neben erheblichen Kupferreserven, betrieben von BHP; ihre Groesse untermauert Australiens Rolle als fuehrender Uranexporteur in verbuendete Kernkraftmaerkte.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- NICKEL
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('new_caledonia_nickel_belt', 'New Caledonia Nickel Belt', 'Neukaledonischer Nickelguertel', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[164.7,-20.6],[166.9,-20.6],[166.9,-22.3],[164.7,-22.3],[164.7,-20.6]]]}'::jsonb,
 ARRAY['nickel'], ARRAY['EUROPE-FRANCE'], 3,
 '{"share_note": "holds roughly a tenth of world nickel reserves; French Pacific territory"}'::jsonb,
 'A French Pacific territory holding a major share of world nickel reserves; the 2024 pro-independence unrest shut down much of the smelting capacity and exposed how political instability in an overseas territory can rattle a critical minerals market.',
 'Ein franzoesisches Pazifikterritorium mit einem bedeutenden Anteil der weltweiten Nickelreserven; die Unruhen der Unabhaengigkeitsbewegung 2024 legten einen Grossteil der Schmelzkapazitaet still und zeigten, wie politische Instabilitaet in einem Uebersee-Territorium einen kritischen Rohstoffmarkt erschuettern kann.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- LITHIUM
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('salar_de_uyuni_lithium', 'Salar de Uyuni Lithium Resource', 'Lithiumvorkommen Salar de Uyuni', 'facility',
 '{"type":"Point","coordinates":[-67.5,-20.2]}'::jsonb,
 ARRAY['lithium'], ARRAY['AMERICAS-BOLIVIA'], 2,
 '{"share_note": "holds the largest identified lithium resource in the world, but remains barely developed"}'::jsonb,
 'The worlds largest identified lithium resource, but state control and technical setbacks have left it barely developed decades after discovery, making Bolivia the great unrealized wildcard in the global lithium supply race.',
 'Das weltweit groesste identifizierte Lithiumvorkommen, doch staatliche Kontrolle und technische Rueckschlaege haben es Jahrzehnte nach seiner Entdeckung kaum erschlossen, was Bolivien zum grossen ungenutzten Unsicherheitsfaktor im globalen Wettlauf um Lithium macht.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- BAUXITE
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('weipa_bauxite_mine', 'Weipa Bauxite Mine', 'Weipa-Bauxitmine', 'facility',
 '{"type":"Point","coordinates":[141.87,-12.63]}'::jsonb,
 ARRAY['bauxite'], ARRAY['OCEANIA-AUSTRALIA'], 3,
 '{"share_note": "one of the largest bauxite mines in the world, operated by Rio Tinto"}'::jsonb,
 'One of the largest bauxite mines on earth, operated by Rio Tinto on Queensland Cape York Peninsula, anchoring Australia position as a top global bauxite and alumina exporter.',
 'Eine der groessten Bauxitminen der Welt, betrieben von Rio Tinto auf der Cape-York-Halbinsel in Queensland, und Grundlage von Australiens Position als fuehrender weltweiter Bauxit- und Aluminiumoxid-Exporteur.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- GOLD
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('muruntau_gold_mine', 'Muruntau Gold Mine', 'Muruntau-Goldmine', 'facility',
 '{"type":"Point","coordinates":[64.58,41.5]}'::jsonb,
 ARRAY['gold'], ARRAY[]::text[], 2,
 '{"share_note": "the worlds largest open-pit gold mine by reserves"}'::jsonb,
 'The worlds largest open-pit gold mine, state-owned and central to Uzbekistan gold export earnings, which the government has increasingly leaned on as a hard-currency buffer.',
 'Die groesste Tagebau-Goldmine der Welt, in Staatsbesitz und zentral fuer Usbekistans Goldexporteinnahmen, auf die sich die Regierung zunehmend als Devisenpuffer stuetzt.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- TIN
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('bangka_belitung_tin', 'Bangka-Belitung Tin Belt', 'Zinnguertel Bangka-Belitung', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[105.5,-1.5],[107.2,-1.5],[107.2,-3.2],[105.5,-3.2],[105.5,-1.5]]]}'::jsonb,
 ARRAY['tin'], ARRAY['ASIA-SOUTHEAST'], 2,
 '{"share_note": "the source of most of Indonesias tin output, one of the largest global suppliers"}'::jsonb,
 'The island source of most of Indonesia tin output, making the country one of the top global suppliers for solder used throughout electronics manufacturing.',
 'Die Inselregion, aus der der Grossteil von Indonesiens Zinnfoerderung stammt, was das Land zu einem der weltweit fuehrenden Lieferanten von Lot fuer die Elektronikfertigung macht.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- GRAPHITE
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('balama_graphite_mine', 'Balama Graphite Mine', 'Balama-Graphitmine', 'facility',
 '{"type":"Point","coordinates":[39.6,-13.3]}'::jsonb,
 ARRAY['graphite'], ARRAY[]::text[], 3,
 '{"share_note": "one of the largest graphite mines in the world, a key battery anode material source"}'::jsonb,
 'One of the worlds largest graphite mines, operated by Syrah Resources, supplying natural graphite for battery anodes as manufacturers seek alternatives to Chinese-dominated graphite processing.',
 'Eine der groessten Graphitminen der Welt, betrieben von Syrah Resources, die Naturgraphit fuer Batterieanoden liefert, waehrend Hersteller nach Alternativen zur chinesisch dominierten Graphitverarbeitung suchen.')

ON CONFLICT (id) DO NOTHING;
