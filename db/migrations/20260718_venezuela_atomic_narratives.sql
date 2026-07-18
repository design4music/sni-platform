-- Venezuela theater: atomic narratives (2026-07-18).
--
-- Own-goal 3-stance model (spec §5) for oil / transition / coercion. The
-- supportive Western coalition is itself split (the same mainstream outlets run
-- "restart is pragmatic" AND "Trump plundered the oil / democracy was betrayed /
-- the strikes are illegal"), so publisher alone cannot separate stance. Model:
--   +1 supportive   and  -1 friendly-critic  SHARE a neutral Western pool,
--     both framing_required=true with DISJOINT framing keywords;
--   -2 adversary uses a DISJOINT Russia/China/Iran/Arab pool, framing_required
--     =false (publisher suffices).
-- Stance-distinct publishers are added to the side they actually take (Fox +
-- Israeli -> coercion +1; business/Indian/Latam lean -> oil +1).
-- Essequibo is a thin 2-stance pro/con with fully disjoint pools.
--
-- Publisher strings are exact publisher_name values verified in the 180d
-- Venezuela corpus. framing_keywords are ILIKE substrings, multilingual
-- (EN + DE + ES -- the three heaviest corpus languages). Reversible: DELETE.

BEGIN;

DELETE FROM narratives_v2 WHERE fn_id IN
  ('venezuela_sanctions_oil','venezuela_political_transition','us_venezuela_relations','essequibo_dispute');

-- ============================ A. OIL RESTART ============================
INSERT INTO narratives_v2
 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
  name_en, name_de, claim_en, claim_de, actor_centroids, publishers,
  framing_keywords, framing_required) VALUES
('ven_oil_restart_opportunity','venezuela_sanctions_oil',1,1,
 'Pragmatic restart & recovery','Pragmatischer Neustart & Erholung',
 'Sanctions relief reopens Venezuela''s oil to the world',
 'Sanktionslockerung öffnet Venezuelas Öl wieder für die Welt',
 'Lifting sanctions and welcoming the majors back is a pragmatic win -- Venezuelan crude eases global supply, funds recovery and pulls the economy off the floor.',
 'Die Aufhebung der Sanktionen und die Rückkehr der Ölkonzerne sind ein pragmatischer Gewinn -- venezolanisches Rohöl entlastet den Weltmarkt, finanziert den Wiederaufbau und richtet die Wirtschaft wieder auf.',
 ARRAY['AMERICAS-USA','NON-STATE-EU','AMERICAS-VENEZUELA'],
 ARRAY['Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Frankfurter Allgemeine','Le Monde','Le Figaro','El País','El Mundo','Corriere della Sera','La Repubblica','Der Standard','Die Presse','The Telegraph','ABC News','Sky News','Bloomberg','Wall Street Journal','Financial Times','OilPrice','S&P Global','Mining.com','Times of India','NDTV','The Hindu','Hindustan Times','WION','Folha de S.Paulo','O Globo','El Universal','Clarín','La Nación'],
 ARRAY['restart','rebound','return','comeback','opportunity','recovery','invest','deal','exports','production','output','billions','rush','energy security','supply','black gold','Neustart','Erholung','Investition','Ölgeschäft','Rückkehr','recuperación','inversión','oportunidad','exportaciones','reactivación','producción'],
 true),
('ven_oil_deals_opacity','venezuela_sanctions_oil',2,-1,
 'Opaque deals & who profits','Undurchsichtige Deals & Profiteure',
 'The oil restart is opaque and serves Trump, not Venezuelans',
 'Der Öl-Neustart ist undurchsichtig und dient Trump, nicht den Venezolanern',
 'Behind the comeback are secret contracts and a president boasting he "made a fortune" -- the opacity, cronyism and unanswered question of who benefits are the real story.',
 'Hinter dem Comeback stehen Geheimverträge und ein Präsident, der prahlt, er habe "ein Vermögen gemacht" -- die Intransparenz, Vetternwirtschaft und die offene Frage, wer profitiert, sind die eigentliche Geschichte.',
 ARRAY['AMERICAS-USA','NON-STATE-EU','AMERICAS-VENEZUELA'],
 ARRAY['Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Frankfurter Allgemeine','Le Monde','Le Figaro','El País','El Mundo','Corriere della Sera','La Repubblica','Der Standard','Die Presse','The Telegraph','ABC News','Sky News','Bloomberg','Wall Street Journal','Financial Times'],
 ARRAY['secret','opaque','opacity','transparency','made a fortune','fortune','who benefits','cronies','crony','linger','murky','plunder','looting','kickback','no accountability','Geheim','undurchsichtig','Intransparenz','Vermögen gemacht','wer profitiert','secreto','opaco','opacidad','transparencia','saqueo','a quién beneficia'],
 true),
('ven_oil_imperial_plunder','venezuela_sanctions_oil',3,-2,
 'Imperial resource grab','Imperiale Ressourcenplünderung',
 'Washington is looting Venezuela''s oil wealth',
 'Washington plündert Venezuelas Ölreichtum',
 'The whole operation was about seizing the world''s largest reserves -- the US toppled a government to take the oil, a textbook imperial resource grab dressed up as sanctions relief.',
 'Bei der ganzen Operation ging es darum, sich die größten Reserven der Welt zu sichern -- die USA stürzten eine Regierung, um das Öl zu nehmen: eine imperiale Ressourcenplünderung im Gewand der Sanktionslockerung.',
 ARRAY['EUROPE-RUSSIA','ASIA-CHINA','MIDEAST-IRAN'],
 ARRAY['TASS (EN)','TASS','RT','Lenta.ru','Izvestia','CGTN','China Daily','Global Times','Press TV','Al Jazeera','Al Arabiya','Al-Ahram','Anadolu Agency'],
 NULL,
 false),

-- ======================= B. POLITICAL TRANSITION =======================
('ven_transition_stabilization','venezuela_political_transition',1,1,
 'Stabilisation & reform','Stabilisierung & Reform',
 'The interim government is stabilising Venezuela',
 'Die Übergangsregierung stabilisiert Venezuela',
 'The Rodríguez caretaker administration is restoring order, raising wages and steering a pragmatic transition -- a fragile but real chance to stabilise the country.',
 'Die geschäftsführende Regierung Rodríguez stellt die Ordnung wieder her, erhöht die Löhne und steuert einen pragmatischen Übergang -- eine fragile, aber echte Chance, das Land zu stabilisieren.',
 ARRAY['AMERICAS-VENEZUELA','AMERICAS-USA'],
 ARRAY['Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Frankfurter Allgemeine','Le Monde','Le Figaro','El País','El Mundo','Corriere della Sera','La Repubblica','Der Standard','Die Presse','The Telegraph','ABC News','Sky News','Bloomberg','Financial Times','Clarín','La Nación','Folha de S.Paulo','O Globo','El Universal'],
 ARRAY['stabil','reform','recovery','wage','minimum income','normalis','normaliz','pragmat','rebuild','order','100 days','first 100','Stabil','Reform','Erholung','Lohnerhöhung','Aufbau','Ordnung','estabil','reforma','recuperación','salario','normaliza','orden','primeros 100'],
 true),
('ven_transition_democracy_betrayed','venezuela_political_transition',2,-1,
 'Stolen transition','Gestohlener Übergang',
 'Chavismo survives; the opposition is frozen out',
 'Der Chavismo überlebt; die Opposition bleibt ausgeschlossen',
 'A chavista clique simply swapped faces: Machado and the opposition are sidelined, promised elections never come, and the "transition" entrenches the old regime under a new manager.',
 'Eine chavistische Clique hat nur die Gesichter getauscht: Machado und die Opposition werden ausgebootet, versprochene Wahlen bleiben aus, und der "Übergang" zementiert das alte Regime unter neuer Führung.',
 ARRAY['NON-STATE-EU','AMERICAS-VENEZUELA','AMERICAS-USA'],
 ARRAY['Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Frankfurter Allgemeine','Le Monde','Le Figaro','El País','El Mundo','Corriere della Sera','La Repubblica','Der Standard','Die Presse','The Telegraph','ABC News','Sky News','Clarín','La Nación','Reforma','O Estado de S. Paulo'],
 ARRAY['frozen out','sidelined','no elections','without elections','sham','illegitim','opposition demands','Machado','betray','authoritarian','entrench','power grab','crackdown','unrest','ausgeschlossen','keine Wahlen','Schein','illegitim','Opposition','Demokratie','frozen','sin elecciones','oposición','fraude','ilegítim','represión'],
 true),
('ven_transition_imperial_puppet','venezuela_political_transition',3,-2,
 'US-installed puppet','Von den USA eingesetzte Marionette',
 'The transition is a US-installed puppet regime',
 'Der Übergang ist ein von den USA eingesetztes Marionettenregime',
 'Washington abducted a president and hand-picked his successor -- the "transition" is illegal regime change and a foreign-imposed government with no legitimacy.',
 'Washington entführte einen Präsidenten und wählte seinen Nachfolger aus -- der "Übergang" ist illegaler Regimewechsel und eine von außen eingesetzte Regierung ohne Legitimität.',
 ARRAY['EUROPE-RUSSIA','ASIA-CHINA','MIDEAST-IRAN'],
 ARRAY['TASS (EN)','TASS','RT','Lenta.ru','Izvestia','CGTN','China Daily','Global Times','Press TV','Al Jazeera','Al Arabiya','Al-Ahram','Anadolu Agency'],
 NULL,
 false),

-- ==================== C. US COERCION & MILITARY ACTION ==================
('ven_coercion_justified','us_venezuela_relations',1,1,
 'Justified action','Gerechtfertigtes Eingreifen',
 'The US removed a narco-dictator and a security threat',
 'Die USA beseitigten einen Narco-Diktator und eine Sicherheitsbedrohung',
 'Capturing Maduro and striking Tren de Aragua ended a narco-state on America''s doorstep -- a justified counter-narcotics and security operation.',
 'Die Festnahme Maduros und die Schläge gegen Tren de Aragua beendeten einen Narco-Staat vor Amerikas Haustür -- eine gerechtfertigte Anti-Drogen- und Sicherheitsoperation.',
 ARRAY['AMERICAS-USA','MIDEAST-ISRAEL'],
 ARRAY['Fox News','The Australian','Jerusalem Post','Times of Israel','i24NEWS','Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','France 24 (EN)','Der Spiegel','Die Zeit','El País','El Mundo','Bloomberg','The Telegraph','ABC News','Sky News'],
 ARRAY['narco-dictator','narco-state','narco','counter-narcotics','drug','cartel','Tren de Aragua','threat','security','liberat','freed','removed','justice','justified','Diktator','Bedrohung','Sicherheit','Drogen','Kartell','befreit','narcodictador','narcotráfico','amenaza','seguridad','cártel','liberar'],
 true),
('ven_coercion_western_critical','us_venezuela_relations',2,-1,
 'Illegal overreach','Illegaler Machtmissbrauch',
 'The intervention is lawless regime change',
 'Die Intervention ist gesetzloser Regimewechsel',
 'Abducting a head of state, extrajudicial drug-boat killings and troops sent without a war-powers vote are unlawful overreach -- coercion, not the rule of law.',
 'Die Entführung eines Staatschefs, außergerichtliche Tötungen auf Drogenbooten und ohne Kriegsvollmachten entsandte Truppen sind gesetzloser Machtmissbrauch -- Zwang statt Rechtsstaatlichkeit.',
 ARRAY['NON-STATE-EU','AMERICAS-USA','AMERICAS-VENEZUELA'],
 ARRAY['Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Frankfurter Allgemeine','Le Monde','Le Figaro','El País','El Mundo','Corriere della Sera','La Repubblica','Der Standard','Die Presse','ABC News','Sky News'],
 ARRAY['illegal','unlawful','without authorization','war powers','extrajudicial','overreach','abduct','coercion','no evidence','lawless','violation','rechtswidrig','ohne Mandat','Kriegsvollmachten','außergerichtlich','Machtmissbrauch','Entführung','Völkerrecht','ilegal','sin autorización','extrajudicial','coerción','secuestro'],
 true),
('ven_coercion_anti_imperial','us_venezuela_relations',3,-2,
 'Imperial aggression','Imperiale Aggression',
 'US gunboat imperialism against a sovereign nation',
 'US-Kanonenboot-Imperialismus gegen eine souveräne Nation',
 'Invading a sovereign country to seize its president and its oil is naked imperialism -- gunboat diplomacy that shreds international law and threatens all of Latin America.',
 'In ein souveränes Land einzumarschieren, um seinen Präsidenten und sein Öl zu ergreifen, ist blanker Imperialismus -- Kanonenbootpolitik, die das Völkerrecht zerreißt und ganz Lateinamerika bedroht.',
 ARRAY['EUROPE-RUSSIA','ASIA-CHINA','MIDEAST-IRAN'],
 ARRAY['TASS (EN)','TASS','RT','Lenta.ru','Izvestia','CGTN','China Daily','Global Times','Press TV','Al Jazeera','Al Arabiya','Al-Ahram','Anadolu Agency'],
 NULL,
 false),

-- ========================= D. ESSEQUIBO DISPUTE ========================
('ven_essequibo_venezuelan_claim','essequibo_dispute',1,1,
 'Venezuelan sovereign claim','Venezolanischer Souveränitätsanspruch',
 'Essequibo is historically Venezuelan territory',
 'Essequibo ist historisch venezolanisches Gebiet',
 'The Guayana Esequiba is Venezuelan by historical right; the World Court has no jurisdiction and Guyana''s unilateral oil auctions in disputed waters are the real provocation.',
 'Die Guayana Esequiba ist historisch venezolanisch; das Weltgericht ist nicht zuständig, und Guyanas einseitige Ölauktionen in umstrittenen Gewässern sind die eigentliche Provokation.',
 ARRAY['AMERICAS-VENEZUELA','EUROPE-RUSSIA','ASIA-CHINA'],
 ARRAY['TASS (EN)','TASS','RT','CGTN','China Daily','Global Times','Press TV'],
 NULL,
 false),
('ven_essequibo_guyana_sovereignty','essequibo_dispute',2,-1,
 'Guyana sovereignty & rule of law','Guyanas Souveränität & Rechtsstaatlichkeit',
 'Venezuela''s claim is an oil-driven threat to Guyana',
 'Venezuelas Anspruch ist eine öl-getriebene Bedrohung Guyanas',
 'The border was settled long ago; Venezuela''s revived claim over Guyana''s Stabroek oil is coercion against a small neighbour, and the World Court''s jurisdiction must be upheld.',
 'Die Grenze wurde vor langer Zeit festgelegt; Venezuelas wiederbelebter Anspruch auf Guyanas Stabroek-Öl ist Zwang gegen einen kleinen Nachbarn, und die Zuständigkeit des Weltgerichts muss gewahrt bleiben.',
 ARRAY['AMERICAS-USA','NON-STATE-EU','AMERICAS-CARIBBEAN'],
 ARRAY['Reuters','Associated Press','BBC World','CNN','The Guardian','France 24 (EN)','Bloomberg','Financial Times'],
 NULL,
 false);

COMMIT;
