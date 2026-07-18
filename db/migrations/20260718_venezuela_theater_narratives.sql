-- Venezuela theater-level narrative cards (§5.5, 2026-07-18).
--
-- The theater carries NO fn_anchor bundle and never matches titles.
-- THEATER_ROLLUP_SQL sources each card's headlines + count from the MEMBER
-- ATOMICS' title_narratives, where a title qualifies iff
--   sign(atomic.stance) = sign(theater.stance)  AND  publisher IN card.publishers.
--
-- HARD RULE: publisher-disjoint WITHIN a stance-sign bucket (counts are uncapped
-- over (sign, publisher), so same-sign overlap double-counts).
--   negative bucket: -1 Western non-state  vs  -2 Russia/China/Iran state  -> DISJOINT.
--   +2 shares Western publishers with -1, but opposite signs pull different-signed
--   atomic titles, so no title double-counts (spec §5.5 explicitly allows this).
--
-- NB: no earthquake / aid-competition card. The June quake (972 titles) is
-- attributed to no atomic, and a theater card cannot source non-atomic titles --
-- it would render empty. Backlogged as fn_type='situation' (see the
-- project_situation_entity memory).

BEGIN;

DELETE FROM narratives_v2 WHERE fn_id = 'venezuela_theater';

INSERT INTO narratives_v2
 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
  name_en, name_de, claim_en, claim_de, actor_centroids, publishers,
  framing_keywords, framing_required) VALUES

('ven_theater_western_consensus','venezuela_theater',1,2,
 'Pragmatic Western consensus','Pragmatischer westlicher Konsens',
 'Removing Maduro opened a stabilising, pragmatic path for Venezuela',
 'Maduros Absetzung öffnete einen stabilisierenden, pragmatischen Weg für Venezuela',
 'With the narco-state gone, an interim government is restoring order and the oil sector is reopening -- a fragile but genuine chance for Venezuelan recovery and for global energy supply.',
 'Mit dem Ende des Narco-Staats stellt eine Übergangsregierung die Ordnung wieder her und der Ölsektor öffnet sich erneut -- eine fragile, aber echte Chance für Venezuelas Erholung und die globale Energieversorgung.',
 ARRAY['AMERICAS-USA','NON-STATE-EU','AMERICAS-VENEZUELA'],
 ARRAY['Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Frankfurter Allgemeine','Le Monde','Le Figaro','El País','El Mundo','Corriere della Sera','La Repubblica','Der Standard','Die Presse','The Telegraph','ABC News','Sky News','Bloomberg','Wall Street Journal','Financial Times','OilPrice','S&P Global','Mining.com','Clarín','La Nación','Reforma','Folha de S.Paulo','O Globo','O Estado de S. Paulo','El Universal','Times of India','NDTV','The Hindu','Hindustan Times','WION','Fox News','The Australian','Jerusalem Post','Times of Israel','i24NEWS'],
 ARRAY['stabil','reform','recovery','restart','opportunity','transition','invest','estabil','reforma','recuperación','Stabil','Erholung'],
 false),

('ven_theater_western_critical','venezuela_theater',2,-1,
 'Lawless means, hollow transition','Rechtlose Mittel, hohler Übergang',
 'The means were lawless and the transition is hollow',
 'Die Mittel waren rechtlos und der Übergang ist hohl',
 'Even sympathetic Western coverage sees a head of state abducted without legal mandate, an opposition frozen out of the settlement, and oil deals struck behind closed doors.',
 'Selbst wohlwollende westliche Berichterstattung sieht einen ohne Rechtsgrundlage entführten Staatschef, eine von der Einigung ausgeschlossene Opposition und hinter verschlossenen Türen geschlossene Ölgeschäfte.',
 ARRAY['NON-STATE-EU','AMERICAS-USA','AMERICAS-VENEZUELA'],
 ARRAY['Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Frankfurter Allgemeine','Le Monde','Le Figaro','El País','El Mundo','Corriere della Sera','La Repubblica','Der Standard','Die Presse','The Telegraph','ABC News','Sky News','Bloomberg','Wall Street Journal','Financial Times','OilPrice','S&P Global','Mining.com','Clarín','La Nación','Reforma','Folha de S.Paulo','O Globo','O Estado de S. Paulo','El Universal','Straits Times'],
 ARRAY['illegal','unlawful','war powers','frozen out','no elections','secret','opaque','abduct','overreach','sin elecciones','ilegal','rechtswidrig','Entführung','ausgeschlossen'],
 false),

('ven_theater_anti_imperial','venezuela_theater',3,-2,
 'Anti-imperial counter-framing','Anti-imperiale Gegenerzählung',
 'A US imperial operation to seize a sovereign nation''s oil',
 'Eine imperiale US-Operation zur Aneignung des Öls einer souveränen Nation',
 'Washington abducted a president, installed a compliant government and took the world''s largest oil reserves -- gunboat imperialism that shreds international law and puts all of Latin America on notice.',
 'Washington entführte einen Präsidenten, setzte eine gefügige Regierung ein und nahm sich die größten Ölreserven der Welt -- Kanonenbootimperialismus, der das Völkerrecht zerreißt und ganz Lateinamerika warnt.',
 ARRAY['EUROPE-RUSSIA','ASIA-CHINA','MIDEAST-IRAN'],
 ARRAY['TASS (EN)','TASS','RT','Lenta.ru','Izvestia','CGTN','China Daily','Global Times','Press TV','Al Jazeera','Al Arabiya','Al-Ahram','Anadolu Agency'],
 ARRAY['imperial','sovereignty','regime change','plunder','puppet','soberanía','imperialismo','Souveränität','Regimewechsel'],
 false);

COMMIT;
