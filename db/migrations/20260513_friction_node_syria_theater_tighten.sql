-- Syria theater tightening — fixes over-attribution from initial seed.
-- 2026-05-13
--
-- Two systemic issues with the seed migration:
--   1. Atomic FN centroid_ids included home centroids of engaging actors
--      (USA, UK, France, Russia, Ukraine, Germany, etc.). This caused
--      every diplomatic-verb story IN those countries to pass the gate.
--      Foreign engagers belong in narrative publisher cohorts, NOT in
--      friction_nodes.centroid_ids — which must be the FN's geographic
--      conflict surface.
--   2. Atomic FN anchors carried generic Pillar-4 verbs (strike, raid,
--      operation, visit, talks, deal, summit) that match unrelated news
--      under broad centroid scope.
--
-- Fix:
--   - Narrow atomic FN centroid_ids to the actual conflict geography.
--   - Drop generic Pillar-4 verbs from atomic FN anchors. Keep them on
--     the theater bundle where the geographic gate is via specific
--     own-side actor names (Sharaa, Jolani, HTS, Damascus).
--   - Theater centroid_ids stays broad because its anchor is precise
--     (own-side names only, no generic verbs).

BEGIN;

-- ============================================================
-- 1. Narrow atomic FN centroid_ids to conflict geography
-- ============================================================

UPDATE friction_nodes SET centroid_ids = ARRAY['MIDEAST-LEVANT','MIDEAST-IRAQ']
WHERE id = 'syria_kurdish_question';

UPDATE friction_nodes SET centroid_ids = ARRAY['MIDEAST-LEVANT']
WHERE id = 'syria_israeli_strikes';

UPDATE friction_nodes SET centroid_ids = ARRAY['MIDEAST-LEVANT','MIDEAST-IRAQ']
WHERE id = 'syria_counter_terror';

UPDATE friction_nodes SET centroid_ids = ARRAY['MIDEAST-LEVANT']
WHERE id = 'syria_recognition_and_normalisation';

-- Theater stays broad — its anchor is precise enough
-- (Sharaa, Jolani, HTS, Damascus, Tartus, Khmeimim — all own-side names).

-- ============================================================
-- 2. Tighten anchors — drop generic Pillar-4 verbs
-- ============================================================

-- syria_kurdish_question — drop generic verbs, keep only own-side actors + geography + programs
UPDATE taxonomy_v3 SET aliases = jsonb_build_object(
   'en', jsonb_build_array(
     'SDF','YPG','YPJ','PKK','AANES','Mazloum','Asayish','Peshmerga',
     'Rojava','Hasaka','Hasakah','Qamishli','Raqqa','Kobani','Manbij','Deir ez-Zor',
     'Sheikh Maqsoud','Tal Rifaat','Ras al-Ayn','Tel Tamer',
     'Autonomous Administration','self-administration','Kurds','Kurdish'),
   'de', jsonb_build_array(
     'Kurden','kurdisch','Selbstverwaltung','Autonome Verwaltung',
     'Hasaka','Kamischli','Rakka','Kobane'),
   'es', jsonb_build_array(
     'kurdos','kurdo','autoadministracion','administracion autonoma',
     'Hasaka','Qamishli'),
   'it', jsonb_build_array(
     'curdi','curdo','autogoverno','amministrazione autonoma'),
   'fr', jsonb_build_array(
     'Kurdes','kurde','autoadministration','administration autonome',
     'Hassake','Kamechli'),
   'ru', jsonb_build_array(
     'СДС','YPG','РПК','курды','курдский','Рожава','самоуправление',
     'Хасеке','Камышлы','Ракка','Кобани','автономная администрация'),
   'hi', jsonb_build_array(
     'कुर्द','कुर्दिश','एसडीएफ','वाईपीजी','पीकेके','स्वायत्त प्रशासन'),
   'zh', jsonb_build_array(
     '库尔德','库尔德人','叙利亚民主军','SDF','YPG','人民保护部队','工人党','PKK',
     '罗贾瓦','哈塞克','卡米什利','拉卡','自治政府'),
   'ar', jsonb_build_array(
     'قسد','قوات سوريا الديمقراطية','وحدات حماية الشعب','حزب العمال الكردستاني',
     'الإدارة الذاتية','الأكراد','الكردي','الكردية','روج آفا','الحسكة','القامشلي',
     'الرقة','عين العرب','منبج','دير الزور','الشيخ مقصود','تل رفعت','رأس العين',
     'الحكم الذاتي','مظلوم'),
   'ja', jsonb_build_array(
     'クルド','クルド人','シリア民主軍','SDF','YPG','PKK','ロジャヴァ',
     'ハサカ','カミシュリ','ラッカ','自治政府')
)
WHERE taxonomy_function='fn_anchor' AND linked_id='syria_kurdish_question';

-- syria_israeli_strikes — keep only Syria-specific geography + IDF + targeted-site names
-- Drop generic "strike, airstrike, raid, bombing, interception" — they catch every Israeli op everywhere.
-- Damascus + Quneitra + buffer zone + Mazzeh + Golan are Syria-specific enough.
UPDATE taxonomy_v3 SET aliases = jsonb_build_object(
   'en', jsonb_build_array(
     'Quneitra','Daraa','Suwayda','Mazzeh','Tiyas','T-4',
     'Golan buffer','buffer zone','Mount Hermon','UNDOF',
     'Syrian air defense','Syrian air defence','Syrian army positions'),
   'de', jsonb_build_array(
     'Pufferzone Golan','Golan-Pufferzone','syrische Luftabwehr','syrische Armeestellungen'),
   'es', jsonb_build_array(
     'zona de amortiguamiento Golan','defensa aerea siria'),
   'it', jsonb_build_array(
     'zona cuscinetto Golan','difesa aerea siriana'),
   'fr', jsonb_build_array(
     'zone tampon Golan','defense aerienne syrienne'),
   'ru', jsonb_build_array(
     'Кунейтра','Дераа','Эс-Сувейда','Мазза','Тияс','буферная зона Голаны',
     'сирийская ПВО','сирийские военные позиции'),
   'hi', jsonb_build_array(
     'गोलान बफर ज़ोन','कुनैत्रा','सीरियाई वायु रक्षा'),
   'zh', jsonb_build_array(
     '库奈特拉','德拉','斯威达','马泽','梯亚斯','戈兰缓冲区','叙利亚防空','UNDOF'),
   'ar', jsonb_build_array(
     'القنيطرة','درعا','السويداء','المزة','تي 4','تياس',
     'المنطقة العازلة الجولان','جبل الشيخ','الدفاع الجوي السوري','مواقع الجيش السوري',
     'يوندوف'),
   'ja', jsonb_build_array(
     'クネイトラ','ダラア','スワイダ','マゼ','ティヤス','ゴラン緩衝地帯',
     'シリア防空','シリア軍陣地','UNDOF')
)
WHERE taxonomy_function='fn_anchor' AND linked_id='syria_israeli_strikes';

-- syria_counter_terror — drop "operation, raid, airstrike, counter-terrorism" generic verbs.
-- Keep only ISIS / Daesh / specific facilities / specific operations.
UPDATE taxonomy_v3 SET aliases = jsonb_build_object(
   'en', jsonb_build_array(
     'ISIS','ISIL','Daesh','Islamic State','al-Qaeda','al-Qaida','Hurras al-Din',
     'Operation Inherent Resolve','Centcom','CJTF-OIR',
     'al-Hol','al-Hawl','al-Roj','Hasaka prison','Ghweran',
     'Conoco','Green Village','al-Tanf','Tower 22',
     'ISIS detainees','ISIS prisoners','ISIS fighters','ISIS leader','ISIS cell'),
   'de', jsonb_build_array(
     'IS','Daesh','Islamischer Staat','al-Qaida','IS-Haeftlinge','IS-Gefangene','IS-Fuehrer','IS-Zelle'),
   'es', jsonb_build_array(
     'EI','Estado Islamico','al-Qaeda','detenidos del EI','combatientes del EI'),
   'it', jsonb_build_array(
     'Stato Islamico','al-Qaeda','detenuti dell ISIS','combattenti dell ISIS'),
   'fr', jsonb_build_array(
     'EI','Etat Islamique','al-Qaida','detenus de l EI','combattants de l EI'),
   'ru', jsonb_build_array(
     'ИГИЛ','ИГ','Даиш','Исламское государство','аль-Каида','Хуррас ад-Дин',
     'операция Непоколебимая решимость','Центком',
     'аль-Холь','аль-Радж','тюрьма Хасаке','Эрбиль',
     'заключенные ИГИЛ','боевики ИГИЛ','главарь ИГИЛ'),
   'hi', jsonb_build_array(
     'आईएसआईएस','दाएश','इस्लामिक स्टेट','अल-कायदा','आईएसआईएस कैदी'),
   'zh', jsonb_build_array(
     '伊斯兰国','ISIS','达伊沙','基地组织','哈拉斯丁',
     '坚定决心行动','中央司令部','霍尔','哈塞克监狱','埃尔比勒',
     'ISIS被拘留者','ISIS战士','ISIS头目'),
   'ar', jsonb_build_array(
     'داعش','تنظيم الدولة الإسلامية','تنظيم الدولة','القاعدة','حراس الدين',
     'عملية العزم الصلب','القيادة المركزية الأمريكية','التحالف الدولي',
     'الهول','الروج','سجن الحسكة','غويران','أربيل',
     'معتقلو داعش','مقاتلو داعش','زعيم داعش','خلية داعش'),
   'ja', jsonb_build_array(
     'イスラム国','ISIS','ダーイシュ','アルカイダ',
     '不動の決意作戦','中央軍','有志連合','アルホル','ハサカ刑務所','エルビル',
     'ISIS被拘禁者','ISIS戦闘員','ISIS指導者')
)
WHERE taxonomy_function='fn_anchor' AND linked_id='syria_counter_terror';

-- syria_recognition_and_normalisation — drop generic diplomatic verbs.
-- Keep: own-side names (Sharaa, Jolani, HTS, SANA, Damascus, Tartus, Khmeimim),
-- recognition-specific concept terms (normalisation, recognition, sanctions relief,
-- delisting, terror list, terrorist designation), and recognition-domain orgs (Arab League, GCC).
-- Drop everything that matches generic diplomatic stories anywhere
-- (talks, summit, visit, delegation, agreement, deal, meeting, ties, restoring).
UPDATE taxonomy_v3 SET aliases = jsonb_build_object(
   'en', jsonb_build_array(
     'Sharaa','Jolani','Jawlani','HTS','Hayat Tahrir al-Sham','SANA',
     'Damascus','Tartus','Khmeimim',
     'Arab League','GCC',
     'normalisation','normalization','recognition',
     'sanctions relief','sanctions easing','sanctions lifted','delisting',
     'terror list','terrorist designation',
     'transitional government','interim government','transitional authorities'),
   'de', jsonb_build_array(
     'Normalisierung','Anerkennung','Sanktionen Aufhebung','Sanktionen Lockerung',
     'Terrorliste','Terrordesignation','Streichung von der Liste',
     'Arabische Liga','Uebergangsregierung','Interimsregierung'),
   'es', jsonb_build_array(
     'normalizacion','reconocimiento','levantamiento de sanciones','flexibilizacion de sanciones',
     'lista de terroristas','designacion terrorista','eliminacion de lista',
     'Liga Arabe','gobierno de transicion','gobierno interino'),
   'it', jsonb_build_array(
     'normalizzazione','riconoscimento','revoca delle sanzioni','allentamento delle sanzioni',
     'lista terroristi','designazione terrorista','rimozione dalla lista',
     'Lega Araba','governo di transizione','governo ad interim'),
   'fr', jsonb_build_array(
     'normalisation','reconnaissance','levee des sanctions','assouplissement des sanctions',
     'liste des terroristes','designation terroriste','retrait de la liste',
     'Ligue arabe','gouvernement de transition','gouvernement interimaire'),
   'ru', jsonb_build_array(
     'аш-Шараа','аль-Джулани','ХТШ','Дамаск','Тартус','Хмеймим',
     'Лига арабских государств','переходное правительство','временное правительство',
     'нормализация','признание','снятие санкций','ослабление санкций',
     'исключение из списка террористов','список террористов'),
   'hi', jsonb_build_array(
     'सामान्यीकरण','मान्यता','प्रतिबंध हटाना','प्रतिबंधों में छूट',
     'आतंकी सूची से हटाना','आतंकी सूची','अरब लीग','संक्रमणकालीन सरकार'),
   'zh', jsonb_build_array(
     '关系正常化','正常化','承认','解除制裁','放松制裁','除名','移除',
     '阿拉伯联盟','过渡政府','临时政府','恐怖组织名单','沙拉','朱拉尼'),
   'ar', jsonb_build_array(
     'الشرع','الجولاني','هيئة تحرير الشام','دمشق','طرطوس','حميميم',
     'الجامعة العربية','مجلس التعاون الخليجي','الحكومة الانتقالية','الحكومة المؤقتة',
     'التطبيع','الاعتراف','رفع العقوبات','تخفيف العقوبات','إلغاء العقوبات',
     'شطب من قائمة الإرهاب','قائمة الإرهاب','تصنيف إرهابي'),
   'ja', jsonb_build_array(
     'シャラア','ジョラニ','HTS','ダマスカス','タルトゥース',
     'アラブ連盟','過渡政府','暫定政府',
     '正常化','承認','制裁解除','制裁緩和','テロリスト指定','テロリスト名簿',
     '名簿からの削除')
)
WHERE taxonomy_function='fn_anchor' AND linked_id='syria_recognition_and_normalisation';

COMMIT;
