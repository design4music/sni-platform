SET client_encoding TO 'UTF8';

-- Migration: Add conservative/right-of-center news feeds
-- Date: 2026-07-14
-- Purpose: Fill ingest gap for pro-Trump/America-First perspective in geopolitics coverage
-- Target: ~14 outlets spanning MAGA populist to establishment conservative to paleoconservative/realist
-- All URLs use Google News RSS site-search format for consistency with existing feeds

INSERT INTO feeds (
  id,
  name,
  url,
  language_code,
  country_code,
  is_active,
  priority,
  fetch_interval_minutes,
  source_domain,
  slug,
  description,
  description_de
) VALUES
-- Populist/MAGA outlets
(
  gen_random_uuid(),
  'Breitbart',
  'https://news.google.com/rss/search?q=site:breitbart.com&hl=en',
  'en',
  'US',
  true,
  1,
  60,
  'breitbart.com',
  'breitbart',
  'US populist-nationalist outlet with extensive world news coverage and national-security focus.',
  'US-Nachrichtenportal mit populistisch-nationalistischer Ausrichtung, umfangreiche Weltberichterstattung und Schwerpunkt auf nationale Sicherheit.'
),
(
  gen_random_uuid(),
  'Daily Caller',
  'https://news.google.com/rss/search?q=site:dailycaller.com&hl=en',
  'en',
  'US',
  true,
  1,
  60,
  'dailycaller.com',
  'daily-caller',
  'US right-wing populist news outlet covering NATO policy, defense issues, and military commitments.',
  'US-Nachrichtenportal mit rechts-populistischer Ausrichtung, Berichterstattung über NATO, Verteidigungspolitik und Militärverpflichtungen.'
),
(
  gen_random_uuid(),
  'Daily Wire',
  'https://news.google.com/rss/search?q=site:dailywire.com&hl=en',
  'en',
  'US',
  true,
  1,
  60,
  'dailywire.com',
  'daily-wire',
  'US right-wing conservative outlet with dedicated foreign policy section covering defense and international affairs.',
  'US-Nachrichtenportal mit konservativ-rechter Ausrichtung und eigener Abteilung für Außenpolitik, Verteidigung und internationale Angelegenheiten.'
),

-- Establishment conservative outlets
(
  gen_random_uuid(),
  'Townhall',
  'https://news.google.com/rss/search?q=site:townhall.com&hl=en',
  'en',
  'US',
  true,
  1,
  60,
  'townhall.com',
  'townhall',
  'US establishment-conservative outlet emphasizing national defense advocacy and assertive geopolitical analysis.',
  'US-Nachrichtenportal mit etabliert-konservativer Ausrichtung, Schwerpunkt auf nationale Verteidigungspolitik und assertive geopolitische Analyse.'
),
(
  gen_random_uuid(),
  'Washington Examiner',
  'https://news.google.com/rss/search?q=site:washingtonexaminer.com&hl=en',
  'en',
  'US',
  true,
  1,
  60,
  'washingtonexaminer.com',
  'washington-examiner',
  'US right-center outlet with dedicated foreign policy section covering military support and interventionist perspectives.',
  'US-Nachrichtenportal mit rechts-gemäßigter Ausrichtung und eigener Außenpolitik-Rubrik, Berichterstattung über Militärhilfe und interventionistische Perspektiven.'
),
(
  gen_random_uuid(),
  'National Review',
  'https://news.google.com/rss/search?q=site:nationalreview.com&hl=en',
  'en',
  'US',
  true,
  1,
  60,
  'nationalreview.com',
  'national-review',
  'US establishment-conservative publication with prominent foreign policy coverage and neoconservative analysis.',
  'US-Publikation mit etabliert-konservativer Ausrichtung, hervorragende Außenpolitik-Berichterstattung und neokonservative Analyse.'
),

-- Neoconservative / Interventionist outlets
(
  gen_random_uuid(),
  'Washington Times',
  'https://news.google.com/rss/search?q=site:washingtontimes.com&hl=en',
  'en',
  'US',
  true,
  1,
  60,
  'washingtontimes.com',
  'washington-times',
  'US neoconservative publication with hawkish foreign policy stance and strong pro-Israel coverage.',
  'US-Publikation mit neokonservativer Ausrichtung, Falken-Außenpolitik und starke pro-Israel-Berichterstattung.'
),
(
  gen_random_uuid(),
  'Washington Free Beacon',
  'https://news.google.com/rss/search?q=site:freebeacon.com&hl=en',
  'en',
  'US',
  true,
  1,
  60,
  'freebeacon.com',
  'washington-free-beacon',
  'US neoconservative outlet with investigative journalism focus and international security reporting.',
  'US-Outlet mit neokonservativer Ausrichtung, investigativer Journalismus und Fokus auf internationale Sicherheitsberichterstattung.'
),
(
  gen_random_uuid(),
  'Commentary Magazine',
  'https://news.google.com/rss/search?q=site:commentarymagazine.com&hl=en',
  'en',
  'US',
  true,
  1,
  60,
  'commentarymagazine.com',
  'commentary-magazine',
  'US neoconservative monthly journal with serious foreign policy analysis and defense-focused intellectual commentary.',
  'US-Monatszeitschrift mit neokonservativer Ausrichtung, ernsthafte Außenpolitik-Analyse und verteidigungsorientiertes intellektuelles Kommentar.'
),

-- Realist / Restraint-oriented outlets
(
  gen_random_uuid(),
  'American Conservative',
  'https://news.google.com/rss/search?q=site:theamericanconservative.com&hl=en',
  'en',
  'US',
  true,
  1,
  60,
  'theamericanconservative.com',
  'american-conservative',
  'US paleoconservative outlet emphasizing foreign policy realism and skepticism toward military intervention.',
  'US-Outlet mit palaokonservativer Ausrichtung, betont außenpolitischen Realismus und Skepsis gegenüber militärischen Interventionen.'
),
(
  gen_random_uuid(),
  'National Interest',
  'https://news.google.com/rss/search?q=site:nationalinterest.org&hl=en',
  'en',
  'US',
  true,
  1,
  60,
  'nationalinterest.org',
  'national-interest',
  'US foreign policy and security analysis outlet using realist theoretical framework for geopolitical coverage.',
  'US-Publikation für Außenpolitik und Sicherheitsanalyse mit realistischem theoretischem Rahmen für geopolitische Berichterstattung.'
),

-- Center-right / Institutional outlets
(
  gen_random_uuid(),
  'RealClearWorld',
  'https://news.google.com/rss/search?q=site:realclearworld.com&hl=en',
  'en',
  'US',
  true,
  1,
  60,
  'realclearworld.com',
  'realclear-world',
  'US center-right news aggregator curating international coverage and global affairs from multiple outlets.',
  'US-Nachrichtenaggregator mit rechts-gemäßigter Ausrichtung, kuratiert internationale Berichterstattung und globale Angelegenheiten von verschiedenen Medien.'
),
(
  gen_random_uuid(),
  'The Dispatch',
  'https://news.google.com/rss/search?q=site:thedispatch.com&hl=en',
  'en',
  'US',
  true,
  1,
  60,
  'thedispatch.com',
  'the-dispatch',
  'US center-right independent outlet founded by Jonah Goldberg with serious foreign policy and national security analysis.',
  'US-unabhängiges Nachrichtenportal mit rechts-gemäßigter Ausrichtung, gegründet von Jonah Goldberg, mit ernsthafter Außenpolitik und Sicherheitsanalyse.'
),

-- Transatlantic (UK) outlet
(
  gen_random_uuid(),
  'Spectator',
  'https://news.google.com/rss/search?q=site:spectator.co.uk&hl=en',
  'en',
  'GB',
  true,
  1,
  60,
  'spectator.co.uk',
  'spectator-uk',
  'British right-center weekly magazine with Eurosceptic and Atlanticist perspectives on geopolitics and international affairs.',
  'Britisches rechts-gemäßigtes Wochenmagazin mit Eurosceptiker- und Atlantiker-Perspektiven auf Geopolitik und internationale Angelegenheiten.'
)

ON CONFLICT (url) DO NOTHING;
