-- Fills a curation gap: Russia had oil/gas/minerals coverage but no
-- domestic power generation and no grain production cluster, despite being
-- a top-4 nuclear generator and the world's #1 wheat exporter. The earlier
-- batches listed plants/belts by name and simply omitted Russian ones.

INSERT INTO strategic_assets
  (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de)
VALUES
(
  'leningrad_npp',
  'Leningrad Nuclear Power Plant',
  'Kernkraftwerk Leningrad',
  'facility',
  '{"type":"Point","coordinates":[29.06,59.85]}'::jsonb,
  ARRAY['electricity','nuclear'],
  ARRAY['EUROPE-RUSSIA'],
  3,
  '{"share_note":"One of Russia''s largest nuclear stations; anchors power supply for St Petersburg and the northwest."}'::jsonb,
  'One of Russia''s largest nuclear stations, on the Gulf of Finland west of St Petersburg; Russia is a top-four nuclear generator and Rosatom the dominant global reactor exporter.',
  'Eines der groessten Kernkraftwerke Russlands am Finnischen Meerbusen westlich von St. Petersburg; Russland zaehlt zu den vier groessten Kernstromerzeugern und Rosatom ist der fuehrende Reaktorexporteur weltweit.'
),
(
  'sayano_shushenskaya_dam',
  'Sayano-Shushenskaya Dam',
  'Talsperre Sajano-Schuschenskaja',
  'facility',
  '{"type":"Point","coordinates":[91.37,52.83]}'::jsonb,
  ARRAY['electricity','hydro'],
  ARRAY['EUROPE-RUSSIA'],
  3,
  '{"share_note":"Russia''s largest power plant by capacity; feeds Siberian aluminium smelting."}'::jsonb,
  'Russia''s largest power station by capacity, on the Yenisei in Khakassia; powers Siberian aluminium smelting and site of the 2009 turbine-hall disaster.',
  'Groesstes Kraftwerk Russlands nach Kapazitaet am Jenissei in Chakassien; versorgt die sibirische Aluminiumverhuettung und Schauplatz der Turbinenhaus-Katastrophe von 2009.'
),
(
  'south_russia_grain_belt',
  'South Russia Grain Belt',
  'Suedrussischer Getreideguertel',
  'production_cluster',
  '{"type":"Polygon","coordinates":[[[37.5,43.8],[46.5,44.5],[47.0,49.0],[40.0,52.0],[36.0,49.5],[37.5,43.8]]]}'::jsonb,
  ARRAY['wheat','grain'],
  ARRAY['EUROPE-RUSSIA'],
  4,
  '{"share_note":"Krasnodar, Rostov, Stavropol and Central Black Earth regions; source of the world''s largest wheat export flow via Novorossiysk."}'::jsonb,
  'The Kuban, Rostov, Stavropol and Central Black Earth regions feeding the world''s largest wheat export flow through Novorossiysk and the Turkish Straits; sets the price floor for import-dependent buyers across the Middle East and North Africa.',
  'Die Regionen Kuban, Rostow, Stawropol und die zentrale Schwarzerde speisen den groessten Weizenexportstrom der Welt ueber Noworossijsk und die tuerkischen Meerengen; bestimmt das Preisniveau fuer importabhaengige Kaeufer im Nahen Osten und Nordafrika.'
)
ON CONFLICT (id) DO NOTHING;
