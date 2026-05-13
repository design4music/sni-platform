-- Syria theater seed: 1 theater + 4 atomic FNs + 11 narratives + 5 fn_anchor bundles.
-- 2026-05-13
--
-- Architecture follows iran_theater (D-075..D-079) and israel_theater (2026-05-12).
-- fn_anchor bundles strictly follow docs/context/FN_ANCHOR_VOCABULARY_SPEC.md
-- (4 pillars: own-side actors, sub-centroid geography, relevant systems, domain
-- actions; atoms not phrases; shortest unique form; no third-party leaders;
-- Latin-script collapse — proper names + identical-spelling concepts go EN only).
--
-- Stance is toward the new Syrian (HTS-led) transitional government, the
-- theater's primary actor.

BEGIN;

-- ============================================================
-- 1. Theater + atomic friction_nodes
-- ============================================================

INSERT INTO friction_nodes (id, name_en, name_de, description_en, description_de,
    editorial_summary_en, editorial_summary_de, centroid_ids, fn_type, member_fn_ids,
    is_active, display_order)
VALUES

('syria_theater', 'Syria in post-Assad transition', 'Syrien im Uebergang nach Assad',
 'Syria after the fall of Bashar al-Assad: an HTS-led transitional government under Ahmad al-Sharaa governs from Damascus, while Kurdish-led forces hold the northeast, foreign militaries operate against ISIS remnants, Israel strikes Syrian targets, and Arab and Western capitals weigh recognition. The contest spans governance legitimacy, territorial unity, foreign military presence, and the diplomatic act of engaging a former al-Qaeda operative.',
 'Syrien nach dem Sturz Bashar al-Assads: eine HTS-gefuehrte Uebergangsregierung unter Ahmad al-Sharaa regiert von Damaskus aus, waehrend kurdisch gefuehrte Kraefte den Nordosten halten, auslaendische Militaers gegen IS-Reste operieren, Israel syrische Ziele angreift und arabische und westliche Hauptstaedte ueber Anerkennung beraten. Der Konflikt umfasst Regierungslegitimitaet, territoriale Einheit, auslaendische Militaerpraesenz und den diplomatischen Akt der Anerkennung eines ehemaligen al-Qaida-Funktionaers.',
 'Syria is the most consequential governance question in the post-Assad Middle East. The theater holds four contested surfaces: the Kurdish self-administration in the northeast, Israeli strikes on Syrian territory, the residual counter-ISIS coalition operations, and the international recognition / normalisation trajectory. The umbrella narratives above run across them: the legitimacy of the HTS-led transition, the substantive jihadist-takeover warning, and the Russia/Iran loss lament as their regional position collapses.',
 'Syrien ist die folgenreichste Regierungsfrage im Nahen Osten nach Assad. Die Konfliktzone umfasst vier umstrittene Felder: kurdische Selbstverwaltung im Nordosten, israelische Schlaege auf syrisches Territorium, Anti-IS-Operationen der Koalition und die internationale Anerkennungs- und Normalisierungsentwicklung. Die uebergreifenden Narrative: Legitimitaet des HTS-gefuehrten Uebergangs, substantielle Warnung vor jihadistischer Machtuebernahme und Russland-Iran-Verlust-Lament beim Zusammenbruch ihrer regionalen Position.',
 ARRAY['MIDEAST-LEVANT','MIDEAST-TURKEY','MIDEAST-IRAN','MIDEAST-ISRAEL','MIDEAST-GULF','MIDEAST-SAUDI','MIDEAST-IRAQ','MIDEAST-EGYPT','AMERICAS-USA','EUROPE-UK','EUROPE-FRANCE','EUROPE-GERMANY','EUROPE-RUSSIA','EUROPE-UKRAINE','NON-STATE-EU'],
 'theater', ARRAY['syria_kurdish_question','syria_israeli_strikes','syria_counter_terror','syria_recognition_and_normalisation'],
 true, 30),

('syria_kurdish_question', 'Kurdish self-administration in northeast Syria', 'Kurdische Selbstverwaltung in Nordostsyrien',
 'The Syrian Democratic Forces (SDF) and the Autonomous Administration of North and East Syria (AANES) hold roughly a third of Syrian territory after Assad''s fall. Damascus seeks territorial reunification; Turkey treats the SDF as a PKK extension; the US backs the SDF in counter-ISIS operations. The contest is over Kurdish self-rule, territorial sovereignty, and Turkey''s anti-PKK red lines.',
 'Die Syrischen Demokratischen Kraefte (SDF) und die Autonome Verwaltung Nord- und Ostsyriens (AANES) kontrollieren nach Assads Sturz rund ein Drittel des syrischen Territoriums. Damaskus strebt die territoriale Wiedervereinigung an; die Tuerkei behandelt die SDF als PKK-Ableger; die USA unterstuetzen die SDF bei Anti-IS-Operationen. Umstritten sind kurdische Selbstverwaltung, territoriale Souveraenitaet und die tuerkischen Anti-PKK-Grenzen.',
 'The Kurdish question is the deepest unresolved contest inside Syria. SDF-Damascus ceasefires in January 2026 produced temporary calm; permanent settlement requires resolving three incompatible demands: Kurdish federalism, Damascus central authority, and Turkish security guarantees. Western framing tends to side with the SDF as a democratic experiment and ISIS-jailer; Turkish state media frames the SDF as PKK in another uniform; pro-Damascus framing calls SDF a separatist project backed by foreign powers.',
 'Die Kurdenfrage ist der tiefste ungeloeste Konflikt in Syrien. SDF-Damaskus-Waffenstillstaende im Januar 2026 schufen voruebergehende Ruhe; eine dauerhafte Loesung erfordert die Aufloesung von drei unvereinbaren Forderungen: kurdischer Foederalismus, zentrale Autoritaet Damaskus und tuerkische Sicherheitsgarantien. Westliche Rahmung sieht die SDF als demokratisches Experiment und IS-Waechter; tuerkische Staatsmedien rahmen die SDF als PKK in anderer Uniform; pro-Damaskus-Rahmung nennt die SDF ein separatistisches Projekt mit auslaendischer Rueckendeckung.',
 ARRAY['MIDEAST-LEVANT','MIDEAST-TURKEY','MIDEAST-IRAQ','AMERICAS-USA'],
 'atomic', NULL, true, 31),

('syria_israeli_strikes', 'Israeli strikes on Syrian targets', 'Israelische Schlaege gegen syrische Ziele',
 'Israeli airstrikes inside Syria targeting residual Iranian and Hezbollah logistics and, increasingly after Assad''s fall, Syrian army positions. The buffer zone south of Damascus and Golan-adjacent operations are the recurring friction surface. Distinct from israel_iran_strikes (direct Iran-Israel exchange) and israel_lebanon_border (Litani crossings).',
 'Israelische Luftangriffe in Syrien gegen verbliebene iranische und Hisbollah-Logistik und zunehmend gegen syrische Armeeziele nach Assads Sturz. Die Pufferzone suedlich von Damaskus und die Operationen entlang des Golan sind die wiederkehrende Konfliktflaeche. Abgegrenzt von israel_iran_strikes (direkter Iran-Israel-Schlagabtausch) und israel_lebanon_border (Litani-Ueberquerungen).',
 'Israeli strikes on Syria escalated through 2025-2026 as Israel sought to prevent residual Iranian assets and Syrian army capability from re-establishing in southern Syria. Pro-Israel framing treats these as legitimate preventive defense; pro-Syrian sovereignty framing now extends to the new transitional government, which has begun protesting Israeli incursions despite Israel''s rationale that the new government inherits the threat posture.',
 'Israelische Schlaege gegen Syrien eskalierten in 2025-2026, da Israel verbliebene iranische Assets und syrische Armee-Kapazitaeten im Sueden Syriens unterbinden wollte. Pro-israelische Rahmung sieht diese als legitime Praevention; pro-syrische Souveraenitaets-Rahmung erstreckt sich nun auch auf die neue Uebergangsregierung, die israelische Einfaelle trotz israelischer Bedrohungsbegruendung zunehmend protestiert.',
 ARRAY['MIDEAST-LEVANT','MIDEAST-ISRAEL','MIDEAST-IRAN'],
 'atomic', NULL, true, 32),

('syria_counter_terror', 'Counter-ISIS operations and residual terrorism', 'Anti-IS-Operationen und verbliebener Terrorismus',
 'US-led coalition operations against the Islamic State residue in Syria and Iraq: detainee transfers from SDF custody to Iraq, prison-break risk at al-Hol and al-Roj, al-Qaeda residual leadership strikes, foreign troop deployments at Erbil and northeast Syria bases. UK and French air operations are part of the cycle.',
 'Operationen der US-gefuehrten Koalition gegen die IS-Reste in Syrien und Irak: Verlegung von Haeftlingen aus SDF-Gewahrsam in den Irak, Risiko eines Gefangenenausbruchs in al-Hol und al-Roj, Schlaege gegen verbliebene al-Qaida-Fuehrer, auslaendische Truppenstationierungen in Erbil und Nordostsyrien. Britische und franzoesische Luftoperationen gehoeren zum Zyklus.',
 'The coalition counter-ISIS mission is a low-intensity but persistent surface. The transition raises the operational question of whether the new Syrian government should inherit custody of ISIS detainees and the territorial responsibility, or whether the coalition continues its parallel mission. Western framing emphasises prison-break risk; pro-sovereignty framing argues for foreign-military withdrawal and transfer to national jurisdictions.',
 'Die Anti-IS-Mission der Koalition ist eine niedrigschwellige, aber dauerhafte Front. Der Uebergang wirft die operative Frage auf, ob die neue syrische Regierung die Verwahrung von IS-Haeftlingen und die territoriale Verantwortung uebernehmen soll, oder ob die Koalition ihre parallele Mission fortsetzt. Westliche Rahmung betont das Ausbruchsrisiko; Souveraenitaetsrahmung argumentiert fuer auslaendischen Truppenabzug und Uebergabe an nationale Jurisdiktionen.',
 ARRAY['MIDEAST-LEVANT','MIDEAST-IRAQ','AMERICAS-USA','EUROPE-UK','EUROPE-FRANCE'],
 'atomic', NULL, true, 33),

('syria_recognition_and_normalisation', 'International recognition and normalisation with the new Syrian government', 'Internationale Anerkennung und Normalisierung mit der neuen syrischen Regierung',
 'Every flavour of handshake with the al-Sharaa-led transitional government: Arab investment and recognition trajectories (Saudi, Gulf, Egypt), Western sanctions easing and calibrated engagement, Russia''s base-preservation negotiations, Ukraine''s Damascus visit. The shared substance is the *act of engaging*; the contest is whether engagement stabilises Syria or legitimises a former al-Qaeda operative.',
 'Jede Form von Handschlag mit der von al-Sharaa gefuehrten Uebergangsregierung: arabische Investitions- und Anerkennungstrajektorien (Saudi-Arabien, Golf, Aegypten), westliche Sanktionslockerung und kalibrierte Diplomatie, russische Verhandlungen zum Erhalt der Marinebasen, ukrainischer Damaskus-Besuch. Substanziell geht es um den *Akt des Engagements*; umstritten ist, ob er Syrien stabilisiert oder einen ehemaligen al-Qaida-Funktionaer legitimiert.',
 'The recognition trajectory is the most visible diplomatic axis of the post-Assad era. Arab capitals moved first (Saudi investment deals, Arab League re-engagement, Egypt-Turkey rapprochement on Syria). Western capitals followed with calibrated easing of sanctions and high-level visits. Russia negotiated base continuity. Ukraine made a symbolic security-talks visit. Israeli right and Iranian state media both frame the engagement as legitimising a designated terrorist organisation.',
 'Die Anerkennungstrajektorie ist die sichtbarste diplomatische Achse nach Assad. Arabische Hauptstaedte gingen voran (saudische Investitionen, Wiedereinbindung in die Arabische Liga, aegyptisch-tuerkische Annaeherung in Syrien-Fragen). Westliche Hauptstaedte folgten mit kalibrierter Sanktionslockerung und hochrangigen Besuchen. Russland verhandelt den Erhalt der Basen. Die Ukraine machte einen symbolischen Sicherheitsgespraech-Besuch. Israelische Rechte und iranische Staatsmedien rahmen das Engagement als Legitimation einer designierten terroristischen Organisation.',
 ARRAY['MIDEAST-LEVANT','MIDEAST-SAUDI','MIDEAST-GULF','MIDEAST-EGYPT','MIDEAST-TURKEY','AMERICAS-USA','EUROPE-UK','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-RUSSIA','EUROPE-UKRAINE','NON-STATE-EU'],
 'atomic', NULL, true, 34);

-- ============================================================
-- 2. fn_anchor bundles in taxonomy_v3
-- Each bundle follows FN_ANCHOR_VOCABULARY_SPEC.md:
--   Pillar 1: own-side actors (people, orgs, parties)
--   Pillar 2: sub-centroid geography (cities, regions, facilities)
--   Pillar 3: relevant systems / programs / operations / treaties
--   Pillar 4: domain actions (atomic verbs, concept nouns)
-- Latin-script collapse: identical-spelling tokens appear in EN only.
-- ============================================================

INSERT INTO taxonomy_v3 (item_raw, aliases, is_active, taxonomy_function, linked_id) VALUES

('syria_theater fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'Sharaa','Jolani','Jawlani','HTS','Hayat Tahrir al-Sham','SANA','Assad',
     'Syria','Damascus','Aleppo','Tartus','Khmeimim','Latakia','Homs',
     'transitional government','interim government','transitional authorities',
     'post-Assad','transition'),
   'de', jsonb_build_array(
     'Uebergangsregierung','Interimsregierung','syrische Uebergangsbehoerden',
     'Damaskus','Latakia'),
   'es', jsonb_build_array(
     'gobierno de transicion','gobierno interino','autoridades de transicion',
     'Damasco','Alepo'),
   'it', jsonb_build_array(
     'governo di transizione','governo ad interim','autorita di transizione',
     'Damasco'),
   'fr', jsonb_build_array(
     'gouvernement de transition','gouvernement interimaire','autorites de transition',
     'Damas','Alep'),
   'ru', jsonb_build_array(
     'Сирия','Дамаск','Алеппо','Тартус','Хмеймим','Латакия','Хомс',
     'аш-Шараа','аль-Джулани','ХТШ','Хайят Тахрир аш-Шам','Асад',
     'переходное правительство','временное правительство','переходные власти'),
   'hi', jsonb_build_array(
     'सीरिया','दमिश्क','अलेप्पो','अल-शराअ','जोलानी','एचटीएस',
     'संक्रमणकालीन सरकार','अंतरिम सरकार'),
   'zh', jsonb_build_array(
     '叙利亚','大马士革','阿勒颇','塔尔图斯','赫梅米姆','沙拉','朱拉尼',
     '沙姆解放组织','过渡政府','临时政府'),
   'ar', jsonb_build_array(
     'سوريا','سورية','دمشق','حلب','طرطوس','حميميم','اللاذقية','حمص',
     'الشرع','الجولاني','هيئة تحرير الشام','الأسد','سانا',
     'الحكومة الانتقالية','الحكومة المؤقتة','السلطات الانتقالية'),
   'ja', jsonb_build_array(
     'シリア','ダマスカス','アレッポ','タルトゥース','フメイミム',
     'シャラア','ジョラニ','HTS','過渡政府','暫定政府')
 ),
 true, 'fn_anchor', 'syria_theater'),

('syria_kurdish_question fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'SDF','YPG','YPJ','PKK','AANES','Mazloum','Asayish','Peshmerga',
     'Rojava','Hasaka','Hasakah','Qamishli','Raqqa','Kobani','Manbij','Deir ez-Zor',
     'Sheikh Maqsoud','Tal Rifaat','Ras al-Ayn','Tel Tamer',
     'Autonomous Administration','self-administration','Kurds','Kurdish',
     'federalism','federation','autonomy'),
   'de', jsonb_build_array(
     'Kurden','kurdisch','Selbstverwaltung','Autonome Verwaltung','Foederalismus',
     'Hasaka','Kamischli','Rakka','Kobane'),
   'es', jsonb_build_array(
     'kurdos','kurdo','autoadministracion','administracion autonoma','federalismo',
     'Hasaka','Qamishli'),
   'it', jsonb_build_array(
     'curdi','curdo','autogoverno','amministrazione autonoma','federalismo'),
   'fr', jsonb_build_array(
     'Kurdes','kurde','autoadministration','administration autonome','federalisme',
     'Hassaké','Kamechli','Raqqa'),
   'ru', jsonb_build_array(
     'СДС','YPG','РПК','курды','курдский','Рожава','самоуправление',
     'Хасеке','Камышлы','Ракка','Кобани','автономная администрация','федерализм'),
   'hi', jsonb_build_array(
     'कुर्द','कुर्दिश','एसडीएफ','वाईपीजी','पीकेके','स्वायत्त प्रशासन','स्वशासन'),
   'zh', jsonb_build_array(
     '库尔德','库尔德人','叙利亚民主军','SDF','YPG','人民保护部队','工人党','PKK',
     '罗贾瓦','哈塞克','卡米什利','拉卡','自治政府','联邦制'),
   'ar', jsonb_build_array(
     'قسد','قوات سوريا الديمقراطية','وحدات حماية الشعب','حزب العمال الكردستاني',
     'الإدارة الذاتية','الأكراد','الكردي','الكردية','روج آفا','الحسكة','القامشلي',
     'الرقة','عين العرب','منبج','دير الزور','الشيخ مقصود','تل رفعت','رأس العين',
     'الفيدرالية','الحكم الذاتي','مظلوم'),
   'ja', jsonb_build_array(
     'クルド','クルド人','シリア民主軍','SDF','YPG','PKK','ロジャヴァ',
     'ハサカ','カミシュリ','ラッカ','自治政府','連邦制')
 ),
 true, 'fn_anchor', 'syria_kurdish_question'),

('syria_israeli_strikes fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'IDF','Mossad','Israeli air force','Israeli army',
     'Damascus','Quneitra','Daraa','Suwayda','Mazzeh','T-4','Tiyas',
     'Golan','buffer zone',
     'airstrike','air strike','strike','strikes','bombing','raid','interception'),
   'de', jsonb_build_array(
     'Luftangriff','Angriff','Bombardierung','Razzia','Abfangen',
     'israelische Luftwaffe','israelische Armee','Pufferzone'),
   'es', jsonb_build_array(
     'ataque aereo','bombardeo','redada','intercepcion',
     'fuerza aerea israeli','ejercito israeli','zona de amortiguamiento'),
   'it', jsonb_build_array(
     'attacco aereo','raid','bombardamento','intercettazione',
     'aeronautica israeliana','esercito israeliano','zona cuscinetto'),
   'fr', jsonb_build_array(
     'frappe aerienne','frappe','bombardement','raid','interception',
     'armee de lair israelienne','armee israelienne','zone tampon'),
   'ru', jsonb_build_array(
     'удар','авиаудар','бомбардировка','рейд','перехват',
     'ЦАХАЛ','израильская армия','израильские ВВС','Голаны','буферная зона',
     'Дамаск','Кунейтра','Дераа','Эс-Сувейда','Мазза','Тияс'),
   'hi', jsonb_build_array(
     'हमला','हवाई हमला','बमबारी','छापा',
     'इज़राइली वायुसेना','आईडीएफ','गोलान','बफर ज़ोन'),
   'zh', jsonb_build_array(
     '袭击','空袭','轰炸','突袭','拦截',
     '以色列国防军','IDF','以色列空军','戈兰','缓冲区',
     '大马士革','库奈特拉','德拉','马泽','梯亚斯'),
   'ar', jsonb_build_array(
     'غارة','غارات','ضربة','ضربات','قصف','اعتراض',
     'جيش الدفاع الإسرائيلي','الجيش الإسرائيلي','الموساد','سلاح الجو الإسرائيلي',
     'دمشق','القنيطرة','درعا','السويداء','المزة','تي 4','تياس',
     'الجولان','المنطقة العازلة'),
   'ja', jsonb_build_array(
     '空爆','空襲','爆撃','襲撃','迎撃',
     'イスラエル軍','IDF','イスラエル空軍','ゴラン','緩衝地帯',
     'ダマスカス','クネイトラ','ダラア','スワイダ')
 ),
 true, 'fn_anchor', 'syria_israeli_strikes'),

('syria_counter_terror fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'ISIS','ISIL','Daesh','Islamic State','al-Qaeda','al-Qaida','Hurras al-Din',
     'Centcom','coalition','Operation Inherent Resolve',
     'al-Hol','al-Hawl','al-Roj','Hasaka prison','Ghweran',
     'Erbil','Conoco','Green Village','al-Tanf','Manbij',
     'detainees','detainee','prisoners','prison break','prison breakout',
     'counter-terrorism','counterterrorism','airstrike','raid','operation'),
   'de', jsonb_build_array(
     'IS','Daesh','Islamischer Staat','al-Qaida',
     'Anti-Terror','Terrorbekaempfung','Koalitionsschlaege','Razzia',
     'IS-Haeftlinge','Haeftlinge','Gefangenenausbruch'),
   'es', jsonb_build_array(
     'EI','Daesh','Estado Islamico','al-Qaeda',
     'antiterrorismo','contraterrorismo','coalicion','redada',
     'detenidos','prisioneros','fuga de prision'),
   'it', jsonb_build_array(
     'ISIS','Daesh','Stato Islamico','al-Qaeda',
     'antiterrorismo','coalizione','raid',
     'detenuti','prigionieri','evasione'),
   'fr', jsonb_build_array(
     'EI','Daech','Etat Islamique','al-Qaida',
     'antiterrorisme','contre-terrorisme','coalition','raid',
     'detenus','prisonniers','evasion'),
   'ru', jsonb_build_array(
     'ИГИЛ','ИГ','Даиш','Исламское государство','аль-Каида','Хуррас ад-Дин',
     'Центком','коалиция','операция Непоколебимая решимость',
     'аль-Холь','аль-Радж','тюрьма Хасаке','Эрбиль',
     'заключенные','задержанные','побег','контртерроризм','рейд'),
   'hi', jsonb_build_array(
     'आईएसआईएस','दाएश','इस्लामिक स्टेट','अल-कायदा',
     'गठबंधन','आतंकवाद विरोधी','कैदी','जेल से भागना'),
   'zh', jsonb_build_array(
     '伊斯兰国','ISIS','达伊沙','基地组织','哈拉斯丁',
     '中央司令部','联盟','坚定决心行动',
     '霍尔','哈塞克监狱','埃尔比勒',
     '被拘留者','囚犯','越狱','反恐','突袭'),
   'ar', jsonb_build_array(
     'داعش','تنظيم الدولة الإسلامية','تنظيم الدولة','القاعدة','حراس الدين',
     'القيادة المركزية الأمريكية','التحالف الدولي','عملية العزم الصلب',
     'الهول','الروج','سجن الحسكة','غويران','أربيل',
     'معتقلون','معتقلين','سجناء','تهريب من السجن','مكافحة الإرهاب','مداهمة'),
   'ja', jsonb_build_array(
     'イスラム国','ISIS','ダーイシュ','アルカイダ',
     '中央軍','有志連合','不動の決意作戦','アルホル','ハサカ刑務所','エルビル',
     '被拘禁者','囚人','脱獄','テロ対策','急襲')
 ),
 true, 'fn_anchor', 'syria_counter_terror'),

('syria_recognition_and_normalisation fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'Sharaa','Jolani','Jawlani','HTS','Hayat Tahrir al-Sham','SANA',
     'Damascus','Tartus','Khmeimim',
     'Arab League','GCC','transitional government','interim government',
     'terror list','terrorist designation',
     'normalisation','normalization','recognition','recognise','recognize',
     'sanctions','lifted','easing','relief','delisting',
     'reconstruction','investment','deal','agreement','talks','summit','visit',
     'delegation','embassy','ambassador','meeting','ties','restoring','restored'),
   'de', jsonb_build_array(
     'Normalisierung','Anerkennung','Sanktionen','Aufhebung','Lockerung','Streichung',
     'Wiederaufbau','Investitionen','Abkommen','Vereinbarung','Gespraeche','Gipfel',
     'Besuch','Delegation','Botschaft','Botschafter','Treffen','Beziehungen',
     'Wiederherstellung','Arabische Liga','Uebergangsregierung','Interimsregierung',
     'Terrorliste'),
   'es', jsonb_build_array(
     'normalizacion','reconocimiento','sanciones','levantamiento','flexibilizacion',
     'eliminacion de lista','reconstruccion','inversion','acuerdo','conversaciones',
     'cumbre','visita','delegacion','embajada','embajador','reunion','relaciones',
     'restablecimiento','Liga Arabe','gobierno de transicion','lista de terroristas'),
   'it', jsonb_build_array(
     'normalizzazione','riconoscimento','sanzioni','revoca','allentamento','rimozione',
     'ricostruzione','investimento','accordo','colloqui','vertice','visita',
     'delegazione','ambasciata','ambasciatore','incontro','relazioni','ripristino',
     'Lega Araba','governo di transizione','lista terroristi'),
   'fr', jsonb_build_array(
     'normalisation','reconnaissance','sanctions','levee','assouplissement','retrait',
     'reconstruction','investissement','accord','pourparlers','sommet','visite',
     'delegation','ambassade','ambassadeur','reunion','relations','retablissement',
     'Ligue arabe','gouvernement de transition','liste des terroristes'),
   'ru', jsonb_build_array(
     'аш-Шараа','аль-Джулани','ХТШ','Дамаск','Тартус','Хмеймим',
     'Лига арабских государств','переходное правительство','временное правительство',
     'нормализация','признание','санкции','снятие','ослабление','исключение из списка',
     'восстановление','инвестиции','соглашение','переговоры','саммит','визит',
     'делегация','посольство','посол','встреча','отношения','список террористов'),
   'hi', jsonb_build_array(
     'सामान्यीकरण','मान्यता','प्रतिबंध','हटाना','छूट','आतंकी सूची से हटाना',
     'पुनर्निर्माण','निवेश','समझौता','वार्ता','शिखर सम्मेलन','यात्रा','प्रतिनिधिमंडल',
     'दूतावास','राजदूत','बैठक','संबंध','अरब लीग','संक्रमणकालीन सरकार'),
   'zh', jsonb_build_array(
     '关系正常化','正常化','承认','制裁','解除','放松','除名','移除',
     '重建','投资','协议','会谈','峰会','访问','代表团','大使馆','大使','会晤',
     '关系','恢复','阿拉伯联盟','过渡政府','恐怖组织名单','沙拉','朱拉尼'),
   'ar', jsonb_build_array(
     'الشرع','الجولاني','هيئة تحرير الشام','دمشق','طرطوس','حميميم',
     'الجامعة العربية','مجلس التعاون الخليجي','الحكومة الانتقالية','الحكومة المؤقتة',
     'التطبيع','الاعتراف','العقوبات','رفع','تخفيف','إلغاء','شطب',
     'إعادة الإعمار','الاستثمار','اتفاق','اتفاقية','محادثات','قمة','زيارة',
     'وفد','سفارة','سفير','اجتماع','لقاء','العلاقات','استعادة','قائمة الإرهاب'),
   'ja', jsonb_build_array(
     'シャラア','ジョラニ','HTS','ダマスカス','タルトゥース',
     'アラブ連盟','過渡政府','暫定政府',
     '正常化','承認','制裁','解除','緩和','削除','テロリスト指定',
     '再建','投資','合意','協定','会談','首脳会談','訪問','代表団',
     '大使館','大使','会合','関係','回復')
 ),
 true, 'fn_anchor', 'syria_recognition_and_normalisation');

-- ============================================================
-- 3. Narratives (11 total: 3 theater-level + 2 per atomic FN)
-- Stance is toward the new Syrian (HTS-led) government.
-- ============================================================

-- ---------- 3a. Theater-level narratives (3) ----------

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('syria_legitimate_transition', 'syria_theater', 1, 2,
 'Legitimate transition', 'Legitimer Uebergang',
 'New Syrian government is a legitimate post-Assad transition',
 'Neue syrische Regierung ist ein legitimer Uebergang nach Assad',
 'Pro-engagement coverage frames the HTS-led transitional government under al-Sharaa as a legitimate post-Assad outcome. The vocabulary: "transitional government", "interim authorities", "inclusive process", "reform of HTS", "international community should engage", "sanctions relief is overdue", "reconstruction", "stabilisation". Prescription: recognise the transition, lift sanctions, fund reconstruction, integrate Syria into regional architecture (Arab League, GCC).',
 'Pro-Engagement-Berichterstattung rahmt die HTS-gefuehrte Uebergangsregierung unter al-Sharaa als legitimes Ergebnis nach Assad. Vokabular: "Uebergangsregierung", "Interimsbehoerden", "inklusiver Prozess", "Reform der HTS", "internationale Gemeinschaft sollte engagieren", "Sanktionen ueberfaellig aufheben", "Wiederaufbau", "Stabilisierung". Vorschrift: Uebergang anerkennen, Sanktionen aufheben, Wiederaufbau finanzieren, Syrien in die regionale Architektur integrieren.',
 ARRAY['MIDEAST-LEVANT','MIDEAST-TURKEY','MIDEAST-SAUDI','MIDEAST-GULF','MIDEAST-EGYPT'],
 ARRAY['Anadolu Agency','Daily Sabah','TRT World','Al Jazeera','Arab News','The National','Khaleej Times','Gulf News','Al-Ahram','Reuters','BBC World','Financial Times','Le Monde','Deutsche Welle'],
 ARRAY['transitional government','interim government','inclusive','reform','engagement','reconstruction','stabilisation','sanctions relief','recognition'],
 true),

('syria_jihadist_takeover_warning', 'syria_theater', 2, -2,
 'Jihadist takeover warning', 'Warnung vor jihadistischer Machtuebernahme',
 'HTS rule is rebranded al-Qaeda and a long-term security threat',
 'HTS-Herrschaft ist umbenannte al-Qaida und eine langfristige Sicherheitsbedrohung',
 'Pro-Israel, Iranian state, and Western conservative voices frame HTS rule substantively: al-Sharaa is a former al-Qaeda operative, the transition is cosmetic, sectarian violence against Alawites, Druze, and Christians is already underway, governance is fragile and ideologically extremist. Evidence: incidents in coastal Alawite communities, restrictions on minorities, jihadist factions within the HTS coalition. The vocabulary: "rebranded al-Qaeda", "sectarian cleansing", "minority massacre", "Alawite pogroms", "Druze under threat", "ISIS lite", "Trojan horse", "jihadist takeover". Prescription: maintain terrorist designation, withhold recognition, sanction sectarian actors, protect minorities.',
 'Pro-israelische, iranisch-staatliche und westlich-konservative Stimmen rahmen die HTS-Herrschaft substantiell: al-Sharaa ist ehemaliger al-Qaida-Funktionaer, der Uebergang kosmetisch, sektiererische Gewalt gegen Alawiten, Drusen und Christen laeuft bereits, die Regierungsfuehrung ist fragil und ideologisch extremistisch. Belege: Vorfaelle in alawitischen Kuestengemeinden, Einschraenkungen fuer Minderheiten, jihadistische Fraktionen innerhalb der HTS-Koalition. Vokabular: "umbenannte al-Qaida", "sektiererische Saeuberung", "Massaker an Minderheiten", "Alawiten-Pogrome", "Drusen unter Bedrohung", "ISIS light", "trojanisches Pferd", "jihadistische Machtuebernahme". Vorschrift: Terrordesignation beibehalten, Anerkennung vorenthalten, sektiererische Akteure sanktionieren, Minderheiten schuetzen.',
 ARRAY['MIDEAST-ISRAEL','MIDEAST-IRAN','AMERICAS-USA'],
 ARRAY['Jerusalem Post','Times of Israel','The Times of Israel','i24NEWS','Israel Hayom','Arutz Sheva','Ynetnews','Fox News','Press TV','Fars News','IRNA','Al Mayadeen'],
 ARRAY['rebranded al-Qaeda','sectarian','minority massacre','Alawite','Druze','Christians','jihadist','extremist','Trojan horse','ISIS lite','pogrom'],
 true),

('russia_iran_loss_lament', 'syria_theater', 3, -1,
 'Russia-Iran loss lament', 'Russland-Iran-Verlust-Lament',
 'Russia and Iran lament the loss of Syria as a multipolar setback',
 'Russland und Iran beklagen den Verlust Syriens als multipolaren Rueckschlag',
 'Russian and Iranian state media frame the fall of Assad and the rise of a Turkey- and West-aligned transitional government as a setback for the multipolar order. The vocabulary: "Western proxy", "Turkish-backed", "imperial restoration", "loss of resistance axis", "Tartus uncertainty", "Khmeimim future", "Iranian withdrawal". Prescription: preserve Russian basing through negotiation, maintain residual Iranian channels, frame transition as illegitimate Western-Turkish project.',
 'Russische und iranische Staatsmedien rahmen den Sturz Assads und den Aufstieg einer tuerkisch- und westlich-orientierten Uebergangsregierung als Rueckschlag fuer die multipolare Ordnung. Vokabular: "westlicher Stellvertreter", "tuerkisch gestuetzt", "imperiale Restauration", "Verlust der Widerstandsachse", "Tartus-Unsicherheit", "Khmeimim-Zukunft", "iranischer Rueckzug". Vorschrift: russische Basen durch Verhandlung erhalten, residuale iranische Kanaele halten, Uebergang als illegitimes westlich-tuerkisches Projekt rahmen.',
 ARRAY['EUROPE-RUSSIA','MIDEAST-IRAN'],
 ARRAY['RT','TASS (EN)','Press TV','Fars News','IRNA','Al Mayadeen','CGTN'],
 ARRAY['Western proxy','Turkish-backed','imperial','resistance axis','Tartus','Khmeimim','withdrawal','illegitimate'],
 true);

-- ---------- 3b. syria_kurdish_question narratives (2) ----------

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('damascus_territorial_reunification', 'syria_kurdish_question', 1, 2,
 'Reunify Syrian territory', 'Syrisches Territorium wiedervereinigen',
 'Damascus must restore central authority over all Syrian territory',
 'Damaskus muss zentrale Autoritaet ueber das gesamte syrische Territorium wiederherstellen',
 'Pro-Damascus and Turkish state framing: the new Syrian government must restore central authority over the northeast; the SDF is a separatist project backed by external powers (US, occasionally framed as Israeli/PKK collusion); Kurdish federalism would Balkanise Syria. The vocabulary: "territorial integrity", "national unity", "separatist", "PKK extension", "external sponsorship", "reunification", "Damascus authority". Prescription: SDF disarmament and absorption into national army, no federal carve-out, end of US partnership with SDF.',
 'Pro-Damaskus- und tuerkische Staatsrahmung: die neue syrische Regierung muss zentrale Autoritaet ueber den Nordosten wiederherstellen; die SDF ist ein separatistisches Projekt mit auslaendischer Rueckendeckung (USA, gelegentlich als israelisch/PKK-Kollusion gerahmt); kurdischer Foederalismus wuerde Syrien balkanisieren. Vokabular: "territoriale Integritaet", "nationale Einheit", "Separatist", "PKK-Ableger", "auslaendische Patenschaft", "Wiedervereinigung", "Damaskus-Autoritaet". Vorschrift: SDF-Entwaffnung und Aufnahme in nationale Armee, keine foederalistische Auskoppelung, Ende der US-Partnerschaft mit SDF.',
 ARRAY['MIDEAST-LEVANT','MIDEAST-TURKEY'],
 ARRAY['Anadolu Agency','Daily Sabah','TRT World','Al-Ahram','SANA','Hurriyet Daily News'],
 ARRAY['territorial integrity','national unity','separatist','PKK','reunification','sovereignty','central authority'],
 true),

('kurdish_self_administration', 'syria_kurdish_question', 2, -1,
 'Kurdish self-administration is legitimate', 'Kurdische Selbstverwaltung ist legitim',
 'Kurdish self-administration is a legitimate democratic experiment to be protected',
 'Kurdische Selbstverwaltung ist ein legitimes demokratisches Experiment, das geschuetzt werden muss',
 'Western mainstream, Israeli, and parts of Arab coverage frame the SDF-led Autonomous Administration of North and East Syria (AANES) as a multi-ethnic democratic experiment that fought ISIS, jails 10,000+ detainees on behalf of the international community, and deserves protection from Turkish and Damascus pressure. The vocabulary: "Rojava model", "multi-ethnic", "democratic experiment", "ISIS jailers", "Kurdish-led", "self-administration", "federal solution", "minority protection". Prescription: maintain US partnership, prevent Turkish operations, condition Damascus normalisation on Kurdish rights, support federal arrangement.',
 'Westliche Mainstream-, israelische und Teile der arabischen Berichterstattung rahmen die SDF-gefuehrte Autonome Verwaltung Nord- und Ostsyriens (AANES) als multiethnisches demokratisches Experiment, das den IS bekaempfte, ueber 10.000 Haeftlinge fuer die internationale Gemeinschaft verwahrt und Schutz vor tuerkischem und Damaszener Druck verdient. Vokabular: "Rojava-Modell", "multiethnisch", "demokratisches Experiment", "IS-Waechter", "kurdisch gefuehrt", "Selbstverwaltung", "foederalistische Loesung", "Minderheitenschutz". Vorschrift: US-Partnerschaft erhalten, tuerkische Operationen verhindern, Normalisierung Damaskus an kurdische Rechte knuepfen, foederalistische Loesung unterstuetzen.',
 ARRAY['AMERICAS-USA','EUROPE-FRANCE','EUROPE-UK','EUROPE-GERMANY','MIDEAST-ISRAEL','NON-STATE-EU'],
 ARRAY['Al Jazeera','France 24 (EN)','BBC World','Deutsche Welle','Reuters','Wall Street Journal','Haaretz','The Times of Israel','The Guardian','Le Monde','Associated Press'],
 ARRAY['Rojava','multi-ethnic','democratic','ISIS jailers','self-administration','federalism','autonomy','Kurdish rights','minority protection'],
 true);

-- ---------- 3c. syria_israeli_strikes narratives (2) ----------

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('israeli_strikes_on_syria_legitimate', 'syria_israeli_strikes', 1, -1,
 'Israeli strikes are legitimate self-defense', 'Israelische Schlaege sind legitime Selbstverteidigung',
 'Israeli strikes on Syria are legitimate preventive defense',
 'Israelische Schlaege gegen Syrien sind legitime Praevention',
 'Israeli sources frame strikes inside Syria as legitimate preventive defense: residual Hezbollah logistics and Iranian assets in southern Syria remain a threat; the new transitional government inherits the security obligation; Golan-adjacent buffer-zone enforcement is a non-negotiable Israeli security perimeter. The vocabulary: "preventive defense", "Iranian assets", "Hezbollah logistics", "buffer zone enforcement", "Golan security perimeter", "weapons transfer interdiction". Prescription: continue strikes until threat capability is degraded, maintain buffer zone, condition relations with Damascus on Israeli security demands.',
 'Israelische Quellen rahmen Schlaege in Syrien als legitime Praevention: verbliebene Hisbollah-Logistik und iranische Assets im Sueden Syriens bleiben eine Bedrohung; die neue Uebergangsregierung uebernimmt die Sicherheitsverpflichtung; die Durchsetzung der Golan-Pufferzone ist ein nicht verhandelbarer israelischer Sicherheitsperimeter. Vokabular: "Praevention", "iranische Assets", "Hisbollah-Logistik", "Pufferzonen-Durchsetzung", "Golan-Sicherheitsperimeter", "Unterbindung von Waffentransfers". Vorschrift: Schlaege fortsetzen, bis Bedrohungs-Kapazitaet abgebaut ist, Pufferzone aufrechterhalten, Beziehungen mit Damaskus an israelische Sicherheitsforderungen knuepfen.',
 ARRAY['MIDEAST-ISRAEL','AMERICAS-USA'],
 ARRAY['Jerusalem Post','Times of Israel','The Times of Israel','i24NEWS','Israel Hayom','Arutz Sheva','Ynetnews','Fox News'],
 ARRAY['preventive defense','Iranian assets','Hezbollah logistics','buffer zone','Golan','weapons transfer','self-defense'],
 true),

('syrian_sovereignty_under_israeli_aggression', 'syria_israeli_strikes', 2, 2,
 'Defend Syrian sovereignty', 'Syrische Souveraenitaet verteidigen',
 'Israeli strikes violate Syrian sovereignty and undermine the transition',
 'Israelische Schlaege verletzen syrische Souveraenitaet und untergraben den Uebergang',
 'Pan-Arab, Iranian, Turkish, and post-Assad Syrian state coverage frames Israeli strikes on Syrian territory as aggression that violates Syrian sovereignty and undermines the legitimate transition. The buffer zone south of Damascus is framed as illegal occupation. The vocabulary: "Israeli aggression", "sovereignty violation", "illegal occupation", "buffer zone occupation", "international law", "UN Charter Article 2", "Syrian airspace violation". Prescription: end Israeli strikes, withdraw from buffer zone, condition any Syrian-Israeli engagement on Israeli compliance with international law.',
 'Panarabische, iranische, tuerkische und nach-Assad-syrische Staatsberichterstattung rahmt israelische Schlaege auf syrisches Territorium als Aggression, die syrische Souveraenitaet verletzt und den legitimen Uebergang untergraebt. Die Pufferzone suedlich von Damaskus gilt als illegale Besatzung. Vokabular: "israelische Aggression", "Verletzung der Souveraenitaet", "illegale Besatzung", "Besetzung der Pufferzone", "Voelkerrecht", "UN-Charta Artikel 2", "Verletzung syrischen Luftraums". Vorschrift: israelische Schlaege beenden, aus der Pufferzone abziehen, jedes syrisch-israelische Engagement an israelische Voelkerrechtskonformitaet knuepfen.',
 ARRAY['MIDEAST-LEVANT','MIDEAST-IRAN','MIDEAST-TURKEY','MIDEAST-GULF'],
 ARRAY['SANA','Al Jazeera','Anadolu Agency','TRT World','Daily Sabah','Press TV','Al Mayadeen','Fars News','IRNA'],
 ARRAY['Israeli aggression','sovereignty violation','illegal occupation','buffer zone','international law','UN Charter','airspace violation'],
 true);

-- ---------- 3d. syria_counter_terror narratives (2) ----------

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('coalition_counter_isis_necessary', 'syria_counter_terror', 1, 0,
 'Coalition counter-ISIS presence is necessary', 'Anti-IS-Praesenz der Koalition ist notwendig',
 'Coalition counter-ISIS operations are necessary until ISIS threat is contained',
 'Anti-IS-Operationen der Koalition sind notwendig, bis die IS-Bedrohung eingedaemmt ist',
 'Western mainstream and Israeli framing: US, UK, French, and Italian forces in Syria and Iraq remain necessary to contain ISIS residue. SDF custody of ~10,000 ISIS detainees at al-Hol, al-Roj, and Hasaka prisons carries severe prison-break risk; the transitional government lacks capacity to take over; sustained coalition presence is the prudent option. The vocabulary: "ISIS resurgence risk", "prison-break risk", "detainee custody", "coalition mandate", "Inherent Resolve continuation", "Erbil base". Prescription: maintain coalition presence, continue strikes, condition detainee transfers on receiving-country capacity.',
 'Westliche Mainstream- und israelische Rahmung: US-, britische, franzoesische und italienische Kraefte in Syrien und Irak bleiben noetig, um IS-Reste einzudaemmen. SDF-Verwahrung von rund 10.000 IS-Haeftlingen in al-Hol, al-Roj und Hasaka-Gefaengnis birgt schweres Ausbruchsrisiko; der Uebergangsregierung fehlt die Kapazitaet zur Uebernahme; anhaltende Koalitionspraesenz ist die vorsichtige Option. Vokabular: "IS-Wiedererstarken", "Ausbruchsrisiko", "Haeftlingsverwahrung", "Koalitionsmandat", "Inherent Resolve fortsetzen", "Erbil-Stuetzpunkt". Vorschrift: Koalitionspraesenz aufrechterhalten, Schlaege fortsetzen, Haeftlingsverlegungen an Kapazitaet der Empfaengerstaaten knuepfen.',
 ARRAY['AMERICAS-USA','EUROPE-UK','EUROPE-FRANCE','MIDEAST-ISRAEL'],
 ARRAY['Reuters','Associated Press','BBC World','France 24 (EN)','Jerusalem Post','Fox News','Wall Street Journal','CNN','NPR','Deutsche Welle'],
 ARRAY['ISIS resurgence','prison-break','detainee custody','coalition mandate','Inherent Resolve','Erbil','counter-terrorism'],
 true),

('foreign_military_withdrawal_demand', 'syria_counter_terror', 2, 1,
 'Foreign forces should leave Syria', 'Auslaendische Truppen sollten Syrien verlassen',
 'Foreign military presence violates sovereignty and should withdraw',
 'Auslaendische Militaerpraesenz verletzt Souveraenitaet und sollte abgezogen werden',
 'Russian, Iranian, Turkish, and post-Assad Syrian framing: Western military presence in Syria violates Syrian sovereignty; counter-ISIS operations should transfer to the new Syrian government and Iraqi authorities; ISIS detainees should be transferred to national jurisdictions; the coalition mandate has outlived its purpose. The vocabulary: "foreign occupation", "sovereignty violation", "withdrawal", "national jurisdiction", "transfer of responsibility", "mandate expired". Prescription: full coalition withdrawal, transfer of detainees, end of US-SDF partnership, Syrian forces assume counter-terrorism responsibility.',
 'Russische, iranische, tuerkische und nach-Assad-syrische Rahmung: westliche Militaerpraesenz in Syrien verletzt die syrische Souveraenitaet; Anti-IS-Operationen sollten an die neue syrische Regierung und irakische Behoerden uebergehen; IS-Haeftlinge sollten an nationale Jurisdiktionen uebergeben werden; das Koalitionsmandat ist ueberholt. Vokabular: "auslaendische Besatzung", "Souveraenitaetsverletzung", "Abzug", "nationale Jurisdiktion", "Uebertragung der Verantwortung", "Mandat abgelaufen". Vorschrift: vollstaendiger Abzug der Koalition, Uebergabe der Haeftlinge, Ende der US-SDF-Partnerschaft, syrische Kraefte uebernehmen Anti-Terror-Verantwortung.',
 ARRAY['EUROPE-RUSSIA','MIDEAST-IRAN','MIDEAST-TURKEY','MIDEAST-LEVANT'],
 ARRAY['SANA','Anadolu Agency','TRT World','Press TV','Fars News','IRNA','TASS (EN)','RT','Al Mayadeen'],
 ARRAY['foreign occupation','sovereignty violation','withdrawal','national jurisdiction','mandate expired','transfer responsibility'],
 true);

-- ---------- 3e. syria_recognition_and_normalisation narratives (2) ----------

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('international_engagement_pragmatic', 'syria_recognition_and_normalisation', 1, 2,
 'International engagement is pragmatic and stabilising', 'Internationales Engagement ist pragmatisch und stabilisierend',
 'Arab, Western, and Russia/Ukraine engagement with Damascus is pragmatic stabilisation',
 'Arabisches, westliches und russisch-ukrainisches Engagement mit Damaskus ist pragmatische Stabilisierung',
 'Arab capitals (Saudi, Gulf, Egypt) moved first with investment and recognition trajectories; Western capitals followed with calibrated sanctions easing and high-level visits; Russia negotiates base continuity; Ukraine made a symbolic security-talks visit. The shared logic: realism over purity tests, pull Syria out of the Iranian orbit, fund reconstruction, stabilise the Levant. The vocabulary: "pragmatic engagement", "calibrated sanctions relief", "reconstruction needs", "regional stabilisation", "post-conflict reintegration", "diplomatic realism". Prescription: continue calibrated engagement, condition relief on reform milestones, fund reconstruction, maintain dialogue.',
 'Arabische Hauptstaedte (Saudi-Arabien, Golf, Aegypten) gingen mit Investitions- und Anerkennungstrajektorien voran; westliche Hauptstaedte folgten mit kalibrierter Sanktionslockerung und hochrangigen Besuchen; Russland verhandelt den Erhalt der Basen; die Ukraine machte einen symbolischen Sicherheitsgespraech-Besuch. Gemeinsame Logik: Realismus statt Reinheitstest, Syrien aus dem iranischen Orbit ziehen, Wiederaufbau finanzieren, Levante stabilisieren. Vokabular: "pragmatisches Engagement", "kalibrierte Sanktionslockerung", "Wiederaufbau-Bedarf", "regionale Stabilisierung", "Nachkriegs-Reintegration", "diplomatischer Realismus". Vorschrift: kalibriertes Engagement fortsetzen, Lockerung an Reformfortschritt knuepfen, Wiederaufbau finanzieren, Dialog aufrechterhalten.',
 ARRAY['MIDEAST-SAUDI','MIDEAST-GULF','MIDEAST-EGYPT','MIDEAST-TURKEY','AMERICAS-USA','EUROPE-UK','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-RUSSIA','EUROPE-UKRAINE'],
 ARRAY['Arab News','The National','Khaleej Times','Gulf News','Al-Ahram','Anadolu Agency','Daily Sabah','Reuters','BBC World','Financial Times','Le Monde','Tagesschau','Deutsche Welle','Associated Press','Euronews','Sky News','TASS (EN)'],
 ARRAY['pragmatic','calibrated','sanctions relief','reconstruction','stabilisation','reintegration','realism','engagement','dialogue'],
 true),

('recognition_legitimises_jihadists', 'syria_recognition_and_normalisation', 2, -2,
 'Recognition legitimises a jihadist government', 'Anerkennung legitimiert eine jihadistische Regierung',
 'International recognition whitewashes a former al-Qaeda operative',
 'Internationale Anerkennung weisst einen ehemaligen al-Qaida-Funktionaer rein',
 'Israeli right, Iranian state media, and Western conservative voices frame each act of engagement — Saudi investment deals, sanctions relief, head-of-state meetings with al-Sharaa, Russian base preservation, Ukrainian Damascus visit — as whitewashing a former al-Qaeda operative and rewarding extremism. The image of world leaders shaking the hand of a designated terrorist is itself the harm. The vocabulary: "whitewash", "rebranded al-Qaeda", "rewarding extremism", "legitimising terror", "moral surrender", "appeasement", "terror list mistake". Prescription: maintain terrorist designation, halt sanctions relief, refuse high-level engagement, sanction enablers.',
 'Israelische Rechte, iranische Staatsmedien und westlich-konservative Stimmen rahmen jeden Akt des Engagements — saudische Investitionsdeals, Sanktionslockerung, Treffen von Staatschefs mit al-Sharaa, russische Basen-Erhaltung, ukrainischer Damaskus-Besuch — als Reinwaschung eines ehemaligen al-Qaida-Funktionaers und Belohnung von Extremismus. Das Bild von Weltfuehrern, die einem designierten Terroristen die Hand schuetteln, ist selbst der Schaden. Vokabular: "Reinwaschung", "umbenannte al-Qaida", "Belohnung von Extremismus", "Legitimation des Terrors", "moralische Kapitulation", "Beschwichtigung", "Terrorlisten-Fehler". Vorschrift: Terrordesignation beibehalten, Sanktionslockerung stoppen, hochrangiges Engagement verweigern, Ermoeglicher sanktionieren.',
 ARRAY['MIDEAST-ISRAEL','MIDEAST-IRAN','AMERICAS-USA'],
 ARRAY['Jerusalem Post','Times of Israel','The Times of Israel','i24NEWS','Israel Hayom','Arutz Sheva','Ynetnews','Fox News','Press TV','Fars News','IRNA','Al Mayadeen'],
 ARRAY['whitewash','rebranded al-Qaeda','rewarding extremism','legitimising','appeasement','terror designation','moral surrender'],
 true);

-- ============================================================
-- 4. Sanity check before commit
-- ============================================================

DO $$
DECLARE
    n_fn integer; n_nar integer; n_anchor integer;
BEGIN
    SELECT COUNT(*) INTO n_fn FROM friction_nodes WHERE id IN
        ('syria_theater','syria_kurdish_question','syria_israeli_strikes',
         'syria_counter_terror','syria_recognition_and_normalisation');
    SELECT COUNT(*) INTO n_nar FROM narratives_v2 WHERE fn_id IN
        ('syria_theater','syria_kurdish_question','syria_israeli_strikes',
         'syria_counter_terror','syria_recognition_and_normalisation');
    SELECT COUNT(*) INTO n_anchor FROM taxonomy_v3
        WHERE taxonomy_function = 'fn_anchor' AND linked_id IN
        ('syria_theater','syria_kurdish_question','syria_israeli_strikes',
         'syria_counter_terror','syria_recognition_and_normalisation');
    IF n_fn <> 5 OR n_nar <> 11 OR n_anchor <> 5 THEN
        RAISE EXCEPTION 'Syria theater sanity check failed: friction_nodes=%, narratives=%, fn_anchors=% (expected 5/11/5)',
            n_fn, n_nar, n_anchor;
    END IF;
END $$;

COMMIT;
