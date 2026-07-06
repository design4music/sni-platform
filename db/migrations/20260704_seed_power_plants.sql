-- Seed power generation batch for the strategic-asset map: major nuclear,
-- hydro, coal and offshore wind facilities. asset_type = 'facility' for all.
-- Commodities convention: ['electricity', <generation_type>] where
-- generation_type in nuclear | hydro | coal | gas | wind. Drives map
-- category and future generation-type filters.
-- Idempotent: safe to re-run.

-- =========================================================================
-- NUCLEAR
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('zaporizhzhia_npp', 'Zaporizhzhia Nuclear Power Plant', 'Kernkraftwerk Saporischschja', 'facility',
 '{"type":"Point","coordinates":[34.585,47.512]}'::jsonb,
 ARRAY['electricity','nuclear'], ARRAY['EUROPE-UKRAINE', 'EUROPE-RUSSIA'], 5,
 '{"capacity_mw": 5700, "note": "Europes largest nuclear plant, under Russian military occupation since March 2022, operated by Ukrainian staff under IAEA monitoring"}'::jsonb,
 'Europe largest nuclear power station, seized by Russian forces in 2022 and repeatedly caught in shelling near the front line, making it one of the highest-stakes nuclear-safety flashpoints in the world.',
 'Europas groesstes Kernkraftwerk, 2022 von russischen Streitkraeften besetzt und wiederholt in der Naehe der Frontlinie beschossen, damit einer der brisantesten nuklearen Sicherheits-Brennpunkte weltweit.'),

('akkuyu_npp', 'Akkuyu Nuclear Power Plant', 'Kernkraftwerk Akkuyu', 'facility',
 '{"type":"Point","coordinates":[33.54,36.14]}'::jsonb,
 ARRAY['electricity','nuclear'], ARRAY['MIDEAST-TURKEY'], 3,
 '{"capacity_mw": 4800, "operator": "Rosatom", "note": "Turkeys first nuclear plant, built, owned and operated by Russias Rosatom under a build-own-operate model"}'::jsonb,
 'Turkey first nuclear plant, fully built and owned by Russias Rosatom, giving Moscow decades of built-in energy leverage over a NATO member.',
 'Die Tuerkeis erstes Kernkraftwerk, vollstaendig gebaut und im Besitz von Russlands Rosatom, was Moskau jahrzehntelangen strukturellen Energie-Einfluss auf ein NATO-Mitglied verschafft.'),

('barakah_npp', 'Barakah Nuclear Power Plant', 'Kernkraftwerk Barakah', 'facility',
 '{"type":"Point","coordinates":[52.28,23.97]}'::jsonb,
 ARRAY['electricity','nuclear'], ARRAY['MIDEAST-GULF'], 3,
 '{"capacity_mw": 5600, "note": "the Arab worlds first commercial nuclear power plant"}'::jsonb,
 'The Arab world first operating nuclear plant, anchoring the UAE push to diversify its power mix away from gas ahead of a Gulf energy transition.',
 'Das erste laufende Kernkraftwerk der arabischen Welt, zentral fuer die Bestrebungen der VAE, den Strommix vor einer Energiewende am Golf von Gas zu diversifizieren.'),

('kashiwazaki_kariwa_npp', 'Kashiwazaki-Kariwa Nuclear Power Plant', 'Kernkraftwerk Kashiwazaki-Kariwa', 'facility',
 '{"type":"Point","coordinates":[138.60,37.43]}'::jsonb,
 ARRAY['electricity','nuclear'], ARRAY['ASIA-JAPAN'], 3,
 '{"capacity_mw": 8212, "note": "the worlds largest nuclear power plant by installed capacity"}'::jsonb,
 'The world largest nuclear plant by capacity, largely idled since Fukushima and a bellwether for whether Japan restarts its nuclear fleet amid energy security pressure.',
 'Das nach installierter Leistung groesste Kernkraftwerk der Welt, seit Fukushima weitgehend stillgelegt und ein Fruehindikator dafuer, ob Japan seine Atomflotte angesichts des Energiesicherheitsdrucks wieder hochfaehrt.'),

('kori_saeul_npp', 'Kori-Saeul Nuclear Cluster', 'Kernkraftwerkscluster Kori-Saeul', 'facility',
 '{"type":"Point","coordinates":[129.30,35.32]}'::jsonb,
 ARRAY['electricity','nuclear'], ARRAY['ASIA-SOUTHKOREA'], 3,
 '{"capacity_mw": 7489, "note": "South Koreas largest nuclear complex, combining the Kori and Saeul stations"}'::jsonb,
 'South Korea largest concentration of nuclear capacity, underpinning both domestic power supply and Seoul export ambitions in the global reactor market.',
 'Suedkoreas groesste Konzentration von Kernkraftkapazitaet, Grundlage sowohl der heimischen Stromversorgung als auch Seouls Exportambitionen auf dem globalen Reaktormarkt.'),

('gravelines_npp', 'Gravelines Nuclear Power Plant', 'Kernkraftwerk Gravelines', 'facility',
 '{"type":"Point","coordinates":[2.15,51.02]}'::jsonb,
 ARRAY['electricity','nuclear'], ARRAY['EUROPE-FRANCE'], 3,
 '{"capacity_mw": 5460, "note": "the largest nuclear power plant in Western Europe"}'::jsonb,
 'Western Europe largest nuclear plant, a pillar of the low-carbon baseload power that gives France an outsized role in EU electricity export flows.',
 'Westeuropas groesstes Kernkraftwerk, eine Saeule der CO2-armen Grundlastversorgung, die Frankreich eine ueberproportionale Rolle bei den EU-Stromexportfluessen verschafft.'),

('taishan_npp', 'Taishan Nuclear Power Plant', 'Kernkraftwerk Taishan', 'facility',
 '{"type":"Point","coordinates":[112.97,21.94]}'::jsonb,
 ARRAY['electricity','nuclear'], ARRAY['ASIA-CHINA'], 3,
 '{"capacity_mw": 3500, "note": "home to the worlds first operating EPR reactors, a Franco-Chinese joint project"}'::jsonb,
 'Site of the worlds first EPR reactors to enter commercial service, a showcase for Chinas fast-expanding nuclear buildout and its technology partnerships with France.',
 'Standort der weltweit ersten kommerziell betriebenen EPR-Reaktoren, ein Aushaengeschild fuer Chinas rasch wachsenden Nuklearausbau und seine Technologiepartnerschaften mit Frankreich.'),

('kudankulam_npp', 'Kudankulam Nuclear Power Plant', 'Kernkraftwerk Kudankulam', 'facility',
 '{"type":"Point","coordinates":[77.71,8.17]}'::jsonb,
 ARRAY['electricity','nuclear'], ARRAY['ASIA-INDIA'], 3,
 '{"capacity_mw": 2000, "operator": "built with Rosatom", "note": "Indias largest nuclear power station, built with Russian reactor technology and financing"}'::jsonb,
 'India largest nuclear plant, built with Rosatom reactors and financing, illustrating how Russia retains a strategic energy foothold in India even as New Delhi diversifies its partnerships.',
 'Indiens groesstes Kernkraftwerk, gebaut mit Rosatom-Reaktoren und russischer Finanzierung, ein Beleg dafuer, dass Russland trotz Neu-Delhis Diversifizierung strategischen Energie-Einfluss in Indien behaelt.'),

('vogtle_npp', 'Vogtle Nuclear Power Plant', 'Kernkraftwerk Vogtle', 'facility',
 '{"type":"Point","coordinates":[-81.98,33.14]}'::jsonb,
 ARRAY['electricity','nuclear'], ARRAY['AMERICAS-USA'], 2,
 '{"capacity_mw": 4536, "note": "site of the first new US reactors to enter service in decades"}'::jsonb,
 'Home to the first newly built US reactors in over 30 years, a costly and delayed project now cited as the test case for whether America can revive large-scale nuclear construction.',
 'Standort der ersten seit ueber 30 Jahren neu gebauten US-Reaktoren, ein teures und verzoegertes Projekt, das nun als Testfall dafuer gilt, ob die USA den Bau von Grossreaktoren wiederbeleben koennen.'),

('bruce_npp', 'Bruce Nuclear Generating Station', 'Kernkraftwerk Bruce', 'facility',
 '{"type":"Point","coordinates":[-81.60,44.33]}'::jsonb,
 ARRAY['electricity','nuclear'], ARRAY['AMERICAS-CANADA'], 2,
 '{"capacity_mw": 6430, "note": "the worlds largest operating nuclear power plant by number of reactors"}'::jsonb,
 'The world largest operating nuclear site by reactor count, anchoring Ontario low-carbon grid and Canada position as a major uranium and reactor-technology supplier.',
 'Der nach Reaktoranzahl groesste in Betrieb befindliche Nuklearstandort der Welt, Grundlage von Ontarios CO2-armem Stromnetz und Kanadas Rolle als bedeutender Uran- und Reaktortechnologie-Lieferant.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- HYDRO
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('three_gorges_dam', 'Three Gorges Dam', 'Drei-Schluchten-Damm', 'facility',
 '{"type":"Point","coordinates":[111.00,30.82]}'::jsonb,
 ARRAY['electricity','hydro'], ARRAY['ASIA-CHINA'], 4,
 '{"capacity_mw": 22500, "note": "the worlds largest power station by installed capacity"}'::jsonb,
 'The world largest power station by capacity, a centerpiece of Chinese engineering that also controls flood flows on the Yangtze for hundreds of millions of people downstream.',
 'Das nach installierter Leistung groesste Kraftwerk der Welt, ein Aushaengeschild chinesischer Ingenieurskunst, das zugleich die Hochwasserabfluesse des Jangtse fuer hunderte Millionen Menschen flussabwaerts steuert.'),

('itaipu_dam', 'Itaipu Dam', 'Itaipu-Staudamm', 'facility',
 '{"type":"Point","coordinates":[-54.59,-25.41]}'::jsonb,
 ARRAY['electricity','hydro'], ARRAY['AMERICAS-BRAZIL'], 4,
 '{"capacity_mw": 14000, "note": "jointly owned and operated by Brazil and Paraguay on the Parana River"}'::jsonb,
 'A Brazil-Paraguay joint venture on the Parana River supplying a large share of Paraguay total electricity and a significant share of Brazil, making the treaty governing its output a recurring bilateral flashpoint.',
 'Ein brasilianisch-paraguayisches Gemeinschaftsprojekt am Parana, das einen Grossteil von Paraguays gesamtem Strombedarf und einen bedeutenden Anteil Brasiliens deckt, wodurch der zugrunde liegende Vertrag wiederholt zum bilateralen Streitpunkt wird.'),

('gerd_dam', 'Grand Ethiopian Renaissance Dam', 'Grosser Aethiopischer Renaissance-Staudamm', 'facility',
 '{"type":"Point","coordinates":[35.09,11.22]}'::jsonb,
 ARRAY['electricity','hydro'], ARRAY['AFRICA-ETHIOPIA', 'MIDEAST-EGYPT'], 4,
 '{"capacity_mw": 5150, "note": "Africas largest hydropower dam, on the Blue Nile"}'::jsonb,
 'Africa largest hydropower dam on the Blue Nile, filled and operated unilaterally by Ethiopia despite years of objections from downstream Egypt and Sudan over Nile water shares, keeping it one of Africa most volatile transboundary disputes.',
 'Afrikas groesster Wasserkraftstaudamm am Blauen Nil, von Aethiopien einseitig befuellt und betrieben trotz jahrelanger Einwaende der Nil-Unterlieger Aegypten und Sudan bezueglich der Wasseranteile, damit einer der instabilsten grenzueberschreitenden Konflikte Afrikas.'),

('kariba_dam', 'Kariba Dam', 'Kariba-Staudamm', 'facility',
 '{"type":"Point","coordinates":[28.76,-16.52]}'::jsonb,
 ARRAY['electricity','hydro'], ARRAY[]::text[], 2,
 '{"capacity_mw": 2130, "note": "jointly operated by Zambia and Zimbabwe on the Zambezi River, forming the worlds largest reservoir by volume"}'::jsonb,
 'A Zambia-Zimbabwe shared dam on the Zambezi whose reservoir is the world largest by volume; recurring droughts have forced both countries into severe power rationing.',
 'Ein von Sambia und Simbabwe gemeinsam betriebener Staudamm am Sambesi, dessen Stausee der weltweit groesste nach Volumen ist; wiederkehrende Duerren haben beide Laender zu schwerer Stromrationierung gezwungen.'),

('aswan_high_dam', 'Aswan High Dam', 'Assuan-Staudamm', 'facility',
 '{"type":"Point","coordinates":[32.88,23.97]}'::jsonb,
 ARRAY['electricity','hydro'], ARRAY['MIDEAST-EGYPT'], 3,
 '{"capacity_mw": 2100, "note": "regulates the Nile flow and created Lake Nasser"}'::jsonb,
 'The dam that gave Egypt control over Nile flooding and a strategic power source, making downstream Nile flow security an existential concern in its dispute with Ethiopia over the Renaissance Dam.',
 'Der Staudamm, der Aegypten die Kontrolle ueber die Nilueberschwemmungen und eine strategische Stromquelle verschaffte, weshalb die Sicherung des Nilabflusses fuer Aegypten im Streit um den aethiopischen Renaissance-Staudamm existenziell ist.'),

('belo_monte_dam', 'Belo Monte Dam', 'Belo-Monte-Staudamm', 'facility',
 '{"type":"Point","coordinates":[-51.79,-3.10]}'::jsonb,
 ARRAY['electricity','hydro'], ARRAY['AMERICAS-BRAZIL'], 2,
 '{"capacity_mw": 11233, "note": "the worlds fourth-largest hydropower plant, on the Xingu River in the Amazon"}'::jsonb,
 'A major Amazon hydropower project on the Xingu River whose construction displaced indigenous communities and became a global symbol of the tension between Brazil clean-energy buildout and rainforest protection.',
 'Ein bedeutendes Amazonas-Wasserkraftprojekt am Xingu, dessen Bau indigene Gemeinschaften verdraengte und zu einem weltweiten Symbol fuer den Zielkonflikt zwischen Brasiliens Ausbau sauberer Energie und dem Schutz des Regenwalds wurde.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- COAL
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('tuoketuo_power_station', 'Tuoketuo Power Station', 'Kraftwerk Tuoketuo', 'facility',
 '{"type":"Point","coordinates":[111.18,40.35]}'::jsonb,
 ARRAY['electricity','coal'], ARRAY['ASIA-CHINA'], 2,
 '{"capacity_mw": 6720, "note": "among the largest coal-fired power stations in the world"}'::jsonb,
 'One of the largest coal-fired power stations on earth, illustrating the scale of the coal fleet China continues to build even as it leads the world in renewable capacity additions.',
 'Eines der groessten Kohlekraftwerke der Welt, ein Beleg fuer das Ausmass der Kohleflotte, die China weiterhin ausbaut, obwohl es weltweit fuehrend beim Zubau erneuerbarer Kapazitaeten ist.'),

('medupi_kusile_power_stations', 'Medupi-Kusile Power Stations', 'Kraftwerke Medupi-Kusile', 'facility',
 '{"type":"Point","coordinates":[27.55,-23.68]}'::jsonb,
 ARRAY['electricity','coal'], ARRAY['AFRICA-SOUTHAFRICA'], 2,
 '{"capacity_mw": 9564, "operator": "Eskom", "note": "Eskoms newest and largest coal plants, plagued by construction delays and breakdowns"}'::jsonb,
 'Eskom newest and largest coal plants, whose chronic construction delays and breakdowns have been central to the rolling blackouts that have destabilized South Africa economy for years.',
 'Eskoms neueste und groesste Kohlekraftwerke, deren chronische Bauverzoegerungen und Ausfaelle massgeblich zu den rollierenden Stromabschaltungen beigetragen haben, die Suedafrikas Wirtschaft seit Jahren destabilisieren.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- OFFSHORE WIND CLUSTERS
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('hornsea_dogger_wind', 'Hornsea-Dogger Bank Offshore Wind Cluster', 'Offshore-Windcluster Hornsea-Dogger-Bank', 'facility',
 '{"type":"Point","coordinates":[2.15,54.30]}'::jsonb,
 ARRAY['electricity','wind'], ARRAY['EUROPE-UK'], 3,
 '{"capacity_mw": 8000, "note": "the worlds largest offshore wind zone, combining the Hornsea and Dogger Bank projects in the North Sea"}'::jsonb,
 'The world largest offshore wind zone in the North Sea, central to the UK bet on offshore wind to replace gas generation and reduce exposure to volatile import prices.',
 'Die weltweit groesste Offshore-Windzone in der Nordsee, zentral fuer Grossbritanniens Strategie, Gaserzeugung durch Offshore-Wind zu ersetzen und die Abhaengigkeit von volatilen Importpreisen zu verringern.'),

('german_bight_wind', 'German Bight Offshore Wind Cluster', 'Offshore-Windcluster Deutsche Bucht', 'facility',
 '{"type":"Point","coordinates":[6.50,54.50]}'::jsonb,
 ARRAY['electricity','wind'], ARRAY['EUROPE-GERMANY'], 3,
 '{"capacity_mw": 7700, "note": "Germanys main offshore wind development zone in the North Sea"}'::jsonb,
 'Germany principal offshore wind buildout zone in the North Sea, a linchpin of Berlin plan to replace retiring nuclear and coal capacity while cutting reliance on imported gas.',
 'Deutschlands zentrale Offshore-Wind-Ausbauzone in der Nordsee, ein Schluesselelement von Berlins Plan, auslaufende Kernkraft- und Kohlekapazitaeten zu ersetzen und die Abhaengigkeit von importiertem Gas zu senken.')

ON CONFLICT (id) DO NOTHING;
