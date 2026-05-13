-- Turkey theater seed: 1 theater + 4 atomic FNs + 11 narratives + 5 fn_anchor bundles.
-- 2026-05-13
--
-- Architecture follows iran_theater / israel_theater / syria_theater. See
-- docs/context/TURKEY_THEATER_SPEC.md for narrative rationale and source data.
--
-- Centroid scope discipline (lesson from Syria seed):
--   - Atomic FN centroid_ids = the conflict's actual geographic surface
--   - Foreign engagers live in narrative publisher cohorts, NOT in centroid_ids
--   - Theater centroid stays broader because its anchor is precise own-side names
--
-- Anchor discipline: atoms where they discriminate, phrase forms where atoms
-- are too generic (e.g. "Patriot system" not "system"). No third-party leader
-- names. No country-name repetition (centroid handles MIDEAST-TURKEY).
--
-- Stance is toward Turkey under Erdogan as primary actor.

BEGIN;

-- ============================================================
-- 1. friction_nodes
-- ============================================================

INSERT INTO friction_nodes (id, name_en, name_de, description_en, description_de,
    editorial_summary_en, editorial_summary_de, centroid_ids, fn_type, member_fn_ids,
    is_active, display_order)
VALUES

('turkey_theater', 'Turkey as contested regional power', 'Tuerkei als umkaempfte Regionalmacht',
 'Turkey under Erdogan operates as a contested regional power across four parallel surfaces: a self-styled mediator role spanning Gaza, Iran, Ukraine and the Gulf; domestic democratic backsliding around the Imamoglu trial and the CHP crackdown; the Turkey-side framing of the Kurdish question with the PKK disarmament process and cross-border operations against the YPG/SDF; and the spillover of the Iran war into Turkish airspace and NATO deployments.',
 'Die Tuerkei unter Erdogan ist eine umstrittene Regionalmacht entlang vier paralleler Felder: selbst inszenierte Vermittlerrolle zwischen Gaza, Iran, Ukraine und Golf; demokratischer Ruecklaeufer im Inland um den Imamoglu-Prozess und das CHP-Verfahren; die tuerkische Rahmung der Kurdenfrage mit PKK-Entwaffnungsprozess und grenzueberschreitenden Operationen gegen YPG/SDF; und das Uebergreifen des Iran-Kriegs in tuerkischen Luftraum und NATO-Stationierungen.',
 'Turkey is the densest non-Iran / non-Israel Middle East signal in the corpus. The theater holds four contested surfaces, each with its own publisher cohort split: Turkish state desk vs. pan-Arab vs. Western liberal vs. Israeli right. The umbrella narratives above all four: Turkey as independent middle power, Turkey as unreliable NATO ally, and an EU pragmatic-engagement framing.',
 'Die Tuerkei ist das dichteste Nahost-Signal jenseits Irans und Israels im Korpus. Die Konfliktzone umfasst vier umstrittene Felder mit je eigener Publikations-Aufteilung: tuerkische Staatslinie vs. panarabisch vs. westlich-liberal vs. israelische Rechte. Uebergreifende Narrative: Tuerkei als unabhaengige Mittelmacht, Tuerkei als unzuverlaessiger NATO-Partner, EU-pragmatische Linie.',
 ARRAY['MIDEAST-TURKEY','MIDEAST-LEVANT','MIDEAST-IRAN','MIDEAST-ISRAEL','MIDEAST-EGYPT','MIDEAST-SAUDI','MIDEAST-GULF','MIDEAST-IRAQ','AMERICAS-USA','EUROPE-RUSSIA','EUROPE-UKRAINE','EUROPE-GERMANY','EUROPE-GREECE','NON-STATE-EU','NON-STATE-NATO'],
 'theater', ARRAY['turkey_mediator_role','turkey_democratic_backsliding','turkey_kurdish_question','turkey_iran_war_spillover'],
 true, 50),

('turkey_mediator_role', 'Turkey as regional mediator', 'Tuerkei als regionaler Vermittler',
 'Erdogan''s positioning as broker across multiple regional contests: Gaza peace board membership, originally proposed Istanbul venue for Iran-US nuclear talks, Zelensky-Erdogan Istanbul talks, Sisi-Erdogan rapprochement, Fidan shuttle diplomacy on Iran ceasefire. The contest: legitimate balanced mediator vs. opportunistic two-faced player.',
 'Erdogans Positionierung als Vermittler zwischen mehreren regionalen Konflikten: Mitgliedschaft im Gaza-Friedensrat, urspruenglich Istanbul als Veranstaltungsort fuer Iran-US-Atomgespraeche, Selenskyj-Erdogan-Gespraeche in Istanbul, aegyptisch-tuerkische Annaeherung, Fidan-Shuttle-Diplomatie zum Iran-Waffenstillstand. Kontest: legitimer ausgleichender Vermittler vs. opportunistischer Doppelspieler.',
 'Turkey''s mediator self-image is a central thread of Erdogan-era foreign policy. Pro-Turkey publishers frame the convening capacity as indispensable; critics frame it as vanity diplomacy that buys influence without deliverables. The pattern repeats across Gaza (Trump''s peace board offer), Ukraine (Zelensky''s Istanbul visit), Iran (Istanbul venue and Fidan''s talks), Egypt (Sisi rapprochement) and the Gulf.',
 'Das Vermittler-Selbstbild der Tuerkei ist ein roter Faden der Erdogan-Aera. Pro-tuerkische Medien rahmen die Vermittlungs-Kapazitaet als unverzichtbar; Kritiker rahmen sie als Eitelkeits-Diplomatie ohne Resultate. Das Muster wiederholt sich bei Gaza, Ukraine, Iran und Aegypten.',
 ARRAY['MIDEAST-TURKEY','MIDEAST-IRAN','MIDEAST-ISRAEL','MIDEAST-EGYPT','MIDEAST-GULF','MIDEAST-SAUDI','EUROPE-UKRAINE'],
 'atomic', NULL, true, 51),

('turkey_democratic_backsliding', 'Turkish domestic democratic backsliding', 'Demokratische Ruecklaeufigkeit in der Tuerkei',
 'The Imamoglu trial, broader CHP corruption investigations (Ankara chair detention, Izmir municipality bribery), opposition mayor detentions, journalist arrests (DW correspondent), and protest waves a year after Imamoglu''s initial arrest. The contest: Western liberal critique of authoritarian drift vs. domestic state-desk defence as legitimate anti-corruption proceedings.',
 'Der Imamoglu-Prozess, weitere CHP-Korruptionsverfahren, Festnahmen von Oppositionsbuergermeistern, Journalisten-Verhaftungen und Protestwellen ein Jahr nach Imamoglus erster Verhaftung. Kontest: westlich-liberale Kritik am autoritaeren Abgleiten vs. inlaendische Verteidigung als legitime Antikorruptions-Verfahren.',
 'Domestic backsliding is the most-watched Turkey story for the DACH cohort (Tagesschau, FAZ, Die Zeit, Süddeutsche, Der Standard, Kurier) because of diaspora interest. The Turkish state desk treats the legal proceedings as routine anti-graft; Western press treats them as political persecution of Erdogan''s most credible 2028 challenger.',
 'Inlands-Backsliding ist die am meisten verfolgte Tuerkei-Geschichte fuer die DACH-Kohorte wegen Diaspora-Interesses. Die tuerkische Staatslinie behandelt die Verfahren als gewoehnliche Antikorruption; westliche Presse als politische Verfolgung des glaubwuerdigsten Erdogan-Herausforderers fuer 2028.',
 ARRAY['MIDEAST-TURKEY','EUROPE-GERMANY','NON-STATE-EU'],
 'atomic', NULL, true, 52),

('turkey_kurdish_question', 'Turkey-side Kurdish question', 'Kurdische Frage aus tuerkischer Sicht',
 'The Turkish framing of the Kurdish question: PKK disarmament process initiated via Bahceli''s 2024 opening, DEM Party (HDP successor) negotiations, Ocalan''s Imrali messaging from prison, "terror-free Türkiye" doctrine, cross-border operations against YPG/SDF in northeast Syria and PKK leadership in northern Iraq. Distinct from syria_kurdish_question (Damascus-SDF reunification) — same entities, different framing.',
 'Die tuerkische Rahmung der Kurdenfrage: PKK-Entwaffnungsprozess seit Bahcelis Eroeffnung 2024, Verhandlungen mit der DEM-Partei (HDP-Nachfolger), Botschaften Oecalans aus dem Imrali-Gefaengnis, Doktrin "terrorfreie Tuerkei", grenzueberschreitende Operationen gegen YPG/SDF in Nordostsyrien und PKK-Fuehrung im Nordirak. Abgegrenzt von syria_kurdish_question (Damaskus-SDF-Wiedervereinigung) — gleiche Akteure, andere Rahmung.',
 'The Kurdish question registered in two different ways in our corpus: the Turkey-side framing centres on PKK as terror, disarmament as the precondition for any political process, cross-border anti-YPG operations as legitimate counter-terror. The Syria-side framing centres on Damascus-SDF territorial reunification. Both can attach to the same title if publisher and anchor match — that is the correct outcome under 1-to-1.',
 'Die Kurdenfrage erscheint in unserem Korpus zweifach: die tuerkische Rahmung mit PKK als Terror, Entwaffnung als Vorbedingung jeder politischen Loesung, grenzueberschreitende Anti-YPG-Operationen als legitime Anti-Terror-Massnahme. Die syrische Rahmung mit Damaskus-SDF-Territorialvereinigung. Beide koennen auf denselben Titel zutreffen.',
 ARRAY['MIDEAST-TURKEY','MIDEAST-LEVANT','MIDEAST-IRAQ'],
 'atomic', NULL, true, 53),

('turkey_iran_war_spillover', 'Iran-war spillover into Turkey', 'Auswirkungen des Iran-Kriegs auf die Tuerkei',
 'The Iran-war consequences that materialise inside Turkish territory and NATO posture: Iranian ballistic missile intercepted by NATO air defence over Turkey, US Patriot redeployment to Malatya from Ramstein, Erdogan publicly opposing US-Israel strikes on Iran, Erdogan-Putin call about Iran, Erdogan-Trump conversations about Iran ceasefire. Distinct from israel_iran_strikes (direct exchange) and iran_theater (Iran''s posture).',
 'Die Iran-Kriegsfolgen, die auf tuerkischem Territorium und in der NATO-Haltung materialisieren: iranische ballistische Rakete von NATO-Luftabwehr ueber der Tuerkei abgefangen, US-Patriot-Stationierung nach Malatya von Ramstein aus, Erdogans oeffentlicher Widerspruch gegen US-israelische Schlaege auf Iran. Abgegrenzt von israel_iran_strikes und iran_theater.',
 'The spillover surface has a clear narrative split: pro-Turkey and NATO-aligned framing treats Patriot redeployment and missile interception as legitimate alliance solidarity and territorial defence. Israeli-right and hawkish-US framing treats Erdogan''s opposition to US-Israel Iran action as Turkey siding with the wrong side, shielding the Iranian regime from accountability.',
 'Die Spillover-Front hat eine klare Narrativ-Spaltung: pro-tuerkisch und NATO-orientiert wertet Patriot-Stationierung und Raketenabfang als legitime Buendnis-Solidaritaet. Die israelische Rechte und harte US-Linie wertet Erdogans Widerspruch als Stellungnahme auf der falschen Seite.',
 ARRAY['MIDEAST-TURKEY','MIDEAST-IRAN'],
 'atomic', NULL, true, 54);

-- ============================================================
-- 2. fn_anchor bundles
-- Strict atoms + phrase-form precision where atoms are too generic.
-- No third-party leader names. No `Turkey` / `Turkish` (centroid handles).
-- ============================================================

INSERT INTO taxonomy_v3 (item_raw, aliases, is_active, taxonomy_function, linked_id) VALUES

('turkey_theater fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'Erdogan','Fidan','Hakan Fidan','AKP','MHP','Bahceli','Yilmaz Tunc',
     'Istanbul','Ankara','Bosphorus','Anatolia','Turkiye','Türkiye',
     'Turkic Council','Organization of Turkic States','EU accession'),
   'de', jsonb_build_array(
     'tuerkische Aussenpolitik','EU-Beitritt Tuerkei','tuerkische Diaspora'),
   'es', jsonb_build_array(
     'política turca','adhesión a la UE de Turquía','diáspora turca'),
   'fr', jsonb_build_array(
     'politique turque','adhésion de la Turquie','diaspora turque'),
   'it', jsonb_build_array(
     'politica turca','adesione della Turchia','diaspora turca'),
   'ru', jsonb_build_array(
     'Эрдоган','Фидан','Хакан Фидан','Стамбул','Анкара','Босфор',
     'тюркский совет','турецкая диаспора','вступление в ЕС'),
   'hi', jsonb_build_array(
     'एर्दोआन','फिदान','इस्तांबुल','अंकारा','तुर्किये','तुर्की डायस्पोरा'),
   'zh', jsonb_build_array(
     '埃尔多安','费丹','哈坎·费丹','伊斯坦布尔','安卡拉','博斯普鲁斯','突厥国家组织'),
   'ar', jsonb_build_array(
     'إردوغان','فيدان','هاكان فيدان','إسطنبول','أنقرة','البوسفور',
     'مجلس الدول التركية','الجالية التركية'),
   'ja', jsonb_build_array(
     'エルドアン','フィダン','ハカン・フィダン','イスタンブール','アンカラ',
     'ボスポラス','テュルク評議会')
 ),
 true, 'fn_anchor', 'turkey_theater'),

('turkey_mediator_role fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'Erdogan','Fidan','Hakan Fidan',
     'Dolmabahce','Istanbul venue',
     'peace board','Gaza peace board','Board of Peace',
     'Astana process','Astana format','grain corridor','Black Sea grain initiative',
     'Antalya forum','Antalya diplomacy forum',
     'Turkish mediation','Turkish broker','Erdogan mediator','Erdogan-Putin call',
     'Erdogan-Trump call','Erdogan-Zelensky','Erdogan-Sisi','Fidan visit'),
   'de', jsonb_build_array(
     'tuerkische Vermittlung','Vermittler Erdogan','Getreidekorridor Schwarzes Meer',
     'Astana-Format','Antalya-Forum'),
   'es', jsonb_build_array(
     'mediación turca','mediador Erdogan','corredor de granos del Mar Negro',
     'formato de Astaná'),
   'fr', jsonb_build_array(
     'médiation turque','médiateur Erdogan','corridor céréalier de la mer Noire',
     'format Astana'),
   'it', jsonb_build_array(
     'mediazione turca','mediatore Erdogan','corridoio del grano del Mar Nero',
     'formato Astana'),
   'ru', jsonb_build_array(
     'турецкое посредничество','посредник Эрдоган','зерновой коридор',
     'астанинский формат','Долмабахче','форум Антальи',
     'звонок Эрдоган-Путин','звонок Эрдогана Трампу'),
   'hi', jsonb_build_array(
     'तुर्की मध्यस्थता','मध्यस्थ एर्दोआन','अनाज गलियारा','अस्ताना प्रारूप'),
   'zh', jsonb_build_array(
     '土耳其调停','调解人埃尔多安','黑海粮食走廊','阿斯塔纳进程','和平委员会',
     '加沙和平委员会','安塔利亚论坛','多尔玛巴赫切'),
   'ar', jsonb_build_array(
     'الوساطة التركية','وسيط إردوغان','ممر الحبوب','مسار أستانا','منتدى أنطاليا',
     'مجلس السلام','مجلس سلام غزة','دولما باهتشه','مكالمة إردوغان بوتين',
     'مكالمة إردوغان ترامب'),
   'ja', jsonb_build_array(
     'トルコの仲介','仲介者エルドアン','黒海穀物回廊','アスタナ協議','和平委員会',
     'ガザ和平委員会','アンタルヤ・フォーラム','ドルマバフチェ')
 ),
 true, 'fn_anchor', 'turkey_mediator_role'),

('turkey_democratic_backsliding fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'Imamoglu','Ekrem Imamoglu','CHP','Republican People''s Party','Ozel','Yavas',
     'DEM Party','HDP','Silivri prison','Silivri',
     'opposition mayor','opposition crackdown','press freedom Turkey','press freedom Turkiye',
     'RTUK','RTÜK','social media ban','social media restriction',
     'journalist arrested in Turkey','corruption probe Turkey','indictment Turkey'),
   'de', jsonb_build_array(
     'Imamoglu','CHP','DEM-Partei','Oppositionsbuergermeister Tuerkei',
     'Pressefreiheit Tuerkei','Korruptionsverfahren Tuerkei','Verhaftung Journalist Tuerkei',
     'RTUEK','Silivri-Gefaengnis'),
   'es', jsonb_build_array(
     'Imamoglu','partido CHP','alcalde opositor turco','libertad de prensa en Turquía',
     'detención periodista Turquía','procesamiento Turquía'),
   'fr', jsonb_build_array(
     'Imamoglu','CHP','maire d''opposition turc','liberté de la presse Turquie',
     'inculpation Turquie','arrestation journaliste Turquie'),
   'it', jsonb_build_array(
     'Imamoglu','CHP','sindaco d''opposizione turco','libertà di stampa Turchia',
     'incriminazione Turchia','arresto giornalista Turchia'),
   'ru', jsonb_build_array(
     'Имамоглу','Экрем Имамоглу','НРП','ДЕМ','оппозиционный мэр Турции',
     'свобода прессы в Турции','арест журналиста в Турции',
     'коррупционное дело в Турции','Силиври'),
   'hi', jsonb_build_array(
     'इमामोग्लू','सीएचपी','तुर्की विपक्षी मेयर','तुर्की प्रेस की स्वतंत्रता'),
   'zh', jsonb_build_array(
     '伊马姆奥卢','共和人民党','土耳其反对派市长','土耳其新闻自由',
     '土耳其记者被捕','锡利夫里监狱','DEM党'),
   'ar', jsonb_build_array(
     'إمام أوغلو','أكرم إمام أوغلو','حزب الشعب الجمهوري','حزب ديم',
     'عمدة معارض تركي','حرية الصحافة في تركيا','اعتقال صحفي تركي',
     'لائحة اتهام تركيا','سجن سيليفري'),
   'ja', jsonb_build_array(
     'イマモール','共和人民党','トルコ野党市長','トルコ報道の自由',
     'トルコ記者逮捕','シリブリ刑務所','DEM党')
 ),
 true, 'fn_anchor', 'turkey_democratic_backsliding'),

('turkey_kurdish_question fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'PKK','YPG','SDF','DEM Party','HDP','Ocalan','Abdullah Ocalan','Mazloum',
     'Imrali','Imrali process','Qandil','Diyarbakir','Hakkari','Sirnak',
     'terror-free Turkey','terror-free Türkiye','PKK disarmament','lay down arms',
     'Operation Claw','Pence-Kilit','Euphrates Shield','Olive Branch',
     'cross-border operation Iraq','cross-border operation Syria',
     'Tal Rifaat','Manbij','Kobani','PKK headquarters'),
   'de', jsonb_build_array(
     'PKK-Entwaffnung','terrorfreie Tuerkei','Operation Klaue',
     'grenzueberschreitende Operation Tuerkei','DEM-Partei','HDP','Oecalan','Diyarbakir'),
   'es', jsonb_build_array(
     'desarme del PKK','Turquía libre de terror','Operación Garra',
     'operación transfronteriza turca','partido DEM'),
   'fr', jsonb_build_array(
     'désarmement du PKK','Turquie sans terreur','Opération Griffe',
     'opération transfrontalière turque','parti DEM'),
   'it', jsonb_build_array(
     'disarmo del PKK','Turchia libera dal terrore','Operazione Artiglio',
     'operazione transfrontaliera turca','partito DEM'),
   'ru', jsonb_build_array(
     'РПК','ДЕМ','ХДП','Оджалан','Имралы','Кандиль','Диярбакыр',
     'разоружение РПК','Турция без терроризма','операция Коготь',
     'трансграничная операция Турции'),
   'hi', jsonb_build_array(
     'पीकेके','डीईएम','ओजलान','इमराली','पीकेके निरस्त्रीकरण',
     'आतंक मुक्त तुर्की','तुर्की सीमा पार ऑपरेशन'),
   'zh', jsonb_build_array(
     '库尔德工人党','PKK','人民保护部队','YPG','叙利亚民主力量','SDF','DEM党',
     '厄贾兰','奥贾兰','伊姆拉勒','坎迪勒','迪亚巴克尔',
     'PKK解除武装','无恐怖土耳其','利爪行动','土耳其跨境行动'),
   'ar', jsonb_build_array(
     'حزب العمال الكردستاني','ي ب ك','قسد','حزب ديم','حزب الشعوب الديمقراطي',
     'أوجلان','عبدالله أوجلان','إيمرالي','قنديل','ديار بكر',
     'نزع سلاح حزب العمال الكردستاني','تركيا خالية من الإرهاب',
     'عملية المخلب','عملية درع الفرات','عملية تركية عبر الحدود'),
   'ja', jsonb_build_array(
     'クルド労働者党','PKK','YPG','シリア民主軍','SDF','DEM党','オジャラン',
     'イムラル','カンディル','PKK武装解除','テロなきトルコ','クロウ作戦',
     'トルコ越境作戦')
 ),
 true, 'fn_anchor', 'turkey_kurdish_question'),

('turkey_iran_war_spillover fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'NATO Patriot','Patriot system','Patriot battery','NATO air defence','NATO air defense',
     'AN/TPY-2','Kurecik radar','Kurecik','Malatya','Incirlik','AWACS Konya',
     'Article 5','Article V','airspace violation Turkey','airspace violation Turkiye',
     'Iranian missile over Turkey','Iranian drone over Turkey',
     'Ramstein redeployment','NATO solidarity Turkey'),
   'de', jsonb_build_array(
     'NATO-Patriot','Patriot-System','NATO-Luftabwehr','Kurecik-Radar',
     'Artikel 5','Luftraumverletzung Tuerkei','iranische Rakete ueber Tuerkei'),
   'es', jsonb_build_array(
     'Patriot de la OTAN','sistema Patriot','defensa aérea de la OTAN','radar Kurecik',
     'Artículo 5','violación del espacio aéreo turco','misil iraní sobre Turquía'),
   'fr', jsonb_build_array(
     'Patriot OTAN','système Patriot','défense aérienne OTAN','radar Kurecik',
     'article 5','violation de l''espace aérien turc','missile iranien sur la Turquie'),
   'it', jsonb_build_array(
     'Patriot NATO','sistema Patriot','difesa aerea NATO','radar Kurecik',
     'articolo 5','violazione dello spazio aereo turco','missile iraniano sulla Turchia'),
   'ru', jsonb_build_array(
     'Patriot НАТО','система Patriot','ПВО НАТО','радар Куреджик','Куреджик',
     'Малатья','Инджирлик','статья 5','нарушение воздушного пространства Турции',
     'иранская ракета над Турцией','Рамштайн'),
   'hi', jsonb_build_array(
     'नाटो पैट्रियट','पैट्रियट प्रणाली','नाटो वायु रक्षा','मलात्या','कुरेजिक रडार',
     'अनुच्छेद 5','तुर्की हवाई क्षेत्र उल्लंघन','तुर्की पर ईरानी मिसाइल'),
   'zh', jsonb_build_array(
     '北约爱国者','爱国者系统','北约防空','库雷吉克雷达','马拉蒂亚','因吉尔利克',
     '第五条款','土耳其领空侵犯','飞越土耳其的伊朗导弹','拉姆施泰因'),
   'ar', jsonb_build_array(
     'باتريوت الناتو','منظومة باتريوت','الدفاع الجوي للناتو','رادار كوريجك',
     'كوريجك','ملاطية','إنجرليك','المادة الخامسة','انتهاك المجال الجوي التركي',
     'صاروخ إيراني فوق تركيا','رامشتاين'),
   'ja', jsonb_build_array(
     'NATOパトリオット','パトリオット','NATO防空','クレジクレーダー','マラティヤ',
     'インジルリク','第5条','トルコ領空侵犯','トルコ上空のイランミサイル',
     'ラムシュタイン')
 ),
 true, 'fn_anchor', 'turkey_iran_war_spillover');

-- ============================================================
-- 3. Narratives (11 = 3 theater + 2 per atomic)
-- ============================================================

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

-- Theater (3)
('turkey_independent_middle_power', 'turkey_theater', 1, 2,
 'Independent middle power', 'Unabhaengige Mittelmacht',
 'Turkey has earned regional stature through balanced diplomacy',
 'Tuerkei hat regionale Statur durch ausgewogene Diplomatie erworben',
 'Pro-Turkey publishers frame Erdogan''s Turkey as an independent middle power earning regional stature through balanced diplomacy across Gaza, Iran, Ukraine, Egypt, and the Gulf. The vocabulary: "regional power", "autonomous foreign policy", "convening capacity", "balanced diplomacy", "respected NATO ally", "Türkiye century". Prescription: respect Turkey''s autonomous foreign policy stance within NATO, accept Turkic Council and Organization of Turkic States as legitimate spheres of influence, treat Ankara as indispensable on Gaza, Iran, Ukraine and Black Sea questions.',
 'Pro-tuerkische Medien rahmen Erdogans Tuerkei als unabhaengige Mittelmacht, die durch ausgewogene Diplomatie zwischen Gaza, Iran, Ukraine, Aegypten und Golf regionale Statur erworben hat. Vokabular: "Regionalmacht", "autonome Aussenpolitik", "Vermittlungs-Kapazitaet", "ausgewogene Diplomatie", "respektierter NATO-Partner", "tuerkisches Jahrhundert". Vorschrift: autonome aussenpolitische Linie der Tuerkei innerhalb der NATO respektieren, Tuerk-Rat und Organisation der Tuerk-Staaten als legitime Einflusssphaeren anerkennen.',
 ARRAY['MIDEAST-TURKEY'],
 ARRAY['Daily Sabah','Anadolu Agency','TRT World','Al-Ahram','Al Jazeera','Khaleej Times','TASS (EN)'],
 ARRAY['regional power','autonomous foreign policy','convening capacity','balanced diplomacy','Türkiye century','Turkic Council'],
 true),

('turkey_unreliable_ally_warning', 'turkey_theater', 2, -2,
 'Unreliable NATO ally warning', 'Warnung vor unzuverlaessigem NATO-Partner',
 'Erdogan''s Turkey is a hostile or unreliable NATO partner',
 'Erdogans Tuerkei ist ein feindseliger oder unzuverlaessiger NATO-Partner',
 'Israeli right and hawkish-US commentary frame Erdogan''s Turkey as a hostile or at best unreliable NATO partner: courting Russia, opposing US-Israel Iran action, hosting Hamas leadership, undermining EU accession criteria, refusing to follow alliance line. The vocabulary: "unreliable ally", "two-faced", "Russia-friendly NATO state", "Hamas patron", "Erdogan as authoritarian outlier", "alliance disloyalty". Prescription: condition NATO defence cooperation on Turkey''s alignment, treat Erdogan rhetoric as adversarial signaling.',
 'Israelische Rechte und hartes US-Kommentariat rahmen Erdogans Tuerkei als feindseligen oder bestenfalls unzuverlaessigen NATO-Partner: Anbiederung an Russland, Widerspruch gegen US-israelische Iran-Aktion, Beherbergung der Hamas-Fuehrung, Unterminierung der EU-Beitrittskriterien, Verweigerung der Buendnislinie. Vokabular: "unzuverlaessiger Verbuendeter", "Doppelspiel", "russlandfreundlicher NATO-Staat", "Hamas-Schirmherr", "Erdogan als autoritaerer Aussenseiter", "Buendnis-Illoyalitaet". Vorschrift: NATO-Verteidigungskooperation an Ausrichtung knuepfen, Erdogan-Rhetorik als feindseliges Signal lesen.',
 ARRAY['MIDEAST-ISRAEL','AMERICAS-USA','EUROPE-GREECE'],
 ARRAY['Jerusalem Post','Times of Israel','The Times of Israel','i24NEWS','Arutz Sheva','Fox News','eKathimerini','Cyprus Mail'],
 ARRAY['unreliable ally','two-faced','Russia-friendly','Hamas patron','authoritarian','alliance disloyalty','outlier'],
 true),

('turkey_eu_engagement_pragmatic', 'turkey_theater', 3, 0,
 'EU pragmatic engagement', 'EU-pragmatische Linie',
 'Engage Turkey on shared interests while flagging democratic concerns',
 'Tuerkei pragmatisch im Eigeninteresse einbinden, demokratische Bedenken benennen',
 'EU and E3 (Germany, France, UK) coverage frames Turkey as a partner requiring calibrated rather than confrontational engagement. Position is genuinely two-sided: cooperate on migration, energy, Black Sea security, NATO eastern flank AND continue to flag democratic backsliding around the Imamoglu trial, journalist arrests, Cyprus and Aegean disputes. The vocabulary: "calibrated engagement", "shared interests", "rule of law concerns", "EU-Turkey customs union", "migration cooperation", "Cyprus question". Prescription: sustained dialogue, conditional support, no rupture, no normalisation of backsliding.',
 'Die EU und die E3 (Deutschland, Frankreich, Grossbritannien) rahmen die Tuerkei als Partner, der kalibriertes statt konfrontatives Engagement erfordert. Position genuin doppelseitig: Kooperation bei Migration, Energie, Schwarzes-Meer-Sicherheit, NATO-Ostflanke UND fortgesetzte Hinweise auf demokratischen Ruecklauf um Imamoglu-Prozess, Journalisten-Verhaftungen, Zypern und Aegaeis. Vokabular: "kalibriertes Engagement", "gemeinsame Interessen", "Rechtsstaats-Bedenken", "EU-Tuerkei-Zollunion", "Migrationskooperation", "Zypern-Frage". Vorschrift: anhaltender Dialog, bedingte Unterstuetzung, kein Bruch, keine Normalisierung des Ruecklaufs.',
 ARRAY['NON-STATE-EU','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK'],
 ARRAY['Tagesschau','Deutsche Welle','Die Zeit','Frankfurter Allgemeine','Süddeutsche Zeitung','Der Standard','Die Presse','Der Spiegel','Handelsblatt','Le Monde','Financial Times','Reuters','BBC World','Euronews','Kurier'],
 ARRAY['calibrated engagement','rule of law','customs union','migration cooperation','Cyprus question','EU-Turkey relations'],
 true),

-- turkey_mediator_role (2)
('turkey_legitimate_broker', 'turkey_mediator_role', 1, 2,
 'Legitimate balanced broker', 'Legitimer ausgleichender Vermittler',
 'Erdogan''s mediation across Gaza, Iran, Ukraine is indispensable',
 'Erdogans Vermittlung zwischen Gaza, Iran, Ukraine ist unverzichtbar',
 'Pro-Turkey and pan-Arab publishers frame Erdogan''s simultaneous channels to Trump, Putin, Pezeshkian, Zelensky, Sisi, and the Gulf as exactly the convening capacity the region needs. The Istanbul venue for Iran-US talks, Gaza peace board membership, Astana process continuity, grain corridor history, Egypt rapprochement all evidence Turkey''s indispensable role. The vocabulary: "balanced broker", "shuttle diplomacy", "convening power", "Istanbul venue", "Antalya forum", "honest broker". Prescription: international acceptance of Turkey''s mediator role, no exclusion from regional settlements.',
 'Pro-tuerkische und panarabische Medien rahmen Erdogans gleichzeitige Kanaele zu Trump, Putin, Pezeshkian, Selenskyj, Sisi und Golf als unverzichtbare Vermittlungs-Kapazitaet. Istanbul-Veranstaltungsort fuer Iran-US-Gespraeche, Gaza-Friedensrat-Mitgliedschaft, Astana-Kontinuitaet, Getreidekorridor-Geschichte, aegyptische Annaeherung als Belege. Vokabular: "ausgewogener Vermittler", "Shuttle-Diplomatie", "Vermittlungs-Macht", "Istanbul-Veranstaltungsort", "Antalya-Forum", "ehrlicher Vermittler". Vorschrift: internationale Anerkennung der Vermittlerrolle, kein Ausschluss aus regionalen Loesungen.',
 ARRAY['MIDEAST-TURKEY'],
 ARRAY['Daily Sabah','Anadolu Agency','TRT World','Al-Ahram','Egypt Today','Khaleej Times','Arab News','Al Jazeera','TASS (EN)'],
 ARRAY['balanced broker','shuttle diplomacy','convening power','Istanbul venue','Antalya forum','honest broker','rapprochement'],
 true),

('turkey_two_faced_opportunist', 'turkey_mediator_role', 2, -2,
 'Opportunistic two-faced player', 'Opportunistischer Doppelspieler',
 'Erdogan plays every side for influence without delivering',
 'Erdogan spielt jede Seite fuer Einfluss ohne Resultate',
 'Israeli right, Greek-Cypriot, and Fox-News-style framing: Erdogan plays every side — Hamas patron while courting the Gaza peace board, NATO member while opposing US-Israel Iran action, Ukraine ally while preserving Russian energy and tourism ties. The "mediator" framing is a vanity project that buys influence without delivering deliverables. The vocabulary: "two-faced", "opportunist", "vanity diplomacy", "Hamas patron", "Russia-friendly NATO", "no deliverables", "double game". Prescription: refuse to legitimise Turkish mediation; treat parallel channels as evidence of unreliability.',
 'Israelische Rechte, griechisch-zypriotische und Fox-News-Linien-Rahmung: Erdogan spielt jede Seite — Hamas-Schirmherr und gleichzeitig Bewerber um den Gaza-Friedensrat, NATO-Mitglied und gleichzeitig Gegner der US-israelischen Iran-Aktion, Ukraine-Verbuendeter und gleichzeitig Bewahrer russischer Energie- und Tourismus-Verbindungen. Die Vermittler-Rahmung ist ein Eitelkeits-Projekt ohne Ergebnisse. Vokabular: "Doppelspieler", "Opportunist", "Eitelkeits-Diplomatie", "Hamas-Schirmherr", "russlandfreundlicher NATO-Staat", "keine Resultate", "Doppelspiel". Vorschrift: tuerkische Vermittlung nicht legitimieren; parallele Kanaele als Unzuverlaessigkeits-Beleg lesen.',
 ARRAY['MIDEAST-ISRAEL','EUROPE-GREECE','AMERICAS-USA'],
 ARRAY['Jerusalem Post','Times of Israel','The Times of Israel','i24NEWS','Arutz Sheva','Haaretz','eKathimerini','Cyprus Mail','Fox News','The National'],
 ARRAY['two-faced','opportunist','vanity diplomacy','Hamas patron','no deliverables','double game','unreliable'],
 true),

-- turkey_democratic_backsliding (2)
('turkey_authoritarian_drift_critique', 'turkey_democratic_backsliding', 1, -2,
 'Authoritarian drift critique', 'Kritik am autoritaeren Abgleiten',
 'Imamoglu trial and CHP crackdown dismantle Turkish democracy',
 'Imamoglu-Prozess und CHP-Verfahren zerlegen tuerkische Demokratie',
 'Western liberal coverage, especially the DACH cohort, frames the Imamoglu trial, mass CHP detentions, journalist arrests, and crackdown on opposition mayors as the dismantling of Turkish democracy — an Erdogan move to neutralise his strongest 2028 challenger and consolidate one-man rule. Evidence: indictment without robust public evidence, judicial composition concerns, social media restrictions on protest coverage, press card revocations. The vocabulary: "authoritarian drift", "political persecution", "judicial weaponisation", "press freedom collapse", "consolidation of power", "neutralising challengers". Prescription: EU/E3 pressure, conditional cooperation, support for Turkish civil society and independent press.',
 'Westliche liberale Berichterstattung, vor allem die DACH-Kohorte, rahmt Imamoglu-Prozess, CHP-Massenverhaftungen, Journalisten-Verhaftungen und Vorgehen gegen Oppositionsbuergermeister als Zerlegung der tuerkischen Demokratie — Erdogans Zug zur Neutralisierung seines staerksten Herausforderers fuer 2028 und Konsolidierung der Ein-Mann-Herrschaft. Belege: Anklage ohne robuste oeffentliche Beweise, Bedenken zur Justiz-Zusammensetzung, Social-Media-Einschraenkungen, Pressekarten-Entzug. Vokabular: "autoritaerer Ruecklauf", "politische Verfolgung", "Justiz-Instrumentalisierung", "Pressefreiheit-Kollaps", "Macht-Konsolidierung", "Herausforderer ausschalten". Vorschrift: EU/E3-Druck, bedingte Kooperation, Unterstuetzung tuerkischer Zivilgesellschaft.',
 ARRAY['NON-STATE-EU','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','AMERICAS-USA'],
 ARRAY['Tagesschau','Deutsche Welle','Die Zeit','Frankfurter Allgemeine','Süddeutsche Zeitung','Der Standard','Die Presse','Der Spiegel','Kurier','BBC World','Reuters','Associated Press','Le Monde','France 24 (EN)'],
 ARRAY['authoritarian drift','political persecution','judicial weaponisation','press freedom','consolidation','neutralising challengers'],
 true),

('turkey_anti_graft_legalism_defense', 'turkey_democratic_backsliding', 2, 2,
 'Anti-graft legal process defence', 'Verteidigung als Antikorruptions-Verfahren',
 'Imamoglu indictment is routine anti-corruption process',
 'Imamoglu-Anklage ist gewoehnliches Antikorruptions-Verfahren',
 'Turkish state desk framing: investigations and trials against CHP officials, the Imamoglu indictment, and detentions of opposition mayors are legitimate anti-corruption proceedings handled by independent courts. Western press and pro-FETÖ commentary frame routine legal action as political persecution to delegitimise the elected government. The vocabulary: "anti-graft", "judicial independence", "rule of law", "FETÖ remnants", "Western interference", "legitimate prosecution", "evidence-based investigation". Prescription: respect Turkish judicial sovereignty, reject foreign meddling in domestic legal process.',
 'Tuerkische Staatslinie: Untersuchungen und Verfahren gegen CHP-Funktionaere, die Imamoglu-Anklage und die Festnahmen von Oppositionsbuergermeistern sind legitime Antikorruptions-Verfahren unabhaengiger Gerichte. Westliche Presse und FETOe-nahe Kommentare rahmen gewoehnliche rechtliche Schritte als politische Verfolgung zur Delegitimierung der gewaehlten Regierung. Vokabular: "Antikorruption", "Justizunabhaengigkeit", "Rechtsstaat", "FETOe-Reste", "westliche Einmischung", "legitime Strafverfolgung", "evidenzbasierte Untersuchung". Vorschrift: tuerkische Justizsouveraenitaet respektieren, auslaendische Einmischung ablehnen.',
 ARRAY['MIDEAST-TURKEY'],
 ARRAY['Daily Sabah','Anadolu Agency','TRT World'],
 ARRAY['anti-graft','judicial independence','rule of law','FETÖ','Western interference','legitimate prosecution'],
 true),

-- turkey_kurdish_question (2)
('pkk_terror_full_disarmament', 'turkey_kurdish_question', 1, 2,
 'PKK as terror, full disarmament required', 'PKK als Terror, vollstaendige Entwaffnung erforderlich',
 'PKK / YPG / SDF are one terror organisation; disarmament is the only acceptable path',
 'PKK / YPG / SDF sind eine Terror-Organisation; Entwaffnung ist der einzige akzeptable Weg',
 'Turkish state desk framing: the PKK and its Syrian YPG / SDF affiliates are a unified terrorist organisation; the only acceptable political process is full disarmament and dissolution; cross-border operations against YPG positions in Syria and PKK leadership in Iraq are legitimate counter-terrorism; "terror-free Türkiye" is the binding state doctrine. Bahceli''s 2024 opening and Ocalan''s Imrali messaging are accepted only on these terms. The vocabulary: "PKK terror", "YPG/PKK extension", "terror-free Türkiye", "lay down arms", "Operation Claw", "Euphrates Shield", "cross-border counter-terror", "Qandil leadership decapitation". Prescription: continue cross-border operations until PKK is dissolved; condition any political accommodation on disarmament.',
 'Tuerkische Staatslinie: PKK und ihre syrischen YPG-/SDF-Ableger sind eine vereinigte Terror-Organisation; der einzige akzeptable politische Prozess ist vollstaendige Entwaffnung und Aufloesung; grenzueberschreitende Operationen gegen YPG-Stellungen in Syrien und PKK-Fuehrung im Irak sind legitime Anti-Terror-Massnahmen; "terrorfreie Tuerkei" ist die bindende Staatsdoktrin. Bahcelis Oeffnung 2024 und Oecalans Imrali-Botschaften werden nur zu diesen Bedingungen akzeptiert. Vokabular: "PKK-Terror", "YPG/PKK-Ableger", "terrorfreie Tuerkei", "Waffen niederlegen", "Operation Klaue", "Euphrat-Schild", "grenzueberschreitende Anti-Terror-Massnahme", "Qandil-Fuehrungs-Enthauptung". Vorschrift: grenzueberschreitende Operationen fortsetzen, bis die PKK aufgeloest ist; politische Akkommodation an Entwaffnung knuepfen.',
 ARRAY['MIDEAST-TURKEY'],
 ARRAY['Daily Sabah','Anadolu Agency','TRT World'],
 ARRAY['PKK terror','YPG extension','terror-free Türkiye','lay down arms','Operation Claw','Euphrates Shield','counter-terror','disarmament'],
 true),

('kurdish_political_rights_critique', 'turkey_kurdish_question', 2, -1,
 'Kurdish political rights critique', 'Kritik fuer kurdische politische Rechte',
 'Turkey collapses Kurdish political rights into terror designation',
 'Tuerkei kollabiert kurdische politische Rechte in Terror-Designation',
 'Western liberal, pan-Arab Al Jazeera, and Israeli centrist framing: Turkey''s anti-PKK framing collapses legitimate Kurdish political representation (DEM Party, HDP heritage) into terror designation; YPG / SDF in Syria are democratic partners against ISIS, not PKK affiliates; Ocalan''s Imrali messaging shows willingness for political resolution that Ankara repeatedly rejects; cross-border strikes risk regional escalation. The vocabulary: "Kurdish political rights", "DEM Party legitimacy", "democratic SDF", "Imrali process", "negotiated peace", "cross-border escalation", "minority rights". Prescription: separate political Kurdish representation from PKK terror designation; support DEM Party participation; protect SDF in Syria.',
 'Westlich-liberale, panarabische Al-Jazeera- und israelische zentristische Rahmung: die tuerkische Anti-PKK-Rahmung kollabiert legitime kurdische politische Vertretung (DEM-Partei, HDP-Erbe) in Terror-Designation; YPG / SDF in Syrien sind demokratische Partner gegen den IS, keine PKK-Ableger; Oecalans Imrali-Botschaften zeigen Bereitschaft zu politischer Loesung, die Ankara wiederholt ablehnt; grenzueberschreitende Schlaege riskieren regionale Eskalation. Vokabular: "kurdische politische Rechte", "DEM-Partei-Legitimitaet", "demokratische SDF", "Imrali-Prozess", "Verhandlungsfrieden", "grenzueberschreitende Eskalation", "Minderheitenrechte". Vorschrift: politische kurdische Vertretung von PKK-Terror trennen; DEM-Beteiligung unterstuetzen; SDF in Syrien schuetzen.',
 ARRAY['MIDEAST-LEVANT','AMERICAS-USA','NON-STATE-EU'],
 ARRAY['Al Jazeera','BBC World','Deutsche Welle','France 24 (EN)','Reuters','Associated Press','Times of Israel','Jerusalem Post'],
 ARRAY['Kurdish political rights','DEM Party','democratic SDF','Imrali process','negotiated peace','minority rights'],
 true),

-- turkey_iran_war_spillover (2)
('nato_solidarity_territorial_defense', 'turkey_iran_war_spillover', 1, 1,
 'NATO solidarity and territorial defence', 'NATO-Solidaritaet und territoriale Verteidigung',
 'Patriot redeployment and missile interception are legitimate alliance defence',
 'Patriot-Stationierung und Raketenabfang sind legitime Buendnis-Verteidigung',
 'Pro-Turkey and NATO-aligned framing: Iran''s ballistic missile crossing Turkish airspace was an act of aggression intercepted by NATO; the Patriot redeployment to Malatya from Ramstein is legitimate alliance solidarity; Erdogan''s call for de-escalation is responsible great-power behaviour, not appeasement. The vocabulary: "NATO solidarity", "territorial defence", "Article 5 readiness", "Patriot redeployment", "airspace integrity", "responsible de-escalation". Prescription: maintain NATO commitment to Turkish territorial defence; treat Iranian airspace violations as alliance-level provocations.',
 'Pro-tuerkische und NATO-orientierte Rahmung: die iranische ballistische Rakete im tuerkischen Luftraum war ein Aggressionsakt, von der NATO abgefangen; die Patriot-Stationierung nach Malatya aus Ramstein ist legitime Buendnis-Solidaritaet; Erdogans Aufruf zur Deeskalation ist verantwortungsvolles Grossmacht-Verhalten, keine Beschwichtigung. Vokabular: "NATO-Solidaritaet", "territoriale Verteidigung", "Artikel-5-Bereitschaft", "Patriot-Stationierung", "Luftraum-Integritaet", "verantwortungsvolle Deeskalation". Vorschrift: NATO-Verpflichtung zur tuerkischen territorialen Verteidigung aufrechterhalten; iranische Luftraumverletzungen als Buendnis-Provokationen behandeln.',
 ARRAY['MIDEAST-TURKEY','NON-STATE-NATO'],
 ARRAY['Daily Sabah','Anadolu Agency','TRT World','Reuters','Associated Press','Bloomberg','France 24 (EN)','Tagesschau','Deutsche Welle'],
 ARRAY['NATO solidarity','territorial defence','Article 5','Patriot redeployment','airspace integrity','responsible de-escalation'],
 true),

('turkey_wrong_side_on_iran', 'turkey_iran_war_spillover', 2, -1,
 'Turkey on the wrong side of the Iran war', 'Tuerkei auf der falschen Seite im Iran-Krieg',
 'Erdogan shields the Iranian regime from accountability',
 'Erdogan schuetzt das iranische Regime vor Rechenschaft',
 'Israeli right and hawkish-US framing: by publicly opposing US-Israel strikes on Iran, telling Putin Turkey is against attacks on Iran, and offering Istanbul as a US-Iran venue, Erdogan is shielding the Iranian regime from accountability; NATO solidarity should be unequivocal. The vocabulary: "shielding Iran", "wrong side of Iran", "appeasement", "NATO disloyalty", "Erdogan-Pezeshkian channel", "moral neutrality on existential threat". Prescription: confront Turkey''s Iran posture; condition NATO defence cooperation on alignment with the Iran-isolation policy.',
 'Israelische Rechte und harte US-Rahmung: indem Erdogan oeffentlich gegen US-israelische Schlaege auf Iran ist, Putin sagt, die Tuerkei sei gegen Angriffe auf Iran, und Istanbul als US-Iran-Veranstaltungsort anbietet, schuetzt er das iranische Regime vor Rechenschaft; NATO-Solidaritaet sollte eindeutig sein. Vokabular: "Iran schuetzen", "falsche Seite zu Iran", "Beschwichtigung", "NATO-Illoyalitaet", "Erdogan-Pezeshkian-Kanal", "moralische Neutralitaet gegen existenzielle Bedrohung". Vorschrift: tuerkische Iran-Haltung konfrontieren; NATO-Verteidigungskooperation an Iran-Isolierungs-Politik knuepfen.',
 ARRAY['MIDEAST-ISRAEL','AMERICAS-USA'],
 ARRAY['Jerusalem Post','Times of Israel','The Times of Israel','i24NEWS','Arutz Sheva','Fox News','eKathimerini','Cyprus Mail','WION'],
 ARRAY['shielding Iran','wrong side','appeasement','NATO disloyalty','moral neutrality','Erdogan Iran posture'],
 true);

-- ============================================================
-- 4. Sanity check
-- ============================================================

DO $$
DECLARE
    n_fn integer; n_nar integer; n_anchor integer;
BEGIN
    SELECT COUNT(*) INTO n_fn FROM friction_nodes WHERE id IN
        ('turkey_theater','turkey_mediator_role','turkey_democratic_backsliding',
         'turkey_kurdish_question','turkey_iran_war_spillover');
    SELECT COUNT(*) INTO n_nar FROM narratives_v2 WHERE fn_id IN
        ('turkey_theater','turkey_mediator_role','turkey_democratic_backsliding',
         'turkey_kurdish_question','turkey_iran_war_spillover');
    SELECT COUNT(*) INTO n_anchor FROM taxonomy_v3
        WHERE taxonomy_function = 'fn_anchor' AND linked_id IN
        ('turkey_theater','turkey_mediator_role','turkey_democratic_backsliding',
         'turkey_kurdish_question','turkey_iran_war_spillover');
    IF n_fn <> 5 OR n_nar <> 11 OR n_anchor <> 5 THEN
        RAISE EXCEPTION 'Turkey theater sanity check failed: friction_nodes=%, narratives=%, fn_anchors=% (expected 5/11/5)',
            n_fn, n_nar, n_anchor;
    END IF;
END $$;

COMMIT;
