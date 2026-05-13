-- Syria theater iteration 4 — strict CTM-centroid gate + counter_terror
-- ISIS-collision fix + expanded centroid scopes.
-- 2026-05-13
--
-- Two root-cause fixes combined:
--   1. Code change in scripts/bootstrap_friction_node.py: event attribution
--      now uses the event's CTM centroid_id (single, primary) instead of
--      "any member title's centroid_ids overlap". The lenient gate was
--      catching events in AMERICAS-USA / EUROPE-* CTMs whose ISIS-tagged
--      titles got backfilled to MIDEAST-LEVANT via Phase 2.2.
--   2. Anchor: drop bare 'ISIS' (4 chars, matches 'crISIS' — every "Lebanon
--      humanitarian crisis" title was qualifying). Replace with phrase forms
--      that require ISIS to appear in an ISIS-specific context.
--
-- Centroid scope expansion: with the strict gate, each FN must list ALL
-- CTM centroids where its legitimate events live. Syria FNs gain:
--   - NON-STATE-ISIS / NON-STATE-AL-QAEDA / NON-STATE-KURDISTAN where
--     non-state-actor-anchored events sit
--   - MIDEAST-TURKEY for cross-border ops, recognition diplomacy
--   - MIDEAST-IRAN for Iranian framings (israeli strikes, counter-terror)
--   - AMERICAS-USA for coalition counter-terror ops headquartered there

BEGIN;

-- ============================================================
-- 1. Expand Syria FN centroid_ids
-- ============================================================

UPDATE friction_nodes SET centroid_ids = ARRAY[
  'MIDEAST-LEVANT','MIDEAST-IRAQ','MIDEAST-TURKEY','MIDEAST-IRAN','AMERICAS-USA',
  'NON-STATE-ISIS','NON-STATE-AL-QAEDA','NON-STATE-KURDISTAN'
] WHERE id = 'syria_counter_terror';

UPDATE friction_nodes SET centroid_ids = ARRAY[
  'MIDEAST-LEVANT','MIDEAST-IRAQ','MIDEAST-TURKEY','AMERICAS-USA',
  'NON-STATE-KURDISTAN','NON-STATE-ISIS'
] WHERE id = 'syria_kurdish_question';

UPDATE friction_nodes SET centroid_ids = ARRAY[
  'MIDEAST-LEVANT','MIDEAST-ISRAEL','MIDEAST-IRAN'
] WHERE id = 'syria_israeli_strikes';

UPDATE friction_nodes SET centroid_ids = ARRAY[
  'MIDEAST-LEVANT','MIDEAST-TURKEY','MIDEAST-SAUDI','MIDEAST-GULF',
  'MIDEAST-EGYPT','AMERICAS-USA','EUROPE-UK','EUROPE-GERMANY',
  'EUROPE-FRANCE','EUROPE-RUSSIA','EUROPE-UKRAINE','NON-STATE-EU'
] WHERE id = 'syria_recognition_and_normalisation';

-- ============================================================
-- 2. syria_counter_terror anchor — drop bare ISIS (crISIS collision)
--    Replace with ISIS-context phrase forms.
-- ============================================================

UPDATE taxonomy_v3 SET aliases = jsonb_build_object(
   'en', jsonb_build_array(
     'ISIL','Daesh','Islamic State','al-Qaeda','al-Qaida','Hurras al-Din',
     'Operation Inherent Resolve','CJTF-OIR',
     'al-Hol','al-Hawl','al-Roj','Hasaka prison','Ghweran',
     'Conoco','Green Village','al-Tanf',
     'ISIS detainees','ISIS prisoners','ISIS fighters','ISIS leader','ISIS cell',
     'ISIS militants','ISIS resurgence','ISIS members','ISIS attack','ISIS group',
     'ISIS-linked','ISIS-affiliated','ISIS supporter','ISIS supporters',
     'against ISIS','strikes ISIS','target ISIS','ISIS in Syria','ISIS in Iraq',
     'IS detainees','IS fighters','IS leader','IS militants'),
   'de', jsonb_build_array(
     'Daesh','Islamischer Staat','al-Qaida','IS-Haeftlinge','IS-Gefangene',
     'IS-Fuehrer','IS-Zelle','IS-Kaempfer','IS-Anhaenger','IS-Anschlag',
     'gegen den IS','IS-Wiedererstarken'),
   'es', jsonb_build_array(
     'Daesh','Estado Islamico','al-Qaeda','detenidos del EI','combatientes del EI',
     'lider del EI','militantes del EI','simpatizante del EI','contra el EI'),
   'it', jsonb_build_array(
     'Daesh','Stato Islamico','al-Qaeda','detenuti dell ISIS','combattenti dell ISIS',
     'capo dell ISIS','militanti dell ISIS','contro l ISIS'),
   'fr', jsonb_build_array(
     'Daech','Etat Islamique','al-Qaida','detenus de l EI','combattants de l EI',
     'chef de l EI','militants de l EI','sympathisant de l EI','contre l EI'),
   'ru', jsonb_build_array(
     'ИГИЛ','Даиш','Исламское государство','аль-Каида','Хуррас ад-Дин',
     'операция Непоколебимая решимость','аль-Холь','аль-Радж','тюрьма Хасаке',
     'Эрбиль','заключенные ИГИЛ','боевики ИГИЛ','главарь ИГИЛ',
     'сторонник ИГИЛ','против ИГИЛ','удары по ИГИЛ'),
   'hi', jsonb_build_array(
     'दाएश','इस्लामिक स्टेट','अल-कायदा','आईएसआईएस कैदी','आईएसआईएस लड़ाके',
     'आईएसआईएस के खिलाफ','आईएसआईएस समर्थक'),
   'zh', jsonb_build_array(
     '伊斯兰国','达伊沙','基地组织','哈拉斯丁','坚定决心行动',
     '霍尔','哈塞克监狱','埃尔比勒',
     '伊斯兰国被拘留者','伊斯兰国战士','伊斯兰国头目','伊斯兰国分子',
     '打击伊斯兰国','伊斯兰国支持者'),
   'ar', jsonb_build_array(
     'داعش','تنظيم الدولة الإسلامية','تنظيم الدولة','القاعدة','حراس الدين',
     'عملية العزم الصلب','التحالف الدولي','الهول','الروج','سجن الحسكة',
     'غويران','أربيل','معتقلو داعش','مقاتلو داعش','زعيم داعش','خلية داعش',
     'مؤيد داعش','هجوم داعش','ضد داعش','استهداف داعش'),
   'ja', jsonb_build_array(
     'イスラム国','ダーイシュ','アルカイダ','不動の決意作戦',
     '有志連合','アルホル','ハサカ刑務所','エルビル',
     'イスラム国の被拘禁者','イスラム国の戦闘員','イスラム国の指導者',
     'イスラム国の支持者','イスラム国に対する')
)
WHERE taxonomy_function='fn_anchor' AND linked_id='syria_counter_terror';

COMMIT;
