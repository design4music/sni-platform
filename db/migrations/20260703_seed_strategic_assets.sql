-- Seed ~35 globally significant strategic assets: chokepoints, ports,
-- production clusters, and pipelines. Static ground-truth layer that
-- friction nodes press on (see 20260703_strategic_assets.sql for schema).
-- Idempotent: safe to re-run.

-- =========================================================================
-- CHOKEPOINTS (LineString across the waterway)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('strait_of_hormuz', 'Strait of Hormuz', 'Strasse von Hormus', 'chokepoint',
 '{"type":"LineString","coordinates":[[56.25,26.55],[56.4,26.65],[56.6,26.7]]}'::jsonb,
 ARRAY['oil','lng'], ARRAY['MIDEAST-IRAN','MIDEAST-GULF','MIDEAST-SAUDI'], 5,
 '{"share_note": "roughly one fifth of global oil consumption transits daily"}'::jsonb,
 'The only sea route out of the Persian Gulf; a closure would sever the largest concentration of the world oil and LNG export capacity.',
 'Die einzige Seeroute aus dem Persischen Golf; eine Sperrung wuerde die groesste Konzentration weltweiter Oel- und LNG-Exportkapazitaet abschneiden.'),

('bab_el_mandeb', 'Bab el-Mandeb', 'Bab al-Mandab', 'chokepoint',
 '{"type":"LineString","coordinates":[[43.3,12.65],[43.45,12.55],[43.55,12.45]]}'::jsonb,
 ARRAY['oil','lng','containers'], ARRAY['MIDEAST-YEMEN', 'AFRICA-EGYPT'], 5,
 '{"share_note": "gateway between the Red Sea and the Gulf of Aden for Suez-bound traffic"}'::jsonb,
 'Narrow strait linking the Red Sea to the Indian Ocean; Houthi attacks since 2023 have already diverted much of the container trade around Africa.',
 'Enge Meerenge zwischen Rotem Meer und Indischem Ozean; Huthi-Angriffe seit 2023 haben bereits einen Grossteil des Containerverkehrs um Afrika umgeleitet.'),

('suez_canal', 'Suez Canal', 'Suezkanal', 'chokepoint',
 '{"type":"LineString","coordinates":[[32.58,31.26],[32.5,30.6],[32.35,29.95]]}'::jsonb,
 ARRAY['oil','lng','containers'], ARRAY['MIDEAST-EGYPT', 'AFRICA-EGYPT'], 5,
 '{"share_note": "roughly 12 percent of global trade volume normally passes through"}'::jsonb,
 'Shortest sea link between Europe and Asia; the 2021 Ever Given grounding and the 2023-24 Red Sea diversions both showed how fast global freight costs react to disruption here.',
 'Kuerzeste Seeverbindung zwischen Europa und Asien; die Ever-Given-Havarie 2021 und die Umleitungen im Roten Meer 2023-24 zeigten, wie schnell globale Frachtkosten auf Stoerungen hier reagieren.'),

('panama_canal', 'Panama Canal', 'Panamakanal', 'chokepoint',
 '{"type":"LineString","coordinates":[[-79.92,9.35],[-79.6,9.08],[-79.55,8.9]]}'::jsonb,
 ARRAY['containers','lng','grain'], ARRAY['AMERICAS-USA'], 4,
 '{"share_note": "handles a large share of US coast-to-coast and Asia-US East Coast trade"}'::jsonb,
 'Key shortcut between the Atlantic and Pacific; recent drought-driven draft restrictions showed how climate stress can throttle a chokepoint without any conflict at all.',
 'Wichtige Abkuerzung zwischen Atlantik und Pazifik; duerrebedingte Tiefgangsbeschraenkungen zeigten zuletzt, wie Klimastress einen Knotenpunkt auch ganz ohne Konflikt drosseln kann.'),

('strait_of_malacca', 'Strait of Malacca', 'Strasse von Malakka', 'chokepoint',
 '{"type":"LineString","coordinates":[[98.4,4.1],[100.3,2.9],[103.5,1.2]]}'::jsonb,
 ARRAY['oil','lng','containers'], ARRAY['ASIA-CHINA'], 5,
 '{"share_note": "primary sea route for East Asia bound energy and trade from the Indian Ocean"}'::jsonb,
 'The busiest and narrowest chokepoint feeding China, Japan and South Korea; any blockage forces a costly detour via the Lombok or Sunda straits.',
 'Der verkehrsreichste und engste Knotenpunkt fuer China, Japan und Suedkorea; jede Blockade erzwingt einen teuren Umweg ueber die Lombok- oder Sunda-Strasse.'),

('turkish_straits', 'Turkish Straits (Bosphorus)', 'Tuerkische Meerengen (Bosporus)', 'chokepoint',
 '{"type":"LineString","coordinates":[[28.98,41.1],[29.05,41.2],[29.1,41.3]]}'::jsonb,
 ARRAY['oil','grain'], ARRAY['MIDEAST-TURKEY', 'EUROPE-UKRAINE', 'EUROPE-RUSSIA'], 4,
 '{"share_note": "sole sea exit for Russian and Ukrainian Black Sea grain and oil exports"}'::jsonb,
 'The only maritime outlet from the Black Sea; Turkey controls transit rights under the Montreux Convention, giving Ankara leverage over both Russian and Ukrainian exports.',
 'Der einzige Seeausgang aus dem Schwarzen Meer; die Tuerkei kontrolliert die Durchfahrtsrechte gemaess der Montreux-Konvention und hat damit Einfluss auf russische wie ukrainische Exporte.'),

('taiwan_strait', 'Taiwan Strait', 'Taiwanstrasse', 'chokepoint',
 '{"type":"LineString","coordinates":[[119.5,24.0],[120.0,24.5],[120.6,25.2]]}'::jsonb,
 ARRAY['containers','semiconductors'], ARRAY['ASIA-TAIWAN', 'ASIA-CHINA'], 5,
 '{"share_note": "carries a large share of global container traffic and nearly all advanced chip exports"}'::jsonb,
 'The most militarized commercial waterway in the world; a blockade or conflict here would simultaneously cut global chip supply and a core East Asia shipping lane.',
 'Die am staerksten militarisierte Handelswasserstrasse der Welt; eine Blockade oder ein Konflikt wuerde gleichzeitig die globale Chipversorgung und eine zentrale ostasiatische Schifffahrtsroute unterbrechen.'),

('strait_of_gibraltar', 'Strait of Gibraltar', 'Strasse von Gibraltar', 'chokepoint',
 '{"type":"LineString","coordinates":[[-5.6,35.95],[-5.4,36.0],[-5.2,36.05]]}'::jsonb,
 ARRAY['oil','containers'], ARRAY['EUROPE-UK'], 3,
 '{"share_note": "principal entry and exit point for Mediterranean shipping"}'::jsonb,
 'Gateway between the Atlantic and the Mediterranean; a chokepoint for European energy imports and transatlantic container flows alike.',
 'Tor zwischen Atlantik und Mittelmeer; ein Knotenpunkt sowohl fuer europaeische Energieimporte als auch fuer transatlantische Containerstroeme.'),

('danish_straits', 'Danish Straits', 'Daenische Meerengen', 'chokepoint',
 '{"type":"LineString","coordinates":[[12.6,55.6],[12.7,55.7],[12.9,55.9]]}'::jsonb,
 ARRAY['oil','gas'], ARRAY['EUROPE-RUSSIA'], 3,
 '{"share_note": "main route for Russian and Baltic seaborne oil exports to reach open water"}'::jsonb,
 'The exit route for the Baltic Sea into the North Sea; heavily used by the aging Russian shadow-fleet tankers that have raised sanctions-evasion and spill concerns.',
 'Die Ausfahrtroute aus der Ostsee in die Nordsee; stark genutzt von alternden russischen Schattenflotten-Tankern, was Sorgen ueber Sanktionsumgehung und Oelunfaelle ausgeloest hat.'),

('northern_sea_route', 'Northern Sea Route', 'Nordostpassage', 'chokepoint',
 '{"type":"LineString","coordinates":[[33.0,70.0],[60.0,73.0],[90.0,76.0],[140.0,74.0],[170.0,68.5]]}'::jsonb,
 ARRAY['oil','lng'], ARRAY['EUROPE-RUSSIA'], 3,
 '{"share_note": "an emerging Arctic shortcut between Europe and Asia as sea ice retreats"}'::jsonb,
 'Russia-controlled Arctic passage that shortens Europe-Asia transit time; its growing viability under warming conditions is reshaping Arctic strategic competition.',
 'Von Russland kontrollierte arktische Passage, die die Transitzeit zwischen Europa und Asien verkuerzt; ihre wachsende Nutzbarkeit unter Erwaermungsbedingungen veraendert den strategischen Wettbewerb in der Arktis.'),

('cape_of_good_hope_route', 'Cape of Good Hope Route', 'Kap-der-Guten-Hoffnung-Route', 'chokepoint',
 '{"type":"LineString","coordinates":[[16.5,-34.8],[18.4,-34.4],[20.0,-34.8]]}'::jsonb,
 ARRAY['oil','containers'], ARRAY['AFRICA-EGYPT'], 3,
 '{"share_note": "the fallback route absorbing traffic diverted from the Suez Canal and Bab el-Mandeb"}'::jsonb,
 'The long way around Africa that shipping falls back on whenever the Red Sea corridor is unsafe, adding roughly two weeks of transit time and raising freight costs globally.',
 'Der lange Weg um Afrika, auf den die Schifffahrt ausweicht, sobald der Korridor im Roten Meer unsicher ist, was rund zwei Wochen Transitzeit hinzufuegt und die Frachtkosten weltweit erhoeht.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- PORTS (Point)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('port_of_shanghai', 'Port of Shanghai', 'Hafen von Shanghai', 'port',
 '{"type":"Point","coordinates":[121.65,31.23]}'::jsonb,
 ARRAY['containers'], ARRAY['ASIA-CHINA'], 4,
 '{"share_note": "the worlds busiest container port by throughput"}'::jsonb,
 'The busiest container port on earth; disruption here ripples through global manufacturing supply chains within days.',
 'Der verkehrsreichste Containerhafen der Welt; Stoerungen hier wirken sich innerhalb weniger Tage auf globale Fertigungslieferketten aus.'),

('port_of_singapore', 'Port of Singapore', 'Hafen von Singapur', 'port',
 '{"type":"Point","coordinates":[103.82,1.26]}'::jsonb,
 ARRAY['oil','containers'], ARRAY['ASIA-CHINA'], 4,
 '{"share_note": "the worlds largest transshipment and bunkering hub"}'::jsonb,
 'The premier transshipment and bunkering hub guarding the eastern end of the Strait of Malacca.',
 'Der wichtigste Umschlag- und Bunkerhafen am oestlichen Ende der Strasse von Malakka.'),

('port_of_rotterdam', 'Port of Rotterdam', 'Hafen von Rotterdam', 'port',
 '{"type":"Point","coordinates":[4.15,51.95]}'::jsonb,
 ARRAY['oil','containers','chemicals'], ARRAY['EUROPE-GERMANY'], 4,
 '{"share_note": "the largest port in Europe by cargo volume"}'::jsonb,
 'Europe largest port and the main entry point for energy and manufactured goods reaching the continental interior.',
 'Europas groesster Hafen und der wichtigste Eingangspunkt fuer Energie und Fertigwaren ins kontinentale Hinterland.'),

('jebel_ali_port', 'Jebel Ali Port (Dubai)', 'Hafen Jebel Ali (Dubai)', 'port',
 '{"type":"Point","coordinates":[55.06,25.01]}'::jsonb,
 ARRAY['containers','oil'], ARRAY['MIDEAST-GULF'], 3,
 '{"share_note": "the largest man-made harbour and a key Gulf transshipment hub"}'::jsonb,
 'The Gulf premier logistics and re-export hub, positioned to absorb trade diverted around Hormuz-related disruptions.',
 'Der fuehrende Logistik- und Re-Export-Knotenpunkt am Golf, gut positioniert, um durch Hormus-bedingte Stoerungen umgeleiteten Handel aufzunehmen.'),

('ras_tanura', 'Ras Tanura Oil Terminal', 'Oelterminal Ras Tanura', 'port',
 '{"type":"Point","coordinates":[50.17,26.64]}'::jsonb,
 ARRAY['oil'], ARRAY['MIDEAST-SAUDI'], 5,
 '{"share_note": "Saudi Arabias largest crude oil export terminal"}'::jsonb,
 'Saudi Aramco largest crude export terminal, feeding a substantial share of the oil that transits the Strait of Hormuz.',
 'Saudi Aramcos groesstes Rohoel-Exportterminal, das einen erheblichen Teil des durch die Strasse von Hormus transportierten Oels speist.'),

('novorossiysk_port', 'Port of Novorossiysk', 'Hafen Noworossijsk', 'port',
 '{"type":"Point","coordinates":[37.78,44.72]}'::jsonb,
 ARRAY['oil','grain'], ARRAY['EUROPE-RUSSIA'], 4,
 '{"share_note": "Russias main Black Sea oil and grain export terminal"}'::jsonb,
 'Russia primary Black Sea export terminal for crude oil and grain, and a repeated target of Ukrainian long-range strikes.',
 'Russlands wichtigstes Export-Terminal am Schwarzen Meer fuer Rohoel und Getreide, und wiederholtes Ziel ukrainischer Langstreckenangriffe.'),

('odesa_port', 'Port of Odesa', 'Hafen Odessa', 'port',
 '{"type":"Point","coordinates":[30.73,46.48]}'::jsonb,
 ARRAY['grain'], ARRAY['EUROPE-UKRAINE'], 4,
 '{"share_note": "Ukraines principal grain export gateway to world markets"}'::jsonb,
 'Ukraine main grain export gateway; its blockade and repeated shelling since 2022 have directly affected global food prices.',
 'Ukraines wichtigstes Tor fuer Getreideexporte; seine Blockade und wiederholter Beschuss seit 2022 haben die globalen Lebensmittelpreise direkt beeinflusst.'),

('piraeus_port', 'Port of Piraeus', 'Hafen Piraeus', 'port',
 '{"type":"Point","coordinates":[23.63,37.94]}'::jsonb,
 ARRAY['containers'], ARRAY['EUROPE-GREECE'], 3,
 '{"share_note": "Chinas largest port investment in Europe and a Mediterranean gateway"}'::jsonb,
 'Mediterranean gateway port majority-owned by Chinas COSCO, central to Chinese trade access into Southeastern Europe.',
 'Mittelmeer-Hafen mehrheitlich im Besitz von Chinas COSCO, zentral fuer den chinesischen Handelszugang nach Suedosteuropa.'),

('hamburg_port', 'Port of Hamburg', 'Hafen Hamburg', 'port',
 '{"type":"Point","coordinates":[9.97,53.53]}'::jsonb,
 ARRAY['containers'], ARRAY['EUROPE-GERMANY'], 3,
 '{"share_note": "Germanys largest port and a key hub for Central and Eastern Europe"}'::jsonb,
 'Germany largest seaport and a critical hub feeding trade into Central and Eastern Europe.',
 'Deutschlands groesster Seehafen und ein kritischer Knotenpunkt fuer den Handel nach Mittel- und Osteuropa.'),

('port_of_la_long_beach', 'Port of Los Angeles/Long Beach', 'Hafen Los Angeles/Long Beach', 'port',
 '{"type":"Point","coordinates":[-118.25,33.74]}'::jsonb,
 ARRAY['containers'], ARRAY['AMERICAS-USA'], 4,
 '{"share_note": "the busiest container gateway in the United States"}'::jsonb,
 'The largest US container gateway, handling a substantial share of trans-Pacific trade with Asia.',
 'Das groesste US-Container-Tor, das einen erheblichen Teil des transpazifischen Handels mit Asien abwickelt.'),

('santos_port', 'Port of Santos', 'Hafen Santos', 'port',
 '{"type":"Point","coordinates":[-46.33,-23.96]}'::jsonb,
 ARRAY['grain','containers'], ARRAY['AMERICAS-BRAZIL'], 3,
 '{"share_note": "Latin Americas busiest port and Brazils main soy and grain export outlet"}'::jsonb,
 'Latin America busiest port and the primary export outlet for Brazilian soybeans, sugar and grain.',
 'Lateinamerikas verkehrsreichster Hafen und das wichtigste Exporttor fuer brasilianische Sojabohnen, Zucker und Getreide.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- PRODUCTION CLUSTERS (Polygon, coarse hull)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('permian_basin', 'Permian Basin', 'Perm-Becken', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-104.0,33.5],[-101.5,33.5],[-101.5,31.0],[-104.0,31.0],[-104.0,33.5]]]}'::jsonb,
 ARRAY['oil','gas'], ARRAY['AMERICAS-USA'], 4,
 '{"share_note": "the largest US shale oil and gas producing region"}'::jsonb,
 'The largest US shale play, whose output has made the country a top global oil and gas producer and swing exporter.',
 'Das groesste US-Schieferoelgebiet, dessen Foerderung das Land zu einem der weltweit fuehrenden Oel- und Gasproduzenten und Swing-Exporteuren gemacht hat.'),

('ghawar_field', 'Ghawar Field', 'Ghawar-Feld', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[49.3,26.0],[49.9,26.0],[49.9,24.7],[49.3,24.7],[49.3,26.0]]]}'::jsonb,
 ARRAY['oil'], ARRAY['MIDEAST-SAUDI'], 5,
 '{"share_note": "the largest conventional oil field ever discovered"}'::jsonb,
 'The worlds largest conventional oil field, underpinning Saudi Arabia role as the systemically important swing producer.',
 'Das groesste konventionelle Oelfeld der Welt, Grundlage fuer Saudi-Arabiens Rolle als systemisch wichtiger Swing-Produzent.'),

('west_siberian_basin', 'West Siberian Basin', 'Westsibirisches Becken', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[65.0,64.0],[78.0,64.0],[78.0,58.0],[65.0,58.0],[65.0,64.0]]]}'::jsonb,
 ARRAY['oil','gas'], ARRAY['EUROPE-RUSSIA'], 4,
 '{"share_note": "the source of the majority of Russias oil and gas production"}'::jsonb,
 'Russia core hydrocarbon-producing region, funding the state budget and underpinning its energy leverage over Europe and Asia.',
 'Russlands zentrale Kohlenwasserstoff-Foerderregion, finanziert den Staatshaushalt und untermauert seinen energiepolitischen Einfluss auf Europa und Asien.'),

('pilbara_iron_belt', 'Pilbara Iron Ore Belt', 'Pilbara-Eisenerzguertel', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[115.5,-20.0],[119.5,-20.0],[119.5,-23.5],[115.5,-23.5],[115.5,-20.0]]]}'::jsonb,
 ARRAY['iron_ore'], ARRAY['ASIA-AUSTRALIA'], 4,
 '{"share_note": "supplies the majority of the seaborne iron ore market, mostly to China"}'::jsonb,
 'The worlds premier iron ore mining region, whose exports feed Chinese steelmaking and anchor the Australia-China trade relationship.',
 'Die weltweit fuehrende Eisenerz-Foerderregion, deren Exporte die chinesische Stahlproduktion versorgen und die Handelsbeziehung zwischen Australien und China verankern.'),

('australian_lithium_belt', 'Australian Lithium Belt (WA)', 'Australischer Lithiumguertel (WA)', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[117.0,-31.0],[121.5,-31.0],[121.5,-34.5],[117.0,-34.5],[117.0,-31.0]]]}'::jsonb,
 ARRAY['lithium'], ARRAY['ASIA-AUSTRALIA'], 3,
 '{"share_note": "the largest source of mined lithium globally"}'::jsonb,
 'Western Australia hard-rock lithium mines supply the majority of the worlds mined lithium feeding battery and EV supply chains.',
 'Westaustraliens Hartgestein-Lithiumminen liefern den Grossteil des weltweit geforderten Lithiums fuer Batterie- und Elektrofahrzeug-Lieferketten.'),

('ukrainian_grain_belt', 'Ukrainian Grain Belt', 'Ukrainischer Getreideguertel', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[24.0,51.0],[36.0,51.0],[36.0,47.0],[24.0,47.0],[24.0,51.0]]]}'::jsonb,
 ARRAY['grain'], ARRAY['EUROPE-UKRAINE'], 4,
 '{"share_note": "one of the worlds most important wheat, corn and sunflower oil producing regions"}'::jsonb,
 'The fertile black-soil heartland that made Ukraine a top global grain exporter; war disruption here has repeatedly moved world food prices.',
 'Das fruchtbare Schwarzerde-Kernland, das die Ukraine zu einem der weltweit fuehrenden Getreideexporteure machte; kriegsbedingte Stoerungen haben wiederholt die globalen Lebensmittelpreise bewegt.'),

('tsmc_hsinchu', 'TSMC Hsinchu Semiconductor Cluster', 'TSMC Hsinchu Halbleiter-Cluster', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[120.95,24.78],[121.05,24.78],[121.05,24.7],[120.95,24.7],[120.95,24.78]]]}'::jsonb,
 ARRAY['semiconductors'], ARRAY['ASIA-TAIWAN'], 5,
 '{"share_note": "produces the large majority of the worlds most advanced logic chips"}'::jsonb,
 'The worlds most advanced chip fabrication cluster; its concentration in Taiwan is the central material stake in any Taiwan Strait contingency.',
 'Der fortschrittlichste Chip-Fertigungscluster der Welt; seine Konzentration in Taiwan ist der zentrale materielle Einsatz jedes Taiwanstrasse-Konflikts.'),

('ara_chemical_cluster', 'ARA Chemical Cluster (Netherlands/Belgium)', 'ARA-Chemiecluster (Niederlande/Belgien)', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[3.6,51.1],[4.6,51.1],[4.6,51.7],[3.6,51.7],[3.6,51.1]]]}'::jsonb,
 ARRAY['chemicals','oil'], ARRAY['EUROPE-GERMANY'], 3,
 '{"share_note": "the largest integrated petrochemical cluster in Europe"}'::jsonb,
 'The Antwerp-Rotterdam-Amsterdam refining and petrochemical complex, Europe largest integrated industrial cluster and highly exposed to feedstock price shocks.',
 'Der Raffinerie- und Petrochemie-Komplex Antwerpen-Rotterdam-Amsterdam, Europas groesster integrierter Industriecluster und stark exponiert gegenueber Rohstoffpreisschocks.'),

('rhine_ruhr_industrial', 'German Industrial Rhine-Ruhr Cluster', 'Deutscher Industriecluster Rhein-Ruhr', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[6.3,51.0],[7.6,51.0],[7.6,51.7],[6.3,51.7],[6.3,51.0]]]}'::jsonb,
 ARRAY['chemicals'], ARRAY['EUROPE-GERMANY'], 3,
 '{"share_note": "historically the industrial core of the German and European economy"}'::jsonb,
 'Germany historic industrial heartland of steel, chemicals and heavy manufacturing, and a bellwether for European energy cost competitiveness.',
 'Deutschlands historisches industrielles Kernland fuer Stahl, Chemie und Schwerindustrie, und ein Fruehindikator fuer die europaeische Energiekostenwettbewerbsfaehigkeit.'),

('qatar_north_field', 'Qatari North Field LNG', 'Katarisches Nordfeld LNG', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[51.0,26.3],[52.3,26.3],[52.3,25.3],[51.0,25.3],[51.0,26.3]]]}'::jsonb,
 ARRAY['lng','gas'], ARRAY['MIDEAST-GULF'], 4,
 '{"share_note": "part of the largest natural gas field in the world, shared with Iran"}'::jsonb,
 'Qatar share of the worlds largest gas field and the base of its LNG export capacity, a critical alternative supply for Europe and Asia.',
 'Katars Anteil am groessten Gasfeld der Welt und Grundlage seiner LNG-Exportkapazitaet, eine kritische alternative Versorgungsquelle fuer Europa und Asien.'),

('guinea_bauxite_belt', 'Guinea Bauxite Belt', 'Guineischer Bauxitguertel', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-14.5,10.0],[-11.5,10.0],[-11.5,8.0],[-14.5,8.0],[-14.5,10.0]]]}'::jsonb,
 ARRAY['bauxite'], ARRAY['AFRICA-GUINEA'], 3,
 '{"share_note": "one of the largest bauxite reserves and exporters in the world"}'::jsonb,
 'Guinea vast bauxite deposits supply a large share of global alumina and aluminum production, making the country pivotal to that supply chain.',
 'Guineas riesige Bauxitvorkommen versorgen einen Grossteil der weltweiten Aluminiumoxid- und Aluminiumproduktion, was das Land zentral fuer diese Lieferkette macht.'),

('katanga_copper_belt', 'DRC Copper-Cobalt Belt (Katanga)', 'DRK Kupfer-Kobalt-Guertel (Katanga)', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[25.5,-10.0],[28.0,-10.0],[28.0,-12.5],[25.5,-12.5],[25.5,-10.0]]]}'::jsonb,
 ARRAY['copper','cobalt'], ARRAY['AFRICA-DRC'], 4,
 '{"share_note": "produces the large majority of the worlds mined cobalt"}'::jsonb,
 'The source of most of the worlds cobalt and a major copper producer, making it indispensable to battery and EV supply chains despite chronic instability.',
 'Die Quelle des meisten weltweit geforderten Kobalts und ein bedeutender Kupferproduzent, unverzichtbar fuer Batterie- und Elektrofahrzeug-Lieferketten trotz chronischer Instabilitaet.'),

('atacama_lithium_triangle', 'Chilean Lithium Triangle (Atacama)', 'Chilenisches Lithiumdreieck (Atacama)', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[-68.5,-22.5],[-67.3,-22.5],[-67.3,-24.2],[-68.5,-24.2],[-68.5,-22.5]]]}'::jsonb,
 ARRAY['lithium'], ARRAY['AMERICAS-CHILE'], 4,
 '{"share_note": "part of the salt-flat region holding a large share of the worlds identified lithium resources"}'::jsonb,
 'The Chilean portion of the Andean salt-flat lithium triangle, a resource base central to global battery supply chain diversification away from China processing dominance.',
 'Der chilenische Teil des andinen Salzsee-Lithiumdreiecks, eine Rohstoffbasis, die zentral fuer die Diversifizierung der globalen Batterie-Lieferkette weg von Chinas Verarbeitungsdominanz ist.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- PIPELINES (LineString, approximate route)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES
('power_of_siberia', 'Power of Siberia Pipeline', 'Pipeline Kraft Sibiriens', 'pipeline',
 '{"type":"LineString","coordinates":[[118.0,53.5],[122.0,50.5],[126.5,48.0],[127.5,50.5]]}'::jsonb,
 ARRAY['gas'], ARRAY['EUROPE-RUSSIA', 'ASIA-CHINA'], 3,
 '{"share_note": "Russias flagship gas export pipeline redirecting supply eastward to China"}'::jsonb,
 'Russia main eastward gas pipeline to China, central to Moscow pivot away from European markets after 2022 sanctions.',
 'Russlands wichtigste Gaspipeline nach China, zentral fuer Moskaus Abkehr von europaeischen Maerkten nach den Sanktionen von 2022.'),

('turkstream', 'TurkStream Pipeline', 'TurkStream-Pipeline', 'pipeline',
 '{"type":"LineString","coordinates":[[37.8,44.7],[36.5,43.5],[33.5,42.0],[28.5,41.2],[26.5,41.8]]}'::jsonb,
 ARRAY['gas'], ARRAY['EUROPE-RUSSIA', 'MIDEAST-TURKEY'], 3,
 '{"share_note": "Russias main remaining gas export route into Southeastern Europe via Turkey"}'::jsonb,
 'A subsea gas pipeline under the Black Sea that became one of Russia few remaining gas export routes into Europe after other lines were cut or sabotaged.',
 'Eine Unterwasser-Gaspipeline unter dem Schwarzen Meer, die zu einer von Russlands wenigen verbliebenen Gasexportrouten nach Europa wurde, nachdem andere Leitungen gekappt oder sabotiert wurden.'),

('btc_pipeline', 'Baku-Tbilisi-Ceyhan Pipeline', 'Baku-Tiflis-Ceyhan-Pipeline', 'pipeline',
 '{"type":"LineString","coordinates":[[49.8,40.4],[44.8,41.7],[41.6,41.0],[35.9,36.9]]}'::jsonb,
 ARRAY['oil'], ARRAY['MIDEAST-TURKEY', 'EUROPE-RUSSIA'], 3,
 '{"share_note": "a major non-Russian, non-Hormuz route for Caspian oil to reach world markets"}'::jsonb,
 'Carries Azerbaijani Caspian oil to the Mediterranean while bypassing both Russian territory and the Strait of Hormuz, making it a strategic diversification route.',
 'Transportiert aserbaidschanisches Kaspi-Oel zum Mittelmeer unter Umgehung sowohl russischen Territoriums als auch der Strasse von Hormus, eine strategische Diversifizierungsroute.'),

('druzhba_pipeline_west', 'Druzhba Pipeline (Western Segment)', 'Druschba-Pipeline (Westabschnitt)', 'pipeline',
 '{"type":"LineString","coordinates":[[38.0,52.5],[30.5,50.5],[24.0,50.5],[19.0,50.0]]}'::jsonb,
 ARRAY['oil'], ARRAY['EUROPE-RUSSIA', 'EUROPE-UKRAINE', 'EUROPE-POLAND'], 3,
 '{"share_note": "historically one of the worlds longest oil pipelines, still supplying select central European refineries"}'::jsonb,
 'Soviet-era pipeline still carrying Russian crude to select central European refineries; its western segment through Ukraine has been repeatedly disrupted since 2022.',
 'Pipeline aus Sowjetzeiten, die weiterhin russisches Rohoel zu ausgewaehlten mitteleuropaeischen Raffinerien transportiert; ihr Westabschnitt durch die Ukraine wurde seit 2022 wiederholt gestoert.')

ON CONFLICT (id) DO NOTHING;
