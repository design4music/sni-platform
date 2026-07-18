-- Western Standard: deliberate exception to the "major national outlets only" rule.
--
-- Alberta-based and regional, so it fails the national test that excluded it from
-- 20260718_canadian_conservative_feeds.sql. Added anyway because it is the single
-- outlet that fixes a measured hole: alberta_separatism_us_ties currently has NO
-- publisher arguing Alberta's side, so alberta_legitimate_grievance (+1) sits at 4
-- titles while alberta_unity_defence (-1) holds 82. Every outlet in the corpus covers
-- the secession push from Ottawa's or the courts' vantage point. Coverage weight does
-- not track outlet reach: on this specific conflict a Calgary paper carries more
-- signal than another international wire.
--
-- Verified against live Google News RSS 2026-07-18 (curl -L, count <item>):
--   100 items, 79 from 2026, but only 5 from Jul 2026 -- Google indexes this domain
--   more slowly than the national dailies, so expect a low per-fetch yield of NEW
--   items rather than a burst. The last_pubdate_utc watermark accumulates it over
--   time; rss_fetcher.py:277 drops anything before 2026.
-- Sample headlines confirm the editorial position that is missing from the corpus:
--   "STEPHAN: Does the MOU mean Alberta should now be quiet and be a good colony?"
--   "Judge temporarily freezes top Alberta independence advocate's assets"
--
-- Also wires the outlet into the grievance coalitions so its titles route correctly
-- from the first ingest rather than sitting homeless. It is deliberately NOT added to
-- alberta_unity_defence: that narrative is ungated (framing_required=false), so
-- listing it there would double-file every Western Standard title onto both sides.
--
-- Forward-only, and must be applied on Render to affect production ingest.
SET client_encoding TO 'UTF8';

INSERT INTO feeds (name, url, language_code, country_code, is_active, priority, fetch_interval_minutes, source_domain, slug, description, description_de, strip_patterns)
VALUES
('Western Standard', 'https://news.google.com/rss/search?q=site:westernstandard.news&hl=en', 'en', 'CA', true, 1, 60, 'westernstandard.news', 'western-standard',
 'Canadian conservative news outlet based in Calgary, Alberta, relaunched in 2019. It reports from a Western Canadian perspective and is a principal outlet for coverage of Alberta provincial politics, resource policy and the province''s independence movement.',
 'Kanadisches konservatives Nachrichtenportal mit Sitz in Calgary, Alberta, 2019 neu gegründet. Es berichtet aus westkanadischer Perspektive und ist ein zentrales Medium für die Berichterstattung über die Politik der Provinz Alberta, die Ressourcenpolitik und die Unabhängigkeitsbewegung der Provinz.',
 ARRAY['WESTERN STANDARD','WESTERNSTANDARD','westernstandard.news'])
ON CONFLICT (url) DO NOTHING;

-- ---- route its coverage: atomic +1 and theater +1 ------------------------
UPDATE narratives_v2 SET
  publishers = publishers || ARRAY['Western Standard'],
  framing_keywords = framing_keywords || ARRAY['colony','independence advocate','Ottawa''s','federal overreach'],
  updated_at = NOW()
WHERE id = 'alberta_legitimate_grievance';

UPDATE narratives_v2 SET
  publishers = publishers || ARRAY['Western Standard'],
  updated_at = NOW()
WHERE id = 'uscat_provincial_grievance';
