-- "Gas everything" batch: the LNG import/export terminals and gas fields
-- that sit downstream and upstream of the pipelines/chokepoints already
-- seeded. These are the dependency endpoints -- where gas actually lands,
-- ships from, or comes out of the ground. Idempotent: safe to re-run.
-- See 20260703_strategic_assets.sql for schema.

-- =========================================================================
-- LNG IMPORT / REGAS TERMINALS (Point)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES

('futtsu_sodegaura_lng', 'Futtsu-Sodegaura LNG Terminals (Tokyo Bay)', 'Futtsu-Sodegaura LNG-Terminals (Tokio-Bucht)', 'facility',
 '{"type":"Point","coordinates":[139.85,35.3]}'::jsonb,
 ARRAY['lng'], ARRAY['ASIA-JAPAN'], 4,
 '{"share_note": "among the largest LNG receiving terminal clusters in the world, feeding the Tokyo metropolitan grid"}'::jsonb,
 'The Tokyo Bay LNG terminal cluster that keeps Japan power-starved capital region running, a legacy of the post-Fukushima shift away from nuclear.',
 'Der LNG-Terminalcluster in der Tokio-Bucht, der die energiehungrige japanische Hauptstadtregion versorgt, ein Erbe der Abkehr von der Kernkraft nach Fukushima.'),

('incheon_pyeongtaek_lng', 'Incheon-Pyeongtaek LNG Terminals', 'Incheon-Pyeongtaek LNG-Terminals', 'facility',
 '{"type":"Point","coordinates":[126.55,37.15]}'::jsonb,
 ARRAY['lng'], ARRAY['ASIA-SOUTHKOREA'], 4,
 '{"share_note": "the two largest LNG import terminals feeding the South Korean grid"}'::jsonb,
 'South Korea main LNG import gateway near Seoul, critical because the country has no pipeline gas option and depends entirely on seaborne cargoes.',
 'Suedkoreas wichtigstes LNG-Einfuhrtor nahe Seoul, entscheidend, weil das Land keine Pipeline-Option hat und vollstaendig auf Schiffsladungen angewiesen ist.'),

('yancheng_binhai_lng', 'Yancheng-Binhai LNG Terminal', 'Yancheng-Binhai LNG-Terminal', 'facility',
 '{"type":"Point","coordinates":[120.3,34.25]}'::jsonb,
 ARRAY['lng'], ARRAY['ASIA-CHINA'], 3,
 '{"share_note": "one of Chinas fast-expanding coastal LNG receiving terminals"}'::jsonb,
 'A coastal receiving terminal feeding gas into the Jiangsu grid, part of Chinas buildout of LNG import capacity to diversify away from pipeline dependence on Russia and Central Asia.',
 'Ein Kuestenterminal, das Gas in das Jiangsu-Netz einspeist, Teil von Chinas Ausbau der LNG-Importkapazitaet zur Diversifizierung weg von der Pipeline-Abhaengigkeit von Russland und Zentralasien.'),

('zeebrugge_lng', 'Zeebrugge LNG Terminal', 'LNG-Terminal Zeebrugge', 'facility',
 '{"type":"Point","coordinates":[3.2,51.33]}'::jsonb,
 ARRAY['lng'], ARRAY['NON-STATE-EU'], 3,
 '{"share_note": "one of the largest LNG import and reloading hubs on the European continent"}'::jsonb,
 'A major Belgian LNG import and reloading hub that re-exports cargoes onward into the wider European pipeline network.',
 'Ein bedeutendes belgisches LNG-Einfuhr- und Umschlagzentrum, das Ladungen weiter in das europaeische Pipelinenetz re-exportiert.'),

('gate_rotterdam_lng', 'Gate Terminal Rotterdam', 'Gate-Terminal Rotterdam', 'facility',
 '{"type":"Point","coordinates":[4.02,51.98]}'::jsonb,
 ARRAY['lng'], ARRAY['EUROPE-BENELUX'], 4,
 '{"share_note": "the Netherlands largest LNG import terminal and a key Northwest European entry point"}'::jsonb,
 'The Netherlands main LNG gateway, a critical Northwest European entry point since the loss of Russian pipeline gas.',
 'Die Niederlande wichtigstes LNG-Tor, ein entscheidender nordwesteuropaeischer Einfuhrpunkt seit dem Wegfall russischen Pipelinegases.'),

('wilhelmshaven_fsru', 'Wilhelmshaven FSRU', 'FSRU Wilhelmshaven', 'facility',
 '{"type":"Point","coordinates":[8.15,53.53]}'::jsonb,
 ARRAY['lng'], ARRAY['EUROPE-GERMANY'], 4,
 '{"share_note": "Germanys first LNG import terminal, built in under a year after the loss of Russian pipeline gas"}'::jsonb,
 'The floating terminal Germany rushed into service after Nord Stream went dark, now a lifeline import point for a country that had almost no LNG capacity before 2022.',
 'Das schwimmende Terminal, das Deutschland nach dem Ausfall von Nord Stream im Eiltempo in Betrieb nahm, heute ein lebenswichtiger Einfuhrpunkt fuer ein Land, das vor 2022 kaum LNG-Kapazitaet besass.'),

('swinoujscie_lng', 'Swinoujscie LNG Terminal', 'LNG-Terminal Swinemuende', 'facility',
 '{"type":"Point","coordinates":[14.27,53.98]}'::jsonb,
 ARRAY['lng'], ARRAY['EUROPE-VISEGRAD'], 4,
 '{"share_note": "Polands first LNG terminal and a cornerstone of its pivot away from Russian gas"}'::jsonb,
 'Poland original LNG import terminal on the Baltic coast, central to Warsaw long campaign to end dependence on Russian pipeline supply.',
 'Polens urspruengliches LNG-Einfuhrterminal an der Ostseekueste, zentral fuer Warschaus langjaehrige Kampagne zur Beendigung der Abhaengigkeit von russischen Pipelinelieferungen.'),

('klaipeda_fsru', 'Klaipeda FSRU', 'FSRU Klaipeda', 'facility',
 '{"type":"Point","coordinates":[21.09,55.7]}'::jsonb,
 ARRAY['lng'], ARRAY['EUROPE-BALTIC'], 3,
 '{"share_note": "the terminal that ended the Baltic states single-supplier dependence on Russian gas"}'::jsonb,
 'The floating terminal Lithuania nicknamed Independence, which broke the Baltic states former total reliance on Gazprom pipeline gas.',
 'Das schwimmende Terminal, das Litauen Unabhaengigkeit nannte und die frueher vollstaendige Abhaengigkeit der baltischen Staaten von Gazprom-Pipelinegas beendete.'),

('revithoussa_lng', 'Revithoussa LNG Terminal', 'LNG-Terminal Revithoussa', 'facility',
 '{"type":"Point","coordinates":[23.55,38.02]}'::jsonb,
 ARRAY['lng'], ARRAY['EUROPE-SOUTH'], 3,
 '{"share_note": "Greeces main LNG import terminal and a growing corridor for gas into the Balkans"}'::jsonb,
 'Greece primary LNG entry point near Athens, increasingly used as a re-supply corridor for Balkan and Southeastern European buyers cutting Russian pipeline ties.',
 'Griechenlands wichtigstes LNG-Einfuhrterminal nahe Athen, zunehmend als Nachschubkorridor fuer Balkan- und suedosteuropaeische Abnehmer genutzt, die russische Pipelineverbindungen kappen.'),

('barcelona_sagunto_lng', 'Barcelona-Sagunto LNG Terminals', 'LNG-Terminals Barcelona-Sagunto', 'facility',
 '{"type":"Point","coordinates":[2.15,41.35]}'::jsonb,
 ARRAY['lng'], ARRAY['NON-STATE-EU'], 3,
 '{"share_note": "part of Spains outsized LNG import capacity, the largest regasification base in Europe"}'::jsonb,
 'Two of the Spanish terminals that give the country Europe largest LNG regasification capacity, though poor interconnection limits how much can reach France and beyond.',
 'Zwei der spanischen Terminals, die dem Land Europas groesste LNG-Regasifizierungskapazitaet verleihen, wobei schwache Verbindungsleitungen begrenzen, wie viel Gas nach Frankreich und darueber hinaus gelangt.'),

('dahej_lng', 'Dahej LNG Terminal', 'LNG-Terminal Dahej', 'facility',
 '{"type":"Point","coordinates":[72.62,21.68]}'::jsonb,
 ARRAY['lng'], ARRAY['ASIA-INDIA'], 4,
 '{"share_note": "Indias largest LNG import terminal by capacity"}'::jsonb,
 'India single largest LNG import terminal, a critical feed point for a gas market growing faster than domestic production can supply.',
 'Indiens groesstes LNG-Einfuhrterminal, ein entscheidender Einspeisepunkt fuer einen Gasmarkt, der schneller waechst, als die heimische Foerderung liefern kann.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- LNG EXPORT TERMINALS (Point)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES

('freeport_lng', 'Freeport LNG', 'Freeport LNG', 'facility',
 '{"type":"Point","coordinates":[-95.31,28.94]}'::jsonb,
 ARRAY['lng'], ARRAY['AMERICAS-USA'], 3,
 '{"share_note": "one of the largest US LNG export terminals on the Texas Gulf Coast"}'::jsonb,
 'A major US Gulf Coast export terminal whose 2022 fire and prolonged outage showed how a single facility can tighten global LNG supply.',
 'Ein bedeutendes US-Exportterminal an der texanischen Golfkueste, dessen Brand 2022 und laengerer Ausfall zeigten, wie eine einzelne Anlage das globale LNG-Angebot verknappen kann.'),

('cameron_lng', 'Cameron LNG', 'Cameron LNG', 'facility',
 '{"type":"Point","coordinates":[-93.34,29.79]}'::jsonb,
 ARRAY['lng'], ARRAY['AMERICAS-USA'], 3,
 '{"share_note": "a major Louisiana Gulf Coast LNG export terminal"}'::jsonb,
 'A Louisiana export terminal that ships US shale gas to Asian and European buyers under long-term offtake contracts.',
 'Ein Exportterminal in Louisiana, das US-Schiefergas im Rahmen langfristiger Abnahmevertraege an asiatische und europaeische Kaeufer verschifft.'),

('corpus_christi_lng', 'Corpus Christi LNG', 'Corpus Christi LNG', 'facility',
 '{"type":"Point","coordinates":[-97.28,27.83]}'::jsonb,
 ARRAY['lng'], ARRAY['AMERICAS-USA'], 4,
 '{"share_note": "one of the largest LNG export terminals in the United States"}'::jsonb,
 'A top-tier US LNG export terminal that became a core supply source for Europe after 2022, distinct from the crude-oil export hub of the same city.',
 'Ein erstklassiges US-LNG-Exportterminal, das nach 2022 zu einer zentralen Versorgungsquelle fuer Europa wurde, zu unterscheiden vom Rohoel-Exportknoten derselben Stadt.'),

('hammerfest_melkoya_lng', 'Hammerfest LNG (Melkoya)', 'Hammerfest LNG (Melkoya)', 'facility',
 '{"type":"Point","coordinates":[23.6,70.68]}'::jsonb,
 ARRAY['lng'], ARRAY['NON-STATE-EU'], 3,
 '{"share_note": "Europes northernmost LNG export plant, fed by the Snohvit field in the Barents Sea"}'::jsonb,
 'Norway Arctic LNG export plant on Melkoya island, a niche but symbolically important non-Russian gas source in the high north.',
 'Norwegens arktische LNG-Exportanlage auf der Insel Melkoya, eine kleine, aber symbolisch wichtige nicht-russische Gasquelle im hohen Norden.'),

('bintulu_lng', 'Bintulu LNG Complex', 'LNG-Komplex Bintulu', 'facility',
 '{"type":"Point","coordinates":[113.07,3.17]}'::jsonb,
 ARRAY['lng'], ARRAY['ASIA-SOUTHEAST'], 4,
 '{"share_note": "one of the largest single-site LNG export complexes in the world"}'::jsonb,
 'Malaysia flagship LNG export complex on Borneo, a long-running, reliable supplier to Northeast Asian buyers.',
 'Malaysias fuehrender LNG-Exportkomplex auf Borneo, ein langjaehriger, verlaesslicher Lieferant fuer nordostasiatische Abnehmer.'),

('idku_damietta_lng', 'Idku-Damietta LNG Terminals', 'LNG-Terminals Idku-Damietta', 'facility',
 '{"type":"Point","coordinates":[31.3,31.35]}'::jsonb,
 ARRAY['lng'], ARRAY['MIDEAST-EGYPT', 'MIDEAST-EGYPT'], 3,
 '{"share_note": "Egypts two Mediterranean LNG export plants"}'::jsonb,
 'Egypt Mediterranean coast export terminals, which have swung between exporting surplus gas and being idled during domestic shortages depending on the year.',
 'Aegyptens Exportterminals an der Mittelmeerkueste, die je nach Jahr zwischen Exportueberschuss und Stilllegung wegen innerstaatlicher Engpaesse schwankten.'),

('arzew_skikda_lng', 'Arzew-Skikda LNG Complex', 'LNG-Komplex Arzew-Skikda', 'facility',
 '{"type":"Point","coordinates":[-0.28,35.85]}'::jsonb,
 ARRAY['lng'], ARRAY['NON-STATE-EU'], 4,
 '{"share_note": "Algerias core Mediterranean LNG and pipeline gas export base"}'::jsonb,
 'Algeria main gas export complex, a critical southern supply route for Italy and Spain as Europe worked to replace Russian pipeline volumes.',
 'Algeriens wichtigster Gasexportkomplex, eine kritische suedliche Versorgungsroute fuer Italien und Spanien, waehrend Europa daran arbeitete, russische Pipelinemengen zu ersetzen.'),

('coral_south_fsru', 'Coral South FLNG', 'Coral South FLNG', 'facility',
 '{"type":"Point","coordinates":[40.85,-11.2]}'::jsonb,
 ARRAY['lng'], ARRAY[]::text[], 3,
 '{"share_note": "Africas first deepwater floating LNG facility, offshore Mozambique"}'::jsonb,
 'A floating liquefaction vessel moored off Mozambique that opened one of the newest frontiers in global LNG supply, though onshore expansion nearby has been slowed by insurgent violence.',
 'Ein schwimmendes Verfluessigungsschiff vor Mosambik, das eine der neuesten Grenzen der globalen LNG-Versorgung eroeffnete, waehrend der geplante Ausbau an Land durch Aufstaendische verzoegert wurde.'),

('png_lng', 'PNG LNG', 'PNG LNG', 'facility',
 '{"type":"Point","coordinates":[147.13,-9.48]}'::jsonb,
 ARRAY['lng'], ARRAY[]::text[], 2,
 '{"share_note": "Papua New Guineas sole large-scale LNG export project"}'::jsonb,
 'A single-project gas economy for Papua New Guinea, shipping almost entirely to long-term Japanese and Chinese buyers.',
 'Eine auf ein einziges Projekt gestuetzte Gaswirtschaft fuer Papua-Neuguinea, die fast ausschliesslich an langfristige japanische und chinesische Abnehmer liefert.'),

('gladstone_lng', 'Gladstone LNG Cluster', 'LNG-Cluster Gladstone', 'facility',
 '{"type":"Point","coordinates":[151.28,-23.85]}'::jsonb,
 ARRAY['lng'], ARRAY['OCEANIA-AUSTRALIA'], 3,
 '{"share_note": "three coal-seam-gas-fed LNG export plants on Australias east coast"}'::jsonb,
 'Australia east coast LNG export hub, whose demand for feed gas has repeatedly collided with domestic east-coast gas shortages and price spikes.',
 'Australiens LNG-Exportzentrum an der Ostkueste, dessen Bedarf an Einsatzgas wiederholt mit innerstaatlichen Gasengpaessen und Preisspitzen an der Ostkueste kollidierte.')

ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- GAS FIELDS (Polygon, coarse hull)
-- =========================================================================

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de) VALUES

('south_pars_field', 'South Pars Field (Iran)', 'Suedpars-Feld (Iran)', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[52.0,27.3],[52.8,27.3],[52.8,26.6],[52.0,26.6],[52.0,27.3]]]}'::jsonb,
 ARRAY['gas'], ARRAY['MIDEAST-IRAN'], 4,
 '{"share_note": "Irans share of the worlds largest natural gas field, shared with Qatar"}'::jsonb,
 'Iran side of the giant offshore gas field it shares with Qatar, held back from its full potential by sanctions that have blocked the foreign capital needed to develop it.',
 'Irans Anteil am riesigen Offshore-Gasfeld, das es sich mit Katar teilt, weit unter seinem vollen Potenzial gehalten durch Sanktionen, die das zur Erschliessung noetige auslaendische Kapital blockieren.'),

('shah_deniz_field', 'Shah Deniz Field', 'Shah-Deniz-Feld', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[50.1,40.2],[50.7,40.2],[50.7,39.7],[50.1,39.7],[50.1,40.2]]]}'::jsonb,
 ARRAY['gas'], ARRAY['EUROPE-AZERBAIJAN'], 3,
 '{"share_note": "Azerbaijans flagship Caspian gas field feeding the Southern Gas Corridor to Europe"}'::jsonb,
 'Azerbaijan largest gas field, whose output feeds the Southern Gas Corridor and has made the country a small but valued non-Russian supplier to Southeastern Europe.',
 'Aserbaidschans groesstes Gasfeld, dessen Foerderung den Suedlichen Gaskorridor speist und das Land zu einem kleinen, aber geschaetzten nicht-russischen Lieferanten fuer Suedosteuropa gemacht hat.'),

('hassi_rmel_field', 'Hassi R Mel Field', 'Hassi-R-Mel-Feld', 'production_cluster',
 '{"type":"Polygon","coordinates":[[[3.0,33.1],[3.6,33.1],[3.6,32.6],[3.0,32.6],[3.0,33.1]]]}'::jsonb,
 ARRAY['gas'], ARRAY['NON-STATE-EU'], 4,
 '{"share_note": "Algerias largest gas field and the hub feeding its export pipeline network"}'::jsonb,
 'Algeria largest gas field and the central hub feeding both its pipeline exports to Europe and its Mediterranean LNG plants.',
 'Algeriens groesstes Gasfeld und der zentrale Knotenpunkt, der sowohl seine Pipeline-Exporte nach Europa als auch seine LNG-Anlagen am Mittelmeer speist.')

ON CONFLICT (id) DO NOTHING;
