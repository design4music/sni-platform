-- Syria theater iteration 2 — anchor tightening + theater intro rewrite.
-- 2026-05-13
--
-- User-reported precision failures after iteration 1:
--   1. russia_iran_loss_lament: every top title irrelevant — root cause
--      `Assad` (5 chars) matches `ambASSADor`, attaching every Russian and
--      Iranian diplomatic story to a Syria narrative.
--   2. syria_legitimate_transition picked up "Lufthansa strike cancels
--      hundreds of flights..." — root cause `HTS` (3 chars) matches
--      `fligHTS`, `rigHTS`, `thougHTS`, etc.
--   3. syria_counter_terror is dominated by Israel-Lebanon strikes — root
--      cause Latin-script 2-char anchors:
--        de:"IS"  matches "ISraeli", "thIS", "is"
--        es:"EI"  matches "thEIr", "EIght"
--        fr:"EI"  same
--        ru:"ИГ"  matches Russian common words
--   4. syria_israeli_strikes leaks Israel-Lebanon strikes — generic
--      phrases ("Israeli strike", "Israeli strikes", "buffer zone")
--      catch every Israeli operation on the northern front. Anchor needs
--      to require Syria-specific geography.
--   5. syria_recognition_and_normalisation leaks Lebanon stories — generic
--      concept words ("normalisation", "recognition", "Arab League",
--      "sanctions relief") catch Lebanon-Israel normalisation, EU
--      sanctions stories, etc.

BEGIN;

-- ============================================================
-- 1. syria_theater anchor — drop Assad (collides with ambassador),
--    drop HTS (collides with flights/rights), drop bare "transition"
-- ============================================================

UPDATE taxonomy_v3 SET aliases = jsonb_build_object(
   'en', jsonb_build_array(
     'Sharaa','Jolani','Jawlani','Hayat Tahrir al-Sham','SANA',
     'al-Assad','Bashar al-Assad','Bashar',
     'Syria','Damascus','Aleppo','Tartus','Khmeimim','Latakia','Homs',
     'transitional government','interim government','transitional authorities',
     'post-Assad'),
   'de', jsonb_build_array(
     'Uebergangsregierung','Interimsregierung','syrische Uebergangsbehoerden',
     'Damaskus','Latakia','al-Assad','Baschar al-Assad'),
   'es', jsonb_build_array(
     'gobierno de transicion','gobierno interino','autoridades de transicion',
     'Damasco','Alepo','al-Assad','Bashar al-Assad'),
   'it', jsonb_build_array(
     'governo di transizione','governo ad interim','autorita di transizione',
     'Damasco','al-Assad','Bashar al-Assad'),
   'fr', jsonb_build_array(
     'gouvernement de transition','gouvernement interimaire','autorites de transition',
     'Damas','Alep','al-Assad','Bachar al-Assad'),
   'ru', jsonb_build_array(
     'Сирия','Дамаск','Алеппо','Тартус','Хмеймим','Латакия','Хомс',
     'аш-Шараа','аль-Джулани','Хайят Тахрир аш-Шам','Башар Асад','аль-Асад',
     'переходное правительство','временное правительство','переходные власти'),
   'hi', jsonb_build_array(
     'सीरिया','दमिश्क','अलेप्पो','अल-शराअ','जोलानी','बशर अल-असद',
     'संक्रमणकालीन सरकार','अंतरिम सरकार'),
   'zh', jsonb_build_array(
     '叙利亚','大马士革','阿勒颇','塔尔图斯','赫梅米姆','沙拉','朱拉尼',
     '沙姆解放组织','巴沙尔','阿萨德','过渡政府','临时政府'),
   'ar', jsonb_build_array(
     'سوريا','سورية','دمشق','حلب','طرطوس','حميميم','اللاذقية','حمص',
     'الشرع','الجولاني','هيئة تحرير الشام','بشار الأسد','الأسد','سانا',
     'الحكومة الانتقالية','الحكومة المؤقتة','السلطات الانتقالية'),
   'ja', jsonb_build_array(
     'シリア','ダマスカス','アレッポ','タルトゥース','フメイミム',
     'シャラア','ジョラニ','ハヤト・タハリール','過渡政府','暫定政府',
     'バッシャール・アサド','アサド')
)
WHERE taxonomy_function='fn_anchor' AND linked_id='syria_theater';

-- ============================================================
-- 2. syria_recognition_and_normalisation anchor — drop ALL generic
--    concept words. Keep only Syria-specific own-side actor names and
--    Syria-specific places. Centroid + publisher cohort + Syria-only
--    anchor = clean conjunction.
-- ============================================================

UPDATE taxonomy_v3 SET aliases = jsonb_build_object(
   'en', jsonb_build_array(
     'Sharaa','Jolani','Jawlani','Hayat Tahrir al-Sham','SANA',
     'Syria','Damascus','Tartus','Khmeimim','al-Assad','Bashar al-Assad'),
   'de', jsonb_build_array(
     'Damaskus','Hayat Tahrir al-Sham','al-Assad'),
   'es', jsonb_build_array(
     'Siria','Damasco','al-Assad'),
   'it', jsonb_build_array(
     'Siria','Damasco','al-Assad'),
   'fr', jsonb_build_array(
     'Syrie','Damas','al-Assad'),
   'ru', jsonb_build_array(
     'аш-Шараа','аль-Джулани','Хайят Тахрир аш-Шам','Дамаск','Тартус','Хмеймим',
     'Сирия','аль-Асад','Башар Асад'),
   'hi', jsonb_build_array(
     'अल-शराअ','जोलानी','दमिश्क','सीरिया','बशर अल-असद'),
   'zh', jsonb_build_array(
     '沙拉','朱拉尼','沙姆解放组织','大马士革','叙利亚','巴沙尔','阿萨德'),
   'ar', jsonb_build_array(
     'الشرع','الجولاني','هيئة تحرير الشام','دمشق','طرطوس','حميميم',
     'سوريا','سورية','بشار الأسد'),
   'ja', jsonb_build_array(
     'シャラア','ジョラニ','ダマスカス','シリア','アサド')
)
WHERE taxonomy_function='fn_anchor' AND linked_id='syria_recognition_and_normalisation';

-- ============================================================
-- 3. syria_israeli_strikes anchor — drop generic strike-phrases that
--    catch Lebanon/Iran. Keep only Syria-specific places and Syrian
--    army/air-defense markers. Israeli intent comes from the
--    publisher cohort, not the anchor.
-- ============================================================

UPDATE taxonomy_v3 SET aliases = jsonb_build_object(
   'en', jsonb_build_array(
     'Damascus','Aleppo','Homs','Latakia',
     'Quneitra','Daraa','Suwayda','Mazzeh','Tiyas','T-4',
     'Golan','Mount Hermon','UNDOF',
     'Syrian army','Syrian air defense','Syrian air defence',
     'Syrian air force'),
   'de', jsonb_build_array(
     'Damaskus','Latakia','Pufferzone Golan','Golan-Pufferzone',
     'syrische Luftabwehr','syrische Armee','syrische Luftwaffe'),
   'es', jsonb_build_array(
     'Damasco','Alepo','zona de amortiguamiento Golan','ejercito sirio',
     'defensa aerea siria','fuerza aerea siria'),
   'it', jsonb_build_array(
     'Damasco','zona cuscinetto Golan','esercito siriano','difesa aerea siriana',
     'aeronautica siriana'),
   'fr', jsonb_build_array(
     'Damas','Alep','zone tampon Golan','armee syrienne','defense aerienne syrienne',
     'armee de lair syrienne'),
   'ru', jsonb_build_array(
     'Дамаск','Алеппо','Хомс','Латакия','Кунейтра','Дераа','Эс-Сувейда',
     'Мазза','Тияс','Голаны','буферная зона Голаны','Мон-Хермон','UNDOF',
     'сирийская армия','сирийская ПВО','сирийские ВВС'),
   'hi', jsonb_build_array(
     'दमिश्क','अलेप्पो','गोलान बफर ज़ोन','सीरियाई सेना','सीरियाई वायु रक्षा'),
   'zh', jsonb_build_array(
     '大马士革','阿勒颇','库奈特拉','德拉','斯威达','马泽','梯亚斯',
     '戈兰缓冲区','叙利亚军队','叙利亚防空','叙利亚空军','UNDOF'),
   'ar', jsonb_build_array(
     'دمشق','حلب','حمص','اللاذقية','القنيطرة','درعا','السويداء','المزة','تي 4','تياس',
     'الجولان','المنطقة العازلة','جبل الشيخ','الجيش السوري','الدفاع الجوي السوري',
     'سلاح الجو السوري','يوندوف'),
   'ja', jsonb_build_array(
     'ダマスカス','アレッポ','クネイトラ','ダラア','スワイダ','マゼ','ティヤス',
     'ゴラン','緩衝地帯','シリア軍','シリア防空','シリア空軍','UNDOF')
)
WHERE taxonomy_function='fn_anchor' AND linked_id='syria_israeli_strikes';

-- ============================================================
-- 4. syria_counter_terror anchor — drop 2-char Latin tokens, drop
--    "Centcom" alone (matches Yemen/Iraq Centcom ops), drop
--    "Tower 22" (Jordan-located, not Syria/Iraq).
-- ============================================================

UPDATE taxonomy_v3 SET aliases = jsonb_build_object(
   'en', jsonb_build_array(
     'ISIS','ISIL','Daesh','Islamic State','al-Qaeda','al-Qaida','Hurras al-Din',
     'Operation Inherent Resolve','CJTF-OIR',
     'al-Hol','al-Hawl','al-Roj','Hasaka prison','Ghweran',
     'Conoco','Green Village','al-Tanf',
     'ISIS detainees','ISIS prisoners','ISIS fighters','ISIS leader','ISIS cell',
     'ISIS resurgence','ISIS militants'),
   'de', jsonb_build_array(
     'Daesh','Islamischer Staat','al-Qaida','IS-Haeftlinge','IS-Gefangene',
     'IS-Fuehrer','IS-Zelle','IS-Kaempfer','IS-Wiedererstarken'),
   'es', jsonb_build_array(
     'Daesh','Estado Islamico','al-Qaeda','detenidos del EI','combatientes del EI',
     'lider del EI'),
   'it', jsonb_build_array(
     'Daesh','Stato Islamico','al-Qaeda','detenuti dell ISIS','combattenti dell ISIS',
     'capo dell ISIS'),
   'fr', jsonb_build_array(
     'Daech','Etat Islamique','al-Qaida','detenus de l EI','combattants de l EI',
     'chef de l EI'),
   'ru', jsonb_build_array(
     'ИГИЛ','Даиш','Исламское государство','аль-Каида','Хуррас ад-Дин',
     'операция Непоколебимая решимость','аль-Холь','аль-Радж','тюрьма Хасаке',
     'Эрбиль','заключенные ИГИЛ','боевики ИГИЛ','главарь ИГИЛ'),
   'hi', jsonb_build_array(
     'आईएसआईएस','दाएश','इस्लामिक स्टेट','अल-कायदा','आईएसआईएस कैदी'),
   'zh', jsonb_build_array(
     '伊斯兰国','ISIS','达伊沙','基地组织','哈拉斯丁',
     '坚定决心行动','霍尔','哈塞克监狱','埃尔比勒',
     'ISIS被拘留者','ISIS战士','ISIS头目'),
   'ar', jsonb_build_array(
     'داعش','تنظيم الدولة الإسلامية','تنظيم الدولة','القاعدة','حراس الدين',
     'عملية العزم الصلب','التحالف الدولي','الهول','الروج','سجن الحسكة',
     'غويران','أربيل','معتقلو داعش','مقاتلو داعش','زعيم داعش','خلية داعش'),
   'ja', jsonb_build_array(
     'イスラム国','ISIS','ダーイシュ','アルカイダ',
     '不動の決意作戦','有志連合','アルホル','ハサカ刑務所','エルビル',
     'ISIS被拘禁者','ISIS戦闘員','ISIS指導者')
)
WHERE taxonomy_function='fn_anchor' AND linked_id='syria_counter_terror';

-- ============================================================
-- 5. syria_theater editorial_summary — expand with brief war recap
-- ============================================================

UPDATE friction_nodes SET
  editorial_summary_en = 'Syria is the most consequential governance question of the 2020s Middle East. The country endured nearly fourteen years of civil war that began in 2011 as anti-government protests and metastasised into a multi-front conflict involving Bashar al-Assad''s regime, a fractured opposition, Kurdish-led forces in the northeast, jihadist groups including the Islamic State, and a Russian-Iranian intervention from 2015 that kept Assad in power. The regime collapsed in late 2024 when a Hayat Tahrir al-Sham-led offensive seized Aleppo, Hama, Homs and Damascus in eleven days. Assad fled to Moscow, ending the Ba''ath era. Ahmad al-Sharaa (formerly Abu Mohammad al-Jolani, the HTS leader) now governs a transitional administration from Damascus, while Kurdish-led forces continue to hold the northeast, Israel strikes Syrian targets to prevent residual Iranian and Hezbollah re-establishment, US-led coalition forces continue counter-ISIS operations, and Arab and Western capitals weigh recognition of the new government. Russia''s Tartus naval and Khmeimim air bases remain in fraught negotiation; Iran has lost its primary Levant land bridge. The theater holds four contested surfaces — the Kurdish question, Israeli strikes, residual counter-terrorism, and the international recognition trajectory — plus three umbrella narratives that span them: legitimacy of the HTS-led transition, the substantive warning that HTS is rebranded al-Qaeda, and the Russia-Iran-axis lament at the regional setback.',
  editorial_summary_de = 'Syrien ist die folgenreichste Regierungsfrage des Nahen Ostens der 2020er. Das Land durchlief fast vierzehn Jahre Buergerkrieg, der 2011 mit Protesten begann und sich zu einem Mehrfrontenkonflikt entwickelte — Bashar al-Assads Regime, eine zersplitterte Opposition, kurdisch gefuehrte Kraefte im Nordosten, jihadistische Gruppen einschliesslich des Islamischen Staats sowie eine russisch-iranische Intervention ab 2015, die Assad an der Macht hielt. Das Regime brach Ende 2024 zusammen, als eine von Hayat Tahrir al-Sham gefuehrte Offensive Aleppo, Hama, Homs und Damaskus in elf Tagen einnahm. Assad floh nach Moskau, die Baath-Aera endete. Ahmad al-Sharaa (frueher Abu Mohammad al-Jolani, HTS-Fuehrer) regiert nun eine Uebergangsverwaltung aus Damaskus; kurdische Kraefte halten weiter den Nordosten; Israel greift syrische Ziele an, um eine Wiederetablierung iranischer und Hisbollah-Strukturen zu verhindern; die US-gefuehrte Koalition fuehrt Anti-IS-Operationen fort; arabische und westliche Hauptstaedte wiegen Anerkennung der neuen Regierung ab. Russlands Marinebasis Tartus und Luftbasis Khmeimim werden zaeh verhandelt; Iran hat seine wichtigste Levante-Landbruecke verloren. Die Konfliktzone umfasst vier umstrittene Felder — Kurdenfrage, israelische Schlaege, verbleibender Anti-Terror-Einsatz und internationale Anerkennungsentwicklung — sowie drei uebergreifende Narrative: Legitimitaet des HTS-gefuehrten Uebergangs, die substantielle Warnung vor HTS als umbenannte al-Qaida und das russisch-iranisch-achsen-Lament am regionalen Rueckschlag.'
WHERE id = 'syria_theater';

COMMIT;
