-- Yemen / Red Sea theater seed: 1 theater + 3 atomic FNs + 9 narratives + 4 fn_anchor bundles.
-- 2026-05-13
--
-- See docs/context/YEMEN_RED_SEA_THEATER_SPEC.md for rationale.
-- Stance is toward the Houthi / Ansar Allah authority in Sanaa.

BEGIN;

-- ============================================================
-- 1. friction_nodes
-- ============================================================

INSERT INTO friction_nodes (id, name_en, name_de, description_en, description_de,
    editorial_summary_en, editorial_summary_de, centroid_ids, fn_type, member_fn_ids,
    is_active, display_order)
VALUES

('yemen_red_sea_theater', 'Yemen and the Red Sea front', 'Jemen und die Front am Roten Meer',
 'Yemen as the fourth operational front of the regional war: Houthi missile and drone attacks on Israel, threats against Bab al-Mandab shipping, the Saudi-led coalition war with Ansar Allah, and the southern STC separatist contest. Coverage clusters around resistance-axis framing on one side and Saudi-Sunni stabilisation framing on the other, with Western shipping desks treating the Red Sea as a freedom-of-navigation problem.',
 'Jemen als vierte Front des regionalen Krieges: Houthi-Raketen und -Drohnen gegen Israel, Drohungen gegen die Schifffahrt am Bab al-Mandab, der Krieg der saudisch gefuehrten Koalition mit Ansar Allah und der suedliche STC-Separatistenstreit. Die Berichterstattung pendelt zwischen Widerstandsachse-Rahmung und saudisch-sunnitischer Stabilisierungs-Rahmung; westliche Schifffahrts-Redaktionen behandeln das Rote Meer als Frage der freien Seefahrt.',
 'Yemen sits on the southern jaw of the Red Sea, hosts a movement (Ansar Allah / the Houthis) that coordinates operationally with Iran and Hezbollah, and remains a contested state — UN-recognised government in Aden, UAE-backed STC separatists, de facto Houthi authority in Sanaa. Narratives split four ways: Saudi-Egyptian state media as Iran-proxy destabilisation, resistance-axis outlets as fourth-front Gaza solidarity, Western shipping desks as freedom-of-navigation, and Israeli outlets as Iran-axis kinetic problem.',
 'Jemen liegt am suedlichen Kiefer des Roten Meeres, beherbergt eine mit Iran und Hisbollah operativ koordinierende Bewegung (Ansar Allah / Houthi) und bleibt ein umstrittener Staat — UN-anerkannte Regierung in Aden, VAE-gestuetzte STC-Separatisten, faktische Houthi-Herrschaft in Sanaa. Narrative spalten vierfach: saudisch-aegyptisch als iranische Stellvertreter-Destabilisierung, Widerstandsachse als vierte Front Gaza-Solidaritaet, westliche Schifffahrts-Redaktionen als Frage der freien Seefahrt, israelische Medien als kinetisches Iran-Achsen-Problem.',
 ARRAY['MIDEAST-YEMEN','MIDEAST-SAUDI','MIDEAST-GULF','MIDEAST-EGYPT','MIDEAST-IRAN','MIDEAST-ISRAEL','AMERICAS-USA','EUROPE-UK'],
 'theater', ARRAY['red_sea_shipping_security','houthi_strikes_on_israel','saudi_houthi_war'],
 true, 60),

('red_sea_shipping_security', 'Red Sea and Bab al-Mandab shipping security', 'Sicherheit der Schifffahrt am Roten Meer und Bab al-Mandab',
 'Houthi attacks on commercial vessels transiting the Bab al-Mandab strait and the southern Red Sea; US-UK-led Operation Prosperity Guardian and EU naval Operation Aspides; the rerouting of container traffic around the Cape of Good Hope; Maersk and other shippers'' on-again-off-again returns; reported Israeli exploration of a Somaliland base.',
 'Houthi-Angriffe auf Handelsschiffe im Bab al-Mandab und im suedlichen Roten Meer; US-britische Operation Prosperity Guardian, EU-Marineoperation Aspides; Umleitung des Containerverkehrs um das Kap der Guten Hoffnung; schwankende Rueckkehr von Maersk und anderen Reedereien; berichtete israelische Sondierung einer Basis in Somaliland.',
 'Distinct from the Strait of Hormuz contest (in iran_theater), Bab al-Mandab is a Yemen-side chokepoint moving roughly 12% of global trade. Western shipping desks and Israeli outlets converge on freedom-of-navigation framing; resistance outlets defend Houthi targeting as Gaza pressure. The double-blockade motif (Hormuz + Bab al-Mandab) is a recurring 2026 theme in Asian shipping coverage.',
 'Anders als der Hormus-Streit (im iran_theater) ist Bab al-Mandab ein Jemen-seitiger Engpass mit rund 12% des Welthandels. Westliche Schifffahrts-Redaktionen und israelische Medien teilen die "Freiheit der Seefahrt"-Rahmung; Widerstands-Stimmen verteidigen Houthi-Schlaege als Gaza-Pression. Die "doppelte Blockade" (Hormus + Bab al-Mandab) ist ein wiederkehrendes Motiv 2026.',
 ARRAY['MIDEAST-YEMEN','MIDEAST-EGYPT','AMERICAS-USA','EUROPE-UK'],
 'atomic', NULL, true, 61),

('houthi_strikes_on_israel', 'Houthi strikes on Israel', 'Houthi-Schlaege gegen Israel',
 'Houthi ballistic missile and drone attacks on Israeli territory (Tel Aviv, Ben Gurion airport, Eilat), declared as joint operations with Iran and Hezbollah; Israeli retaliation in Yemen; intercepts; the question of whether the Houthis act on Tehran''s direction or independently.',
 'Houthi-Raketen und -Drohnenangriffe auf israelisches Gebiet (Tel Aviv, Flughafen Ben Gurion, Eilat), erklaert als gemeinsame Operationen mit Iran und Hisbollah; israelische Vergeltung in Jemen; Abfaenge; die Frage, ob die Houthi auf Teheraner Weisung oder unabhaengig handeln.',
 'The corpus''s strongest Yemen signal (top promoted event = 26 sources). Israeli outlets frame Houthi strikes as Iran-orchestrated multi-front aggression demanding kinetic answers (Hodeidah port, Sanaa airport, reported Somaliland-base agreement). Resistance outlets present the same strikes as legitimate Gaza solidarity under unified axis-of-resistance command. FN boundary: Houthi missile hits Tel Aviv attributes here; Houthi attack on Galaxy Leader attributes to red_sea_shipping_security.',
 'Das staerkste Jemen-Signal im Korpus (Top-Event mit 26 Quellen). Israelische Medien rahmen Houthi-Schlaege als iranisch orchestrierte Mehrfronten-Aggression mit kinetischer Antwort. Widerstands-Medien praesentieren dieselben Schlaege als legitime Gaza-Solidaritaet unter einheitlichem Widerstandsachsen-Kommando.',
 ARRAY['MIDEAST-YEMEN','MIDEAST-ISRAEL','MIDEAST-IRAN'],
 'atomic', NULL, true, 62),

('saudi_houthi_war', 'Saudi-led coalition vs Houthi war and southern STC separatism', 'Saudisch gefuehrte Koalition gegen Houthi und suedlicher STC-Separatismus',
 'The long-running war between the Saudi-led Arab coalition backing the internationally-recognised Presidential Leadership Council in Aden, the Houthi / Ansar Allah authority in Sanaa, and the UAE-backed Southern Transitional Council. Covers the 2026 STC dissolution / disputed disbanding, separatist leader flight, coalition strikes in southern Yemen, and Saudi reconstruction pledges.',
 'Der anhaltende Krieg zwischen der saudisch gefuehrten arabischen Koalition zur Stuetzung des international anerkannten Praesidialen Fuehrungsrats in Aden, der Houthi-Autoritaet in Sanaa und dem von den VAE unterstuetzten Suedlichen Uebergangsrat. Umfasst die STC-Aufloesung 2026, Flucht des Separatistenfuehrers, Koalitionsschlaege im Sueden und saudische Wiederaufbau-Zusagen.',
 'The intra-Arab leg of the Yemen story, dominated by Saudi-Egyptian state press (Al-Ahram, Al Arabiya). Narrative split is NOT the Iran-axis split — it''s Saudi-coalition legitimacy framing vs. pan-Arab critique of southern fragmentation and STC dissolution. The 2026 STC self-dissolution and the separatist leader''s flight to the UAE (with Saudi accusations against Abu Dhabi) opens a thin but real Gulf-bloc fissure.',
 'Der innerarabische Strang der Jemen-Geschichte, dominiert von der saudisch-aegyptischen Staatspresse. Die Spaltung ist nicht die Iran-Achsen-Spaltung — es geht um saudisch-koalitionaere Legitimitaets-Rahmung gegen panarabische Kritik. Die STC-Selbstaufloesung 2026 oeffnet einen duennen, aber realen Riss im Golf-Block.',
 ARRAY['MIDEAST-YEMEN','MIDEAST-SAUDI','MIDEAST-GULF'],
 'atomic', NULL, true, 63);

-- ============================================================
-- 2. fn_anchor bundles
-- ============================================================

INSERT INTO taxonomy_v3 (item_raw, aliases, is_active, taxonomy_function, linked_id) VALUES

('yemen_red_sea_theater fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'Houthi','Houthis','Ansar Allah','Sanaa','Aden','Hodeidah','Hodeida','Hudaydah',
     'Bab al-Mandab','Bab el-Mandeb','Red Sea','Gulf of Aden','Socotra',
     'al-Houthi','Abdul Malik al-Houthi','al-Mashat',
     'Presidential Leadership Council','PLC','Coalition to Restore Legitimacy',
     'STC','Southern Transitional Council'),
   'de', jsonb_build_array(
     'Huthi','Huthis','Rotes Meer','Golf von Aden','Praesidialer Fuehrungsrat',
     'saudisch gefuehrte Koalition','arabische Koalition','Suedlicher Uebergangsrat'),
   'es', jsonb_build_array(
     'hutíes','hutí','Saná','Adén','Mar Rojo','golfo de Adén','Sócotra',
     'Consejo de Liderazgo Presidencial','coalición árabe','Consejo de Transición del Sur'),
   'fr', jsonb_build_array(
     'mer Rouge','golfe d''Aden','Conseil de direction présidentiel',
     'coalition arabe','Conseil de transition du Sud'),
   'it', jsonb_build_array(
     'Mar Rosso','golfo di Aden','Consiglio di guida presidenziale',
     'coalizione araba','Consiglio di transizione del Sud'),
   'ru', jsonb_build_array(
     'хуситы','Ансар Аллах','Сана','Аден','Ходейда','Баб-эль-Мандеб',
     'Красное море','Аденский залив','Сокотра','Президентский совет',
     'аравийская коалиция','Южный переходный совет','Абдул-Малик аль-Хуси'),
   'hi', jsonb_build_array(
     'हूती','अंसार अल्लाह','सना','अदन','होदेइदा','बाब अल-मंदब',
     'लाल सागर','अदन की खाड़ी','राष्ट्रपति नेतृत्व परिषद',
     'सऊदी नेतृत्व वाला गठबंधन','दक्षिणी संक्रमणकालीन परिषद'),
   'zh', jsonb_build_array(
     '胡塞','胡塞武装','安萨尔安拉','萨那','亚丁','荷台达','曼德海峡',
     '红海','亚丁湾','索科特拉','总统领导委员会','沙特领导的联军',
     '南方过渡委员会'),
   'ar', jsonb_build_array(
     'الحوثيون','الحوثي','أنصار الله','صنعاء','عدن','الحديدة','باب المندب',
     'البحر الأحمر','خليج عدن','سقطرى','مجلس القيادة الرئاسي',
     'التحالف بقيادة السعودية','التحالف العربي','المجلس الانتقالي الجنوبي',
     'عبد الملك الحوثي','مهدي المشاط'),
   'ja', jsonb_build_array(
     'フーシ','フーシ派','アンサール・アッラー','サヌア','アデン',
     'ホデイダ','バブ・エル・マンデブ','紅海','アデン湾','ソコトラ',
     '大統領指導評議会','サウジアラビア主導の連合','南部暫定評議会')
 ),
 true, 'fn_anchor', 'yemen_red_sea_theater'),

('red_sea_shipping_security fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'Bab al-Mandab','Bab el-Mandeb','Red Sea','Gulf of Aden','Suez Canal','Yanbu',
     'Operation Prosperity Guardian','Prosperity Guardian','Aspides','Combined Maritime Forces',
     'Fifth Fleet','USS Eisenhower','USS Truman','UKMTO','Galaxy Leader',
     'Maersk','MSC','container ship','tanker','vessel','cargo ship','merchant ship',
     'anti-ship missile','anti-ship ballistic','UNCLOS','freedom of navigation',
     'rerouting','Cape of Good Hope'),
   'de', jsonb_build_array(
     'Rotes Meer','Golf von Aden','Sueskanal','Fuenfte Flotte','Containerschiff',
     'Frachtschiff','Handelsschiff','Antischiffsrakete','freie Seefahrt','Umleitung',
     'Kap der Guten Hoffnung'),
   'es', jsonb_build_array(
     'Mar Rojo','golfo de Adén','canal de Suez','Quinta Flota','portacontenedores',
     'petrolero','carguero','buque mercante','misil antibuque','libertad de navegación',
     'desvío','Cabo de Buena Esperanza'),
   'fr', jsonb_build_array(
     'mer Rouge','golfe d''Aden','canal de Suez','Cinquième Flotte','porte-conteneurs',
     'pétrolier','cargo','navire marchand','missile antinavire','liberté de navigation',
     'déroutement','cap de Bonne-Espérance'),
   'it', jsonb_build_array(
     'Mar Rosso','golfo di Aden','canale di Suez','Quinta Flotta','portacontainer',
     'petroliera','mercantile','nave commerciale','missile antinave','libertà di navigazione',
     'deviazione','Capo di Buona Speranza'),
   'ru', jsonb_build_array(
     'Баб-эль-Мандеб','Красное море','Аденский залив','Суэцкий канал','Янбу',
     'операция Страж процветания','операция Аспидес','Пятый флот','контейнеровоз',
     'танкер','грузовое судно','торговое судно','противокорабельная ракета',
     'свобода судоходства','мыс Доброй Надежды'),
   'hi', jsonb_build_array(
     'बाब अल-मंदब','लाल सागर','अदन की खाड़ी','स्वेज नहर','यनबू',
     'प्रॉस्पेरिटी गार्डियन','पाँचवाँ बेड़ा','कंटेनर जहाज','टैंकर','मालवाहक',
     'जहाज-रोधी मिसाइल','नौवहन की स्वतंत्रता','उत्तमाशा अंतरीप'),
   'zh', jsonb_build_array(
     '曼德海峡','红海','亚丁湾','苏伊士运河','延布','繁荣卫士行动','阿斯皮迪斯行动',
     '第五舰队','银河领袖号','马士基','集装箱船','油轮','货船','商船',
     '反舰导弹','反舰弹道导弹','航行自由','改道','好望角'),
   'ar', jsonb_build_array(
     'باب المندب','البحر الأحمر','خليج عدن','السويس','قناة السويس','ينبع',
     'عملية حارس الازدهار','عملية أسبيدس','الأسطول الخامس','ماسك','مايرسك',
     'ناقلة','سفينة شحن','سفينة تجارية','صاروخ مضاد للسفن','حرية الملاحة',
     'إعادة التوجيه','رأس الرجاء الصالح'),
   'ja', jsonb_build_array(
     'バブ・エル・マンデブ','紅海','アデン湾','スエズ運河','ヤンブー',
     '繁栄の守護者作戦','アスピデス作戦','第五艦隊','ギャラクシー・リーダー','マースク',
     'コンテナ船','タンカー','貨物船','商船','対艦ミサイル','対艦弾道ミサイル',
     '航行の自由','迂回','喜望峰')
 ),
 true, 'fn_anchor', 'red_sea_shipping_security'),

('houthi_strikes_on_israel fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'Tel Aviv','Ben Gurion','Eilat','Ramon airport','Palestine-2',
     'Toofan','Burkan','Quds-1','Quds-2','Quds-3','Hatem',
     'joint operation','fourth front','fourth arena','support front','Yemen front',
     'ballistic missile from Yemen','drone from Yemen','Yemeni missile'),
   'de', jsonb_build_array(
     'Flughafen Ramon','Drohne aus Jemen','jemenitische Rakete','gemeinsame Operation',
     'vierte Front','Unterstuetzungsfront','Jemen-Front'),
   'es', jsonb_build_array(
     'aeropuerto Ramón','misil balístico yemení','dron desde Yemen','operación conjunta',
     'cuarto frente','frente yemení'),
   'fr', jsonb_build_array(
     'Tel-Aviv','Ben Gourion','aéroport Ramon','missile balistique yéménite',
     'drone depuis le Yémen','opération conjointe','quatrième front','front yéménite'),
   'it', jsonb_build_array(
     'aeroporto Ramon','missile balistico yemenita','drone dallo Yemen',
     'operazione congiunta','quarto fronte','fronte yemenita'),
   'ru', jsonb_build_array(
     'Тель-Авив','Бен-Гурион','Эйлат','аэропорт Рамон','баллистическая ракета Йемен',
     'Туфан','Буркан','ракета Кудс','беспилотник из Йемена','йеменская ракета',
     'совместная операция','четвертый фронт','йеменский фронт'),
   'hi', jsonb_build_array(
     'तेल अवीव','बेन गुरियन','इलात','रामोन हवाई अड्डा',
     'यमनी बैलिस्टिक मिसाइल','यमन से ड्रोन','संयुक्त ऑपरेशन','चौथा मोर्चा',
     'यमनी मोर्चा'),
   'zh', jsonb_build_array(
     '特拉维夫','本古里安','埃拉特','拉蒙机场','也门弹道导弹','飓风',
     '火山导弹','圣城导弹','也门无人机','联合行动','第四战线','也门支援前线',
     '也门前线'),
   'ar', jsonb_build_array(
     'تل أبيب','بن غوريون','إيلات','مطار رامون','صاروخ باليستي يمني',
     'صاروخ فلسطين','طوفان','بركان','قدس','حاتم','طائرة مسيرة من اليمن',
     'عملية مشتركة','الجبهة الرابعة','جبهة المساندة','الجبهة اليمنية'),
   'ja', jsonb_build_array(
     'テルアビブ','ベングリオン','エイラート','ラモン空港','イエメン弾道ミサイル',
     'ブルカン','クッズ・ミサイル','イエメンからのドローン','共同作戦',
     '第四戦線','イエメン戦線')
 ),
 true, 'fn_anchor', 'houthi_strikes_on_israel'),

('saudi_houthi_war fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'STC','Southern Transitional Council','Mukalla','Marib','Taiz','Saada','Saadah',
     'Hadhramaut','Hadramaut','Shabwa','Giants Brigades','Joint Forces',
     'Tareq Saleh','al-Zubaidi','al-Alimi','Presidential Leadership Council','PLC',
     'Riyadh Agreement','Stockholm Agreement','Hodeidah Agreement','southern Yemen',
     'separatist','separatists','STC dissolution','coalition strikes'),
   'de', jsonb_build_array(
     'Suedlicher Uebergangsrat','Gemeinsame Kraefte','Praesidialer Fuehrungsrat',
     'Riad-Abkommen','Stockholm-Abkommen','Hodeida-Abkommen','Suedjemen',
     'STC-Aufloesung','Separatisten','Koalitionsschlaege'),
   'es', jsonb_build_array(
     'Consejo de Transición del Sur','Brigadas de los Gigantes','Fuerzas Conjuntas',
     'Consejo de Liderazgo Presidencial','Acuerdo de Riad','Acuerdo de Estocolmo',
     'Acuerdo de Hodeida','sur de Yemen','disolución del STC','separatistas',
     'ataques de la coalición'),
   'fr', jsonb_build_array(
     'Conseil de transition du Sud','Brigades des Géants','Forces conjointes',
     'Conseil de direction présidentiel','accord de Riyad','accord de Stockholm',
     'accord de Hodeïda','sud du Yémen','dissolution du STC','séparatistes',
     'frappes de la coalition'),
   'it', jsonb_build_array(
     'Consiglio di transizione del Sud','Brigate dei Giganti','Forze Congiunte',
     'Consiglio di guida presidenziale','Accordo di Riad','Accordo di Stoccolma',
     'Accordo di Hodeida','Yemen meridionale','dissoluzione dell''STC','separatisti',
     'attacchi della coalizione'),
   'ru', jsonb_build_array(
     'ЮПС','Южный переходный совет','Мукалла','Мариб','Таиз','Саада','Хадрамаут','Шабва',
     'бригады Гигантов','Объединенные силы','Тарик Салех','аль-Зубейди','аль-Алими',
     'Президентский совет','Эр-Риядское соглашение','Стокгольмское соглашение',
     'соглашение по Ходейде','южный Йемен','роспуск ЮПС','сепаратисты','удары коалиции'),
   'hi', jsonb_build_array(
     'एसटीसी','दक्षिणी संक्रमणकालीन परिषद','मुकल्ला','मारिब','ताइज़','सादा',
     'हदरामौत','शबवा','जायंट्स ब्रिगेड','संयुक्त बल','राष्ट्रपति नेतृत्व परिषद',
     'रियाद समझौता','दक्षिणी यमन','एसटीसी विघटन','अलगाववादी','गठबंधन के हमले'),
   'zh', jsonb_build_array(
     '南方过渡委员会','穆卡拉','马里卜','塔伊兹','萨达','哈德拉毛','舍卜瓦',
     '巨人旅','联合部队','总统领导委员会','利雅得协议','斯德哥尔摩协议','荷台达协议',
     '南也门','南方过渡委员会解散','分裂分子','联军袭击'),
   'ar', jsonb_build_array(
     'المجلس الانتقالي الجنوبي','المكلا','مأرب','تعز','صعدة','حضرموت','شبوة',
     'ألوية العمالقة','القوات المشتركة','طارق صالح','عيدروس الزبيدي','الزبيدي',
     'رشاد العليمي','العليمي','مجلس القيادة الرئاسي','اتفاق الرياض','اتفاق ستوكهولم',
     'اتفاق الحديدة','جنوب اليمن','حل المجلس الانتقالي','الانفصاليون','ضربات التحالف'),
   'ja', jsonb_build_array(
     '南部暫定評議会','ムカッラ','マアリブ','タイズ','サアダ','ハドラマウト','シャブワ',
     'ジャイアンツ旅団','統合軍','大統領指導評議会','リヤド合意','ストックホルム合意',
     'ホデイダ合意','南イエメン','STC解散','分離主義者','連合軍の攻撃')
 ),
 true, 'fn_anchor', 'saudi_houthi_war');

-- ============================================================
-- 3. Narratives (9 = 3 theater + 2 per atomic)
-- ============================================================

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('houthis_fourth_front_solidarity', 'yemen_red_sea_theater', 1, 2,
 'Fourth-front solidarity', 'Vierte Front: Solidaritaet',
 'Houthi attacks on Israel and Red Sea shipping are legitimate Gaza solidarity',
 'Houthi-Angriffe auf Israel und Schifffahrt im Roten Meer sind legitime Gaza-Solidaritaet',
 'Resistance / Iran-aligned framing: Houthi attacks on Israel and Red Sea shipping are legitimate solidarity-with-Gaza pressure under a unified axis-of-resistance command; the Yemeni movement has the right to extend the war until Gaza ceasefire holds. The vocabulary: "fourth front", "support front", "axis solidarity", "Gaza pressure", "joint operation", "resistance command". Prescription: maintain pressure until Gaza ceasefire; integrate Houthi operations into unified resistance posture.',
 'Widerstand / Iran-orientierte Rahmung: Houthi-Angriffe auf Israel und Schifffahrt im Roten Meer sind legitime Solidaritaets-Druck mit Gaza unter einem einheitlichen Widerstandsachsen-Kommando; die jemenitische Bewegung hat das Recht, den Krieg auszuweiten, bis ein Gaza-Waffenstillstand haelt. Vokabular: "vierte Front", "Unterstuetzungsfront", "Achsen-Solidaritaet", "Gaza-Druck", "gemeinsame Operation". Vorschrift: Druck bis zum Gaza-Waffenstillstand aufrechterhalten.',
 ARRAY['MIDEAST-IRAN','MIDEAST-YEMEN'],
 ARRAY['Press TV','Al Jazeera','Al Mayadeen','Fars News','IRNA','TRT World','Anadolu Agency','Daily Sabah','CGTN','TASS (EN)','RT'],
 ARRAY['fourth front','support front','axis solidarity','Gaza pressure','joint operation','resistance command'],
 true),

('iran_proxy_destabilisation', 'yemen_red_sea_theater', 2, -2,
 'Iranian proxy destabilising the region', 'Iranischer Stellvertreter destabilisiert die Region',
 'Houthis are an Iranian proxy that has hijacked the Yemeni state',
 'Houthi sind ein iranischer Stellvertreter, der den jemenitischen Staat gekapert hat',
 'Saudi / Egyptian state, Israeli, and pro-Western framing: Houthis are an Iranian-armed proxy that has hijacked the Yemeni state, threatens Arab order, and must be militarily defeated; STC fracture is one symptom of the broader Iran-axis destabilisation. The vocabulary: "Iranian proxy", "Iran-armed", "axis aggression", "hijacked state", "Arab order", "destabilisation". Prescription: military defeat of Houthi capability, restoration of legitimate Yemeni government, interdiction of Iranian weapons pipelines.',
 'Saudisch-aegyptisch, israelisch und prowestlich: Houthi sind ein iranisch bewaffneter Stellvertreter, der den jemenitischen Staat gekapert hat, die arabische Ordnung bedroht und militaerisch besiegt werden muss; STC-Bruch ist ein Symptom der breiteren Iran-Achsen-Destabilisierung. Vokabular: "iranischer Stellvertreter", "iranisch bewaffnet", "Achsen-Aggression", "gekaperter Staat", "arabische Ordnung", "Destabilisierung". Vorschrift: militaerische Niederlage der Houthi-Kapazitaet, Wiederherstellung der legitimen Regierung, Unterbindung iranischer Waffenlieferungen.',
 ARRAY['MIDEAST-SAUDI','MIDEAST-GULF','MIDEAST-EGYPT','MIDEAST-ISRAEL','AMERICAS-USA'],
 ARRAY['Al-Ahram','Al Arabiya','Arab News','The National','Khaleej Times','Gulf News','Egypt Today','Jerusalem Post','Times of Israel','The Times of Israel','i24NEWS','Fox News','Haaretz'],
 ARRAY['Iranian proxy','Iran-armed','axis aggression','hijacked state','Arab order','destabilisation','weapons pipeline'],
 true),

('western_pragmatic_navigation', 'yemen_red_sea_theater', 3, 0,
 'Western pragmatic navigation framing', 'Westliche pragmatische Schifffahrts-Rahmung',
 'Houthi problem is a freedom-of-navigation problem; Gaza ceasefire removes the casus belli',
 'Houthi-Problem ist eine Frage der freien Seefahrt; Gaza-Waffenstillstand entfernt den Casus belli',
 'EU / E3 / US shipping-desk mainstream: the Houthi problem is primarily a freedom-of-navigation problem requiring coalition naval pressure (Prosperity Guardian, Aspides) and a Gaza ceasefire that removes the Houthis'' stated casus belli; humanitarian impact in Yemen is a parallel concern, not the primary frame. The vocabulary: "freedom of navigation", "Prosperity Guardian", "Aspides", "global trade", "coalition naval pressure", "Gaza ceasefire linkage", "humanitarian concern". Prescription: sustained coalition naval pressure, Gaza ceasefire diplomacy, humanitarian access; reject both kinetic escalation and unilateral concession.',
 'EU / E3 / US-Schifffahrts-Mainstream: das Houthi-Problem ist primaer eine Frage der freien Seefahrt, die koalitionaeren Marine-Druck erfordert (Prosperity Guardian, Aspides) und einen Gaza-Waffenstillstand, der den Houthi-Casus-belli entfernt; humanitaere Auswirkungen im Jemen sind eine parallele Sorge, nicht der primaere Rahmen. Vokabular: "freie Seefahrt", "Prosperity Guardian", "Aspides", "Welthandel", "Marine-Druck", "Gaza-Waffenstillstand-Verknuepfung". Vorschrift: anhaltender Marine-Druck, Gaza-Waffenstillstands-Diplomatie, humanitaerer Zugang.',
 ARRAY['NON-STATE-EU','EUROPE-UK','EUROPE-FRANCE','EUROPE-GERMANY','AMERICAS-USA'],
 ARRAY['Reuters','Associated Press','BBC World','France 24','France 24 (EN)','Deutsche Welle','Tagesschau','Financial Times','Bloomberg','Wall Street Journal','The Guardian','Le Monde','Nikkei Asia','Straits Times'],
 ARRAY['freedom of navigation','Prosperity Guardian','Aspides','global trade','coalition pressure','Gaza ceasefire linkage','humanitarian concern'],
 true),

('freedom_of_navigation_defense', 'red_sea_shipping_security', 1, -1,
 'Freedom of navigation must be defended', 'Schutz der freien Seefahrt',
 'Houthi attacks on commercial vessels violate UNCLOS; coalition naval ops are necessary',
 'Houthi-Angriffe auf Handelsschiffe verletzen UNCLOS; koalitionaere Marine-Operationen sind notwendig',
 'Western shipping-desk, Israeli, and Saudi framing: Houthi attacks on commercial vessels violate UNCLOS freedom-of-navigation rights and global trade order; Operation Prosperity Guardian, EU Aspides, and US Fifth Fleet operations are necessary and lawful; Saudi Yanbu rerouting and reported Somaliland base are pragmatic adaptations. The vocabulary: "UNCLOS", "freedom of navigation", "Prosperity Guardian", "Aspides", "Fifth Fleet", "lawful response", "global trade order". Prescription: maintain coalition naval presence, escort merchant traffic, sanction Houthi enablers.',
 'Westliche Schifffahrts-, israelische und saudische Rahmung: Houthi-Angriffe auf Handelsschiffe verletzen UNCLOS und die Welthandelsordnung; Operation Prosperity Guardian, EU Aspides und US-Fuenfte-Flotte-Operationen sind noetig und rechtmaessig; saudische Yanbu-Umleitung und gemeldete Somaliland-Basis sind pragmatische Anpassungen. Vokabular: "UNCLOS", "freie Seefahrt", "Prosperity Guardian", "Aspides", "Fuenfte Flotte", "rechtmaessige Antwort", "Welthandelsordnung". Vorschrift: koalitionaere Marine-Praesenz, Eskortenfahrten, Sanktionen gegen Houthi-Ermoeglicher.',
 ARRAY['AMERICAS-USA','EUROPE-UK','NON-STATE-EU','MIDEAST-ISRAEL','MIDEAST-SAUDI'],
 ARRAY['Reuters','Associated Press','BBC World','France 24','France 24 (EN)','Financial Times','Bloomberg','Wall Street Journal','Nikkei Asia','Straits Times','Jerusalem Post','Times of Israel','Fox News','Al Arabiya','Al-Ahram','The National'],
 ARRAY['UNCLOS','freedom of navigation','Prosperity Guardian','Aspides','Fifth Fleet','lawful response','global trade'],
 true),

('houthi_naval_pressure_legitimate', 'red_sea_shipping_security', 2, 2,
 'Naval pressure is legitimate Gaza solidarity', 'Maritimer Druck als legitime Gaza-Solidaritaet',
 'Houthi targeting of Israel-linked shipping is legitimate non-state pressure tied to Gaza ceasefire',
 'Houthi-Schlaege gegen israelisch-verbundene Schifffahrt sind legitime nicht-staatliche Pression mit Gaza-Bezug',
 'Resistance-axis framing: Houthi targeting of Israel-linked shipping is a legitimate non-state form of pressure tied explicitly to a Gaza ceasefire; Western naval coalitions and reported Israeli outposts in Somaliland are imperial overreach into Yemeni and Arab maritime sovereignty. The vocabulary: "Israel-linked shipping", "Gaza linkage", "non-state pressure", "imperial overreach", "Western fleets", "Yemeni sovereignty", "Arab maritime sovereignty". Prescription: continue selective targeting until Gaza ceasefire; reject Western coalitions as illegitimate; oppose foreign basing on the Horn.',
 'Widerstandsachsen-Rahmung: Houthi-Schlaege gegen israelisch verbundene Schifffahrt sind legitime nicht-staatliche Pression mit explizitem Gaza-Bezug; westliche Marine-Koalitionen und gemeldete israelische Aussenposten in Somaliland sind imperiale Anmassung gegen jemenitische und arabische Seehoheit. Vokabular: "israelisch verbundene Schifffahrt", "Gaza-Verknuepfung", "nicht-staatliche Pression", "imperiale Anmassung", "westliche Flotten", "jemenitische Souveraenitaet". Vorschrift: gezielte Schlaege bis zum Gaza-Waffenstillstand fortsetzen.',
 ARRAY['MIDEAST-YEMEN','MIDEAST-IRAN'],
 ARRAY['Press TV','Al Jazeera','Al Mayadeen','Fars News','IRNA','TRT World','Anadolu Agency','Daily Sabah','CGTN','TASS (EN)'],
 ARRAY['Israel-linked shipping','Gaza linkage','non-state pressure','imperial overreach','Western fleets','Yemeni sovereignty'],
 true),

('houthi_resistance_strikes_legitimate', 'houthi_strikes_on_israel', 1, 2,
 'Solidarity strikes on Israel are legitimate', 'Solidaritaetsschlaege gegen Israel sind legitim',
 'Houthi missile and drone strikes on Israel are legitimate axis-of-resistance action',
 'Houthi-Raketen und -Drohnenangriffe auf Israel sind legitime Widerstandsachsen-Aktion',
 'Resistance-axis framing: Houthi missile and drone attacks on Israel are legitimate solidarity action with Gaza, coordinated with Iran and Hezbollah under a single axis-of-resistance command, deepening Israeli vulnerability and establishing a new deterrence equation. The vocabulary: "solidarity strikes", "axis command", "new deterrence equation", "Yemeni right to retaliate", "Israeli vulnerability". Prescription: integrated axis operations until Gaza ceasefire; develop Houthi missile and drone capabilities further.',
 'Widerstandsachsen-Rahmung: Houthi-Raketen und -Drohnen-Angriffe auf Israel sind legitime Solidaritaets-Aktion mit Gaza, koordiniert mit Iran und Hisbollah unter einem einheitlichen Widerstandsachsen-Kommando, vertiefen israelische Verwundbarkeit und etablieren eine neue Abschreckungsgleichung. Vokabular: "Solidaritaetsschlaege", "Achsen-Kommando", "neue Abschreckungsgleichung", "jemenitisches Vergeltungsrecht", "israelische Verwundbarkeit". Vorschrift: integrierte Achsen-Operationen bis zum Gaza-Waffenstillstand.',
 ARRAY['MIDEAST-YEMEN','MIDEAST-IRAN'],
 ARRAY['Press TV','Fars News','IRNA','Al Mayadeen','Al Jazeera','TRT World','Anadolu Agency','Daily Sabah','CGTN','TASS (EN)'],
 ARRAY['solidarity strikes','axis command','new deterrence equation','Yemeni right','Israeli vulnerability'],
 true),

('houthi_iranian_proxy_aggression', 'houthi_strikes_on_israel', 2, -2,
 'Iranian proxy aggression on Israel', 'Iranische Stellvertreter-Aggression gegen Israel',
 'Houthi strikes are Iranian-orchestrated proxy aggression requiring kinetic answer',
 'Houthi-Schlaege sind iranisch orchestrierte Stellvertreter-Aggression mit kinetischer Antwort',
 'Israeli, pro-Israel, and Saudi-aligned framing: Houthi strikes are Iranian-orchestrated proxy aggression demanding kinetic response on Yemeni soil (Hodeidah port, Sanaa airport, Houthi leadership) plus expanded regional partnerships (Somaliland base, deeper Gulf cooperation) to interdict Iranian weapons pipelines. The vocabulary: "Iranian-orchestrated", "proxy aggression", "Hodeidah port", "Sanaa airport", "Somaliland base", "weapons interdiction", "kinetic answer". Prescription: continue Israeli strikes on Yemeni targets, build Somaliland-Eilat air-defense partnership, sanction Iranian transit nodes.',
 'Israelische, pro-israelische und saudisch-orientierte Rahmung: Houthi-Schlaege sind iranisch orchestrierte Stellvertreter-Aggression mit kinetischer Antwort auf jemenitischem Boden (Hafen Hodeida, Flughafen Sanaa, Houthi-Fuehrung) plus erweiterten regionalen Partnerschaften (Somaliland-Basis, tiefere Golf-Kooperation) zur Unterbindung iranischer Waffenpipelines. Vokabular: "iranisch orchestriert", "Stellvertreter-Aggression", "Hafen Hodeida", "Flughafen Sanaa", "Somaliland-Basis", "Waffen-Unterbindung", "kinetische Antwort". Vorschrift: israelische Schlaege auf jemenitische Ziele fortsetzen.',
 ARRAY['MIDEAST-ISRAEL','AMERICAS-USA','MIDEAST-SAUDI'],
 ARRAY['Jerusalem Post','Times of Israel','The Times of Israel','i24NEWS','Israel Hayom','Fox News','Arutz Sheva','Haaretz','Al-Ahram','Al Arabiya','Arab News'],
 ARRAY['Iranian-orchestrated','proxy aggression','Hodeidah port','Sanaa airport','Somaliland base','weapons interdiction','kinetic answer'],
 true),

('saudi_coalition_legitimacy_restoration', 'saudi_houthi_war', 1, -2,
 'Restoring Yemeni legitimacy', 'Wiederherstellung jemenitischer Legitimitaet',
 'Saudi-led coalition is restoring the internationally-recognised Yemeni government',
 'Saudisch gefuehrte Koalition stellt die international anerkannte jemenitische Regierung wieder her',
 'Saudi, Egyptian, and pan-Arab Sunni framing: the Saudi-led coalition is restoring the internationally-recognised Yemeni government; Houthi rule in Sanaa is an Iran-backed coup; STC self-dissolution and southern unification under the Presidential Leadership Council are necessary; UAE-backed separatism was a destabilising mistake. The vocabulary: "legitimate Yemeni government", "Presidential Leadership Council", "Iran-backed coup", "southern unification", "STC mistake", "Saudi reconstruction". Prescription: continued coalition military pressure on Houthi forces, southern political consolidation under the PLC, Saudi-funded reconstruction.',
 'Saudische, aegyptische und panarabische sunnitische Rahmung: die saudisch gefuehrte Koalition stellt die international anerkannte jemenitische Regierung wieder her; Houthi-Herrschaft in Sanaa ist ein iranisch gestuetzter Putsch; STC-Selbstaufloesung und suedliche Vereinheitlichung unter dem Praesidialen Fuehrungsrat sind noetig; VAE-gestuetzter Separatismus war ein destabilisierender Fehler. Vokabular: "legitime jemenitische Regierung", "Praesidialer Fuehrungsrat", "iranisch gestuetzter Putsch", "suedliche Vereinheitlichung", "STC-Fehler", "saudischer Wiederaufbau". Vorschrift: koalitionaerer Militaer-Druck, suedliche politische Konsolidierung unter dem PLC.',
 ARRAY['MIDEAST-SAUDI','MIDEAST-EGYPT','MIDEAST-GULF'],
 ARRAY['Al-Ahram','Al Arabiya','Arab News','The National','Khaleej Times','Gulf News','Egypt Today','Daily Sabah','Anadolu Agency'],
 ARRAY['legitimate government','Presidential Leadership Council','Iran-backed coup','southern unification','STC mistake','Saudi reconstruction'],
 true),

('houthi_authority_legitimate_resistance', 'saudi_houthi_war', 2, 2,
 'Sanaa government is legitimate national authority', 'Regierung in Sanaa als legitime nationale Autoritaet',
 'Houthi-led Sanaa authority is legitimate national resistance to Saudi-Western intervention',
 'Houthi-gefuehrte Sanaa-Autoritaet ist legitimer nationaler Widerstand gegen saudisch-westliche Intervention',
 'Resistance-axis and critical pan-Arab framing: the de facto Sanaa authority represents Yemeni national resistance to Saudi and Western intervention; the Saudi-led coalition is an aggressor that has destroyed Yemeni infrastructure; the STC was a UAE-backed colonial project whose collapse exposes coalition failure. The vocabulary: "Sanaa authority", "national resistance", "Saudi aggression", "coalition aggression", "STC colonial project", "coalition failure". Prescription: international acceptance of de facto Sanaa governance, end of coalition strikes, withdrawal of foreign forces.',
 'Widerstandsachsen- und kritisch panarabische Rahmung: die faktische Sanaa-Autoritaet vertritt jemenitischen nationalen Widerstand gegen saudisch-westliche Intervention; die saudisch gefuehrte Koalition ist ein Aggressor, der jemenitische Infrastruktur zerstoert hat; der STC war ein VAE-gestuetztes Kolonialprojekt, dessen Kollaps das Scheitern der Koalition belegt. Vokabular: "Sanaa-Autoritaet", "nationaler Widerstand", "saudische Aggression", "Koalitions-Aggression", "STC-Kolonialprojekt", "Koalitions-Scheitern". Vorschrift: internationale Anerkennung der faktischen Sanaa-Regierungsfuehrung, Ende der Koalitions-Schlaege.',
 ARRAY['MIDEAST-YEMEN','MIDEAST-IRAN'],
 ARRAY['Press TV','Al Jazeera','Al Mayadeen','Fars News','IRNA'],
 ARRAY['Sanaa authority','national resistance','Saudi aggression','coalition aggression','STC colonial project','coalition failure'],
 true);

-- ============================================================
-- 4. Sanity check
-- ============================================================

DO $$
DECLARE
    n_fn integer; n_nar integer; n_anchor integer;
BEGIN
    SELECT COUNT(*) INTO n_fn FROM friction_nodes WHERE id IN
        ('yemen_red_sea_theater','red_sea_shipping_security','houthi_strikes_on_israel','saudi_houthi_war');
    SELECT COUNT(*) INTO n_nar FROM narratives_v2 WHERE fn_id IN
        ('yemen_red_sea_theater','red_sea_shipping_security','houthi_strikes_on_israel','saudi_houthi_war');
    SELECT COUNT(*) INTO n_anchor FROM taxonomy_v3
        WHERE taxonomy_function = 'fn_anchor' AND linked_id IN
        ('yemen_red_sea_theater','red_sea_shipping_security','houthi_strikes_on_israel','saudi_houthi_war');
    IF n_fn <> 4 OR n_nar <> 9 OR n_anchor <> 4 THEN
        RAISE EXCEPTION 'Yemen theater sanity check failed: friction_nodes=%, narratives=%, fn_anchors=% (expected 4/9/4)',
            n_fn, n_nar, n_anchor;
    END IF;
END $$;

COMMIT;
