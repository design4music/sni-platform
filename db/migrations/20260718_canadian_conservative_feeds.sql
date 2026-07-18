-- Add major Canadian conservative news outlets (us_canada_theater friction nodes).
-- The corpus had NO Canadian right-of-centre outlet at all (only CBC, CTV, Globe and
-- Mail, Mining.com), which left the +2 narratives on all three us_canada atomics at
-- 0-1 titles. Follows the pattern of 20260714_conservative_feeds.sql.
--
-- Verified against live Google News RSS 2026-07-18 (curl -L, then count <item>
-- occurrences -- NOT `grep -c`, which counts LINES and the feed XML is a single line):
--   nationalpost.com   100 items, 96 from Jul 2026
--   torontosun.com     100 items, 100 from Jul 2026
--   financialpost.com  100 items, only 42 from Jul 2026 -- Google's index for this
--                      domain carries archive material back to 2018. Harmless:
--                      rss_fetcher.py:277 hard-drops pubdate year < 2026 and the
--                      last_pubdate_utc watermark filters the rest.
--
-- Excluded: Western Standard (Alberta-regional, not national -- but it IS the outlet
-- that would most help alberta_separatism_us_ties, revisit if that atomic stays
-- one-sided), Rebel News / True North (activist, low editorial standard),
-- The Hub (thehub.ca -- indexed and viable, but centre-right commentary not news).
--
-- NOTE: locally-added feeds are never fetched by the local daemon (every feed created
-- 2026-07-13 still has last_run_at = NULL). This must be applied on Render to change
-- production ingest. Forward-only -- it cannot backfill the frozen archive, so the
-- us_canada narratives stay thin until these feeds accumulate history.
SET client_encoding TO 'UTF8';

INSERT INTO feeds (name, url, language_code, country_code, is_active, priority, fetch_interval_minutes, source_domain, slug, description, description_de, strip_patterns)
VALUES
('National Post', 'https://news.google.com/rss/search?q=site:nationalpost.com&hl=en', 'en', 'CA', true, 1, 60, 'nationalpost.com', 'national-post',
 'Major Canadian national broadsheet with conservative editorial stance, strong coverage of Canadian politics, business, and foreign policy.',
 'Bedeutende kanadische überregionale Tageszeitung mit konservativer Ausrichtung, umfangreiche Berichterstattung über kanadische Politik, Wirtschaft und Außenpolitik.',
 ARRAY['NATIONAL POST','NATIONALPOST','nationalpost.com']),

('Toronto Sun', 'https://news.google.com/rss/search?q=site:torontosun.com&hl=en', 'en', 'CA', true, 1, 60, 'torontosun.com', 'toronto-sun',
 'Canadian tabloid with right-leaning editorial voice, part of Postmedia chain, focuses on Ontario news with national political coverage.',
 'Kanadische Boulevardzeitung mit rechts geneigter redaktioneller Stimme, Teil der Postmedia-Gruppe, konzentriert sich auf Nachrichten aus Ontario mit landesweiter politischer Berichterstattung.',
 ARRAY['TORONTO SUN','TORONTOSUN','torontosun.com']),

('Financial Post', 'https://news.google.com/rss/search?q=site:financialpost.com&hl=en', 'en', 'CA', true, 1, 60, 'financialpost.com', 'financial-post',
 'National Canadian business daily with right-of-centre perspective, extensive coverage of trade policy, tariffs, and economic nationalism.',
 'Nationale kanadische Wirtschaftstageszeitung mit rechts der Mitte orientierter Perspektive, umfangreiche Berichterstattung zu Handelspolitik, Zöllen und wirtschaftlichem Nationalismus.',
 ARRAY['FINANCIAL POST','FINANCIALPOST','financialpost.com'])
ON CONFLICT (url) DO NOTHING;
