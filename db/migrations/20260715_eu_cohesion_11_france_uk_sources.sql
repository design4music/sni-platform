-- eu_cohesion_theater — additional national-scope right-leaning sources for France + UK.
-- Per user: France is a major actor with a rightward electoral trajectory that was
-- under-represented; UK needs an off-mainstream/pro-Brexit voice for a fuller picture.
-- Deliberately NOT marginal outlets: all three France picks are Bolloré-group properties
-- with major national reach and well-documented rightward editorial shifts (CNews = TV
-- news channel, Europe1 = national radio, JDD = national Sunday paper under editor
-- Geoffroy Lejeune since 2023). UK picks are established national outlets (GB News =
-- licensed TV broadcaster, The Spectator = 150+ year national weekly, Daily Express =
-- mass-market national tabloid, historically pro-Brexit).
-- FRANCE: wired into french_nationalist_challenge's SOV_CORE bloc (extends migration 09's
-- restructure) + the theater's -1 card. UK: feeds added for ingest, but NOT wired into any
-- eu_cohesion narrative yet — post_brexit_realignment is deactivated (Brexit friction
-- measured genuinely thin, ~63 hits/120d, see structural re-assessment) and EUROPE-UK was
-- dropped from the theater's centroids. Needs a decision (see chat) before wiring.
SET client_encoding TO 'UTF8';

INSERT INTO feeds (name, url, language_code, country_code, source_domain, slug, priority, is_active) VALUES
('CNews',              'https://news.google.com/rss/search?q=site:cnews.fr&hl=fr&gl=FR&ceid=FR:fr',       'fr','FR','cnews.fr','cnews',1,true),
('Europe 1',           'https://news.google.com/rss/search?q=site:europe1.fr&hl=fr&gl=FR&ceid=FR:fr',      'fr','FR','europe1.fr','europe-1',1,true),
('Le Journal du Dimanche','https://news.google.com/rss/search?q=site:lejdd.fr&hl=fr&gl=FR&ceid=FR:fr',     'fr','FR','lejdd.fr','le-jdd',1,true),
('GB News',            'https://news.google.com/rss/search?q=site:gbnews.com&hl=en-GB&gl=GB&ceid=GB:en',   'en','GB','gbnews.com','gb-news',1,true),
('The Spectator',      'https://news.google.com/rss/search?q=site:spectator.co.uk&hl=en-GB&gl=GB&ceid=GB:en','en','GB','spectator.co.uk','the-spectator',1,true),
('Daily Express',      'https://news.google.com/rss/search?q=site:express.co.uk&hl=en-GB&gl=GB&ceid=GB:en','en','GB','express.co.uk','daily-express',1,true)
ON CONFLICT (url) DO NOTHING;

-- Append the 3 France outlets to the existing SOV_CORE bloc (france_popular_will +
-- the theater's -1 card only; NOT the +2/mainstream side — these are the sovereigntist
-- addition, matching the Valeurs Actuelles/Causeur/Boulevard Voltaire bloc already there).
UPDATE narratives_v2 SET
  publishers = publishers || ARRAY['CNews','Europe 1','Le Journal du Dimanche'],
  updated_at = NOW()
WHERE id IN ('france_popular_will', 'eu_sovereigntist_revolt');
