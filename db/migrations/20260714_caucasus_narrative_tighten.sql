-- Tighten Caucasus narrative composition (user review):
--  1. armenia_western_pivot: drop awp_western_caution (0 titles) -> clean +2/-2.
--  2. armenia_azerbaijan_settlement: merge the two negatives (armenian_grievance
--     + russia_sidelined) into one contested_settlement (-2) -> two dominant
--     frames +/- for thin coverage.
--  3. caucasus_power_competition: replace the genocide-dominated 3-narrative set
--     with a bipolar axis matching the atomic's real logic -- is outside
--     engagement a beneficial partnership (+1) or a hostile encirclement (-2)?
--     Genocide recognition folds in as one expression of Western/Israeli engagement.
-- Re-bootstrap of settlement + power_competition follows this migration.

BEGIN;

DELETE FROM narratives_v2 WHERE id IN
  ('awp_western_caution','aas_armenian_grievance','aas_russia_sidelined',
   'cpc_genocide_recognition','cpc_genocide_politicized','cpc_russia_iran_squeeze');

ALTER TABLE narratives_v2 ALTER COLUMN actor_centroids SET DEFAULT ARRAY['ASIA-CAUCASUS'];

-- ---- settlement: single merged negative ----
INSERT INTO narratives_v2 (id, fn_id, display_order, stance, framing_required, name_en, name_de, stance_label_en, stance_label_de, claim_en, claim_de, framing_keywords, publishers) VALUES
('aas_contested_settlement','armenia_azerbaijan_settlement',2,-2,true,
 'The settlement is a contested, externally shaped arrangement rather than a genuine peace',
 'Die Regelung ist ein umstrittenes, von außen geformtes Arrangement statt eines echten Friedens',
 'Contested / imposed settlement','Umstrittene / aufgezwungene Regelung',
 'Critics reject the triumphant peace account from two directions: a pro-Armenian and human-rights framing sees a capitulation imposed on a defeated Armenia that leaves the 2023 exodus, prisoners of war and war-crimes accountability unaddressed; a Russian framing sees a Western- and Turkish-brokered arrangement that sidelines Moscow and its peacekeepers.',
 'Kritiker weisen die triumphale Friedenserzählung aus zwei Richtungen zurück: eine proarmenische und menschenrechtliche Deutung sieht eine einem besiegten Armenien aufgezwungene Kapitulation, die den Exodus von 2023, Kriegsgefangene und die Ahndung von Kriegsverbrechen ungeklärt lässt; eine russische Deutung sieht ein westlich-türkisch vermitteltes Arrangement, das Moskau und seine Friedenstruppen an den Rand drängt.',
 ARRAY['ethnic cleansing','forced displacement','exodus','capitulation','dictated','imposed','prisoners of war','war crimes','torture','unpunished','sidelined','hijack','peacekeepers','excludes Russia','ethnische Säuberung','Vertreibung','Kriegsverbrechen','Kriegsgefangene','Kapitulation','aufgezwungen','an den Rand','этническая чистка','военнопленные','капитуляция','навязанный','в обход России'],
 ARRAY['France 24 (EN)','France 24','Le Figaro','Le Monde','The Guardian','Deutsche Welle','Der Spiegel','Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','Der Standard','Haaretz','Carnegie Endowment','TASS (EN)','TASS','tass.com','RT','RIA Novosti','Lenta.ru','Gazeta.ru','gazeta.ru','Kommersant','Izvestia','BelTA','BelTA Russian']);

-- ---- power competition: bipolar engagement vs resistance ----
INSERT INTO narratives_v2 (id, fn_id, display_order, stance, framing_required, name_en, name_de, stance_label_en, stance_label_de, claim_en, claim_de, framing_keywords, publishers) VALUES
('cpc_western_engagement','caucasus_power_competition',1,1,false,
 'Outside engagement brings beneficial partnership and integration to the region',
 'Äußeres Engagement bringt der Region nützliche Partnerschaft und Integration',
 'Beneficial external partnership','Nützliche externe Partnerschaft',
 'A Western, Turkish and Israeli framing presents outside engagement in the South Caucasus as beneficial partnership and integration: Azerbaijani energy exports to Europe through SOCAR and the Southern Gas Corridor, Israeli and Turkish security and economic ties, a growing US role, and -- as an expression of Western and Israeli moral engagement -- recognition of the Armenian Genocide.',
 'Eine westliche, türkische und israelische Deutung stellt das äußere Engagement im Südkaukasus als nützliche Partnerschaft und Integration dar: aserbaidschanische Energieexporte nach Europa über SOCAR und den Südlichen Gaskorridor, israelische und türkische Sicherheits- und Wirtschaftsbeziehungen, eine wachsende US-Rolle und -- als Ausdruck westlichen und israelischen moralischen Engagements -- die Anerkennung des Völkermords an den Armeniern.',
 ARRAY['partnership','integration','ties','cooperation','energy security','strategic partnership','grand deal','moral','justice','SOCAR','Southern Gas Corridor','Partnerschaft','Integration','Zusammenarbeit','moralisch','партнерство','сотрудничество'],
 ARRAY['Reuters','Euronews','Euronews.com','France 24 (EN)','France 24','BBC World','Associated Press','The Guardian','CNN','Deutsche Welle','EurActiv','Financial Times','Bloomberg','ANSA','La Repubblica','El País','Novinite','OilPrice','Carnegie Endowment','NPR','Daily Sabah','Anadolu Agency','TRT World','Jerusalem Post','The Jerusalem Post','Times of Israel','The Times of Israel','i24NEWS']),
('cpc_russia_iran_resistance','caucasus_power_competition',2,-2,false,
 'Outside penetration of the region is a hostile encirclement to be resisted',
 'Das Eindringen von außen in die Region ist eine feindliche Einkreisung, der zu widerstehen ist',
 'Hostile encirclement / resistance','Feindliche Einkreisung / Widerstand',
 'A Russian and Iranian framing casts outside engagement as hostile penetration: US, Turkish and Israeli inroads -- bases, energy and arms deals, and transport corridors -- threaten Russian and Iranian interests and regional stability and are to be resisted through their own partnerships, amid frictions such as the disputes between Russia and Azerbaijan.',
 'Eine russische und iranische Deutung stellt das äußere Engagement als feindliches Eindringen dar: US-amerikanische, türkische und israelische Vorstöße -- Stützpunkte, Energie- und Rüstungsgeschäfte sowie Transportkorridore -- bedrohten russische und iranische Interessen und die regionale Stabilität und seien durch eigene Partnerschaften abzuwehren, inmitten von Reibungen wie den Streitigkeiten zwischen Russland und Aserbaidschan.',
 ARRAY['encirclement','penetration','inroads','threat to stability','red line','foreign base','resist','sphere of influence','espionage','Einkreisung','Vordringen','rote Linie','Bedrohung','угроза','вторжение','красная линия','сфера влияния','шпионаж'],
 ARRAY['TASS (EN)','TASS','tass.com','RT','RIA Novosti','Lenta.ru','Gazeta.ru','gazeta.ru','Kommersant','Izvestia','BelTA','BelTA Russian','IRNA','Press TV']);

ALTER TABLE narratives_v2 ALTER COLUMN actor_centroids DROP DEFAULT;

COMMIT;
