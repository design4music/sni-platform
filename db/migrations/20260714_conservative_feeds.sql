-- Fill the US conservative / America-First ingest gap (europe_us_theater review).
-- The feeds table had only Fox News + WSJ on the right; the +2 "America First"
-- narrative pole is starved as a result. Curated to 6 IMPORTANT, high-signal
-- outlets that actually cover trade / NATO burden-sharing / tech-policy (not
-- culture-war), spanning MAGA-populist -> establishment -> FP-realist. Same
-- Google-News-RSS site-search format as every existing feed. ON CONFLICT (url)
-- DO NOTHING (feeds_url_key). Forward-only: affects future ingest, not the
-- frozen archive. Must also be applied on Render to change production ingest.
SET client_encoding TO 'UTF8';

INSERT INTO feeds (name, url, language_code, country_code, is_active, priority, fetch_interval_minutes, source_domain, slug, description, description_de)
VALUES
('New York Post', 'https://news.google.com/rss/search?q=site:nypost.com&hl=en', 'en', 'US', true, 1, 60, 'nypost.com', 'new-york-post',
 'US right-leaning tabloid with high-volume national politics, business and foreign-affairs coverage.',
 'US-Boulevardzeitung mit rechter Ausrichtung, umfangreiche Berichterstattung zu Innenpolitik, Wirtschaft und Außenpolitik.'),
('Breitbart', 'https://news.google.com/rss/search?q=site:breitbart.com&hl=en', 'en', 'US', true, 1, 60, 'breitbart.com', 'breitbart',
 'US populist-nationalist outlet with extensive world-news and national-security coverage.',
 'US-Nachrichtenportal mit populistisch-nationalistischer Ausrichtung und umfangreicher Weltberichterstattung.'),
('Newsmax', 'https://news.google.com/rss/search?q=site:newsmax.com&hl=en', 'en', 'US', true, 1, 60, 'newsmax.com', 'newsmax',
 'US conservative broadcaster and news site closely aligned with the pro-Trump movement.',
 'US-konservativer Sender und Nachrichtenseite, eng an die Pro-Trump-Bewegung angelehnt.'),
('Washington Examiner', 'https://news.google.com/rss/search?q=site:washingtonexaminer.com&hl=en', 'en', 'US', true, 1, 60, 'washingtonexaminer.com', 'washington-examiner',
 'US right-of-center political outlet with strong Washington policy, defense and foreign-affairs reporting.',
 'US-Politikportal rechts der Mitte mit starker Berichterstattung zu Washingtoner Politik, Verteidigung und Außenpolitik.'),
('National Review', 'https://news.google.com/rss/search?q=site:nationalreview.com&hl=en', 'en', 'US', true, 1, 60, 'nationalreview.com', 'national-review',
 'US flagship intellectual-conservative magazine with substantial foreign-policy commentary.',
 'Fuehrendes intellektuell-konservatives US-Magazin mit umfangreichem aussenpolitischem Kommentar.'),
('The National Interest', 'https://news.google.com/rss/search?q=site:nationalinterest.org&hl=en', 'en', 'US', true, 1, 60, 'nationalinterest.org', 'the-national-interest',
 'US foreign-policy magazine of the realist school, covering grand strategy, defense and great-power competition.',
 'US-aussenpolitisches Magazin der realistischen Schule zu Grosstrategie, Verteidigung und Grossmaechtekonkurrenz.')
ON CONFLICT (url) DO NOTHING;
