-- eu_cohesion_theater — ingest expansion: national-conservative / sovereigntist EU media.
-- The theater's feed had ZERO such outlets (only mainstream/liberal + wire + Kremlin +
-- Chinese state), so the sympathetic-to-sovereigntist narratives could only ever draw on
-- reported speech. This adds a balanced, established set (not fringe/banned) across the
-- theater's member states, and appends them to the Western narrative coalitions so their
-- coverage attributes. framing_required + centroid gates route each title correctly (a
-- French outlet only attributes to FR-centroid titles; sovereigntist framing keywords pick
-- up the sympathetic pieces, mainstream-critical keywords the rest).
-- NOTE: Google News RSS returns only recent items, so historical backfill is limited —
-- these populate going forward as the daemon ingests; a one-off fetch seeds recent coverage.
-- feeds.name is what the fetcher stores as titles_v3.publisher_name, so coalition names
-- below match feed names exactly. Idempotent (ON CONFLICT url / DO NOTHING).
SET client_encoding TO 'UTF8';

INSERT INTO feeds (name, url, language_code, country_code, source_domain, slug, priority, is_active) VALUES
-- Germany
('WELT',            'https://news.google.com/rss/search?q=site:welt.de&hl=de&gl=DE&ceid=DE:de',            'de','DE','welt.de','welt',1,true),
('Junge Freiheit',  'https://news.google.com/rss/search?q=site:jungefreiheit.de&hl=de&gl=DE&ceid=DE:de',  'de','DE','jungefreiheit.de','junge-freiheit',1,true),
('NIUS',            'https://news.google.com/rss/search?q=site:nius.de&hl=de&gl=DE&ceid=DE:de',            'de','DE','nius.de','nius',1,true),
('Cicero',          'https://news.google.com/rss/search?q=site:cicero.de&hl=de&gl=DE&ceid=DE:de',          'de','DE','cicero.de','cicero',1,true),
('Tichys Einblick', 'https://news.google.com/rss/search?q=site:tichyseinblick.de&hl=de&gl=DE&ceid=DE:de', 'de','DE','tichyseinblick.de','tichys-einblick',1,true),
-- France
('Valeurs Actuelles','https://news.google.com/rss/search?q=site:valeursactuelles.com&hl=fr&gl=FR&ceid=FR:fr','fr','FR','valeursactuelles.com','valeurs-actuelles',1,true),
('Le Point',         'https://news.google.com/rss/search?q=site:lepoint.fr&hl=fr&gl=FR&ceid=FR:fr',         'fr','FR','lepoint.fr','le-point',1,true),
('Causeur',          'https://news.google.com/rss/search?q=site:causeur.fr&hl=fr&gl=FR&ceid=FR:fr',         'fr','FR','causeur.fr','causeur',1,true),
('Boulevard Voltaire','https://news.google.com/rss/search?q=site:bvoltaire.fr&hl=fr&gl=FR&ceid=FR:fr',      'fr','FR','bvoltaire.fr','boulevard-voltaire',1,true),
-- Italy
('Il Giornale',      'https://news.google.com/rss/search?q=site:ilgiornale.it&hl=it&gl=IT&ceid=IT:it',      'it','IT','ilgiornale.it','il-giornale',1,true),
('Libero',           'https://news.google.com/rss/search?q=site:liberoquotidiano.it&hl=it&gl=IT&ceid=IT:it','it','IT','liberoquotidiano.it','libero',1,true),
('La Verità',        'https://news.google.com/rss/search?q=site:laverita.info&hl=it&gl=IT&ceid=IT:it',      'it','IT','laverita.info','la-verita',1,true),
-- Spain
('OKdiario',         'https://news.google.com/rss/search?q=site:okdiario.com&hl=es&gl=ES&ceid=ES:es',       'es','ES','okdiario.com','okdiario',1,true),
('El Debate',        'https://news.google.com/rss/search?q=site:eldebate.com&hl=es&gl=ES&ceid=ES:es',       'es','ES','eldebate.com','el-debate',1,true),
('Libertad Digital', 'https://news.google.com/rss/search?q=site:libertaddigital.com&hl=es&gl=ES&ceid=ES:es','es','ES','libertaddigital.com','libertad-digital',1,true),
-- Pan-EU (English)
('Brussels Signal',  'https://news.google.com/rss/search?q=site:brusselssignal.eu&hl=en',                   'en','EU','brusselssignal.eu','brussels-signal',1,true)
ON CONFLICT (url) DO NOTHING;

-- Append the new publishers to every Western narrative coalition (+2 and -1) and both
-- Western theater cards. NOT the Kremlin/-2 narratives (those stay the disjoint Russian
-- bloc). framing_required + framing keywords route sympathetic vs mainstream framing.
UPDATE narratives_v2 SET
  publishers = publishers || ARRAY['WELT','Junge Freiheit','NIUS','Cicero','Tichys Einblick','Valeurs Actuelles','Le Point','Causeur','Boulevard Voltaire','Il Giornale','Libero','La Verità','OKdiario','El Debate','Libertad Digital','Brussels Signal'],
  updated_at = NOW()
WHERE id IN (
  'hungary_eu_standards','hungary_sovereignty_interference',
  'afd_democratic_defense','afd_exclusion_undemocratic',
  'france_republican_defense','france_popular_will',
  'migration_solidarity_rights','migration_national_control',
  'budget_more_europe','budget_national_sovereignty',
  'realignment_firewall_defense','realignment_new_majority',
  'eu_cohesion_hold','eu_sovereigntist_revolt'
);
