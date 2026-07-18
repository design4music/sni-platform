-- us_canada_theater: theater-level narrative cards (§5.5) + one grievance-keyword fix.
--
-- GRIEVANCE FIX: 'richer', 'folly', 'concession' and 'energy policy' were pulling
-- CRITICAL opinion pieces into alberta_legitimate_grievance -- "Separatists think
-- independence makes Quebec and Alberta richer. Really?" is a sceptical column, and
-- "the folly of Carney giving further concessions on energy policy" argues Ottawa
-- conceded too much. Both read as grievance-side on keywords alone and as unity-side
-- to a human. Dropped. The remaining double-files are genuinely two-sided titles.
--
-- THEATER CARDS. Roll-up sources headlines from member atomics' title_narratives
-- where sign(atomic.stance) = sign(theater.stance) AND publisher is in the card's
-- list. Four cards, and BOTH sign buckets are publisher-disjoint:
--   + bucket: us_leverage_case (Fox News)          vs provincial_grievance (Western)
--   - bucket: canadian_consensus (Western/intl)    vs external_rift (Russia/China/Iran state)
-- A positive and a negative card MAY share publishers (opposite signs pull
-- different-signed atomic titles), which is why the Western bloc can appear on both
-- provincial_grievance (+1) and canadian_consensus (-2) without double-counting.
--
-- The +1 Western card exists specifically because alberta_legitimate_grievance (+1,
-- Western publishers) would otherwise be homeless at theater level -- the Arctic
-- build hit the mirror image of this with greenland_sovereignty_defense (-1).
SET client_encoding TO 'UTF8';

UPDATE narratives_v2 SET
  framing_keywords = ARRAY[
    'Western alienation','equalization','equalisation','resource revenue','landlocked',
    'grievance','frustration','neglect','ignored','left behind','oil-rich',
    'argues','defends','treaty rights',
    'Benachteiligung','Ausgleichszahlung','vernachlässigt'
  ],
  updated_at = NOW()
WHERE id = 'alberta_legitimate_grievance';

INSERT INTO narratives_v2 (
  id, fn_id, name_en, name_de, claim_en, claim_de,
  stance, stance_label_en, stance_label_de, display_order,
  publishers, framing_keywords, framing_required, actor_centroids, is_active
) VALUES
(
  'uscat_us_leverage_case',
  'us_canada_theater',
  'A relationship being put on fairer terms',
  'Eine Beziehung auf fairere Grundlage gestellt',
  'The pressure on Canada is presented as an overdue correction: a smaller neighbour that has enjoyed guaranteed market access and American security cover while protecting its own sectors and under-spending on defence is being asked to accept terms that reflect the real balance of the relationship.',
  'Der Druck auf Kanada wird als überfällige Korrektur dargestellt: Ein kleinerer Nachbar, der garantierten Marktzugang und amerikanischen Sicherheitsschutz genoss, während er eigene Sektoren schützte und bei der Verteidigung zu wenig ausgab, solle nun Bedingungen akzeptieren, die das tatsächliche Kräfteverhältnis abbilden.',
  2, 'US leverage is justified', 'US-Druck ist gerechtfertigt', 1,
  ARRAY['Fox News'],
  ARRAY['grateful','small power','biting the hand','unfair','freeload','benchmark','protects','Golden Dome','dankbar','einseitig'],
  false,
  ARRAY['AMERICAS-USA'], true
),
(
  'uscat_provincial_grievance',
  'us_canada_theater',
  'A federation strained from within',
  'Ein Bund, der von innen unter Druck steht',
  'Attention turns to the domestic fault line the confrontation has exposed: a landlocked resource province that sees federal energy and fiscal decisions as made against its interests, and whose separatist movement has drawn interest from officials across the border.',
  'Der Blick richtet sich auf die innere Bruchlinie, die die Konfrontation offengelegt hat: eine rohstoffreiche Binnenprovinz, die föderale Energie- und Finanzentscheidungen als gegen ihre Interessen gerichtet ansieht und deren separatistische Bewegung Interesse bei Amtsträgern jenseits der Grenze geweckt hat.',
  1, 'The internal fault line', 'Die innere Bruchlinie', 2,
  ARRAY['Globe and Mail','The Globe and Mail','CBC','Reuters','BBC World','Bloomberg','Associated Press','Financial Times','Wall Street Journal','The Guardian','New York Times','Washington Post','The Washington Post','CNN','NPR','Euronews','Deutsche Welle','Der Spiegel','El País','France 24 (EN)','France 24','Al Jazeera','NDTV','Anadolu Agency','OilPrice','Mining.com','Straits Times','La Nación','Clarín','Japan Times'],
  ARRAY['alienation','equalization','landlocked','oil-rich','grievance','separatis','referendum','independence'],
  false,
  ARRAY['AMERICAS-CANADA'], true
),
(
  'uscat_canadian_consensus',
  'us_canada_theater',
  'An ally treated as a target',
  'Ein Verbündeter als Zielscheibe',
  'The dominant reading across Canadian and international coverage: tariffs, annexation rhetoric, a withheld border crossing and a rescinded diplomatic invitation amount to sustained pressure on a treaty partner, producing a cross-party sovereignty response and a search for markets and partners beyond the United States.',
  'Die vorherrschende Lesart in der kanadischen und internationalen Berichterstattung: Zölle, Annexionsrhetorik, ein zurückgehaltener Grenzübergang und eine zurückgezogene diplomatische Einladung summieren sich zu anhaltendem Druck auf einen Vertragspartner — mit einer parteiübergreifenden Souveränitätsreaktion und der Suche nach Märkten und Partnern jenseits der USA.',
  -2, 'Pressure on a treaty partner', 'Druck auf einen Vertragspartner', 3,
  ARRAY['Globe and Mail','The Globe and Mail','CBC','Reuters','BBC World','Bloomberg','Associated Press','Financial Times','Wall Street Journal','The Guardian','New York Times','Washington Post','The Washington Post','CNN','NPR','Euronews','Deutsche Welle','Der Spiegel','El País','France 24 (EN)','France 24','Al Jazeera','NDTV','Anadolu Agency','OilPrice','Mining.com','Straits Times','La Nación','Clarín','Japan Times','Reforma','El Universal','Mexico News Daily'],
  ARRAY['sovereignt','coercion','annex','51st state','retaliat','ally','unity','threat','Souveränität','Zwang','Verbündet'],
  false,
  ARRAY['AMERICAS-CANADA'], true
),
(
  'uscat_external_rift',
  'us_canada_theater',
  'The Western bloc coming apart',
  'Der westliche Block zerfällt',
  'Russian, Chinese and Iranian state coverage treats the confrontation as confirmation that the American-led order rests on coercion of its own partners and that Western appeals to shared values and a rules-based order do not survive contact with Washington''s interests. The framing is directed at the alliance itself rather than at either party''s case.',
  'Russische, chinesische und iranische Staatsmedien behandeln die Konfrontation als Bestätigung, dass die amerikanisch geführte Ordnung auf Zwang gegenüber den eigenen Partnern beruht und dass westliche Berufungen auf gemeinsame Werte und eine regelbasierte Ordnung dem Kontakt mit Washingtons Interessen nicht standhalten. Die Darstellung zielt auf das Bündnis selbst, nicht auf die Position einer der beiden Seiten.',
  -1, 'Western order exposed', 'Westliche Ordnung entlarvt', 4,
  ARRAY['RT','TASS (EN)','Global Times','CGTN','People''s Daily','China Daily','Xinhua','Sputnik','Press TV'],
  ARRAY['hegemon','imperial','hypocris','double standard','vassal','decay','so-called','Doppelmoral','Hegemon'],
  false,
  ARRAY['EUROPE-RUSSIA','ASIA-CHINA'], true
);
