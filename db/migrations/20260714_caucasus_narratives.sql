-- Caucasus theater narratives (atomic + theater-level roll-up cards).
-- Bilingual (EN/DE) with framing_keywords in EN+DE+RU. Publisher coalitions
-- from the real ASIA-CAUCASUS corpus. Friendly-critic pattern on the pivot
-- (+2 european_choice / -1 western_caution share Western publishers, both
-- framing_required). Theater cards publisher-DISJOINT within each sign bucket.
-- Reversible: DELETE re-inserts on re-run (idempotent by id).

BEGIN;

-- actor_centroids is NOT NULL with no default; these narratives are all
-- scoped to the Caucasus region. Set a default for this transaction's inserts,
-- then restore the no-default state.
ALTER TABLE narratives_v2 ALTER COLUMN actor_centroids SET DEFAULT ARRAY['ASIA-CAUCASUS'];

DELETE FROM narratives_v2 WHERE fn_id IN
  ('armenia_western_pivot','armenia_azerbaijan_settlement','georgia_geopolitical_drift',
   'caucasus_power_competition','zangezur_corridor','caucasus_theater');

-- =====================================================================
-- ATOMIC: armenia_western_pivot
-- =====================================================================
INSERT INTO narratives_v2 (id, fn_id, display_order, stance, framing_required, name_en, name_de, stance_label_en, stance_label_de, claim_en, claim_de, framing_keywords, publishers) VALUES
('awp_european_choice','armenia_western_pivot',1,2,true,
 'Armenia''s turn to Europe is a sovereign, democratic escape from Russian domination',
 'Armeniens Hinwendung zu Europa ist ein souveräner, demokratischer Ausbruch aus russischer Vorherrschaft',
 'Sovereign European choice','Souveräne europäische Entscheidung',
 'Western/pro-European framing celebrates Armenia''s pivot as a hard-won, democratic choice: a sovereign state escaping a failed Russian security guarantee, winning elections against Moscow''s pressure, and charting a European future through EU trade, accession talks and the EPC summit.',
 'Die westlich/proeuropäische Deutung feiert Armeniens Schwenk als hart erkämpfte demokratische Entscheidung: ein souveräner Staat, der einer gescheiterten russischen Sicherheitsgarantie entkommt, gegen Moskaus Druck Wahlen gewinnt und über EU-Handel, Beitrittsgespräche und den EPG-Gipfel eine europäische Zukunft ansteuert.',
 ARRAY['pivot to Europe','turn to Europe','away from Russia','break with Russia','sovereign choice','pro-Western','historic shift','escape Moscow','European future','defies Russia','Hinwendung nach Europa','Abkehr von Russland','souveräne Entscheidung','historischer Wandel','разворот на Запад','суверенный выбор','европейский выбор'],
 ARRAY['Reuters','Euronews','Euronews.com','France 24 (EN)','France 24','BBC World','Associated Press','The Guardian','CNN','Deutsche Welle','EurActiv','Financial Times','Bloomberg','Washington Post','Der Spiegel','Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','Der Standard','Tagesschau','ANSA','La Repubblica','El País','Le Figaro','Carnegie Endowment','Novinite','Kyiv Post','LRT English','The Economist','Sky News','ABC News','The Australian','The National']),
('awp_western_caution','armenia_western_pivot',2,-1,true,
 'The pivot leaves Armenia dangerously exposed, and the European path may not deliver',
 'Der Schwenk lässt Armenien gefährlich ungeschützt, und der europäische Weg liefert womöglich nicht',
 'Western caution: an exposed pivot','Westliche Skepsis: ein ungeschützter Schwenk',
 'A sympathetic-but-worried Western analytical strand warns the pivot is a gamble: Armenia is walking a tightrope with no security guarantee to replace Russia, faces Moscow''s economic retaliation, and Brussels can offer no real accession path yet -- risk and overreach, not triumph.',
 'Ein wohlwollend-besorgter westlicher Analysestrang warnt, der Schwenk sei ein Wagnis: Armenien balanciert ohne Sicherheitsgarantie als Russland-Ersatz auf einem Drahtseil, riskiert Moskaus wirtschaftliche Vergeltung, und Brüssel kann noch keinen echten Beitrittsweg bieten -- Risiko und Selbstüberschätzung statt Triumph.',
 ARRAY['tightrope','exposed','no security guarantee','no guarantees','security vacuum','risk','risky','gamble','may not','no EU path','cannot protect','retaliation','overreach','specters','Drahtseil','ungeschützt','keine Garantie','Risiko','Vergeltung','риск','без гарантий','канатоходец'],
 ARRAY['Reuters','Euronews','Euronews.com','France 24 (EN)','France 24','BBC World','Associated Press','The Guardian','CNN','Deutsche Welle','EurActiv','Financial Times','Bloomberg','Washington Post','Der Spiegel','Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','Der Standard','Tagesschau','ANSA','La Repubblica','El País','Le Figaro','Carnegie Endowment','Novinite','Kyiv Post','LRT English','The Economist']),
('awp_russian_capture','armenia_western_pivot',3,-2,false,
 'Armenia is being dragged into an anti-Russian orbit by a Western-engineered capture',
 'Armenien wird durch eine vom Westen inszenierte Vereinnahmung in eine antirussische Umlaufbahn gezogen',
 'Western capture / betrayal of alliance','Westliche Vereinnahmung / Bündnisverrat',
 'Russian state framing treats the pivot as a hostile Western operation: elections tainted by "collective West" interference, Pashinyan a Western puppet betraying an ally, Armenia headed for a "Ukraine scenario" and economic ruin once it forfeits EAEU and CSTO benefits.',
 'Die russische Staatsdeutung sieht den Schwenk als feindliche Westoperation: durch Einmischung des "kollektiven Westens" verfälschte Wahlen, Paschinjan als westliche Marionette und Bündnisverräter, Armenien auf dem Weg in ein "Ukraine-Szenario" und den wirtschaftlichen Ruin, sobald es die Vorteile von EAWU und OVKS verspielt.',
 ARRAY['collective West','interference','foreign interference','rigged','irregularities','puppet','Ukraine scenario','economic ruin','freeloading','betrayal','pressure on opposition','Einmischung','Marionette','manipuliert','вмешательство','коллективный Запад','майдан','русофоб'],
 ARRAY['TASS (EN)','TASS','tass.com','RT','RIA Novosti','Lenta.ru','Gazeta.ru','gazeta.ru','Kommersant','Izvestia','BelTA','BelTA Russian']),

-- =====================================================================
-- ATOMIC: armenia_azerbaijan_settlement (war-or-peace container)
-- =====================================================================
('aas_durable_peace','armenia_azerbaijan_settlement',1,2,true,
 'A historic peace is ending a 30-year conflict and normalizing the region',
 'Ein historischer Frieden beendet einen 30-jährigen Konflikt und normalisiert die Region',
 'Historic peace and normalization','Historischer Frieden und Normalisierung',
 'Western and Turkish framing celebrates the Armenia-Azerbaijan settlement -- and the parallel Armenia-Turkey opening -- as a historic, US-brokered peace that ends decades of war, delimits the border, reopens trade and railways, and integrates the South Caucasus.',
 'Die westliche und türkische Deutung feiert die Regelung zwischen Armenien und Aserbaidschan -- samt der parallelen Öffnung zwischen Armenien und der Türkei -- als historischen, von den USA vermittelten Frieden, der jahrzehntelangen Krieg beendet, die Grenze zieht, Handel und Bahnverbindungen öffnet und den Südkaukasus integriert.',
 ARRAY['peace deal','peace treaty','historic','normalization','normalisation','breakthrough','ends conflict','reconciliation','regional integration','signed','direct trade','reopen','Friedensabkommen','historisch','Normalisierung','Aussöhnung','мирный договор','историческое','нормализация','примирение'],
 ARRAY['Reuters','Euronews','Euronews.com','Associated Press','BBC World','The Guardian','CNN','Deutsche Welle','EurActiv','Financial Times','Bloomberg','ANSA','La Repubblica','El País','Novinite','The National','Daily Sabah','Anadolu Agency','TRT World','Express Tribune','Dawn']),
('aas_armenian_grievance','armenia_azerbaijan_settlement',2,-1,true,
 'The "peace" is a capitulation that rewards ethnic cleansing and leaves accountability unmet',
 'Der "Frieden" ist eine Kapitulation, die ethnische Säuberung belohnt und Verantwortung ungesühnt lässt',
 'Coerced peace / Armenian grievance','Erzwungener Frieden / armenisches Unrecht',
 'A pro-Armenian and human-rights framing rejects the triumphalist peace story: the deal was dictated to a defeated Armenia, the 2023 exodus of Karabakh Armenians amounts to ethnic cleansing, prisoners of war remain in Baku, and torture and war crimes go unpunished.',
 'Eine proarmenische und menschenrechtliche Deutung weist die triumphalistische Friedenserzählung zurück: der Deal wurde einem besiegten Armenien diktiert, der Exodus der Karabach-Armenier 2023 komme einer ethnischen Säuberung gleich, Kriegsgefangene säßen weiter in Baku, Folter und Kriegsverbrechen blieben ungesühnt.',
 ARRAY['ethnic cleansing','forced displacement','exodus','capitulation','dictated','prisoners of war','war crimes','torture','unpunished','triumphalism','blockade','hostages','ethnische Säuberung','Vertreibung','Kriegsverbrechen','Kriegsgefangene','Kapitulation','Folter','этническая чистка','военнопленные','капитуляция','военные преступления']||ARRAY['coerced'],
 ARRAY['France 24 (EN)','France 24','Le Figaro','Le Monde','The Guardian','Deutsche Welle','Der Spiegel','Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','Der Standard','Haaretz','Carnegie Endowment']),
('aas_russia_sidelined','armenia_azerbaijan_settlement',3,-2,false,
 'A Western- and Turkish-hijacked settlement sidelines Russia and destabilizes its sphere',
 'Eine vom Westen und der Türkei gekaperte Regelung drängt Russland an den Rand und destabilisiert seine Sphäre',
 'Russia sidelined','Russland an den Rand gedrängt',
 'Russian state framing casts the settlement as a Western and Turkish power grab: Washington and Ankara hijack a peace Moscow once brokered, push out Russian peacekeepers, and impose the Zangezur/"Trump Route" arrangement -- an unstable, externally dictated deal that erodes Russia''s role.',
 'Die russische Staatsdeutung stellt die Regelung als westlich-türkischen Machtgriff dar: Washington und Ankara kaperten einen einst von Moskau vermittelten Frieden, verdrängten russische Friedenstruppen und erzwängen die Sangesur-/"Trump-Route"-Regelung -- ein instabiler, von außen diktierter Deal, der Russlands Rolle untergräbt.',
 ARRAY['sideline','hijack','power grab','push out','peacekeepers','externally imposed','unstable','dictated by the West','excludes Russia','вытеснить','навязанный','миротворцы','в обход России','an den Rand','Machtgriff','Friedenstruppen'],
 ARRAY['TASS (EN)','TASS','tass.com','RT','RIA Novosti','Lenta.ru','Gazeta.ru','gazeta.ru','Kommersant','Izvestia','BelTA','BelTA Russian']),

-- =====================================================================
-- ATOMIC: georgia_geopolitical_drift (placeholder)
-- =====================================================================
('ggd_european_aspiration','georgia_geopolitical_drift',1,2,true,
 'Georgians want a European future their government is betraying',
 'Georgier wollen eine europäische Zukunft, die ihre Regierung verrät',
 'European aspiration betrayed','Verratene europäische Perspektive',
 'Western framing backs Georgia''s pro-European majority against a Georgian Dream government sliding toward Moscow: a Russian-style foreign-agent law, EU-accession freeze, contested elections and street protests met with a crackdown mark a democratic backsliding away from the European path.',
 'Die westliche Deutung stellt sich hinter Georgiens proeuropäische Mehrheit gegen eine Regierung des Georgischen Traums, die Richtung Moskau abdriftet: ein Agentengesetz nach russischem Vorbild, eingefrorener EU-Beitritt, umstrittene Wahlen und niedergeschlagene Straßenproteste markieren einen demokratischen Rückschritt weg vom europäischen Weg.',
 ARRAY['pro-European','pro-EU','protests','democracy','foreign agent','backsliding','crackdown','European path','candidate status','betray','proeuropäisch','Proteste','Rückschritt','Agentengesetz','проевропейск','протесты','иностранных агентов'],
 ARRAY['Reuters','Euronews','Euronews.com','France 24 (EN)','France 24','BBC World','Associated Press','The Guardian','CNN','Deutsche Welle','EurActiv','Financial Times','Der Spiegel','Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','Der Standard','Politico','Novinite','iROZHLAS']),
('ggd_sovereignty_stability','georgia_geopolitical_drift',2,-2,false,
 'Tbilisi is resisting a Western-orchestrated colour revolution and defending its sovereignty',
 'Tiflis widersteht einer vom Westen orchestrierten Farbrevolution und verteidigt seine Souveränität',
 'Anti-Western sovereignty defense','Antiwestliche Souveränitätsverteidigung',
 'Russian state framing praises the Georgian government for resisting a Western-funded "colour revolution": the foreign-agent law is legitimate self-defense against NGO subversion, the protests are an externally engineered Maidan, and Tbilisi is defending sovereignty and stability against EU coercion.',
 'Die russische Staatsdeutung lobt die georgische Regierung für den Widerstand gegen eine westlich finanzierte "Farbrevolution": das Agentengesetz sei legitime Selbstverteidigung gegen NGO-Unterwanderung, die Proteste ein von außen inszenierter Maidan, und Tiflis verteidige Souveränität und Stabilität gegen EU-Zwang.',
 ARRAY['colour revolution','color revolution','Maidan','sovereignty','stability','Western-funded','NGO','subversion','coercion','interference','Farbrevolution','Souveränität','Einmischung','цветная революция','майдан','суверенитет','вмешательство'],
 ARRAY['TASS (EN)','TASS','tass.com','RT','RIA Novosti','Lenta.ru','Gazeta.ru','gazeta.ru','Kommersant','Izvestia','BelTA','BelTA Russian']),

-- =====================================================================
-- ATOMIC: caucasus_power_competition
-- =====================================================================
('cpc_genocide_recognition','caucasus_power_competition',1,1,true,
 'Recognizing the Armenian Genocide is an act of moral clarity and historic justice',
 'Die Anerkennung des Völkermords an den Armeniern ist ein Akt moralischer Klarheit und historischer Gerechtigkeit',
 'Moral recognition','Moralische Anerkennung',
 'An Israeli and Western framing presents recognition of the Armenian Genocide as overdue moral clarity and historic justice -- honoring 1.5 million victims and asserting a duty of memory -- even as it inflames relations with Turkey.',
 'Eine israelische und westliche Deutung stellt die Anerkennung des Völkermords an den Armeniern als überfällige moralische Klarheit und historische Gerechtigkeit dar -- zum Gedenken an 1,5 Millionen Opfer und als Pflicht der Erinnerung -- auch wenn sie das Verhältnis zur Türkei belastet.',
 ARRAY['moral','moral clarity','historic','justice','recognize','recognition','honor','victims','duty','never again','moralisch','historisch','Gerechtigkeit','Anerkennung','Opfer','моральн','признание','геноцида'],
 ARRAY['Jerusalem Post','The Jerusalem Post','Times of Israel','The Times of Israel','i24NEWS','Associated Press','NPR','Euronews','Euronews.com','eKathimerini']),
('cpc_genocide_politicized','caucasus_power_competition',2,-1,true,
 'Israel is weaponizing the genocide label to spite Turkey and deflect from Gaza',
 'Israel instrumentalisiert den Völkermord-Begriff, um der Türkei zu schaden und von Gaza abzulenken',
 'Cynical politicization','Zynische Instrumentalisierung',
 'A Turkish and Azerbaijani framing rejects the recognition as a cynical political weapon: a distortion of history timed to spite Ankara and cover Israel''s own conduct in Gaza, not a sincere act of remembrance.',
 'Eine türkische und aserbaidschanische Deutung weist die Anerkennung als zynische politische Waffe zurück: eine Geschichtsverzerrung, um Ankara zu schaden und Israels eigenes Vorgehen in Gaza zu überdecken -- kein aufrichtiger Akt des Gedenkens.',
 ARRAY['distortion','weaponize','weaponise','politicize','politicise','political','cynical','cover','Gaza','childish','spite','distortion of history','Verzerrung','instrumentalisier','politisch','искажение','политиз'],
 ARRAY['Daily Sabah','Anadolu Agency','TRT World','Al-Ahram','Arab News']),
('cpc_russia_iran_squeeze','caucasus_power_competition',3,-2,false,
 'Western, Turkish and Israeli penetration of the Caucasus is an encirclement to be resisted',
 'Das Vordringen des Westens, der Türkei und Israels in den Kaukasus ist eine Einkreisung, der zu widerstehen ist',
 'Russia/Iran resist encirclement','Russland/Iran widerstehen der Einkreisung',
 'A Russian and Iranian framing casts the competition as hostile external penetration: US, Turkish and Israeli inroads -- bases, energy deals, the Trump Route -- threaten Russian and Iranian interests and regional stability, and must be resisted through their own partnerships.',
 'Eine russische und iranische Deutung stellt den Wettbewerb als feindliches Eindringen von außen dar: US-amerikanische, türkische und israelische Vorstöße -- Stützpunkte, Energieabkommen, die Trump-Route -- bedrohten russische und iranische Interessen und die regionale Stabilität und müssten durch eigene Partnerschaften abgewehrt werden.',
 ARRAY['encirclement','penetration','inroads','threat to stability','red line','Israeli operations','foreign base','resist','sphere of influence','Einkreisung','Vordringen','rote Linie','Bedrohung','угроза','вторжение','красная линия','сфера влияния'],
 ARRAY['TASS (EN)','TASS','tass.com','RT','RIA Novosti','Lenta.ru','Gazeta.ru','gazeta.ru','Kommersant','Izvestia','IRNA','Press TV']),

-- =====================================================================
-- ATOMIC: zangezur_corridor
-- =====================================================================
('zc_connectivity_prosperity','zangezur_corridor',1,1,false,
 'The corridor unlocks connectivity, trade and a regional peace dividend',
 'Der Korridor erschließt Konnektivität, Handel und eine regionale Friedensdividende',
 'Connectivity and prosperity','Konnektivität und Wohlstand',
 'Western, Turkish and Azerbaijani framing presents the Zangezur route -- rebranded the US-backed "Trump Route"/TRIPP -- as a transformative connectivity project unlocking east-west trade, jobs and a peace dividend for the whole region.',
 'Die westliche, türkische und aserbaidschanische Deutung präsentiert die Sangesur-Route -- neu benannt als US-gestützte "Trump-Route"/TRIPP -- als transformatives Konnektivitätsprojekt, das Ost-West-Handel, Arbeitsplätze und eine Friedensdividende für die ganze Region erschließt.',
 ARRAY['connectivity','trade route','prosperity','peace dividend','unlock','transit hub','east-west','Trump Route','TRIPP','Konnektivität','Handelsroute','Wohlstand','Trump-Route','коридор','торговый маршрут'],
 ARRAY['Reuters','Euronews','Euronews.com','Associated Press','Bloomberg','Financial Times','OilPrice','Daily Sabah','Anadolu Agency','TRT World','The Astana Times','Tengrinews','ANSA']),
('zc_sovereignty_threat','zangezur_corridor',2,-1,false,
 'The corridor is an extraterritorial threat to Armenian sovereignty and Iran''s border',
 'Der Korridor ist eine extraterritoriale Bedrohung für Armeniens Souveränität und Irans Grenze',
 'Sovereignty and red-line threat','Souveränitäts- und Grenzbedrohung',
 'An Iranian and Russian framing warns the corridor is a strategic threat: an extraterritorial route carving through Armenian sovereign territory, severing Iran''s land border with Armenia and inserting US/NATO influence -- a red line to be blocked, not a peace project.',
 'Eine iranische und russische Deutung warnt, der Korridor sei eine strategische Bedrohung: eine extraterritoriale Route mitten durch armenisches Hoheitsgebiet, die Irans Landgrenze zu Armenien durchtrenne und US-/NATO-Einfluss einschleuse -- eine rote Linie, die zu blockieren sei, kein Friedensprojekt.',
 ARRAY['extraterritorial','sovereignty','red line','sever','border','security risk','US influence','NATO','block','threat','extraterritorial','Souveränität','rote Linie','Grenze','экстерриториальн','суверенитет','красная линия','угроза'],
 ARRAY['IRNA','Press TV','TASS (EN)','TASS','tass.com','RT','RIA Novosti','Lenta.ru','Gazeta.ru','gazeta.ru','Kommersant','Izvestia']),

-- =====================================================================
-- THEATER-LEVEL ROLL-UP CARDS (publisher-disjoint within each sign)
-- =====================================================================
('caucasus_western_consensus','caucasus_theater',1,2,false,
 'The South Caucasus is realigning westward -- peace, connectivity and a break from Russia',
 'Der Südkaukasus richtet sich neu nach Westen aus -- Frieden, Konnektivität und ein Bruch mit Russland',
 'Western/regional realignment consensus','Konsens westlicher/regionaler Neuordnung',
 'Western, Turkish and Israeli coverage reads the South Caucasus as tilting decisively toward the West and a post-Russian order: Armenia''s European pivot, a US-brokered Armenia-Azerbaijan peace, opening trade corridors, and recognition of historic wrongs together mark a strategic realignment away from Moscow.',
 'Die westliche, türkische und israelische Berichterstattung liest den Südkaukasus als klar nach Westen und zu einer nachrussischen Ordnung neigend: Armeniens europäischer Schwenk, ein von den USA vermittelter Frieden zwischen Armenien und Aserbaidschan, sich öffnende Handelskorridore und die Anerkennung historischen Unrechts markierten zusammen eine strategische Neuordnung weg von Moskau.',
 ARRAY['realignment','pivot','peace','connectivity','European','away from Russia','Neuordnung','Frieden','realignment'],
 ARRAY['Reuters','Euronews','Euronews.com','France 24 (EN)','France 24','BBC World','Associated Press','The Guardian','CNN','Deutsche Welle','EurActiv','Financial Times','Bloomberg','Washington Post','Der Spiegel','Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','Der Standard','Tagesschau','ANSA','La Repubblica','El País','Le Figaro','Carnegie Endowment','Novinite','Kyiv Post','LRT English','The Economist','The National','Daily Sabah','Anadolu Agency','TRT World','Jerusalem Post','The Jerusalem Post','Times of Israel','The Times of Israel','i24NEWS']),
('caucasus_russia_china_counter','caucasus_theater',2,-2,false,
 'The West is destabilizing Russia''s neighbourhood and dragging it into an anti-Russian orbit',
 'Der Westen destabilisiert Russlands Nachbarschaft und zieht sie in eine antirussische Umlaufbahn',
 'Russia/China counter-narrative','Gegenerzählung Russlands/Chinas',
 'Russian and Chinese state media frame the same events as reckless Western expansionism: election interference, colour-revolution engineering and Turkish/US/Israeli penetration are destabilizing Russia''s traditional sphere and steering the Caucasus toward a "Ukraine scenario" of chaos and dependency.',
 'Russische und chinesische Staatsmedien deuten dieselben Ereignisse als rücksichtslosen westlichen Expansionismus: Wahleinmischung, das Inszenieren von Farbrevolutionen und türkisch/US-amerikanisch/israelisches Vordringen destabilisierten Russlands traditionelle Sphäre und steuerten den Kaukasus in ein "Ukraine-Szenario" aus Chaos und Abhängigkeit.',
 ARRAY['interference','colour revolution','Ukraine scenario','encirclement','expansionism','destabiliz','Einmischung','Farbrevolution','вмешательство','дестабилизац'],
 ARRAY['TASS (EN)','TASS','tass.com','RT','RIA Novosti','Lenta.ru','Gazeta.ru','gazeta.ru','Kommersant','Izvestia','BelTA','BelTA Russian','CGTN','news.cgtn.com','Global Times','China Daily','People''s Daily','Xinhua']),
('caucasus_iran_regional','caucasus_theater',3,-1,false,
 'External penetration threatens the region''s balance; Iran defends its borders and ties',
 'Äußeres Vordringen bedroht das Gleichgewicht der Region; Iran verteidigt seine Grenzen und Beziehungen',
 'Iranian regional-resistance framing','Iranische Deutung regionalen Widerstands',
 'Iranian state media offer a distinct regional-resistance reading: US, Israeli and Turkish inroads -- above all the Zangezur/"Trump Route" and Israeli activity via Azerbaijan -- threaten Iran''s northern border and the regional balance, while Tehran stresses its deep friendship with Armenia and opposition to outside interference.',
 'Iranische Staatsmedien bieten eine eigenständige Lesart regionalen Widerstands: US-amerikanische, israelische und türkische Vorstöße -- vor allem die Sangesur-/"Trump-Route" und israelische Aktivitäten über Aserbaidschan -- bedrohten Irans Nordgrenze und das regionale Gleichgewicht, während Teheran seine tiefe Freundschaft mit Armenien und die Ablehnung äußerer Einmischung betone.',
 ARRAY['red line','border','penetration','regional balance','friendship with Armenia','interference','Trump Route','rote Linie','Grenze','красная линия','граница'],
 ARRAY['IRNA','Press TV']);

ALTER TABLE narratives_v2 ALTER COLUMN actor_centroids DROP DEFAULT;

COMMIT;
