-- Ukraine war theater seed: 1 theater + 5 atomic FNs + 13 narratives + 6 fn_anchor bundles.
-- 2026-05-19
--
-- Atomic FNs:
--   1. ukraine_battlefield          kinetic operations both directions including UA deep strikes into RU
--   2. western_aid_to_ukraine       military + economic aid + credits + joint defense production
--   3. ukraine_peace_negotiations   ceasefire / settlement / territorial concessions debate
--   4. ukraine_official_corruption  NABU/SAP investigations, defense procurement scandals
--   5. russia_sanctions_regime      oil cap, frozen assets, secondary sanctions, evasion
--
-- Theater catch-all narratives (3): pro-Ukraine solidarity, Russian SMO framing, proxy-war restraint critique.
-- Each atomic FN carries pro/con pair (2 narratives each).
--
-- Hybrid-warfare FN deliberately omitted per curator decision (attribution
-- evidence considered insufficiently clean to justify dedicated FN).
--
-- Centroid scope: tight (EUROPE-UKRAINE + EUROPE-RUSSIA) per D-080. Belarus
-- titles flowing through Ukraine/Russia coverage will catch via centroid
-- overlap; pure Belarus-internal stories are out of scope here.

BEGIN;

-- ============================================================
-- 1. friction_nodes rows (theater + 5 atomic)
-- ============================================================

INSERT INTO friction_nodes (id, name_en, name_de, description_en, description_de,
    editorial_summary_en, editorial_summary_de, centroid_ids, fn_type, member_fn_ids,
    is_active, display_order)
VALUES

('ukraine_war_theater', 'Ukraine war theater', 'Ukraine-Krieg Theater',
 'The full-scale Russia-Ukraine war and its surrounding contest of framings: battlefield operations, Western military and economic aid, peace negotiations, anti-corruption investigations of Ukrainian officials, and the sanctions regime on Russia. Coverage spans Ukrainian, Russian, Western mainstream, Eastern European, and Global South press with sharply divergent vocabularies for the same events.',
 'Der voll entfaltete russisch-ukrainische Krieg und sein umgebender Rahmungs-Wettstreit: Gefechtsoperationen, westliche militaerische und wirtschaftliche Hilfe, Friedensverhandlungen, Anti-Korruptionsermittlungen gegen ukrainische Beamte und das Sanktionsregime gegen Russland. Berichterstattung umfasst ukrainische, russische, westliche, osteuropaeische und Global-South-Medien mit stark divergierenden Vokabularen fuer dieselben Ereignisse.',
 'The Ukraine war is the single largest narrative-contested theater in the corpus. Ukrainian and Western mainstream press frame it as a war of national defense against Russian aggression requiring full Western support; Russian state media frame it as a special military operation defending Russian-speaking populations against a Western-backed Kyiv regime; Western contrarian and Global South press frame it as a US/NATO proxy war that should be ended through negotiated settlement. The theater catches broad strategic, humanitarian, refugee, war-crimes, and reconstruction coverage that does not fit the atomic sub-FNs.',
 'Der Ukraine-Krieg ist das mit Abstand am staerksten narrativ umkaempfte Theater im Korpus. Ukrainische und westliche Mainstream-Medien rahmen ihn als nationalen Verteidigungskrieg gegen russische Aggression, der volle westliche Unterstuetzung erfordere; russische Staatsmedien als militaerische Spezialoperation zum Schutz russischsprachiger Bevoelkerungen gegen ein westlich gestuetztes Kiewer Regime; westliche dissidente und Global-South-Medien als US/NATO-Stellvertreterkrieg, der durch verhandelte Beilegung beendet werden sollte. Das Theater faengt breite strategische, humanitaere, Flucht-, Kriegsverbrechens- und Wiederaufbau-Berichterstattung ab, die nicht in die Atomic-FNs passt.',
 ARRAY['EUROPE-UKRAINE','EUROPE-RUSSIA'],
 'theater',
 ARRAY['ukraine_battlefield','western_aid_to_ukraine','ukraine_peace_negotiations','ukraine_official_corruption','russia_sanctions_regime'],
 true, 50),

('ukraine_battlefield', 'Ukraine battlefield operations', 'Gefechtsoperationen in der Ukraine',
 'Kinetic war operations on the Russia-Ukraine front in both directions: Russian advances and missile/drone strikes inside Ukraine, Ukrainian counter-offensives, defensive operations, and deep strikes into Russian territory (Belgorod, Kursk, Bryansk, Moscow oil refineries, Crimean fleet).',
 'Kinetische Kriegsoperationen an der russisch-ukrainischen Front in beiden Richtungen: russische Vorstoesse und Raketen-/Drohnenangriffe in der Ukraine, ukrainische Gegenoffensiven, Verteidigungsoperationen und Tiefenschlaege auf russisches Territorium (Belgorod, Kursk, Brjansk, Moskauer Oelraffinerien, Krim-Flotte).',
 'Battlefield framing splits sharply along publisher cohorts. Ukrainian and Western mainstream press treat Ukrainian Armed Forces operations including deep strikes into Russia as legitimate defense against an invader; vocabulary centers on resistance, liberation, sovereign defense, and proportionate response. Russian state media frame the same operations as a defensive special military operation against NATO encroachment, while Ukrainian strikes into Russia are framed as terrorism targeting civilians. Both cohorts cover the same engagements but with mirror-image vocabulary.',
 'Die Gefechtsrahmung trennt scharf entlang von Verleger-Kohorten. Ukrainische und westliche Mainstream-Medien behandeln Operationen der ukrainischen Streitkraefte einschliesslich Tiefenschlaegen nach Russland als legitime Verteidigung gegen einen Angreifer; das Vokabular kreist um Widerstand, Befreiung, souveraene Verteidigung und verhaeltnismaessige Antwort. Russische Staatsmedien rahmen dieselben Operationen als defensive militaerische Spezialoperation gegen NATO-Vormarsch, waehrend ukrainische Angriffe auf Russland als Terrorismus gegen Zivilisten dargestellt werden. Beide Kohorten berichten ueber dieselben Gefechte mit spiegelbildlichem Vokabular.',
 ARRAY['EUROPE-UKRAINE','EUROPE-RUSSIA'],
 'atomic', NULL, true, 51),

('western_aid_to_ukraine', 'Western aid to Ukraine', 'Westliche Hilfe fuer die Ukraine',
 'Western military, economic, and financial assistance to Ukraine: weapons deliveries (HIMARS, ATACMS, F-16, Patriot, Storm Shadow, Taurus, Leopard, Abrams), financial instruments (ERA loan, Ukraine Facility, frozen Russian assets, REPO Act), and joint defense industrial production (Rheinmetall-Ukraine joint ventures, Czech ammunition initiative, BAE local production).',
 'Westliche militaerische, wirtschaftliche und finanzielle Unterstuetzung fuer die Ukraine: Waffenlieferungen (HIMARS, ATACMS, F-16, Patriot, Storm Shadow, Taurus, Leopard, Abrams), Finanzinstrumente (ERA-Darlehen, Ukraine-Fazilitaet, eingefrorenes russisches Vermoegen, REPO Act) und gemeinsame Ruestungsproduktion (Rheinmetall-Ukraine-Joint-Ventures, tschechische Munitions-Initiative, BAE-Lokalproduktion).',
 'Western aid is the most consequential operational lever in the conflict and the most actively contested by publisher cohort. Pro-aid framing (Ukrainian press + Western mainstream + Eastern European hawks) presents continuing and expanding aid as both moral imperative and strategic necessity, with arguments centering on Ukrainian effectiveness, Russian inability to sustain attritional war if denied easy gains, and the precedent of allowing aggression to succeed. Restraint framing (Russian state press + Western contrarian + Global South + some Hungarian-aligned European) presents aid as escalatory proxy war that delays inevitable settlement, wastes taxpayer money, and risks direct NATO-Russia confrontation.',
 'Westliche Hilfe ist der folgenreichste operative Hebel im Konflikt und der am aktivsten umkaempfte nach Verleger-Kohorte. Pro-Hilfe-Rahmung (ukrainische Medien + westlicher Mainstream + osteuropaeische Falken) praesentiert fortgesetzte und ausgebaute Hilfe als moralische Pflicht und strategische Notwendigkeit; Argumente kreisen um ukrainische Wirksamkeit, russische Unfaehigkeit zu attritivem Krieg ohne leichte Gewinne und den Praezedenzfall, Aggression erfolgreich werden zu lassen. Zurueckhaltungs-Rahmung (russische Staatsmedien + westliche Dissidenten + Global South + einige ungarisch-orientierte Europaeer) praesentiert Hilfe als eskalierenden Stellvertreterkrieg, der unvermeidliche Beilegung verzoegert, Steuergeld verschwendet und direkte NATO-Russland-Konfrontation riskiert.',
 ARRAY['EUROPE-UKRAINE'],
 'atomic', NULL, true, 52),

('ukraine_peace_negotiations', 'Ukraine peace negotiations', 'Ukraine-Friedensverhandlungen',
 'Peace process and settlement architecture for the Russia-Ukraine war: Trump administration framework proposals, EU position, Ukrainian red lines on territorial concessions and NATO membership, Russian maximalist demands, ceasefire and freeze proposals, Istanbul / Riyadh / Doha track diplomacy.',
 'Friedensprozess und Beilegungsarchitektur fuer den russisch-ukrainischen Krieg: Rahmungsvorschlaege der Trump-Administration, EU-Position, ukrainische rote Linien zu territorialen Zugestaendnissen und NATO-Mitgliedschaft, russische Maximalforderungen, Waffenstillstands- und Einfrierungs-Vorschlaege, Istanbul- / Riad- / Doha-Track-Diplomatie.',
 'Peace negotiations are the second-most-contested phenomenon after aid. The Ukrainian maximalist position (Ukrainian press + Western hawks + Eastern European) holds that just peace requires full Russian withdrawal to 1991 borders, security guarantees backed by NATO accession, accountability for war crimes, and reparations, treating any territorial concession as appeasement that invites future invasions. The pragmatic-settlement position (Trump administration, Russian state press, Hungarian-aligned European outlets, Global South) holds that the war is unwinnable for either side at acceptable cost, that territorial reality should be acknowledged, and that a freeze along current lines with security architecture concessions is the realistic exit. EU institutional position sits between the two with internal disagreement.',
 'Friedensverhandlungen sind das nach der Hilfe am zweitstaerksten umkaempfte Phaenomen. Die ukrainische Maximalposition (ukrainische Medien + westliche Falken + Osteuropa) haelt fest, dass gerechter Frieden vollen russischen Rueckzug zu Grenzen von 1991, NATO-Beitritt-gestuetzte Sicherheitsgarantien, Rechenschaft fuer Kriegsverbrechen und Reparationen erfordere; jede territoriale Konzession sei Beschwichtigung, die zu kuenftigen Invasionen einlade. Die pragmatische Beilegungsposition (Trump-Administration, russische Staatsmedien, ungarisch-orientierte EU-Medien, Global South) haelt fest, dass der Krieg fuer beide Seiten zu akzeptablen Kosten nicht gewinnbar sei, territoriale Realitaet anerkannt werden muesse und ein Einfrieren entlang aktueller Linien mit Sicherheitsarchitektur-Zugestaendnissen der realistische Ausgang sei. EU-Institutionsposition liegt dazwischen mit internen Differenzen.',
 ARRAY['EUROPE-UKRAINE','EUROPE-RUSSIA'],
 'atomic', NULL, true, 53),

('ukraine_official_corruption', 'Ukrainian official corruption investigations', 'Korruptionsermittlungen gegen ukrainische Beamte',
 'Corruption investigations of senior Ukrainian officials by NABU (National Anti-Corruption Bureau), SAP (Specialised Anti-Corruption Prosecutor), HACC (High Anti-Corruption Court), and NACP (National Agency for Prevention of Corruption). Recurring foci: defense procurement scandals (food procurement, body armor, drones), presidential office personnel (Yermak, deputy heads), regional governors, customs and energy sector.',
 'Korruptionsermittlungen gegen hochrangige ukrainische Beamte durch NABU (Nationales Anti-Korruptions-Buero), SAP (Spezial-Anti-Korruptions-Staatsanwaltschaft), HACC (Hoechstes Anti-Korruptions-Gericht) und NACP (Nationale Agentur zur Korruptionspraevention). Wiederkehrende Schwerpunkte: Ruestungsbeschaffungs-Skandale (Lebensmittel, Schutzwesten, Drohnen), Personal des Praesidialamts (Jermak, stellvertretende Leiter), regionale Gouverneure, Zoll und Energiesektor.',
 'Corruption framing splits between two cohorts who often cover the same investigations with opposite emphasis. Reform-progress framing (Ukrainian reformist press + Western mainstream + EU policy outlets) treats ongoing investigations as evidence that Ukrainian institutions are working as intended under wartime stress, that anti-corruption infrastructure built since 2014 is functioning, and that prosecutions of senior officials prove independence from the Presidential Office. Endemic-corruption framing (Russian state press + Western contrarian + Global South) treats the same investigations as confirmation that the Zelensky inner circle is systemically corrupt, that Western aid is being stolen at scale, that the regime is authoritarian, and that EU/NATO accession on this institutional basis is unrealistic.',
 'Korruptions-Rahmung trennt zwei Kohorten, die oft dieselben Ermittlungen mit gegensaetzlicher Akzentsetzung beleuchten. Reform-Fortschritts-Rahmung (ukrainische Reformmedien + westlicher Mainstream + EU-Politik-Medien) behandelt laufende Ermittlungen als Beleg dafuer, dass ukrainische Institutionen unter Kriegsstress wie beabsichtigt funktionieren, dass die seit 2014 aufgebaute Anti-Korruptions-Infrastruktur arbeitet und dass Strafverfolgung hochrangiger Beamter Unabhaengigkeit vom Praesidialamt belege. Endemisch-Korruptions-Rahmung (russische Staatsmedien + westliche Dissidenten + Global South) behandelt dieselben Ermittlungen als Bestaetigung, dass der Selenskyj-Kreis systemisch korrupt sei, westliche Hilfe in grossem Stil gestohlen werde, das Regime autoritaer sei und EU/NATO-Beitritt auf dieser institutionellen Basis unrealistisch.',
 ARRAY['EUROPE-UKRAINE'],
 'atomic', NULL, true, 54),

('russia_sanctions_regime', 'Russia sanctions regime', 'Russland-Sanktionsregime',
 'Sanctions architecture imposed on Russia following the 2022 invasion: G7 oil price cap, EU sanctions packages (now in the high teens), frozen Russian sovereign assets (~$300B held primarily by Euroclear), REPO Act provisions, secondary sanctions on third-country evaders, shadow-fleet enforcement, SDN designations of oligarchs and entities, and Russian counter-measures (currency controls, gold reserves, BRICS settlement).',
 'Sanktionsarchitektur gegen Russland seit der Invasion 2022: G7-Oelpreisdeckel, EU-Sanktionspakete (jetzt im hohen zweistelligen Bereich), eingefrorenes russisches Staatsvermoegen (~300 Mrd. USD, hauptsaechlich bei Euroclear), REPO-Act-Bestimmungen, Sekundaersanktionen gegen Umgeher in Drittstaaten, Schatten-Flotten-Durchsetzung, SDN-Listungen von Oligarchen und Unternehmen sowie russische Gegenmassnahmen (Waehrungskontrollen, Goldreserven, BRICS-Abwicklung).',
 'Sanctions framing is the third major axis of the Ukraine war contest. Tighten-and-seize framing (Ukrainian + Western mainstream + Eastern European) treats sanctions as a necessary economic constraint on the Russian war machine, calls for closing evasion loopholes (especially via UAE / Turkey / Central Asia), supports outright seizure of frozen sovereign assets for Ukrainian reconstruction, and frames any sanctions relief as rewarding aggression. Sanctions-ineffective framing (Russian state + Global South + some Chinese state + Hungarian-aligned EU) argues that sanctions have hurt European economies more than the Russian, that the Russian economy has adapted, that frozen-asset seizure would destroy trust in the Western financial system, and that the package should be wound down as part of any peace deal.',
 'Sanktions-Rahmung ist die dritte Hauptachse des Ukraine-Krieg-Wettstreits. Verschaerfen-und-Beschlagnahmen-Rahmung (ukrainisch + westlicher Mainstream + Osteuropa) behandelt Sanktionen als notwendige wirtschaftliche Beschraenkung der russischen Kriegsmaschine, fordert Schliessung von Umgehungsluecken (besonders ueber VAE / Tuerkei / Zentralasien), unterstuetzt direkte Beschlagnahme eingefrorenen Staatsvermoegens fuer ukrainischen Wiederaufbau und rahmt jede Sanktionserleichterung als Belohnung von Aggression. Sanktionen-wirkungslos-Rahmung (russische Staatsmedien + Global South + einige chinesische Staatsmedien + ungarisch-orientierte EU) argumentiert, Sanktionen haetten europaeische Wirtschaften staerker geschaedigt als die russische, die russische Wirtschaft habe sich angepasst, Beschlagnahme eingefrorenen Vermoegens wuerde Vertrauen in das westliche Finanzsystem zerstoeren und das Paket sollte als Teil eines Friedensdeals abgewickelt werden.',
 ARRAY['EUROPE-RUSSIA'],
 'atomic', NULL, true, 55);

-- ============================================================
-- 2. fn_anchor bundles in taxonomy_v3 (6)
-- ============================================================

-- Theater catch-all: broad terms not specific to any atomic FN
INSERT INTO taxonomy_v3 (item_raw, aliases, is_active, taxonomy_function, linked_id) VALUES

('ukraine_war_theater fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'NATO','EU','OSCE','G7','Wagner','BRICS','ICC','ICJ',
     'special military operation','SMO','war crimes','prisoner of war','POW','POW exchange',
     'refugees','displaced','reconstruction','rebuild','aid corridor',
     'Donbas','Donbass','Crimea','Black Sea','Sea of Azov',
     'NATO summit','EU summit','Ramstein','UDCG','Ukraine Defense Contact Group',
     'civilian casualties','grain corridor','Black Sea grain'),
   'de', jsonb_build_array(
     'Krieg','Invasion','Donbass','Krim','Schwarzes Meer','Asowsches Meer',
     'Fluechtlinge','Vertriebene','Wiederaufbau','Getreideabkommen','Getreidekorridor',
     'militaerische Spezialoperation','Kriegsverbrechen','Kriegsgefangene','NATO-Gipfel','EU-Gipfel'),
   'es', jsonb_build_array(
     'guerra','invasion','Donbas','Crimea','Mar Negro','refugiados','desplazados',
     'reconstruccion','crimenes de guerra','prisioneros de guerra',
     'operacion militar especial'),
   'fr', jsonb_build_array(
     'guerre','invasion','Donbass','Crimee','mer Noire','refugies','deplaces',
     'reconstruction','crimes de guerre','prisonniers de guerre',
     'operation militaire speciale','corridor cerealier'),
   'it', jsonb_build_array(
     'guerra','invasione','Donbass','Crimea','Mar Nero','rifugiati','sfollati',
     'ricostruzione','crimini di guerra','prigionieri di guerra',
     'operazione militare speciale'),
   'ru', jsonb_build_array(
     'СВО','спецоперация','специальная военная операция','война',
     'Донбасс','Крым','Черное море','Азовское море',
     'беженцы','переселенцы','восстановление','военнопленные','обмен пленными',
     'зерновая сделка','зерновой коридор','НАТО','ЕС','G7','саммит',
     'военные преступления'),
   'hi', jsonb_build_array(
     'यूक्रेन युद्ध','रूस','नाटो','डोनबास','क्रीमिया','काला सागर',
     'शरणार्थी','विशेष सैन्य अभियान','युद्ध अपराध','युद्ध बंदी'),
   'zh', jsonb_build_array(
     '俄乌战争','乌克兰战争','北约','顿巴斯','克里米亚','黑海',
     '难民','重建','特别军事行动','战俘','战犯','峰会'),
   'ar', jsonb_build_array(
     'الحرب','الحرب الاوكرانية','الناتو','حلف الناتو','دونباس','القرم',
     'البحر الاسود','لاجئين','اعادة الاعمار','عملية عسكرية خاصة',
     'جرائم الحرب','اسرى الحرب','تبادل اسرى','قمة'),
   'ja', jsonb_build_array(
     'ウクライナ戦争','戦争','NATO','EU','ドンバス','クリミア','黒海',
     '難民','復興','特別軍事作戦','戦争犯罪','捕虜','穀物協定')
 ),
 true, 'fn_anchor', 'ukraine_war_theater'),

-- ukraine_battlefield: combat operations both directions
('ukraine_battlefield fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'AFU','ZSU','VKS','VDV','GUR','GRU','Wagner','Rosgvardia','Rosgvardiya',
     'Donetsk','Luhansk','Kupiansk','Bakhmut','Avdiivka','Pokrovsk','Vuhledar',
     'Chasiv Yar','Vovchansk','Krynky','Mariupol','Sevastopol',
     'Kursk','Belgorod','Bryansk','Rostov','Voronezh','Engels','Saki','Kerch',
     'Kharkiv','Mykolaiv','Odesa','Zaporizhzhia','Kherson',
     'HIMARS','ATACMS','Storm Shadow','SCALP','Taurus','Patriot','F-16',
     'Bayraktar','IRIS-T','NASAMS','Caesar','Leopard','Abrams','Bradley',
     'Iskander','Kalibr','Kinzhal','Shahed','Geran','Lancet','FAB','KAB','FPV',
     'offensive','counteroffensive','strike','drone strike','missile attack',
     'shelling','mobilisation','conscription','breakthrough','frontline','front line',
     'glide bomb','suicide drone','loitering munition','EW','electronic warfare',
     'Crimean Bridge','Kerch Bridge','Black Sea Fleet'),
   'de', jsonb_build_array(
     'Donezk','Luhansk','Kupjansk','Bachmut','Pokrowsk','Mariupol','Sewastopol',
     'Kursk','Belgorod','Brjansk','Charkiw','Cherson','Saporischschja',
     'Offensive','Gegenoffensive','Angriff','Drohnenangriff','Raketenangriff',
     'Beschuss','Mobilmachung','Wehrpflicht','Durchbruch','Frontlinie',
     'Gleitbombe','Kampfdrohne','Kamikaze-Drohne','Krim-Bruecke'),
   'es', jsonb_build_array(
     'Donetsk','Lugansk','Bajmut','Pokrovsk','Mariupol','Sebastopol',
     'Kursk','Belgorod','Briansk','Jarkov','Jerson','Zaporiyia',
     'ofensiva','contraofensiva','ataque','ataque con drones','ataque con misiles',
     'movilizacion','frente','dron','bomba planeadora','puente de Crimea'),
   'fr', jsonb_build_array(
     'Donetsk','Louhansk','Bakhmout','Pokrovsk','Marioupol','Sebastopol',
     'Koursk','Belgorod','Briansk','Kharkov','Kharkiv','Kherson','Zaporijia',
     'offensive','contre-offensive','frappe','frappe de drone','attaque de missile',
     'mobilisation','ligne de front','drone','bombe planante','pont de Crimee'),
   'it', jsonb_build_array(
     'Donetsk','Lugansk','Bakhmut','Pokrovsk','Mariupol','Sebastopoli',
     'Kursk','Belgorod','Briansk','Kharkiv','Kherson','Zaporizhzhia',
     'offensiva','controffensiva','attacco','attacco con droni','missile',
     'mobilitazione','linea del fronte','drone','bomba planante','ponte di Crimea'),
   'ru', jsonb_build_array(
     'ВСУ','ВКС','ВДВ','ГУР','ГРУ','Вагнер','Росгвардия',
     'Донецк','Луганск','Купянск','Бахмут','Авдеевка','Покровск','Угледар',
     'Часов Яр','Волчанск','Крынки','Мариуполь','Севастополь',
     'Курск','Белгород','Брянск','Ростов','Воронеж','Энгельс',
     'Харьков','Николаев','Одесса','Запорожье','Херсон',
     'Хаймарс','АТАКМС','Шторм Шэдоу','Таурус','Пэтриот','Байрактар',
     'Искандер','Калибр','Кинжал','Шахед','Герань','Ланцет','ФАБ','КАБ',
     'наступление','контрнаступление','удар','удар БПЛА','ракетный удар',
     'обстрел','мобилизация','прорыв','линия фронта','планирующая бомба',
     'Крымский мост','Керченский мост','Черноморский флот'),
   'hi', jsonb_build_array(
     'डोनेट्स्क','लुहान्स्क','बखमुत','मारियुपोल',
     'कुर्स्क','बेलगोरोद','खारकीव','खेरसन','ज़ापोरिज्जिया',
     'हमला','ड्रोन हमला','मिसाइल हमला','मोर्चा','क्रीमिया पुल'),
   'zh', jsonb_build_array(
     '顿涅茨克','卢甘斯克','巴赫穆特','马里乌波尔','塞瓦斯托波尔',
     '库尔斯克','别尔哥罗德','哈尔科夫','赫尔松','扎波罗热',
     '海玛斯','陆军战术导弹','风暴之影','金牛座','爱国者','拜拉克塔尔',
     '伊斯坎德尔','口径','匕首','沙赫德','柳叶刀',
     '进攻','反攻','打击','无人机袭击','导弹袭击','炮击','动员','前线',
     '克里米亚大桥','黑海舰队'),
   'ar', jsonb_build_array(
     'دونيتسك','لوهانسك','باخموت','ماريوبول','سيفاستوبول',
     'كورسك','بيلغورود','بريانسك','خاركيف','خيرسون','زاباروجيا',
     'هايمارس','اتاكمز','ستورم شادو','توروس','باتريوت','بيرقدار',
     'اسكندر','كاليبر','كينجال','شاهد','الجبهة','الخطوط الامامية',
     'هجوم','هجوم مضاد','ضربة','ضربة بطائرة مسيرة','ضربة صاروخية',
     'قصف','تعبئة','اختراق','قنبلة انزلاقية','جسر القرم'),
   'ja', jsonb_build_array(
     'ドネツク','ルガンスク','バフムト','マリウポリ','セバストポリ',
     'クルスク','ベルゴロド','ハリコフ','ヘルソン','ザポリージャ',
     'ハイマース','ATACMS','ストームシャドウ','タウルス','パトリオット',
     'バイラクタル','イスカンデル','カリブル','キンジャール','シャヘド',
     '攻勢','反攻','攻撃','ドローン攻撃','ミサイル攻撃','砲撃','動員',
     '前線','滑空爆弾','クリミア大橋','黒海艦隊')
 ),
 true, 'fn_anchor', 'ukraine_battlefield'),

-- western_aid_to_ukraine: weapons + finance + joint production
('western_aid_to_ukraine fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'Ramstein','UDCG','Ukraine Defense Contact Group','NATO','EU Council',
     'Taurus','HIMARS','ATACMS','Storm Shadow','SCALP','Patriot','F-16',
     'Leopard','Abrams','Bradley','Stinger','Javelin','IRIS-T','NASAMS',
     'Caesar','Archer','AMX-10','PzH 2000','Marder',
     'Rheinmetall','BAE','Lockheed','Raytheon','KMW','Nexter','Saab','Norinco',
     'ERA loan','Ukraine Facility','REPO Act','Lend-Lease','European Peace Facility','EPF',
     'macro-financial assistance','MFA','frozen assets','immobilised assets',
     'aid package','military aid','economic aid','weapons delivery','security assistance',
     'training mission','defence production','defense production','joint venture',
     'ammunition supply','155mm','shells','artillery shells','Czech initiative',
     'extraordinary revenue acceleration','windfall profits'),
   'de', jsonb_build_array(
     'Ramstein','Ukraine-Verteidigungsgruppe','Waffenlieferung','Militaerhilfe',
     'Wirtschaftshilfe','Sicherheitsunterstuetzung','Hilfspaket','Ausbildungsmission',
     'Ruestungsproduktion','Joint Venture','Munition','Granaten','Artilleriegranaten',
     'eingefrorene Vermoegen','Ukraine-Fazilitaet','Friedensfazilitaet','Leopard',
     'tschechische Munitions-Initiative','Sondervermoegen'),
   'es', jsonb_build_array(
     'Ramstein','ayuda militar','ayuda economica','entrega de armas','asistencia de seguridad',
     'paquete de ayuda','mision de entrenamiento','produccion de defensa','municion',
     'proyectiles de artilleria','activos congelados','servicio Ucrania','iniciativa checa'),
   'fr', jsonb_build_array(
     'Ramstein','aide militaire','aide economique','livraison d''armes',
     'assistance de securite','plan d''aide','mission de formation','production de defense',
     'munitions','obus d''artillerie','avoirs geles','facilite Ukraine',
     'initiative tcheque','facilite europeenne de paix'),
   'it', jsonb_build_array(
     'Ramstein','aiuti militari','aiuti economici','consegna di armi','assistenza di sicurezza',
     'pacchetto di aiuti','missione di addestramento','produzione di difesa','munizioni',
     'proietti d''artiglieria','beni congelati','Strumento Ucraina','iniziativa ceca'),
   'ru', jsonb_build_array(
     'Рамштайн','НАТО','Таурус','Хаймарс','АТАКМС','Шторм Шэдоу','Пэтриот',
     'Леопард','Абрамс','Брэдли','Стингер','Джавелин','IRIS-T','NASAMS',
     'военная помощь','экономическая помощь','поставка оружия','учебная миссия',
     'оборонное производство','совместное предприятие','боеприпасы','снаряды',
     'артиллерийские снаряды','замороженные активы','чешская инициатива',
     'фонд мира','REPO','ленд-лиз','Рейнметалл'),
   'hi', jsonb_build_array(
     'सैन्य सहायता','आर्थिक सहायता','हथियार आपूर्ति','नाटो',
     'पैट्रियट','हाईमार्स','तौरस','गोला बारूद','जमे हुए संपत्ति'),
   'zh', jsonb_build_array(
     '军事援助','经济援助','武器交付','安全援助','援助计划','训练任务',
     '国防生产','合资企业','弹药','炮弹','冻结资产','乌克兰基金',
     '莱茵金属','洛克希德','北约','拉姆施泰因'),
   'ar', jsonb_build_array(
     'مساعدات عسكرية','مساعدات اقتصادية','توريد اسلحة','تدريب','مساعدات امنية',
     'حزمة مساعدات','تصنيع دفاعي','ذخيرة','قذائف','اصول مجمدة','صندوق اوكرانيا',
     'مبادرة تشيكية','رامشتاين','الناتو','باتريوت','هايمارس','تاوروس','ابرامز'),
   'ja', jsonb_build_array(
     'ラムシュタイン','軍事援助','経済援助','武器供与','安全保障支援',
     '援助パッケージ','訓練ミッション','防衛生産','合弁事業','弾薬','砲弾',
     '凍結資産','ウクライナ・ファシリティー','チェコ・イニシアチブ',
     'NATO','タウルス','ハイマース','パトリオット','レオパルト','ラインメタル')
 ),
 true, 'fn_anchor', 'western_aid_to_ukraine'),

-- ukraine_peace_negotiations: process, frameworks, settlement architecture
('ukraine_peace_negotiations fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'NATO membership','NATO accession','EU accession','security guarantees',
     'Minsk','Minsk II','Istanbul Communique','Budapest Memorandum','Black Sea grain',
     'Riyadh','Doha','Vienna',
     'ceasefire','armistice','truce','peace talks','peace deal','peace plan',
     'negotiation','settlement','framework','mediation','freeze','frozen conflict',
     'territorial concession','territorial integrity','sovereignty',
     'demilitarisation','demilitarization','denazification','neutrality','autonomy',
     'land swap','line of contact','de-occupation','de occupation',
     'reparations','accountability','prisoner exchange','POW exchange',
     'Trump plan','Trump framework','Witkoff','Kellogg'),
   'de', jsonb_build_array(
     'Waffenstillstand','Waffenruhe','Friedensgespraeche','Friedensplan',
     'Verhandlungen','Vermittlung','Einfrieren','eingefrorener Konflikt',
     'territoriale Zugestaendnisse','Souveraenitaet','Neutralitaet',
     'Sicherheitsgarantien','NATO-Mitgliedschaft','EU-Beitritt','Minsk',
     'Reparationen','Gefangenenaustausch','Trump-Plan'),
   'es', jsonb_build_array(
     'alto el fuego','tregua','conversaciones de paz','plan de paz','negociacion',
     'mediacion','congelacion','concesion territorial','soberania','neutralidad',
     'garantias de seguridad','adhesion a la OTAN','adhesion a la UE','Minsk',
     'reparaciones','intercambio de prisioneros','plan Trump'),
   'fr', jsonb_build_array(
     'cessez-le-feu','treve','pourparlers de paix','plan de paix','negociation',
     'mediation','gel','conflit gele','concession territoriale','souverainete',
     'neutralite','garanties de securite','adhesion a l''OTAN','adhesion a l''UE',
     'Minsk','reparations','echange de prisonniers','plan Trump','Witkoff'),
   'it', jsonb_build_array(
     'cessate il fuoco','tregua','colloqui di pace','piano di pace','negoziato',
     'mediazione','congelamento','conflitto congelato','concessione territoriale',
     'sovranita','neutralita','garanzie di sicurezza','adesione alla NATO',
     'adesione alla UE','Minsk','riparazioni','scambio di prigionieri','piano Trump'),
   'ru', jsonb_build_array(
     'перемирие','прекращение огня','мирные переговоры','мирный план','план мира',
     'переговоры','посредничество','заморозка','замороженный конфликт',
     'территориальные уступки','суверенитет','нейтралитет','автономия',
     'гарантии безопасности','членство в НАТО','вступление в НАТО','вступление в ЕС',
     'Минск','Стамбул','репарации','обмен пленными','план Трампа',
     'демилитаризация','денацификация','линия соприкосновения'),
   'hi', jsonb_build_array(
     'युद्धविराम','शांति वार्ता','शांति योजना','बातचीत','मध्यस्थता',
     'क्षेत्रीय रियायत','तटस्थता','सुरक्षा गारंटी','नाटो सदस्यता','मिन्स्क',
     'युद्धबंदी विनिमय','ट्रंप योजना'),
   'zh', jsonb_build_array(
     '停火','和谈','和平谈判','和平计划','谈判','调解','冻结','冻结冲突',
     '领土让步','主权','中立','安全保障','北约成员资格','加入北约','加入欧盟',
     '明斯克','伊斯坦布尔','赔偿','战俘交换','特朗普计划','去军事化','去纳粹化'),
   'ar', jsonb_build_array(
     'وقف اطلاق النار','هدنة','محادثات سلام','خطة سلام','مفاوضات','وساطة',
     'تجميد','تنازلات اقليمية','سيادة','حياد','ضمانات امنية',
     'عضوية الناتو','الانضمام للناتو','الانضمام للاتحاد الاوروبي','مينسك',
     'اسطنبول','تعويضات','تبادل اسرى','خطة ترامب','نزع السلاح'),
   'ja', jsonb_build_array(
     '停戦','休戦','和平交渉','和平案','和平計画','交渉','仲介',
     '凍結','凍結された紛争','領土譲歩','主権','中立','安全保証',
     'NATO加盟','EU加盟','ミンスク','イスタンブール','賠償','捕虜交換',
     'トランプ案','非軍事化','非ナチ化')
 ),
 true, 'fn_anchor', 'ukraine_peace_negotiations'),

-- ukraine_official_corruption: investigations of Ukrainian officials
('ukraine_official_corruption fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'NABU','SAP','SAPO','HACC','VAKS','NACP','ARMA','PGO','SBI','DBR',
     'corruption','bribery','bribe','embezzlement','kickback','fraud',
     'investigation','indictment','arrest','raid','prosecution','charge',
     'audit','transparency','conflict of interest','reform',
     'defence procurement','defense procurement','procurement scandal',
     'food procurement','body armor','drones procurement','generators',
     'state secrets','asset declaration','illicit enrichment',
     'oligarch','asset recovery','asset seizure','asset forfeiture',
     'EU conditionality','IMF conditionality','reform progress',
     'Yermak','Chernyshov','Reznikov','Umerov',
     'Pechersk court','High Anti-Corruption Court',
     'Anti-Corruption Action Centre','AntAC'),
   'de', jsonb_build_array(
     'Korruption','Bestechung','Schmiergeld','Unterschlagung','Veruntreuung',
     'Betrug','Ermittlung','Anklage','Festnahme','Razzia','Strafverfolgung',
     'Pruefung','Transparenz','Interessenkonflikt','Reform','Oligarch',
     'Ruestungsbeschaffung','Beschaffungsskandal','EU-Konditionalitaet','IWF-Konditionalitaet',
     'Vermoegenserklaerung','Vermoegensrueckfuehrung','Antikorruptionsgericht',
     'Antikorruptionsbuero'),
   'es', jsonb_build_array(
     'corrupcion','soborno','malversacion','desfalco','fraude','investigacion',
     'acusacion','arresto','redada','enjuiciamiento','auditoria','transparencia',
     'conflicto de intereses','reforma','oligarca','adquisicion de defensa',
     'escandalo de adquisicion','condicionalidad de la UE','condicionalidad del FMI',
     'tribunal anticorrupcion','oficina anticorrupcion'),
   'fr', jsonb_build_array(
     'corruption','pot-de-vin','detournement','fraude','enquete','inculpation',
     'arrestation','perquisition','poursuites','audit','transparence',
     'conflit d''interets','reforme','oligarque','marche public de defense',
     'scandale de marche','conditionnalite de l''UE','conditionnalite du FMI',
     'tribunal anticorruption','bureau anticorruption'),
   'it', jsonb_build_array(
     'corruzione','tangente','appropriazione indebita','frode','indagine',
     'accusa','arresto','perquisizione','procedimento','revisione','trasparenza',
     'conflitto di interessi','riforma','oligarca','appalto della difesa',
     'scandalo appalti','condizionalita UE','condizionalita FMI',
     'tribunale anticorruzione','ufficio anticorruzione'),
   'ru', jsonb_build_array(
     'НАБУ','САП','ВАКС','НАЗК','АРМА',
     'коррупция','взятка','хищение','растрата','мошенничество',
     'расследование','обвинение','арест','обыск','прокуратура',
     'аудит','прозрачность','конфликт интересов','реформа','олигарх',
     'оборонзаказ','госзакупки','закупочный скандал',
     'условия ЕС','условия МВФ','декларация о доходах','незаконное обогащение',
     'возврат активов','Ермак','Резников','Умеров',
     'антикоррупционный суд','антикоррупционное бюро'),
   'hi', jsonb_build_array(
     'भ्रष्टाचार','रिश्वत','गबन','धोखाधड़ी','जांच','गिरफ्तारी','छापा',
     'अभियोजन','पारदर्शिता','सुधार','कुलीन','रक्षा खरीद','खरीद घोटाला',
     'भ्रष्टाचार विरोधी न्यायालय','भ्रष्टाचार विरोधी ब्यूरो'),
   'zh', jsonb_build_array(
     '腐败','贪污','受贿','贪腐','挪用公款','欺诈','调查','起诉','逮捕',
     '搜查','检方','审计','透明度','利益冲突','改革','寡头','国防采购',
     '采购丑闻','欧盟条件','国际货币基金组织条件','反腐败法院','反腐败局',
     'NABU','SAP','叶尔马克'),
   'ar', jsonb_build_array(
     'فساد','رشوة','اختلاس','احتيال','تحقيق','اتهام','اعتقال','مداهمة',
     'محاكمة','تدقيق','شفافية','تضارب مصالح','اصلاح','الاوليغارش',
     'مشتريات دفاعية','فضيحة مشتريات','شروط الاتحاد الاوروبي','شروط صندوق النقد',
     'محكمة مكافحة الفساد','مكتب مكافحة الفساد','يرماك'),
   'ja', jsonb_build_array(
     '汚職','贈賄','横領','詐欺','捜査','起訴','逮捕','家宅捜索',
     '訴追','監査','透明性','利益相反','改革','オリガルヒ','防衛調達',
     '調達スキャンダル','EU条件','IMF条件','反汚職裁判所','反汚職局',
     'エルマク','NABU')
 ),
 true, 'fn_anchor', 'ukraine_official_corruption'),

-- russia_sanctions_regime: oil cap, frozen assets, secondary sanctions
('russia_sanctions_regime fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'OFAC','SDN','SDN list','FATF','Euroclear','Clearstream','SWIFT',
     'sanctions package','EU sanctions','sanctions regime','sectoral sanctions',
     'oil price cap','price cap','G7 cap',
     'frozen assets','immobilised assets','immobilized assets','seized assets',
     'asset freeze','asset seizure','REPO Act','REPO','windfall profits','ERA loan',
     'shadow fleet','dark fleet','ghost fleet','tanker','Sovcomflot',
     'secondary sanctions','designation','blacklist','sanctions evasion',
     'sanctions circumvention','export controls','dual-use','dual use',
     'Yamal LNG','Arctic LNG 2','Druzhba','Druzhba pipeline','Nord Stream',
     'Rosneft','Lukoil','Gazprom','Novatek','Surgutneftegaz','Tatneft',
     'Sberbank','VTB','Alfa-Bank','Gazprombank','Otkritie',
     'sanctions relief','lifting sanctions','sanctions package',
     'mirror banking','parallel imports','third country','transshipment'),
   'de', jsonb_build_array(
     'Sanktionen','Sanktionspaket','EU-Sanktionen','Sanktionsregime','Embargo',
     'Oelpreisdeckel','Preisdeckel','eingefrorenes Vermoegen','Vermoegenseinfrierung',
     'Vermoegensbeschlagnahme','Schattenflotte','Dunkelflotte','Sekundaersanktionen',
     'Listung','schwarze Liste','Sanktionsumgehung','Sanktionserleichterung',
     'Sanktionsaufhebung','Exportkontrollen','Doppelverwendung','Gazprom','Rosneft',
     'Sberbank','Druzhba','Nord Stream','Parallelimporte'),
   'es', jsonb_build_array(
     'sanciones','paquete de sanciones','sanciones de la UE','regimen de sanciones',
     'embargo','tope al precio del petroleo','precio maximo','activos congelados',
     'incautacion de activos','flota fantasma','sanciones secundarias','designacion',
     'lista negra','evasion de sanciones','levantamiento de sanciones',
     'controles de exportacion','doble uso','Gazprom','Rosneft','Druzhba','Nord Stream'),
   'fr', jsonb_build_array(
     'sanctions','paquet de sanctions','sanctions de l''UE','regime de sanctions',
     'embargo','plafonnement du prix du petrole','prix plafond','avoirs geles',
     'saisie d''avoirs','flotte fantome','sanctions secondaires','designation',
     'liste noire','contournement des sanctions','levee des sanctions',
     'controles a l''exportation','double usage','Gazprom','Rosneft','Droujba','Nord Stream'),
   'it', jsonb_build_array(
     'sanzioni','pacchetto di sanzioni','sanzioni UE','regime sanzionatorio','embargo',
     'tetto al prezzo del petrolio','prezzo massimo','beni congelati','sequestro di beni',
     'flotta ombra','sanzioni secondarie','designazione','lista nera',
     'elusione delle sanzioni','revoca delle sanzioni','controlli all''esportazione',
     'duplice uso','Gazprom','Rosneft','Druzhba','Nord Stream'),
   'ru', jsonb_build_array(
     'санкции','санкционный пакет','санкции ЕС','санкционный режим','эмбарго',
     'потолок цен','потолок цен на нефть','ценовой потолок','G7',
     'замороженные активы','заморозка активов','конфискация активов',
     'теневой флот','танкер','Совкомфлот','вторичные санкции','SDN',
     'обход санкций','снятие санкций','отмена санкций','экспортный контроль',
     'двойного назначения','Ямал СПГ','Арктик СПГ-2','Дружба','Северный поток',
     'Роснефть','Лукойл','Газпром','Новатэк','Сбербанк','ВТБ','Альфа-Банк',
     'параллельный импорт','реэкспорт','зеркальные банки'),
   'hi', jsonb_build_array(
     'प्रतिबंध','प्रतिबंध पैकेज','तेल मूल्य सीमा','जमे हुए संपत्ति',
     'संपत्ति जब्ती','छाया बेड़ा','द्वितीयक प्रतिबंध','प्रतिबंध हटाना',
     'निर्यात नियंत्रण','गज़प्रोम','रोसनेफ्ट','नॉर्ड स्ट्रीम'),
   'zh', jsonb_build_array(
     '制裁','制裁方案','欧盟制裁','制裁制度','禁运','石油价格上限','价格上限',
     '冻结资产','资产没收','影子船队','暗船队','二级制裁','黑名单','制裁规避',
     '解除制裁','出口管制','两用','俄罗斯天然气工业','俄罗斯石油','北溪',
     '友谊管道','亚马尔','北极LNG-2'),
   'ar', jsonb_build_array(
     'عقوبات','حزمة عقوبات','عقوبات الاتحاد الاوروبي','نظام العقوبات','حظر',
     'سقف سعر النفط','سعر اقصى','اصول مجمدة','مصادرة اصول','اسطول الظل',
     'عقوبات ثانوية','ادراج','قائمة سوداء','التحايل على العقوبات',
     'رفع العقوبات','ضوابط التصدير','الاستخدام المزدوج','جازبروم','روسنفط',
     'نورد ستريم','يامال','القطب الشمالي','سبيربنك'),
   'ja', jsonb_build_array(
     '制裁','制裁パッケージ','EU制裁','制裁レジーム','禁輸','石油価格上限',
     '価格上限','凍結資産','資産差し押さえ','影の船団','二次制裁','指定',
     'ブラックリスト','制裁回避','制裁解除','輸出管理','デュアルユース',
     'ガスプロム','ロスネフチ','ノルドストリーム','ヤマルLNG','北極LNG2',
     'スベルバンク','VTB','ドルジバ')
 ),
 true, 'fn_anchor', 'russia_sanctions_regime');

-- ============================================================
-- 3. Narratives (13: 3 theater + 2 per atomic)
-- ============================================================

-- Theater catch-all narratives (3)
INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('ukraine_resistance_solidarity', 'ukraine_war_theater', 1, 2,
 'Solidarity with Ukrainian resistance', 'Solidaritaet mit ukrainischem Widerstand',
 'Ukraine''s war of national defense deserves full Western and democratic-world solidarity',
 'Der ukrainische Verteidigungskrieg verdient volle westliche und demokratische Solidaritaet',
 'Ukrainian, Western mainstream, and Eastern European press frame the war as Ukraine''s war of national survival against unprovoked Russian aggression. Vocabulary centers on resistance, liberation, sovereign defense, solidarity, and the moral and strategic necessity of supporting Ukraine until Russian forces withdraw. Coverage emphasises Ukrainian agency and courage, Russian war crimes, the humanitarian cost of occupation, and the global stakes (precedent for territorial aggression, NATO credibility, rules-based order). Prescription: sustain and expand military, economic, and diplomatic support; hold Russia accountable; integrate Ukraine into Euro-Atlantic structures.',
 'Ukrainische, westliche Mainstream- und osteuropaeische Medien rahmen den Krieg als ukrainischen Ueberlebenskrieg gegen unprovozierte russische Aggression. Das Vokabular kreist um Widerstand, Befreiung, souveraene Verteidigung, Solidaritaet und die moralische sowie strategische Notwendigkeit, die Ukraine zu unterstuetzen, bis russische Truppen abziehen. Berichterstattung betont ukrainische Handlungsfaehigkeit und Mut, russische Kriegsverbrechen, humanitaere Kosten der Besatzung und globale Einsaetze (Praezedenz fuer territoriale Aggression, NATO-Glaubwuerdigkeit, regelbasierte Ordnung). Vorschrift: militaerische, wirtschaftliche und diplomatische Unterstuetzung aufrechterhalten und ausbauen; Russland zur Rechenschaft ziehen; Ukraine in euro-atlantische Strukturen integrieren.',
 ARRAY['EUROPE-UKRAINE','EUROPE-UK','EUROPE-FRANCE','EUROPE-GERMANY','EUROPE-BALTIC','EUROPE-VISEGRAD','AMERICAS-USA'],
 ARRAY['Kyiv Post','Reuters','Bloomberg','Financial Times','BBC World','The Guardian','The Telegraph','Le Monde','Le Figaro','Frankfurter Allgemeine','Süddeutsche Zeitung','Der Spiegel','Die Zeit','Tagesschau','Handelsblatt','Deutsche Welle','La Repubblica','Corriere della Sera','ANSA','El País','Die Presse','Der Standard','ERR News','LRT English','LSM English','Atlantic Council','Associated Press','The Economist','EurActiv','Novinite','Sky News','CNN','NPR','New York Times','Washington Post','Wall Street Journal','Politico','Defense News','iROZHLAS','eKathimerini'],
 ARRAY['Russian aggression','unprovoked invasion','Ukrainian resistance','sovereign defense','rules-based order','war crimes','support Ukraine','solidarity','liberation','territorial integrity','accountability','democratic Ukraine'],
 true),

('russia_special_military_operation', 'ukraine_war_theater', 2, -2,
 'Special military operation framing', 'Spezialoperation-Rahmung',
 'Russia''s special military operation defends Russian-speaking populations from Western-backed Kyiv regime',
 'Russlands militaerische Spezialoperation verteidigt russischsprachige Bevoelkerungen gegen das vom Westen gestuetzte Kiewer Regime',
 'Russian state press and aligned outlets frame the war as a defensive special military operation (SMO) protecting Russian-speaking populations in Donbas and Crimea from a Western-installed regime in Kyiv that pursued ethnic discrimination and NATO encroachment since 2014. Vocabulary centers on denazification, demilitarisation, NATO expansion, Western interference, Russian world (Russky Mir), and historical Russian-Ukrainian unity. Coverage emphasises Russian military precision and humanitarian conduct, Ukrainian military targeting of civilians, the illegitimacy of the post-Maidan Kyiv government, and the West''s role as the actual aggressor through proxy warfare. Prescription: complete the SMO''s territorial and political objectives; reject Western-imposed settlement frameworks; defend multipolar world order.',
 'Russische Staatsmedien und ausgerichtete Outlets rahmen den Krieg als defensive militaerische Spezialoperation (SMO) zum Schutz russischsprachiger Bevoelkerungen im Donbass und auf der Krim vor einem vom Westen eingesetzten Regime in Kiew, das seit 2014 ethnische Diskriminierung und NATO-Vormarsch betrieben habe. Das Vokabular kreist um Entnazifizierung, Entmilitarisierung, NATO-Erweiterung, westliche Einmischung, russische Welt (Russki Mir) und historische russisch-ukrainische Einheit. Berichterstattung betont russische militaerische Praezision und humanitaeres Verhalten, ukrainische militaerische Angriffe auf Zivilisten, Illegitimitaet der nach-Maidan-Regierung in Kiew und die Rolle des Westens als eigentlicher Aggressor durch Stellvertreterkrieg. Vorschrift: territoriale und politische Ziele der SMO vollenden; westlich auferlegte Beilegungsrahmen ablehnen; multipolare Weltordnung verteidigen.',
 ARRAY['EUROPE-RUSSIA','EUROPE-BELARUS'],
 ARRAY['TASS','TASS (EN)','tass.com','RT','Lenta.ru','lenta.ru','Gazeta.ru','gazeta.ru','Kommersant','Izvestia','RIA Novosti','BelTA','BelTA Russian','Press TV'],
 ARRAY['special military operation','SMO','denazification','demilitarisation','NATO expansion','Western interference','Russian world','Kyiv regime','Ukrainian Nazis','liberation of Donbas','Western proxy','multipolar order','defense of Russian-speakers'],
 true),

('proxy_war_restraint_critique', 'ukraine_war_theater', 3, -1,
 'US/NATO proxy war critique', 'Kritik am US-/NATO-Stellvertreterkrieg',
 'The war is a US/NATO proxy war prolonged by Western intervention; settlement requires restraint',
 'Der Krieg ist ein US-/NATO-Stellvertreterkrieg, verlaengert durch westliche Intervention; Beilegung erfordert Zurueckhaltung',
 'Western contrarian, Global South, and some Chinese state media frame the war as a US/NATO proxy conflict that the West has prolonged through escalating weapons deliveries and refusal of early negotiation opportunities (notably the spring 2022 Istanbul talks). Vocabulary centers on proxy war, NATO expansion as root cause, blocked diplomacy, Western hubris, and Global Majority interests. Coverage emphasises the human and economic costs to Europe, the strain on Western unity, the unsustainability of the Ukrainian position over time, the legitimacy of Russian security concerns, and the absence of Global South support for the Western position. Prescription: immediate negotiated settlement, territorial realism, end weapons deliveries, recognise multipolar reality.',
 'Westliche Dissidenten-, Global-South- und einige chinesische Staatsmedien rahmen den Krieg als US-/NATO-Stellvertreterkonflikt, den der Westen durch eskalierende Waffenlieferungen und Ablehnung frueher Verhandlungschancen (insbesondere Istanbul-Gespraeche im Fruehjahr 2022) verlaengert habe. Das Vokabular kreist um Stellvertreterkrieg, NATO-Erweiterung als Grundursache, blockierte Diplomatie, westliche Hybris und Interessen der globalen Mehrheit. Berichterstattung betont menschliche und wirtschaftliche Kosten fuer Europa, Belastung westlicher Einheit, Unhaltbarkeit der ukrainischen Position auf Dauer, Legitimitaet russischer Sicherheitsbedenken und Abwesenheit von Global-South-Unterstuetzung fuer die westliche Position. Vorschrift: sofortige verhandelte Beilegung, territoriale Realitaet, Ende der Waffenlieferungen, multipolare Realitaet anerkennen.',
 ARRAY['NON-STATE-EU','ASIA-CHINA','ASIA-INDIA'],
 ARRAY['Fox News','Global Times','CGTN','China Daily','Hindustan Times','Times of India','NDTV','The Hindu','WION','Dawn','Express Tribune','Al Jazeera','TRT World','Daily Sabah','Anadolu Agency','O Globo','Bangkok Post','News24','BRICS Info'],
 ARRAY['proxy war','NATO expansion','blocked diplomacy','negotiated settlement','territorial realism','Western escalation','Istanbul talks','Global South','multipolar order','Western hubris','strain on Europe'],
 true);

-- ukraine_battlefield narratives (2)
INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('ukrainian_defense_and_deep_strikes', 'ukraine_battlefield', 1, 2,
 'Legitimate defense including deep strikes', 'Legitime Verteidigung einschliesslich Tiefenschlaegen',
 'Ukrainian Armed Forces conduct legitimate defense; strikes on Russian military infrastructure are valid',
 'Die ukrainischen Streitkraefte fuehren legitime Verteidigung; Schlaege gegen russische Militaerinfrastruktur sind legitim',
 'Ukrainian and Western mainstream press frame Ukrainian Armed Forces (AFU/ZSU) battlefield operations as legitimate defense against an invader, including deep strikes into Russian territory targeting military infrastructure (oil refineries supplying frontline operations, Black Sea Fleet vessels, air bases, ammunition depots, command nodes). Vocabulary: heroic defense, counteroffensive, liberation of occupied territory, targeted strike, military objective, proportionate response. Coverage emphasises Ukrainian effectiveness despite materiel disadvantage, Russian military failures, the legitimacy of striking the infrastructure sustaining the invasion, and humanitarian consequences of Russian shelling and missile strikes on Ukrainian cities. Prescription: enable longer-range strikes, lift restrictions on Western weapons use inside Russia, sustain ammunition supply.',
 'Ukrainische und westliche Mainstream-Medien rahmen Gefechtsoperationen der ukrainischen Streitkraefte (ZSU) als legitime Verteidigung gegen einen Angreifer, einschliesslich Tiefenschlaegen auf russisches Territorium gegen Militaerinfrastruktur (Oelraffinerien zur Versorgung der Front, Schiffe der Schwarzmeerflotte, Luftwaffenstuetzpunkte, Munitionsdepots, Kommandozentralen). Vokabular: heroische Verteidigung, Gegenoffensive, Befreiung besetzten Gebiets, gezielter Schlag, militaerisches Ziel, verhaeltnismaessige Antwort. Berichterstattung betont ukrainische Wirksamkeit trotz Material-Unterlegenheit, russische Militaerversagen, Legitimitaet von Schlaegen auf die invasionserhaltende Infrastruktur und humanitaere Folgen russischer Beschiessung und Raketenangriffe auf ukrainische Staedte. Vorschrift: weitreichendere Schlaege ermoeglichen, Beschraenkungen westlichen Waffeneinsatzes in Russland aufheben, Munitionsversorgung aufrechterhalten.',
 ARRAY['EUROPE-UKRAINE','EUROPE-UK','EUROPE-FRANCE','EUROPE-GERMANY','EUROPE-BALTIC','EUROPE-VISEGRAD','AMERICAS-USA'],
 ARRAY['Kyiv Post','Reuters','Bloomberg','Financial Times','BBC World','The Guardian','The Telegraph','Le Monde','Le Figaro','Frankfurter Allgemeine','Süddeutsche Zeitung','Der Spiegel','Tagesschau','Deutsche Welle','La Repubblica','Corriere della Sera','ANSA','El País','ERR News','LRT English','LSM English','Atlantic Council','Associated Press','Defense News','Janes','Sky News','CNN','New York Times','Washington Post','Wall Street Journal','Politico'],
 ARRAY['heroic defense','counteroffensive','liberation','targeted strike','military objective','proportionate response','Ukrainian effectiveness','Russian failure','occupied territory','deep strike','legitimate target','war of aggression'],
 true),

('russian_smo_operations', 'ukraine_battlefield', 2, -2,
 'Russian precision operations and Ukrainian terror', 'Russische Praezisionsoperationen und ukrainischer Terror',
 'Russian forces conduct precision operations; Ukrainian strikes on Russia are terrorism against civilians',
 'Russische Streitkraefte fuehren Praezisionsoperationen; ukrainische Angriffe auf Russland sind Terror gegen Zivilisten',
 'Russian state press frames Russian military operations as precision strikes on legitimate military targets (decision-making centres, training bases, military-industrial sites, mercenary positions) conducted with care to minimise civilian harm. The same press frames Ukrainian strikes into Russia (Belgorod, Kursk, Bryansk, Moscow oil refineries, Crimean Bridge) as terrorist attacks targeting civilians, supplied and authorised by Western patrons. Vocabulary: precision strike, decision-making centre, military objective, Kyiv regime terror, civilian victim, Western-supplied weapon, escalation by NATO. Coverage emphasises Russian military discipline, Ukrainian military failures and Western dependence, the deliberate targeting of Russian civilians, and the West''s role in supplying the weapons used in such attacks. Prescription: respond to Ukrainian terror with proportionate strikes on Ukrainian decision-making centres; hold Western suppliers accountable.',
 'Russische Staatsmedien rahmen russische Militaeroperationen als Praezisionsschlaege gegen legitime militaerische Ziele (Entscheidungszentren, Ausbildungsbasen, militaerisch-industrielle Anlagen, Soeldnerstellungen), gefuehrt mit Sorgfalt zur Minimierung ziviler Schaeden. Dieselben Medien rahmen ukrainische Schlaege nach Russland (Belgorod, Kursk, Brjansk, Moskauer Oelraffinerien, Krim-Bruecke) als Terroranschlaege gegen Zivilisten, geliefert und autorisiert von westlichen Patronen. Vokabular: Praezisionsschlag, Entscheidungszentrum, militaerisches Ziel, Kiewer Terror, ziviles Opfer, westlich geliefertes Waffensystem, NATO-Eskalation. Berichterstattung betont russische militaerische Disziplin, ukrainische militaerische Versagen und westliche Abhaengigkeit, vorsaetzliche Zielsetzung auf russische Zivilisten und die Rolle des Westens als Lieferant der Waffen. Vorschrift: ukrainischen Terror mit verhaeltnismaessigen Schlaegen auf ukrainische Entscheidungszentren beantworten; westliche Lieferanten zur Verantwortung ziehen.',
 ARRAY['EUROPE-RUSSIA','EUROPE-BELARUS'],
 ARRAY['TASS','TASS (EN)','tass.com','RT','Lenta.ru','lenta.ru','Gazeta.ru','gazeta.ru','Kommersant','Izvestia','RIA Novosti','BelTA','BelTA Russian','Press TV'],
 ARRAY['precision strike','decision-making centre','military objective','Kyiv regime terror','civilian victim','Western-supplied','NATO escalation','foreign mercenary','provocation','retaliation strike','HIMARS attack','ATACMS strike'],
 true);

-- western_aid_to_ukraine narratives (2)
INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('aid_sustains_defense', 'western_aid_to_ukraine', 1, 2,
 'Aid sustains Ukrainian defense', 'Hilfe sichert ukrainische Verteidigung',
 'Western military, economic, and industrial aid is sustaining and must be scaled',
 'Westliche militaerische, wirtschaftliche und industrielle Hilfe traegt und muss skaliert werden',
 'Pro-aid framing (Ukrainian press + Western mainstream + Eastern European hawks) treats Western military, economic, and financial assistance as both moral imperative and strategic necessity. Coverage tracks weapons deliveries (HIMARS, ATACMS, Storm Shadow, Taurus debates, F-16 deployment, Patriot replenishment), financial mechanisms (ERA loan from windfall profits on frozen Russian assets, Ukraine Facility, REPO Act seizure provisions, European Peace Facility), and the growing defense-industrial partnership (Rheinmetall-Ukraine joint ventures, Czech ammunition initiative, BAE local production). Vocabulary: aid package, security assistance, defense industrial base, joint production, ammunition supply, frozen-asset windfall, sustained commitment. Prescription: scale all three channels; remove restrictions on Western weapons use; seize frozen sovereign assets for Ukrainian reconstruction; build long-term defense-industrial capacity in Ukraine.',
 'Pro-Hilfe-Rahmung (ukrainische Medien + westlicher Mainstream + osteuropaeische Falken) behandelt westliche militaerische, wirtschaftliche und finanzielle Unterstuetzung als moralische Pflicht und strategische Notwendigkeit. Berichterstattung verfolgt Waffenlieferungen (HIMARS, ATACMS, Storm Shadow, Taurus-Debatten, F-16-Stationierung, Patriot-Nachschub), Finanzmechanismen (ERA-Darlehen aus Sondervermoegens-Gewinnen eingefrorenen russischen Vermoegens, Ukraine-Fazilitaet, REPO-Act-Beschlagnahmebestimmungen, Europaeische Friedensfazilitaet) und die wachsende verteidigungsindustrielle Partnerschaft (Rheinmetall-Ukraine-Joint-Ventures, tschechische Munitions-Initiative, BAE-Lokalproduktion). Vokabular: Hilfspaket, Sicherheitsunterstuetzung, Verteidigungsindustrie-Basis, gemeinsame Produktion, Munitionsversorgung, Sondervermoegens-Windfall, anhaltendes Engagement. Vorschrift: alle drei Kanaele skalieren; Beschraenkungen westlichen Waffeneinsatzes aufheben; eingefrorenes Staatsvermoegen fuer ukrainischen Wiederaufbau beschlagnahmen; langfristige Verteidigungsindustrie-Kapazitaet in der Ukraine aufbauen.',
 ARRAY['EUROPE-UKRAINE','EUROPE-UK','EUROPE-FRANCE','EUROPE-GERMANY','EUROPE-BALTIC','EUROPE-VISEGRAD','AMERICAS-USA'],
 ARRAY['Kyiv Post','Reuters','Bloomberg','Financial Times','BBC World','The Guardian','The Telegraph','Le Monde','Frankfurter Allgemeine','Süddeutsche Zeitung','Der Spiegel','Die Zeit','Tagesschau','Handelsblatt','Deutsche Welle','La Repubblica','ANSA','El País','ERR News','LRT English','LSM English','Atlantic Council','Associated Press','The Economist','EurActiv','Defense News','Janes','CNN','New York Times','Washington Post','Wall Street Journal','Politico','iROZHLAS'],
 ARRAY['military aid','aid package','security assistance','weapons delivery','training mission','defence production','joint production','ammunition supply','frozen-asset windfall','ERA loan','seize frozen assets','sustained commitment','long-term partnership'],
 true),

('aid_as_escalation_and_proxy', 'western_aid_to_ukraine', 2, -2,
 'Aid as escalation and proxy waste', 'Hilfe als Eskalation und Stellvertreter-Verschwendung',
 'Western aid prolongs proxy war, wastes taxpayer money, escalates direct NATO-Russia risk',
 'Westliche Hilfe verlaengert Stellvertreterkrieg, verschwendet Steuergeld, eskaliert direktes NATO-Russland-Risiko',
 'Restraint framing (Russian state press + Western contrarian + Global South + Hungarian-aligned EU) treats Western aid as proxy-war escalation that delays inevitable settlement, wastes taxpayer money increasingly diverted from domestic priorities, and risks direct NATO-Russia confrontation by supplying longer-range weapons and authorising their use inside Russia. Vocabulary: proxy war, escalation, taxpayer waste, weapons graveyard, diversion of aid, NATO involvement, red line. Coverage emphasises the corruption risk in aid pipelines, the ineffectiveness of escalating weapons categories in changing the battlefield, Ukrainian losses and recruitment shortages, growing European public fatigue, and the strain on US bipartisan support. Prescription: pause and reassess aid, condition it on negotiated outcomes, prevent direct NATO-Russia escalation, redirect funds to domestic priorities.',
 'Zurueckhaltungs-Rahmung (russische Staatsmedien + westliche Dissidenten + Global South + ungarisch-orientierte EU) behandelt westliche Hilfe als Stellvertreterkriegs-Eskalation, die unvermeidliche Beilegung verzoegert, Steuergeld zunehmend von inlaendischen Prioritaeten umlenkt und direkte NATO-Russland-Konfrontation durch Lieferung weitreichenderer Waffen und deren Autorisierung in Russland riskiert. Vokabular: Stellvertreterkrieg, Eskalation, Steuerverschwendung, Waffenfriedhof, Umlenkung von Hilfe, NATO-Beteiligung, rote Linie. Berichterstattung betont Korruptionsrisiko in Hilfspipelines, Wirkungslosigkeit eskalierender Waffenkategorien fuer den Schlachtfeld-Wandel, ukrainische Verluste und Rekrutierungsmaengel, wachsende europaeische Erschoepfung der Oeffentlichkeit und Belastung ueberparteilicher US-Unterstuetzung. Vorschrift: Hilfe pausieren und neu bewerten, sie an verhandelten Ergebnissen konditionieren, direkte NATO-Russland-Eskalation verhindern, Mittel auf inlaendische Prioritaeten umleiten.',
 ARRAY['EUROPE-RUSSIA','ASIA-CHINA','ASIA-INDIA','NON-STATE-EU'],
 ARRAY['TASS','TASS (EN)','tass.com','RT','Lenta.ru','lenta.ru','Gazeta.ru','gazeta.ru','Kommersant','Izvestia','RIA Novosti','BelTA','BelTA Russian','Press TV','Fox News','Global Times','CGTN','China Daily','Hindustan Times','Times of India','NDTV','TRT World','Daily Sabah'],
 ARRAY['proxy war','escalation','taxpayer waste','weapons graveyard','aid diversion','NATO involvement','red line','red lines','corruption risk','aid fatigue','bipartisan strain','Western recklessness'],
 true);

-- ukraine_peace_negotiations narratives (2)
INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('just_peace_no_concessions', 'ukraine_peace_negotiations', 1, 2,
 'Just peace requires Russian withdrawal', 'Gerechter Frieden erfordert russischen Rueckzug',
 'Just peace requires full Russian withdrawal; territorial concessions reward aggression',
 'Gerechter Frieden erfordert vollen russischen Rueckzug; territoriale Zugestaendnisse belohnen Aggression',
 'Ukrainian maximalist framing (Ukrainian press + Western hawks + Eastern European) treats any territorial concession as appeasement that would reward Russian aggression and embolden future invasions. The framework: just peace requires full Russian withdrawal to internationally recognised 1991 borders, NATO accession or equivalent binding security guarantees, accountability mechanisms for war crimes, and reparations funded through seized Russian sovereign assets. Vocabulary: just peace, territorial integrity, accountability, no appeasement, 1991 borders, NATO accession, security guarantees, reparations. Coverage rejects Trump administration freeze-and-negotiate proposals, frames the 2014 Crimea precedent as proof that frozen conflicts invite escalation, and emphasises Ukrainian society''s rejection of compromise terms. Prescription: continue military pressure until Russian retreat; refuse settlement frameworks that legitimise territorial losses; pre-condition negotiation on Russian withdrawal.',
 'Ukrainische Maximalrahmung (ukrainische Medien + westliche Falken + Osteuropa) behandelt jede territoriale Konzession als Beschwichtigung, die russische Aggression belohnen und kuenftige Invasionen ermutigen wuerde. Das Rahmenwerk: gerechter Frieden erfordert vollen russischen Rueckzug zu international anerkannten Grenzen von 1991, NATO-Beitritt oder gleichwertige verbindliche Sicherheitsgarantien, Rechenschaftsmechanismen fuer Kriegsverbrechen und Reparationen aus beschlagnahmtem russischen Staatsvermoegen. Vokabular: gerechter Frieden, territoriale Integritaet, Rechenschaft, keine Beschwichtigung, Grenzen von 1991, NATO-Beitritt, Sicherheitsgarantien, Reparationen. Berichterstattung lehnt Trump-Administrations-Einfrieren-und-Verhandeln-Vorschlaege ab, rahmt den Krim-Praezedenzfall 2014 als Beleg, dass eingefrorene Konflikte zu Eskalation einladen, und betont die Ablehnung von Kompromissbedingungen in der ukrainischen Gesellschaft. Vorschrift: militaerischen Druck bis zum russischen Rueckzug fortsetzen; Beilegungsrahmen ablehnen, die territoriale Verluste legitimieren; Verhandlungen an russischen Rueckzug vor-konditionieren.',
 ARRAY['EUROPE-UKRAINE','EUROPE-UK','EUROPE-BALTIC','EUROPE-VISEGRAD','EUROPE-FRANCE','EUROPE-GERMANY'],
 ARRAY['Kyiv Post','Reuters','Bloomberg','Financial Times','BBC World','The Guardian','The Telegraph','Le Monde','Le Figaro','Frankfurter Allgemeine','Süddeutsche Zeitung','Der Spiegel','Die Zeit','Tagesschau','Deutsche Welle','La Repubblica','Corriere della Sera','ANSA','El País','Die Presse','ERR News','LRT English','LSM English','Atlantic Council','Associated Press','The Economist','EurActiv','iROZHLAS','Novinite'],
 ARRAY['just peace','territorial integrity','accountability','no appeasement','1991 borders','NATO accession','security guarantees','reparations','rule of law','frozen conflict trap','reward aggression'],
 true),

('pragmatic_freeze_settlement', 'ukraine_peace_negotiations', 2, -1,
 'Pragmatic territorial settlement', 'Pragmatische territoriale Beilegung',
 'Pragmatic settlement requires territorial compromise; freeze the front and negotiate',
 'Pragmatische Beilegung erfordert territorialen Kompromiss; Front einfrieren und verhandeln',
 'Pragmatic-settlement framing (Trump administration adjacent press + Russian state + Hungarian-aligned EU + Global South) treats the war as unwinnable for either side at acceptable cost and argues for negotiated freeze along current lines with security architecture concessions. The framework: acknowledge territorial reality, freeze the line of contact, formalise Ukrainian neutrality (no NATO accession), build a multilateral security guarantee structure outside NATO, lift sanctions in phases tied to compliance, allow refugee return. Vocabulary: realistic settlement, freeze, line of contact, territorial reality, neutrality, multipolar security, end the killing, sustainable peace. Coverage emphasises the human cost of continued fighting, Ukrainian recruitment shortages, European political fatigue, Trump administration leverage on both sides, and historical precedents (Korean armistice). Prescription: immediate freeze; convene Istanbul-style talks; Ukrainian constitutional neutrality; phased sanctions relief tied to verified compliance.',
 'Pragmatische Beilegungs-Rahmung (Trump-Administration nahestehende Medien + russische Staatsmedien + ungarisch-orientierte EU + Global South) behandelt den Krieg als fuer beide Seiten zu akzeptablen Kosten nicht gewinnbar und argumentiert fuer verhandeltes Einfrieren entlang aktueller Linien mit Sicherheitsarchitektur-Zugestaendnissen. Das Rahmenwerk: territoriale Realitaet anerkennen, Beruehrungslinie einfrieren, ukrainische Neutralitaet formalisieren (kein NATO-Beitritt), multilaterale Sicherheitsgarantie-Struktur ausserhalb der NATO aufbauen, Sanktionen in Phasen an Einhaltung knuepfen, Fluechtlingsrueckkehr ermoeglichen. Vokabular: realistische Beilegung, Einfrieren, Beruehrungslinie, territoriale Realitaet, Neutralitaet, multipolare Sicherheit, Toeten beenden, nachhaltiger Frieden. Berichterstattung betont menschliche Kosten fortgesetzter Kaempfe, ukrainische Rekrutierungsmaengel, europaeische politische Erschoepfung, Trump-Administrations-Hebel auf beide Seiten und historische Praezedenzfaelle (koreanischer Waffenstillstand). Vorschrift: sofortiges Einfrieren; Istanbul-Stil-Gespraeche einberufen; ukrainische verfassungsrechtliche Neutralitaet; phasenweise Sanktionserleichterung an verifizierte Einhaltung gebunden.',
 ARRAY['EUROPE-RUSSIA','ASIA-CHINA','ASIA-INDIA','NON-STATE-EU'],
 ARRAY['TASS','TASS (EN)','tass.com','RT','Lenta.ru','lenta.ru','Gazeta.ru','gazeta.ru','Kommersant','Izvestia','RIA Novosti','BelTA','BelTA Russian','Press TV','Fox News','Global Times','CGTN','China Daily','Hindustan Times','Times of India','NDTV','TRT World','Daily Sabah','O Globo','Bangkok Post'],
 ARRAY['realistic settlement','freeze','line of contact','territorial reality','neutrality','multipolar security','end the killing','sustainable peace','Korean armistice','phased sanctions relief','negotiated end'],
 true);

-- ukraine_official_corruption narratives (2)
INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('reform_in_progress', 'ukraine_official_corruption', 1, 1,
 'Reform progress under wartime stress', 'Reformfortschritt unter Kriegsbelastung',
 'Ukrainian anti-corruption institutions are investigating and prosecuting successfully',
 'Ukrainische Antikorruptions-Institutionen ermitteln und verfolgen erfolgreich',
 'Reform-progress framing (Ukrainian reformist press + Western mainstream + EU policy outlets) treats ongoing corruption investigations as evidence that Ukrainian anti-corruption infrastructure built since 2014 is functioning under wartime stress. Coverage tracks NABU, SAP, HACC, and NACP investigations of senior officials including Presidential Office personnel, defense procurement scandals, and regional governors. Vocabulary: anti-corruption infrastructure, institutional independence, reform progress, EU conditionality met, IMF benchmark, transparency, accountability, audit. Coverage frames Western audit demands as legitimate and constructive, presents prosecutions of senior officials as proof of independence from the Presidential Office, and contextualises scandals within the broader institutional transformation since 2014. Prescription: sustain institutional protection from political interference; maintain Western conditionality leverage; complete judicial reform; continue prosecuting irrespective of rank.',
 'Reform-Fortschritts-Rahmung (ukrainische Reformmedien + westlicher Mainstream + EU-Politik-Medien) behandelt laufende Korruptionsermittlungen als Beleg, dass die seit 2014 aufgebaute ukrainische Antikorruptions-Infrastruktur unter Kriegsbelastung funktioniert. Berichterstattung verfolgt NABU-, SAP-, HACC- und NACP-Ermittlungen gegen hochrangige Beamte einschliesslich Personal des Praesidialamts, Ruestungsbeschaffungs-Skandale und Regional-Gouverneure. Vokabular: Antikorruptions-Infrastruktur, institutionelle Unabhaengigkeit, Reformfortschritt, EU-Konditionalitaet erfuellt, IWF-Massstab, Transparenz, Rechenschaft, Audit. Berichterstattung rahmt westliche Audit-Forderungen als legitim und konstruktiv, praesentiert Strafverfolgung hochrangiger Beamter als Beleg fuer Unabhaengigkeit vom Praesidialamt und kontextualisiert Skandale in der breiteren institutionellen Transformation seit 2014. Vorschrift: institutionellen Schutz vor politischer Einmischung aufrechterhalten; westliche Konditionalitaets-Hebel aufrechterhalten; Justizreform vollenden; Strafverfolgung unabhaengig vom Rang fortsetzen.',
 ARRAY['EUROPE-UKRAINE','AMERICAS-USA','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','NON-STATE-EU'],
 ARRAY['Kyiv Post','Reuters','Bloomberg','Financial Times','BBC World','The Guardian','The Telegraph','Le Monde','Frankfurter Allgemeine','Süddeutsche Zeitung','Der Spiegel','Die Zeit','Deutsche Welle','La Repubblica','ANSA','El País','ERR News','LRT English','Atlantic Council','Associated Press','The Economist','EurActiv','New York Times','Washington Post','Wall Street Journal','Politico'],
 ARRAY['anti-corruption infrastructure','institutional independence','reform progress','EU conditionality','IMF benchmark','transparency','accountability','NABU investigation','prosecuted','indicted','asset declaration'],
 true),

('zelensky_regime_corruption', 'ukraine_official_corruption', 2, -2,
 'Zelensky regime endemic corruption', 'Endemische Korruption im Selenskyj-Regime',
 'Zelensky inner circle is systemically corrupt; Western aid is being stolen at scale',
 'Der Selenskyj-Kreis ist systemisch korrupt; westliche Hilfe wird in grossem Stil gestohlen',
 'Endemic-corruption framing (Russian state press + Western contrarian + Global South + some Hungarian-aligned EU) treats the same investigations and scandals as confirmation that the Zelensky inner circle is systemically corrupt, that Western aid is being stolen at scale through defense procurement, that the regime is increasingly authoritarian (banned opposition parties, restricted media, cancelled elections, Yermak-centred power concentration), and that EU/NATO accession on this institutional basis is unrealistic. Vocabulary: endemic corruption, regime corruption, stolen aid, defense procurement scandal, Yermak inner circle, authoritarian regime, cancelled elections, banned opposition, Western blind eye. Coverage uses the same anti-corruption agency investigations as evidence of scale, frames prosecutions as theatrical or selective, and emphasises Western media protection of the regime. Prescription: condition or halt aid pending genuine accountability; recognise that the regime cannot deliver promised reforms; reject any settlement that consolidates the current Kyiv leadership.',
 'Endemisch-Korruptions-Rahmung (russische Staatsmedien + westliche Dissidenten + Global South + einige ungarisch-orientierte EU) behandelt dieselben Ermittlungen und Skandale als Bestaetigung, dass der Selenskyj-Kreis systemisch korrupt sei, westliche Hilfe in grossem Stil ueber Ruestungsbeschaffung gestohlen werde, das Regime zunehmend autoritaer sei (verbotene Oppositionsparteien, eingeschraenkte Medien, abgesagte Wahlen, Jermak-zentrierte Machtkonzentration) und EU/NATO-Beitritt auf dieser institutionellen Basis unrealistisch. Vokabular: endemische Korruption, Regime-Korruption, gestohlene Hilfe, Ruestungsbeschaffungs-Skandal, Jermak-Innenkreis, autoritaeres Regime, abgesagte Wahlen, verbotene Opposition, westliches Wegschauen. Berichterstattung nutzt dieselben Antikorruptionsbehoerden-Ermittlungen als Belegmaterial fuer das Ausmass, rahmt Strafverfolgung als theatralisch oder selektiv und betont westlichen Medienschutz des Regimes. Vorschrift: Hilfe an echte Rechenschaft konditionieren oder einstellen; anerkennen, dass das Regime versprochene Reformen nicht liefern kann; jede Beilegung ablehnen, die die gegenwaertige Kiewer Fuehrung konsolidiert.',
 ARRAY['EUROPE-RUSSIA','ASIA-CHINA','NON-STATE-EU'],
 ARRAY['TASS','TASS (EN)','tass.com','RT','Lenta.ru','lenta.ru','Gazeta.ru','gazeta.ru','Kommersant','Izvestia','RIA Novosti','BelTA','BelTA Russian','Press TV','Fox News','Global Times','CGTN','China Daily','Hindustan Times','TRT World','Daily Sabah','O Globo'],
 ARRAY['endemic corruption','regime corruption','stolen aid','defense procurement scandal','Yermak inner circle','authoritarian regime','cancelled elections','banned opposition','Western blind eye','theatrical prosecution','selective justice'],
 true);

-- russia_sanctions_regime narratives (2)
INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('tighten_and_seize', 'russia_sanctions_regime', 1, 2,
 'Tighten sanctions and seize frozen assets', 'Sanktionen verschaerfen und eingefrorenes Vermoegen beschlagnahmen',
 'Sanctions must be tightened, evasion closed, and frozen Russian assets seized for Ukraine',
 'Sanktionen muessen verschaerft, Umgehung geschlossen und eingefrorenes russisches Vermoegen fuer die Ukraine beschlagnahmt werden',
 'Tighten-and-seize framing (Ukrainian press + Western mainstream + Eastern European) treats sanctions as a necessary economic constraint on the Russian war machine and argues for both deepening the package and shifting from freeze to seizure. Vocabulary: oil price cap enforcement, shadow-fleet interdiction, secondary sanctions on UAE/Turkey/Central Asia transshipment hubs, REPO Act, seizure of $300B Euroclear-held sovereign assets for Ukrainian reconstruction, designation expansion, dual-use export controls. Coverage emphasises evidence of Russian economic stress (rouble pressure, defense industrial bottlenecks, labour shortages), the inadequacy of the current price cap as enforced, and the moral and practical case for converting frozen assets into reparations. Prescription: lower the oil price cap; aggressive secondary sanctions on third-country evaders; full seizure of frozen sovereign assets; expand SDN designations; close dual-use loopholes.',
 'Verschaerfen-und-Beschlagnahmen-Rahmung (ukrainische Medien + westlicher Mainstream + Osteuropa) behandelt Sanktionen als notwendige wirtschaftliche Beschraenkung der russischen Kriegsmaschine und argumentiert sowohl fuer Vertiefung des Pakets als auch fuer Verschiebung von Einfrieren zu Beschlagnahme. Vokabular: Oelpreisdeckel-Durchsetzung, Schatten-Flotten-Abfangen, Sekundaersanktionen gegen Umschlag-Drehscheiben in VAE/Tuerkei/Zentralasien, REPO Act, Beschlagnahme von bei Euroclear gehaltenem Staatsvermoegen ueber 300 Mrd. USD fuer ukrainischen Wiederaufbau, Ausweitung der Listungen, Doppelverwendungs-Exportkontrollen. Berichterstattung betont Belegmaterial fuer russischen Wirtschaftsstress (Rubel-Druck, Verteidigungsindustrie-Engpaesse, Arbeitskraefte-Mangel), Unzulaenglichkeit des aktuellen Preisdeckels in der Durchsetzung und moralisch sowie praktisch den Fall fuer Umwandlung eingefrorenen Vermoegens in Reparationen. Vorschrift: Oelpreisdeckel senken; aggressive Sekundaersanktionen gegen Drittland-Umgeher; volle Beschlagnahme eingefrorenen Staatsvermoegens; SDN-Listungen ausweiten; Doppelverwendungs-Schlupfloecher schliessen.',
 ARRAY['EUROPE-UKRAINE','EUROPE-UK','EUROPE-BALTIC','EUROPE-VISEGRAD','EUROPE-FRANCE','EUROPE-GERMANY','AMERICAS-USA'],
 ARRAY['Kyiv Post','Reuters','Bloomberg','Financial Times','BBC World','The Guardian','The Telegraph','Le Monde','Frankfurter Allgemeine','Süddeutsche Zeitung','Der Spiegel','Die Zeit','Tagesschau','Handelsblatt','Deutsche Welle','La Repubblica','ANSA','El País','ERR News','LRT English','LSM English','Atlantic Council','Associated Press','The Economist','EurActiv','New York Times','Washington Post','Wall Street Journal','Politico','OilPrice','Defense News'],
 ARRAY['tighten sanctions','price cap enforcement','shadow fleet interdiction','secondary sanctions','seize frozen assets','REPO','reparations','SDN designation','dual-use controls','evasion crackdown','Russian economic stress','sanctions package'],
 true),

('sanctions_ineffective_and_backfiring', 'russia_sanctions_regime', 2, -2,
 'Sanctions ineffective and backfiring', 'Sanktionen wirkungslos und kontraproduktiv',
 'Sanctions hurt Europe more than Russia; frozen-asset seizure would destroy financial trust',
 'Sanktionen schaden Europa staerker als Russland; Beschlagnahme eingefrorenen Vermoegens wuerde Finanzvertrauen zerstoeren',
 'Sanctions-ineffective framing (Russian state press + Global South + Chinese state press + Hungarian-aligned EU) argues that the sanctions package has hurt European economies more severely than Russia, that the Russian economy has successfully adapted through parallel imports, currency controls, BRICS settlement, and Asian energy markets, and that frozen-asset seizure would set a precedent destroying global trust in the Western financial system. Vocabulary: sanctions backfire, European economic harm, Russian economic resilience, BRICS settlement, de-dollarisation, parallel imports, financial weaponisation, trust collapse, multipolar finance. Coverage emphasises German industrial decline, French inflation, US shale-gas profiteering at European expense, growing Global South neutrality, and the historical failure of sanctions to change behaviour. Prescription: lift or phase out sanctions as part of any peace deal; halt frozen-asset seizure plans; restore Russian energy supply to Europe; recognise multipolar financial reality.',
 'Sanktionen-wirkungslos-Rahmung (russische Staatsmedien + Global South + chinesische Staatsmedien + ungarisch-orientierte EU) argumentiert, dass das Sanktionspaket europaeische Wirtschaften schwerer geschaedigt habe als Russland, die russische Wirtschaft sich durch Parallelimporte, Waehrungskontrollen, BRICS-Abwicklung und asiatische Energiemaerkte erfolgreich angepasst habe und Beschlagnahme eingefrorenen Vermoegens einen Praezedenzfall schaffen wuerde, der globales Vertrauen in das westliche Finanzsystem zerstoere. Vokabular: Sanktionen-Bumerang, europaeischer Wirtschaftsschaden, russische Wirtschaftsresilienz, BRICS-Abwicklung, Ent-Dollarisierung, Parallelimporte, Finanzwaffe, Vertrauenseinbruch, multipolare Finanz. Berichterstattung betont deutschen Industrieabbau, franzoesische Inflation, US-Schiefergas-Profite zu europaeischen Lasten, wachsende Global-South-Neutralitaet und das historische Versagen von Sanktionen, Verhalten zu aendern. Vorschrift: Sanktionen im Rahmen jedes Friedensdeals aufheben oder schrittweise abbauen; Beschlagnahmepleane stoppen; russische Energieversorgung Europas wiederherstellen; multipolare Finanzrealitaet anerkennen.',
 ARRAY['EUROPE-RUSSIA','ASIA-CHINA','ASIA-INDIA','NON-STATE-EU'],
 ARRAY['TASS','TASS (EN)','tass.com','RT','Lenta.ru','lenta.ru','Gazeta.ru','gazeta.ru','Kommersant','Izvestia','RIA Novosti','BelTA','BelTA Russian','Press TV','Global Times','CGTN','China Daily','Hindustan Times','Times of India','NDTV','TRT World','Daily Sabah','O Globo','Bangkok Post','BRICS Info','OilPrice'],
 ARRAY['sanctions backfire','European harm','Russian resilience','BRICS settlement','de-dollarisation','parallel imports','financial weaponisation','trust collapse','multipolar finance','German deindustrialisation','sanctions failed','lift sanctions'],
 true);

-- ============================================================
-- 4. Sanity check
-- ============================================================

DO $$
DECLARE
    n_fn integer; n_atomic integer; n_theater integer;
    n_nar integer; n_anchor integer;
BEGIN
    SELECT COUNT(*) INTO n_fn FROM friction_nodes
        WHERE id IN ('ukraine_war_theater','ukraine_battlefield','western_aid_to_ukraine',
                     'ukraine_peace_negotiations','ukraine_official_corruption','russia_sanctions_regime');
    SELECT COUNT(*) INTO n_atomic FROM friction_nodes
        WHERE id IN ('ukraine_battlefield','western_aid_to_ukraine','ukraine_peace_negotiations',
                     'ukraine_official_corruption','russia_sanctions_regime') AND fn_type = 'atomic';
    SELECT COUNT(*) INTO n_theater FROM friction_nodes
        WHERE id = 'ukraine_war_theater' AND fn_type = 'theater';
    SELECT COUNT(*) INTO n_nar FROM narratives_v2
        WHERE fn_id IN ('ukraine_war_theater','ukraine_battlefield','western_aid_to_ukraine',
                        'ukraine_peace_negotiations','ukraine_official_corruption','russia_sanctions_regime');
    SELECT COUNT(*) INTO n_anchor FROM taxonomy_v3
        WHERE taxonomy_function = 'fn_anchor'
          AND linked_id IN ('ukraine_war_theater','ukraine_battlefield','western_aid_to_ukraine',
                            'ukraine_peace_negotiations','ukraine_official_corruption','russia_sanctions_regime');
    IF n_fn <> 6 OR n_atomic <> 5 OR n_theater <> 1 OR n_nar <> 13 OR n_anchor <> 6 THEN
        RAISE EXCEPTION 'Ukraine theater seed sanity check failed: fn=%, atomic=%, theater=%, narratives=%, anchors=% (expected 6/5/1/13/6)',
            n_fn, n_atomic, n_theater, n_nar, n_anchor;
    END IF;
END $$;

COMMIT;
