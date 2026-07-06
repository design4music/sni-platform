-- Seed ~14 technology & digital infrastructure strategic assets: semiconductor
-- fabs, data center hubs, and submarine cable landing concentrations.
-- Static ground-truth layer that friction nodes press on
-- (see 20260703_strategic_assets.sql for schema).
-- Idempotent: safe to re-run.

-- =========================================================================
-- SEMICONDUCTOR FABS (Point)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('samsung_pyeongtaek_hwaseong', 'Samsung Pyeongtaek-Hwaseong Cluster', 'Samsung Pyeongtaek-Hwaseong-Cluster', 'facility',
 '{"type":"Point","coordinates":[127.05,37.0]}'::jsonb,
 ARRAY['semiconductors'], ARRAY['ASIA-SOUTHKOREA'], 5,
 '{"share_note": "worlds largest memory chip fabrication complex, also a growing advanced foundry site"}'::jsonb,
 'The worlds largest memory chip production complex and Samsung flagship foundry site, concentrating a large share of global DRAM and NAND supply in one metro area.',
 'Der weltweit groesste Speicherchip-Fertigungskomplex und Samsungs wichtigster Foundry-Standort, der einen Grossteil der globalen DRAM- und NAND-Versorgung an einem Standort buendelt.'),

('sk_hynix_icheon', 'SK Hynix Icheon Complex', 'SK Hynix Icheon-Komplex', 'facility',
 '{"type":"Point","coordinates":[127.44,37.27]}'::jsonb,
 ARRAY['semiconductors'], ARRAY['ASIA-SOUTHKOREA'], 4,
 '{"share_note": "SK Hynix largest memory fab and R and D base, a top global DRAM supplier"}'::jsonb,
 'SK Hynix main memory production and research base, making South Korea indispensable to global DRAM and HBM supply for AI accelerators.',
 'SK Hynix wichtigste Speicherchip-Produktions- und Forschungsbasis, die Suedkorea fuer die globale DRAM- und HBM-Versorgung von KI-Beschleunigern unverzichtbar macht.'),

('tsmc_arizona', 'TSMC Arizona Fabs', 'TSMC Arizona-Fabriken', 'facility',
 '{"type":"Point","coordinates":[-111.97,33.31]}'::jsonb,
 ARRAY['semiconductors'], ARRAY['AMERICAS-USA'], 3,
 '{"share_note": "TSMC first major advanced-node fab outside Taiwan, built under US CHIPS Act incentives"}'::jsonb,
 'TSMC flagship US expansion aimed at reducing Washington reliance on Taiwan-concentrated chip production, though the most advanced nodes still trail Hsinchu.',
 'TSMCs zentrale US-Expansion mit dem Ziel, Washingtons Abhaengigkeit von der auf Taiwan konzentrierten Chipproduktion zu verringern, wobei die fortschrittlichsten Knoten weiterhin hinter Hsinchu zurueckbleiben.'),

('tsmc_kumamoto', 'TSMC Kumamoto Fab (JASM)', 'TSMC Kumamoto-Fabrik (JASM)', 'facility',
 '{"type":"Point","coordinates":[130.85,32.84]}'::jsonb,
 ARRAY['semiconductors'], ARRAY['ASIA-JAPAN'], 3,
 '{"share_note": "TSMC joint venture fab anchoring Japans chip industry revival"}'::jsonb,
 'TSMC first Japan fab, built with Sony and Denso as partners, central to Tokyo push to rebuild a domestic chip supply base and diversify away from Taiwan.',
 'TSMCs erste Fabrik in Japan, gebaut mit Sony und Denso als Partner, zentral fuer Tokios Vorhaben, eine heimische Chip-Versorgungsbasis wiederaufzubauen und sich von Taiwan zu diversifizieren.'),

('intel_ocotillo', 'Intel Ocotillo Campus (Chandler)', 'Intel Ocotillo-Campus (Chandler)', 'facility',
 '{"type":"Point","coordinates":[-111.84,33.27]}'::jsonb,
 ARRAY['semiconductors'], ARRAY['AMERICAS-USA'], 3,
 '{"share_note": "Intel largest US fab site and lead location for its advanced-node manufacturing bet"}'::jsonb,
 'Intel largest and most advanced US manufacturing site, carrying the companys bid to regain process leadership and anchor a domestic foundry alternative to TSMC.',
 'Intels groesster und fortschrittlichster US-Fertigungsstandort, der das Unternehmens Vorhaben traegt, die Prozessfuehrung zurueckzugewinnen und eine heimische Foundry-Alternative zu TSMC zu verankern.'),

('micron_boise', 'Micron Boise Campus', 'Micron Boise-Campus', 'facility',
 '{"type":"Point","coordinates":[-116.18,43.6]}'::jsonb,
 ARRAY['semiconductors'], ARRAY['AMERICAS-USA'], 3,
 '{"share_note": "Micron headquarters and lead memory R and D and production site, expanding under CHIPS Act support"}'::jsonb,
 'Microns home campus and the anchor for its planned US memory capacity expansion, the main non-Asian counterweight in a DRAM market dominated by Samsung and SK Hynix.',
 'Microns Heimcampus und Ankerpunkt fuer die geplante US-Speicherchip-Kapazitaetserweiterung, das wichtigste nicht-asiatische Gegengewicht in einem von Samsung und SK Hynix dominierten DRAM-Markt.'),

('asml_veldhoven', 'ASML Veldhoven Headquarters', 'ASML-Hauptsitz Veldhoven', 'facility',
 '{"type":"Point","coordinates":[5.4,51.42]}'::jsonb,
 ARRAY['semiconductors'], ARRAY['EUROPE-BENELUX'], 5,
 '{"share_note": "sole global source of extreme ultraviolet lithography machines required for the most advanced chips"}'::jsonb,
 'The only place on earth that makes extreme ultraviolet lithography machines, giving the Netherlands a single-point veto over who can manufacture the most advanced logic chips.',
 'Der einzige Ort weltweit, an dem Maschinen fuer die Extrem-Ultraviolett-Lithografie hergestellt werden, was den Niederlanden ein Vetorecht darueber gibt, wer die fortschrittlichsten Logikchips fertigen kann.'),

('smic_shanghai', 'SMIC Shanghai Fabs', 'SMIC Shanghai-Fabriken', 'facility',
 '{"type":"Point","coordinates":[121.6,31.2]}'::jsonb,
 ARRAY['semiconductors'], ARRAY['ASIA-CHINA'], 3,
 '{"share_note": "Chinas leading foundry and the focal point of US and allied export controls on advanced chipmaking equipment"}'::jsonb,
 'Chinas most advanced domestic foundry and the central target of US-led export controls on lithography and chipmaking tools, testing how far Beijing can push mature-node workarounds.',
 'Chinas fortschrittlichste heimische Foundry und zentrales Ziel der von den USA angefuehrten Exportkontrollen fuer Lithografie- und Chipfertigungsgeraete, ein Testfall dafuer, wie weit Peking Workarounds bei aelteren Knoten vorantreiben kann.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- DATA CENTER HUBS (Point)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('data_center_alley_ashburn', 'Northern Virginia Data Center Alley (Ashburn)', 'Datacenter-Cluster Nord-Virginia (Ashburn)', 'facility',
 '{"type":"Point","coordinates":[-77.48,39.04]}'::jsonb,
 ARRAY['data'], ARRAY['AMERICAS-USA'], 4,
 '{"share_note": "worlds largest concentration of data center capacity, estimated to carry a large share of global internet traffic"}'::jsonb,
 'The worlds largest concentration of data centers, a single Northern Virginia county through which a disproportionate share of global cloud and internet traffic passes.',
 'Die weltweit groesste Konzentration von Rechenzentren, ein einzelner Landkreis in Nord-Virginia, durch den ein unverhaeltnismaessig grosser Teil des globalen Cloud- und Internetverkehrs laeuft.'),

('frankfurt_data_center_cluster', 'Frankfurt Data Center Cluster', 'Frankfurter Datacenter-Cluster', 'facility',
 '{"type":"Point","coordinates":[8.68,50.11]}'::jsonb,
 ARRAY['data'], ARRAY['EUROPE-GERMANY'], 3,
 '{"share_note": "hosts DE-CIX, the worlds highest-traffic internet exchange point"}'::jsonb,
 'Germanys leading data center hub and home to DE-CIX, the busiest internet exchange point on earth, making Frankfurt a chokepoint for European internet traffic.',
 'Deutschlands fuehrender Datacenter-Standort und Sitz von DE-CIX, dem verkehrsreichsten Internetknoten der Welt, was Frankfurt zu einem Engpass fuer den europaeischen Internetverkehr macht.'),

('singapore_data_center_cluster', 'Singapore Data Center Cluster', 'Singapur Datacenter-Cluster', 'facility',
 '{"type":"Point","coordinates":[103.82,1.32]}'::jsonb,
 ARRAY['data'], ARRAY['ASIA-SOUTHEAST'], 3,
 '{"share_note": "Southeast Asias dominant hyperscale and interconnection hub"}'::jsonb,
 'Southeast Asia premier cloud and interconnection hub, whose small land area and moratorium history have concentrated regional digital dependency into one city-state.',
 'Suedostasiens fuehrender Cloud- und Vernetzungsknoten, dessen begrenzte Flaeche und fruehere Neubau-Moratorien die digitale Abhaengigkeit der Region auf einen einzigen Stadtstaat konzentriert haben.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- SUBMARINE CABLE LANDING CONCENTRATIONS (Point)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('egypt_red_sea_cable_corridor', 'Egypt Red Sea-Mediterranean Cable Corridor', 'Aegyptischer Rotes-Meer-Mittelmeer-Kabelkorridor', 'facility',
 '{"type":"Point","coordinates":[32.9,29.9]}'::jsonb,
 ARRAY['data'], ARRAY['MIDEAST-EGYPT', 'MIDEAST-EGYPT'], 5,
 '{"share_note": "land corridor between Suez and Alexandria carrying the large majority of Europe-Asia submarine cable traffic"}'::jsonb,
 'The narrow land bridge between the Red Sea and the Mediterranean through which most Europe-Asia submarine cable traffic transits, making a single Egyptian corridor a single point of failure for intercontinental internet capacity.',
 'Die schmale Landbruecke zwischen Rotem Meer und Mittelmeer, durch die der groesste Teil des Europa-Asien-Unterseekabelverkehrs laeuft, wodurch ein einzelner aegyptischer Korridor zum Single Point of Failure fuer interkontinentale Internetkapazitaet wird.'),

('marseille_cable_landing_hub', 'Marseille Submarine Cable Landing Hub', 'Marseille Unterseekabel-Landepunkt', 'facility',
 '{"type":"Point","coordinates":[5.37,43.3]}'::jsonb,
 ARRAY['data'], ARRAY['EUROPE-FRANCE'], 3,
 '{"share_note": "Europes busiest submarine cable landing point, linking Europe to Africa, the Middle East and Asia"}'::jsonb,
 'Europe densest submarine cable landing station, funneling most cable routes between Europe, Africa and Asia through a single Mediterranean port city.',
 'Europas dichteste Unterseekabel-Landestation, die die meisten Kabelrouten zwischen Europa, Afrika und Asien durch eine einzige Mittelmeer-Hafenstadt buendelt.'),

('fortaleza_cable_landing_hub', 'Fortaleza Submarine Cable Landing Hub', 'Fortaleza Unterseekabel-Landepunkt', 'facility',
 '{"type":"Point","coordinates":[-38.53,-3.72]}'::jsonb,
 ARRAY['data'], ARRAY['AMERICAS-BRAZIL'], 2,
 '{"share_note": "Brazils main Atlantic cable landing point linking South America to Africa, Europe and North America"}'::jsonb,
 'Brazil principal Atlantic cable gateway, anchoring South America direct links to Africa, Europe and North America and reducing regional reliance on US-routed traffic.',
 'Brasiliens wichtigstes Atlantik-Kabeltor, das Suedamerikas direkte Verbindungen nach Afrika, Europa und Nordamerika verankert und die regionale Abhaengigkeit von ueber die USA gefuehrtem Datenverkehr verringert.')

ON CONFLICT (id) DO NOTHING;
