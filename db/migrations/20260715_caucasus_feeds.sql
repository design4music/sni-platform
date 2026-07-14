-- Add local/regional South Caucasus news feeds (English, politics-focused).
-- Root cause of thin Caucasus coverage: we ingested only Russian/Iranian/Turkish
-- state media + international wires, no local Caucasus outlets. Domains verified
-- (Agenda.ge dropped -- defunct since Feb 2025). Google News site: RSS pattern,
-- matching existing feeds. Idempotent on the unique url. Regional outlets tagged
-- GE (editorial base / Caucasus desk) to strengthen the Georgia gap; they cover
-- Armenia and Azerbaijan too.

BEGIN;

INSERT INTO feeds (name, slug, source_domain, language_code, country_code, priority, fetch_interval_minutes, is_active, description, description_de, strip_patterns, url) VALUES
('Civil.ge','civil-ge','civil.ge','en','GE',1,60,true,
 'Civil.ge (Civil Georgia) is an independent, English-language Georgian news outlet founded in 2001 and run by the UN Association of Georgia. It focuses on Georgian politics, democracy, foreign policy and EU integration, and is widely cited for its coverage of domestic political crises.',
 'Civil.ge (Civil Georgia) ist ein unabhängiges, englischsprachiges georgisches Nachrichtenportal, das 2001 gegründet wurde und von der UN-Vereinigung Georgiens betrieben wird. Es konzentriert sich auf georgische Politik, Demokratie, Außenpolitik und EU-Integration und wird für seine Berichterstattung über innenpolitische Krisen häufig zitiert.',
 ARRAY['Civil.ge','civil.ge','Civil Georgia'],
 'https://news.google.com/rss/search?q=site%3Acivil.ge&hl=en'),
('OC Media','oc-media','oc-media.org','en','GE',1,60,true,
 'OC Media is an independent, English-language news organisation based in Tbilisi covering the Caucasus -- Georgia, Armenia, Azerbaijan and the North Caucasus. It focuses on human rights, minorities, protest movements and politics, with an emphasis on under-reported stories.',
 'OC Media ist eine unabhängige, englischsprachige Nachrichtenorganisation mit Sitz in Tiflis, die über den Kaukasus -- Georgien, Armenien, Aserbaidschan und den Nordkaukasus -- berichtet. Sie konzentriert sich auf Menschenrechte, Minderheiten, Protestbewegungen und Politik, mit Schwerpunkt auf wenig beachteten Themen.',
 ARRAY['OC Media','oc-media.org','OC-Media'],
 'https://news.google.com/rss/search?q=site%3Aoc-media.org&hl=en'),
('Armenpress','armenpress','armenpress.am','en','AM',1,60,true,
 'Armenpress is Armenia''s state news agency, founded in 1918, publishing in English and other languages. It provides high-volume coverage of Armenian government, politics, foreign policy and the South Caucasus from an official Armenian perspective.',
 'Armenpress ist die staatliche Nachrichtenagentur Armeniens, gegründet 1918, die auf Englisch und in weiteren Sprachen publiziert. Sie liefert umfangreiche Berichterstattung über die armenische Regierung, Politik, Außenpolitik und den Südkaukasus aus offizieller armenischer Sicht.',
 ARRAY['Armenpress','armenpress.am','ARMENPRESS'],
 'https://news.google.com/rss/search?q=site%3Aarmenpress.am&hl=en'),
('CivilNet','civilnet','civilnet.am','en','AM',1,60,true,
 'CivilNet is an independent, reader-funded Armenian news and analysis outlet publishing in English. It focuses on Armenian politics, democracy, foreign policy and the Nagorno-Karabakh conflict, with a governance and accountability emphasis.',
 'CivilNet ist ein unabhängiges, leserfinanziertes armenisches Nachrichten- und Analyseportal, das auf Englisch publiziert. Es konzentriert sich auf armenische Politik, Demokratie, Außenpolitik und den Bergkarabach-Konflikt, mit Schwerpunkt auf Regierungsführung und Rechenschaft.',
 ARRAY['CivilNet','civilnet.am'],
 'https://news.google.com/rss/search?q=site%3Acivilnet.am&hl=en'),
('Trend.az','trend-az','trend.az','en','AZ',1,60,true,
 'Trend is an Azerbaijani news agency founded in 1995, publishing in English and several other languages. It provides high-volume coverage of Azerbaijani politics, energy and the wider Caucasus and Central Asia, generally aligned with official positions.',
 'Trend ist eine aserbaidschanische Nachrichtenagentur, gegründet 1995, die auf Englisch und in mehreren weiteren Sprachen publiziert. Sie liefert umfangreiche Berichterstattung über aserbaidschanische Politik, Energie sowie den weiteren Kaukasus und Zentralasien, weitgehend im Einklang mit offiziellen Positionen.',
 ARRAY['Trend.Az','trend.az','Trend News Agency'],
 'https://news.google.com/rss/search?q=site%3Atrend.az&hl=en'),
('APA','apa-az','apa.az','en','AZ',1,60,true,
 'APA is an Azerbaijani independent news agency founded in 2004, publishing in English. It covers Azerbaijani politics, foreign policy and regional affairs, with a focus on diplomacy and the Armenia-Azerbaijan relationship.',
 'APA ist eine unabhängige aserbaidschanische Nachrichtenagentur, gegründet 2004, die auf Englisch publiziert. Sie berichtet über aserbaidschanische Politik, Außenpolitik und regionale Angelegenheiten, mit Schwerpunkt auf Diplomatie und dem Verhältnis zwischen Armenien und Aserbaidschan.',
 ARRAY['APA','apa.az','APA.az'],
 'https://news.google.com/rss/search?q=site%3Aapa.az&hl=en'),
('Eurasianet','eurasianet','eurasianet.org','en','GE',1,60,true,
 'Eurasianet is an independent, English-language outlet affiliated with Columbia University, providing analysis and on-the-ground reporting on the South Caucasus and Central Asia. It focuses on politics, governance and society with an emphasis on in-depth, independent coverage.',
 'Eurasianet ist ein unabhängiges, englischsprachiges Medium, das mit der Columbia University verbunden ist und Analysen sowie Berichterstattung vor Ort über den Südkaukasus und Zentralasien liefert. Es konzentriert sich auf Politik, Regierungsführung und Gesellschaft mit Schwerpunkt auf vertiefter, unabhängiger Berichterstattung.',
 ARRAY['Eurasianet','eurasianet.org'],
 'https://news.google.com/rss/search?q=site%3Aeurasianet.org&hl=en'),
('JAMnews','jamnews','jam-news.net','en','GE',1,60,true,
 'JAMnews is an independent, English-language media outlet covering the South Caucasus -- Georgia, Armenia and Azerbaijan. It publishes politics, conflict and society reporting from journalists across the region, including from both sides of the Armenia-Azerbaijan divide.',
 'JAMnews ist ein unabhängiges, englischsprachiges Medium, das über den Südkaukasus -- Georgien, Armenien und Aserbaidschan -- berichtet. Es veröffentlicht Berichterstattung über Politik, Konflikte und Gesellschaft von Journalisten aus der gesamten Region, auch von beiden Seiten des armenisch-aserbaidschanischen Konflikts.',
 ARRAY['JAMnews','jam-news.net','JAM News'],
 'https://news.google.com/rss/search?q=site%3Ajam-news.net&hl=en')
ON CONFLICT (url) DO NOTHING;

COMMIT;
