-- Syria theater iteration 3 — anchors require BOTH the FN's "what" and
-- Syria context, via 2-3 word phrase forms.
-- 2026-05-13
--
-- After iteration 2, two FNs over-attracted:
--   - syria_israeli_strikes (139 ev / 154 titles) — sample showed Syrian
--     army offensive stories on SDF, Aleppo clashes, civilian incidents.
--     Cause: "Aleppo", "Damascus", "Homs", "Syrian army" match every
--     Syria story under the broad publisher cohort.
--   - syria_recognition_and_normalisation (714 ev / 768 titles) — sample
--     showed Kurdish-question, counter-terror, and Israeli-strike stories.
--     Cause: "Syria" / "Damascus" alone catch all Syria stories under the
--     Reuters/BBC/DW pragmatic-engagement cohort.
--
-- Fix: phrase forms that bind concept + Syria context.
--   - israeli_strikes: "Israeli strikes Syria", "IDF Syria", "Israeli
--     airstrike Damascus", plus Syria-specific air-defense / buffer-zone /
--     Quneitra/Mazzeh/T-4 markers that ARE distinctive to Israeli ops.
--   - recognition: keep own-side names (Sharaa, Jolani, HTS-fullname)
--     and add phrase forms ("lift sanctions Syria", "Syria normalisation",
--     "Syria reconstruction", "recognise Syria") that require Syria word
--     adjacent to a recognition concept.

BEGIN;

-- ============================================================
-- 1. syria_israeli_strikes — phrase forms binding Israel + Syria
-- ============================================================

UPDATE taxonomy_v3 SET aliases = jsonb_build_object(
   'en', jsonb_build_array(
     'Quneitra','Mazzeh','Tiyas','T-4','Mount Hermon','UNDOF',
     'Syrian air defense','Syrian air defence','Syrian air force',
     'buffer zone Syria','Golan buffer','south of Damascus',
     'Israeli strikes Syria','Israeli strike Syria','Israeli airstrike Syria',
     'Israeli airstrikes Syria','Israel strikes Syria','Israel hits Syria',
     'Israeli strikes Damascus','Israeli airstrike Damascus','IDF Syria',
     'IDF strikes Syria','IDF strikes Damascus','Israeli strike Damascus',
     'Israeli forces in Syria','Israeli incursion Syria','Israeli forces Syria',
     'Israel hit Damascus','strikes Syrian','strikes near Damascus',
     'Israel bombs Syria','Israeli strikes on Syria'),
   'de', jsonb_build_array(
     'Pufferzone Golan','Golan-Pufferzone','syrische Luftabwehr','syrische Luftwaffe',
     'israelische Schlaege Syrien','israelischer Luftangriff Syrien',
     'israelische Angriffe Syrien','israelische Truppen in Syrien',
     'Israel bombardiert Syrien','IDF Syrien','israelische Operation Syrien'),
   'es', jsonb_build_array(
     'zona de amortiguamiento Golan','defensa aerea siria','fuerza aerea siria',
     'ataque israeli en Siria','ataques israelies en Siria','FDI Siria',
     'fuerzas israelies en Siria','ataque aereo israeli Siria'),
   'it', jsonb_build_array(
     'zona cuscinetto Golan','difesa aerea siriana','aeronautica siriana',
     'attacco israeliano Siria','attacchi israeliani Siria','IDF Siria',
     'forze israeliane in Siria','raid israeliano Siria'),
   'fr', jsonb_build_array(
     'zone tampon Golan','defense aerienne syrienne','armee de l''air syrienne',
     'frappe israelienne Syrie','frappes israeliennes Syrie','Tsahal Syrie',
     'forces israeliennes en Syrie','raid israelien Syrie'),
   'ru', jsonb_build_array(
     'Кунейтра','Мазза','Тияс','Мон-Хермон','UNDOF',
     'буферная зона на Голанах','сирийская ПВО','сирийские ВВС',
     'израильский удар по Сирии','израильские удары по Сирии',
     'израильский авиаудар Сирия','ЦАХАЛ Сирия',
     'израильские войска в Сирии','израильская операция в Сирии'),
   'hi', jsonb_build_array(
     'गोलान बफर ज़ोन','सीरियाई वायु रक्षा','सीरियाई वायुसेना',
     'सीरिया पर इज़राइली हमला','सीरिया में आईडीएफ','सीरिया में इज़राइली बल'),
   'zh', jsonb_build_array(
     '库奈特拉','马泽','梯亚斯','戈兰缓冲区','叙利亚防空','叙利亚空军','UNDOF',
     '以色列袭击叙利亚','以色列空袭叙利亚','以色列国防军叙利亚','以色列轰炸叙利亚'),
   'ar', jsonb_build_array(
     'القنيطرة','المزة','تي 4','تياس','جبل الشيخ','يوندوف',
     'المنطقة العازلة في الجولان','الدفاع الجوي السوري','سلاح الجو السوري',
     'ضربة إسرائيلية على سوريا','ضربات إسرائيلية على سوريا',
     'غارة إسرائيلية على سوريا','غارات إسرائيلية على سوريا',
     'القوات الإسرائيلية في سوريا','إسرائيل تقصف سوريا',
     'الجيش الإسرائيلي في سوريا','عملية إسرائيلية في سوريا',
     'ضربة إسرائيلية على دمشق','غارة إسرائيلية على دمشق'),
   'ja', jsonb_build_array(
     'クネイトラ','マゼ','ティヤス','ゴラン緩衝地帯','シリア防空','シリア空軍','UNDOF',
     'シリアへのイスラエルの攻撃','シリアへのイスラエル空爆',
     'シリアのイスラエル軍','シリア国内のイスラエル軍')
)
WHERE taxonomy_function='fn_anchor' AND linked_id='syria_israeli_strikes';

-- ============================================================
-- 2. syria_recognition_and_normalisation — own-side names + phrase
--    forms binding recognition concept + Syria context
-- ============================================================

UPDATE taxonomy_v3 SET aliases = jsonb_build_object(
   'en', jsonb_build_array(
     'Sharaa','Jolani','Jawlani','Hayat Tahrir al-Sham','SANA',
     'lift sanctions on Syria','lifts sanctions on Syria',
     'sanctions on Syria lifted','Syria sanctions lifted','Syria sanctions relief',
     'ease sanctions on Syria','easing sanctions on Syria','sanctions relief Syria',
     'recognise Syria','recognize Syria','recognise the new Syrian',
     'recognising Syria','recognition of Syria','Syria recognition',
     'normalise with Syria','normalize with Syria','normalisation with Syria',
     'normalization with Syria','Syria normalisation','Syria normalization',
     'Syria reconstruction','reconstruction of Syria','reconstruction in Syria',
     'Syria investment','investment in Syria','Syria reintegration',
     'reintegration of Syria','Arab League Syria','Syria Arab League',
     'Syrian transitional government','Syrian interim government',
     'delisting HTS','delisting of HTS','removed from terror list',
     'Syrian president visit','president of Syria visit','visits Damascus',
     'visit to Damascus','meets al-Sharaa','meeting with al-Sharaa',
     'met al-Sharaa','meets Sharaa','Sharaa visit','Sharaa meets',
     'reopens embassy in Damascus','ambassador to Syria','embassy in Damascus',
     'Syria embassy reopened'),
   'de', jsonb_build_array(
     'al-Sharaa','al-Scharaa','al-Dscholani','Hayat Tahrir al-Sham',
     'Sanktionen gegen Syrien aufgehoben','Aufhebung der Sanktionen Syrien',
     'Lockerung der Sanktionen Syrien','Sanktionen Syrien aufgehoben',
     'Syrien anerkennen','Anerkennung Syriens','Anerkennung der neuen syrischen',
     'Normalisierung mit Syrien','Syrien-Normalisierung','Wiederaufbau Syriens',
     'Investitionen in Syrien','syrische Uebergangsregierung','Damaskus-Besuch',
     'Besuch in Damaskus','Treffen mit al-Sharaa','trifft al-Sharaa',
     'Botschaft in Damaskus wiedereroeffnet','Botschafter in Damaskus',
     'Arabische Liga Syrien'),
   'es', jsonb_build_array(
     'al-Sharaa','Hayat Tahrir al-Sham','levantar sanciones a Siria',
     'levantamiento de sanciones a Siria','flexibilizar sanciones a Siria',
     'reconocer a Siria','reconocimiento de Siria','normalizacion con Siria',
     'normalizacion de Siria','reconstruccion de Siria','inversion en Siria',
     'gobierno de transicion sirio','visita a Damasco','reunion con al-Sharaa',
     'embajada en Damasco','Liga Arabe Siria'),
   'it', jsonb_build_array(
     'al-Sharaa','Hayat Tahrir al-Sham','revocare le sanzioni alla Siria',
     'revoca delle sanzioni alla Siria','allentare le sanzioni alla Siria',
     'riconoscere la Siria','riconoscimento della Siria','normalizzazione con la Siria',
     'normalizzazione della Siria','ricostruzione della Siria','investimento in Siria',
     'governo di transizione siriano','visita a Damasco','incontro con al-Sharaa',
     'ambasciata a Damasco','Lega Araba Siria'),
   'fr', jsonb_build_array(
     'al-Sharaa','Hayat Tahrir al-Sham','lever les sanctions contre la Syrie',
     'levee des sanctions contre la Syrie','assouplir les sanctions contre la Syrie',
     'reconnaitre la Syrie','reconnaissance de la Syrie','normalisation avec la Syrie',
     'normalisation de la Syrie','reconstruction de la Syrie','investissement en Syrie',
     'gouvernement de transition syrien','visite a Damas','rencontre avec al-Sharaa',
     'ambassade a Damas','Ligue arabe Syrie'),
   'ru', jsonb_build_array(
     'аш-Шараа','аль-Джулани','Хайят Тахрир аш-Шам',
     'снять санкции с Сирии','снятие санкций с Сирии','ослабить санкции Сирии',
     'признать Сирию','признание Сирии','нормализация с Сирией','нормализация Сирии',
     'восстановление Сирии','инвестиции в Сирию','переходное правительство Сирии',
     'визит в Дамаск','встреча с аш-Шараа','посольство в Дамаске',
     'Лига арабских государств Сирия','исключение ХТШ из списка'),
   'hi', jsonb_build_array(
     'अल-शराअ','जोलानी','हयात तहरीर अल-शाम',
     'सीरिया पर प्रतिबंध हटाना','सीरिया को मान्यता','सीरिया के साथ सामान्यीकरण',
     'सीरिया का पुनर्निर्माण','सीरिया में निवेश','दमिश्क की यात्रा',
     'अल-शराअ से मुलाकात'),
   'zh', jsonb_build_array(
     '沙拉','朱拉尼','沙姆解放组织',
     '解除对叙利亚的制裁','取消对叙利亚的制裁','放松对叙利亚的制裁',
     '承认叙利亚','叙利亚的承认','与叙利亚关系正常化','叙利亚关系正常化',
     '叙利亚重建','在叙利亚投资','叙利亚过渡政府',
     '访问大马士革','会见沙拉','大马士革大使馆','阿拉伯联盟叙利亚'),
   'ar', jsonb_build_array(
     'الشرع','الجولاني','هيئة تحرير الشام',
     'رفع العقوبات عن سوريا','إلغاء العقوبات عن سوريا','تخفيف العقوبات السورية',
     'الاعتراف بسوريا','اعتراف بسوريا','التطبيع مع سوريا','تطبيع مع سوريا',
     'إعادة إعمار سوريا','الاستثمار في سوريا','الحكومة الانتقالية السورية',
     'زيارة دمشق','لقاء مع الشرع','اجتماع مع الشرع','إعادة فتح السفارة في دمشق',
     'الجامعة العربية وسوريا','شطب هيئة تحرير الشام'),
   'ja', jsonb_build_array(
     'シャラア','ジョラニ','ハヤト・タハリール',
     'シリアへの制裁解除','シリアへの制裁緩和',
     'シリアを承認','シリアの承認','シリアとの関係正常化','シリアの正常化',
     'シリアの再建','シリアへの投資','シリア過渡政府',
     'ダマスカス訪問','シャラアとの会談','ダマスカスの大使館',
     'アラブ連盟 シリア','HTSのテロ指定解除')
)
WHERE taxonomy_function='fn_anchor' AND linked_id='syria_recognition_and_normalisation';

COMMIT;
