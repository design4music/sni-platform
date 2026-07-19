-- ============================================================================
-- fn_anchor BUNDLE BACKFILL -- RENDER SYNC
-- Generated 2026-07-18 from verified LOCAL state.
-- ============================================================================
--
-- RUN ON RENDER MANUALLY (docker postgres:18 psql), after a pg_dump -Fc backup.
-- safe_db_migrate.py is local-only by design.
--
-- WHY THIS EXISTS
-- fn_anchor bundles are written by scripts/apply_fn_anchor_bundle.py, which
-- targets whatever DB the environment points at -- in practice always local.
-- They therefore never travelled with the per-theater migrations. A read-only
-- audit of Render on 2026-07-18 found 46 active atomics with no bundle, of
-- which 27 already had a finished bundle sitting on local. An atomic without a
-- bundle matches NOTHING, so a bootstrap on Render would silently return zero
-- events for it and look like a failed build rather than a missing input.
--
-- THIS FILE CARRIES 22 OF THOSE 27. The other five are deliberately excluded:
--   colombia_us_alignment / colombia_political_transition /
--   colombia_armed_groups_peace
--       -> shipped by 20260718_colombia_render_sync.sql, which also creates
--          their friction_nodes rows. One owner per row.
--   us_russia_bilateral_channel / us_russia_sanctions_leverage
--       -> their friction_nodes rows do NOT exist on Render yet (parallel
--          session's work in progress). Inserting the bundle first would leave
--          it orphaned. Ships with that theater's own sync.
--
-- All 22 ids here were confirmed present in friction_nodes on Render, so no
-- bundle inserted by this file is orphaned.
--
-- NOT IN SCOPE -- the remaining 21 active atomics have no bundle on EITHER
-- side, because their theaters are not built yet (cuba x3, sahel x4,
-- ethiopia x3, drc/great-lakes x4, balkans x2, somalia, us domestic x4).
-- Those need authoring, not syncing.
--
-- SAFETY: no DELETE, TRUNCATE, DROP or ALTER. Every statement is an idempotent
-- upsert on the partial unique index idx_taxonomy_v3_unique_fn_anchor
-- (linked_id) WHERE taxonomy_function='fn_anchor' AND is_active. Re-running
-- converges on local state. Rollback: see the .ROLLBACK.sql companion.
--
-- Attribution is NOT touched -- bootstrap on Render stays deferred until all
-- remaining theaters are built. Bundles must land BEFORE that batch bootstrap,
-- otherwise it produces zeros for these 22.
--
-- EXPECTED ALIAS COUNTS after apply (verification block repeats this):
--   alberta_separatism_us_ties       81
--   aukus_alliance_reliability       38
--   australia_china_trade_leverage   244
--   balochistan_insurgency           31
--   canada_sovereignty_pressure      82
--   china_threat_assessment          253
--   essequibo_dispute                24
--   india_pakistan_militancy         24
--   indus_water_sharing              32
--   kashmir_dispute                  28
--   latam_eu_market_access           21
--   latam_resource_access            93
--   latam_us_trade_pressure          35
--   myanmar_civil_conflict           30
--   pacific_island_contest           223
--   pakistan_afghanistan_border      79
--   thailand_cambodia_border         57
--   us_canada_trade_coercion         139
--   us_russia_arms_control           133
--   us_venezuela_relations           195
--   venezuela_political_transition   182
--   venezuela_sanctions_oil          189
--
-- ============================================================================

BEGIN;

-- alberta_separatism_us_ties (81 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'alberta_separatism_us_ties', 'alberta_separatism_us_ties fn_anchor', '{"ar": ["انفصالي", "انفصال", "استفتاء الاستقلال", "مشروع ازدهار ألبرتا", "خيانة", "التدخل الأجنبي", "الوحدة الوطنية", "حقوق المعاهدات"], "de": ["Separatis", "Sezession", "Abspaltung", "Unabhängigkeitsreferendum", "Volksabstimmung", "Landesverrat", "ausländische Einmischung", "nationale Einheit", "Vertragsrechte"], "en": ["separatis", "secession", "secede", "referendum", "independence vote", "Alberta Prosperity", "Wexit", "Republic of Alberta", "Sovereignty Act", "treason", "foreign interference", "foreign actor", "national unity", "Western alienation", "equalization", "treaty rights"], "es": ["separatis", "secesión", "referéndum", "injerencia extranjera", "unidad nacional", "derechos de tratado"], "fr": ["séparatis", "sécession", "référendum", "ingérence étrangère", "unité nationale", "droits issus de traités"], "hi": ["अलगाववाद", "पृथक्करण", "जनमत संग्रह", "राजद्रोह", "विदेशी हस्तक्षेप", "राष्ट्रीय एकता", "संधि अधिकार"], "it": ["separatis", "secessione", "referendum", "ingerenza straniera", "unità nazionale", "diritti dei trattati"], "ja": ["分離独立", "離脱", "独立住民投票", "アルバータ独立運動", "反逆", "外国干渉", "国民統合", "条約上の権利"], "ru": ["сепаратис", "отделение", "референдум", "измена", "иностранное вмешательство", "национальное единство", "договорные права"], "zh": ["分离主义", "脱离", "独立公投", "艾伯塔繁荣计划", "叛国", "外国干预", "国家团结", "条约权利"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- aukus_alliance_reliability (38 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'aukus_alliance_reliability', 'aukus_alliance_reliability fn_anchor', '{"ar": ["أوكوس", "غواصة", "غواصة نووية"], "de": ["U-Boot", "Unterseeboot", "Unterwasserdrohne"], "en": ["AUKUS", "submarine", "Virginia-class", "Collins-class", "SSN", "nuclear-powered boat", "underwater drone", "unmanned underwater", "HMAS Stirling", "Naval Support Activity Stirling", "Submarine Rotational Force"], "es": ["submarino", "dron submarino"], "fr": ["sous-marin", "drone sous-marin"], "hi": ["ऑकस", "पनडुब्बी", "परमाणु पनडुब्बी"], "it": ["sottomarino", "drone sottomarino"], "ja": ["オーカス", "潜水艦", "原子力潜水艦", "水中ドローン"], "ru": ["АУКУС", "подводная лодка", "подводный дрон"], "zh": ["奥库斯", "美英澳", "潜艇", "核潜艇", "水下无人机"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- australia_china_trade_leverage (244 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'australia_china_trade_leverage', 'australia_china_trade_leverage fn_anchor', '{"ar": ["لحم البقر", "الشعير", "النبيذ", "خام الحديد", "الفحم", "المعادن النادرة", "الليثيوم", "تعريفة جمركية", "حصة", "مكافحة الإغراق", "حظر التصدير", "قيود التصدير", "الوصول إلى السوق", "حاجز تجاري", "سلسلة التوريد", "وزارة التجارة الصينية", "بيع الحصص", "فحص الاستثمار", "المشتري الحكومي"], "de": ["Rindfleisch", "Gerste", "Hummer", "Eisenerz", "Kohle", "seltene Erden", "kritische Mineralien", "Lithium", "Quote", "Antidumping", "Exportverbot", "Importverbot", "Ausfuhrbeschränkung", "Marktzugang", "Handelsbarriere", "Freihandel", "Lieferkette", "Embargo", "Veräußerung", "Anteilsverkauf", "Investitionsprüfung", "Hafenpacht", "staatlicher Käufer", "Preisstreit"], "en": ["beef", "barley", "wine", "lobster", "canola", "iron ore", "coal", "rare earth", "critical mineral", "lithium", "apple", "bull semen", "tariff", "quota", "anti-dumping", "dumping", "export ban", "import ban", "export restriction", "export licence", "export license", "market access", "trade barrier", "customs", "free trade", "trade deal", "supply chain", "embargo", "suspension", "MOFCOM", "ChAFTA", "CMRG", "FIRB", "Foreign Investment Review Board", "Fortescue", "Lynas", "Landbridge", "Darwin Port", "Treasury Wine", "divest", "stake sale", "forced sale", "investment screening", "national interest test", "port lease", "state buyer", "state-owned buyer", "price index", "pricing dispute"], "es": ["carne de vacuno", "cebada", "langosta", "mineral de hierro", "carbón", "tierras raras", "minerales críticos", "arancel", "cuota", "antidumping", "prohibición de exportación", "restricción a la exportación", "acceso al mercado", "barrera comercial", "libre comercio", "cadena de suministro", "embargo", "desinversión", "venta de participación", "control de inversiones", "comprador estatal"], "fr": ["boeuf", "homard", "minerai de fer", "charbon", "terres rares", "minéraux critiques", "lithium", "tarif douanier", "antidumping", "interdiction d''exportation", "restriction à l''exportation", "accès au marché", "barrière commerciale", "libre-échange", "chaîne d''approvisionnement", "embargo", "cession", "vente de participation", "contrôle des investissements", "acheteur d''État", "différend tarifaire"], "hi": ["गोमांस", "जौ", "शराब", "लौह अयस्क", "कोयला", "दुर्लभ पृथ्वी", "लिथियम", "शुल्क", "कोटा", "डंपिंग रोधी", "निर्यात प्रतिबंध", "बाजार पहुंच", "व्यापार बाधा", "मुक्त व्यापार", "आपूर्ति श्रृंखला", "वाणिज्य मंत्रालय", "विनिवेश", "हिस्सेदारी बिक्री", "निवेश जांच", "राज्य खरीदार"], "it": ["carne bovina", "aragosta", "minerale di ferro", "carbone", "terre rare", "minerali critici", "tariffa", "antidumping", "divieto di esportazione", "accesso al mercato", "barriera commerciale", "libero scambio", "catena di approvvigionamento", "cessione", "vendita di quote", "controllo degli investimenti", "acquirente statale"], "ja": ["牛肉", "大麦", "ワイン", "ロブスター", "鉄鉱石", "石炭", "レアアース", "重要鉱物", "リチウム", "関税", "割当", "反ダンピング", "輸出禁止", "輸出制限", "市場アクセス", "貿易障壁", "自由貿易", "サプライチェーン", "商務省", "株式売却", "投資審査", "国有買い手", "価格指数"], "ru": ["говядина", "ячмень", "вино", "железная руда", "уголь", "редкоземельные", "критические минералы", "литий", "пошлина", "квота", "антидемпинг", "запрет на экспорт", "ограничение экспорта", "доступ на рынок", "торговый барьер", "цепочка поставок", "эмбарго", "Минкоммерции", "продажа доли", "проверка инвестиций", "государственный покупатель", "ценовой спор"], "zh": ["牛肉", "大麦", "葡萄酒", "龙虾", "铁矿石", "煤炭", "稀土", "关键矿产", "锂", "关税", "配额", "反倾销", "出口禁令", "出口限制", "市场准入", "贸易壁垒", "自由贸易", "供应链", "禁运", "商务部", "中国矿产资源集团", "出售股份", "投资审查", "强制出售", "国家买家", "价格指数", "定价争端", "港口租约"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- balochistan_insurgency (31 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'balochistan_insurgency', 'balochistan_insurgency fn_anchor', '{"ar": ["بلوشستان", "كويتا", "جيش تحرير بلوشستان", "انفصاليين"], "de": ["Belutschistan", "Separatisten"], "en": ["Baloch", "Gwadar", "Quetta", "BLA", "Balochistan Liberation", "Mahrang", "separatist", "enforced disappearance"], "es": ["Beluchistán", "separatistas"], "fr": ["Baloutchistan", "séparatistes"], "hi": ["बलूचिस्तान", "क्वेटा", "अलगाववादी"], "it": ["Belucistan"], "ja": ["バルチスタン"], "ru": ["Белуджистан", "Кветта", "Армия освобождения Белуджистана", "сепаратист", "повстанц"], "zh": ["俾路支", "俾路支解放军", "分离主义"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- canada_sovereignty_pressure (82 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'canada_sovereignty_pressure', 'canada_sovereignty_pressure fn_anchor', '{"ar": ["الضم", "الولاية الحادية والخمسين", "السيادة", "جسر غوردي هاو", "القبة الذهبية", "التبعية الاقتصادية", "النظام العالمي", "مقاطعة"], "de": ["Annexion", "Anschluss", "51. Staat", "Souveränität", "Golden Dome", "Abhängigkeit", "Weltordnung", "Boykott"], "en": ["annex", "51st state", "statehood", "sovereignt", "Gordie Howe", "Detroit-Windsor", "Ambassador Bridge", "Board of Peace", "Golden Dome", "dependence", "world order", "boycott", "Buy Canadian"], "es": ["anexión", "estado 51", "soberanía", "Cúpula Dorada", "dependencia", "orden mundial", "boicot"], "fr": ["annexion", "51e État", "souveraineté", "Dôme doré", "dépendance", "ordre mondial", "boycott"], "hi": ["विलय", "51वां राज्य", "संप्रभुता", "गोर्डी होवे पुल", "गोल्डन डोम", "निर्भरता", "विश्व व्यवस्था", "बहिष्कार"], "it": ["annessione", "51esimo stato", "sovranità", "Cupola Dorata", "dipendenza", "ordine mondiale", "boicottaggio"], "ja": ["併合", "51番目の州", "主権", "ゴーディ・ハウ橋", "ゴールデンドーム", "依存", "世界秩序", "ボイコット"], "ru": ["аннекси", "51-й штат", "суверенитет", "мост Горди Хоу", "Золотой купол", "зависимость", "мировой порядок", "бойкот"], "zh": ["吞并", "第51个州", "主权", "戈迪豪大桥", "黄金穹顶", "依赖", "世界秩序", "抵制"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- china_threat_assessment (253 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'china_threat_assessment', 'china_threat_assessment fn_anchor', '{"ar": ["وكالة استخبارات", "مركز أبحاث", "العيون الخمس", "تجسس", "جاسوس", "تدخل أجنبي", "تدخل", "اختراق", "تجنيد", "مراقبة", "هجوم سيبراني", "قرصنة", "تسريب بيانات", "بنية تحتية حيوية", "صاروخ", "باليستي", "قدرة الضربة", "رأس نووي", "سفينة حربية", "توغل", "المنطقة الاقتصادية الخالصة"], "de": ["Geheimdienst", "Denkfabrik", "Nachrichtendienst", "Spionage", "Spion", "ausländische Einflussnahme", "Einflussnahme", "Unterwanderung", "verdeckt", "Anwerbung", "Überwachung", "Sabotage", "Cyberangriff", "Hacker", "Datenleck", "kritische Infrastruktur", "staatlich gesteuert", "Rakete", "ballistisch", "Angriffsreichweite", "atomwaffenfähig", "Sprengkopf", "Flottille", "Kriegsschiff", "Eindringen", "ausschließliche Wirtschaftszone", "Aufrüstung"], "en": ["ASIO", "ASD", "ASPI", "Lowy", "Five Eyes", "think tank", "intelligence agency", "spy agency", "spy chief", "espionage", "spy", "spies", "foreign interference", "interference", "infiltrate", "infiltration", "covert", "informant", "recruit", "United Front", "Confucius Institute", "influence operation", "sabotage", "surveillance", "cyber", "hacking", "hacker", "data breach", "critical infrastructure", "state-sponsored", "missile", "ballistic", "strike capacity", "strike capability", "strike range", "nuclear-capable", "warhead", "flotilla", "warship", "circumnavigat", "incursion", "intercept", "sonar", "EEZ", "exclusive economic zone", "military buildup", "military build-up", "force projection"], "es": ["agencia de inteligencia", "centro de estudios", "espionaje", "espía", "injerencia extranjera", "injerencia", "infiltración", "reclutamiento", "vigilancia", "sabotaje", "ciberataque", "pirata informático", "filtración de datos", "infraestructura crítica", "misil", "balístico", "capacidad de ataque", "con capacidad nuclear", "ojiva", "flotilla", "buque de guerra", "incursión", "zona económica exclusiva"], "fr": ["services de renseignement", "groupe de réflexion", "espionnage", "espion", "ingérence étrangère", "ingérence", "infiltration", "recrutement", "surveillance", "sabotage", "cyberattaque", "pirate informatique", "fuite de données", "infrastructure critique", "missile", "balistique", "capacité de frappe", "à capacité nucléaire", "ogive", "flottille", "navire de guerre", "incursion", "zone économique exclusive"], "hi": ["खुफिया एजेंसी", "थिंक टैंक", "फाइव आईज", "जासूसी", "जासूस", "विदेशी हस्तक्षेप", "हस्तक्षेप", "घुसपैठ", "भर्ती", "निगरानी", "साइबर हमला", "हैकिंग", "डेटा उल्लंघन", "महत्वपूर्ण बुनियादी ढांचा", "मिसाइल", "बैलिस्टिक", "हमला क्षमता", "परमाणु हथियार", "युद्धपोत", "विशेष आर्थिक क्षेत्र"], "it": ["agenzia di intelligence", "centro studi", "spionaggio", "spia", "ingerenza straniera", "ingerenza", "infiltrazione", "reclutamento", "sorveglianza", "attacco informatico", "violazione dei dati", "infrastruttura critica", "missile", "balistico", "capacità di attacco", "testata", "nave da guerra", "incursione", "zona economica esclusiva"], "ja": ["情報機関", "シンクタンク", "ファイブアイズ", "スパイ活動", "スパイ", "外国干渉", "浸透", "工作", "統一戦線", "孔子学院", "監視", "サイバー攻撃", "ハッカー", "情報漏洩", "重要インフラ", "ミサイル", "弾道", "打撃能力", "核弾頭", "軍艦", "侵入", "排他的経済水域", "軍拡"], "ru": ["разведывательное агентство", "аналитический центр", "спецслужба", "шпионаж", "шпион", "иностранное вмешательство", "вмешательство", "вербовка", "слежка", "диверсия", "кибератака", "хакер", "утечка данных", "критическая инфраструктура", "ракета", "баллистическая", "ударный потенциал", "ядерный боезаряд", "флотилия", "военный корабль", "вторжение", "исключительная экономическая зона"], "zh": ["情报机构", "智库", "五眼联盟", "洛伊研究所", "间谍活动", "间谍", "外国干涉", "渗透", "策反", "统战", "孔子学院", "监控", "破坏活动", "网络攻击", "黑客", "数据泄露", "关键基础设施", "国家支持", "导弹", "弹道", "打击能力", "核弹头", "军舰", "闯入", "专属经济区", "军力扩张", "环航"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- essequibo_dispute (24 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'essequibo_dispute', 'essequibo_dispute fn_anchor', '{"ar": ["إيسيكيبو", "إسيكيبو", "محكمة العدل الدولية"], "de": ["Internationaler Gerichtshof", "Weltgericht"], "en": ["Essequibo", "Esequibo", "Guayana Esequiba", "Guyana Esequiba", "Stabroek", "World Court", "International Court of Justice"], "es": ["Corte Internacional de Justicia", "Tribunal Internacional"], "fr": ["Cour internationale de justice"], "hi": ["एसेक्विबो"], "it": ["Corte internazionale di giustizia"], "ja": ["エセキボ", "国際司法裁判所"], "ru": ["Эссекибо", "Эсекибо", "Международный суд"], "zh": ["埃塞奎博", "国际法院"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- india_pakistan_militancy (24 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'india_pakistan_militancy', 'india_pakistan_militancy fn_anchor', '{"ar": ["عسكر طيبة", "جيش محمد", "باهالغام"], "de": [], "en": ["Lashkar", "Hafiz Saeed", "Masood Azhar", "Hizbul", "Al Badr", "Dawood", "ISI", "Pahalgam", "Sindoor", "Pulwama"], "es": [], "fr": [], "hi": ["लश्कर", "जैश", "पहलगाम", "सिंदूर"], "it": [], "ja": ["パハルガム"], "ru": ["Лашкар-е-Тайба", "Джаиш-е-Мохаммад", "Пахалгам"], "zh": ["虔诚军", "穆罕默德军", "帕哈尔加姆"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- indus_water_sharing (32 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'indus_water_sharing', 'indus_water_sharing fn_anchor', '{"ar": ["معاهدة مياه السند", "تشيناب"], "de": ["Indus-Wasser", "Indus-Vertrag"], "en": ["Indus Waters", "IWT", "Permanent Indus Commission", "Chenab", "Jhelum", "Sutlej", "Kishanganga", "Baglihar", "Ratle", "Tarbela", "Mangla", "pondage", "Court of Arbitration"], "es": ["Aguas del Indo"], "fr": ["eaux de l''Indus"], "hi": ["सिंधु जल संधि", "चिनाब", "झेलम", "किशनगंगा", "बगलिहार"], "it": ["acque dell''Indo"], "ja": ["インダス川水条約"], "ru": ["водах Инда", "Договор о водах Инда", "Ченаб", "Джелам"], "zh": ["印度河水条约", "杰赫勒姆"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- kashmir_dispute (28 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'kashmir_dispute', 'kashmir_dispute fn_anchor', '{"ar": ["كشمير", "جامو", "سريناغار", "المادة 370"], "de": ["Kaschmir", "Artikel 370"], "en": ["Kashmir", "J&K", "PoK", "Jammu", "Srinagar", "Gilgit", "Baltistan", "Article 370"], "es": ["Cachemira"], "fr": ["Cachemire"], "hi": ["कश्मीर", "जम्मू", "श्रीनगर", "अनुच्छेद 370"], "it": [], "ja": ["カシミール"], "ru": ["Кашмир", "Джамму", "Сринагар", "статья 370"], "zh": ["克什米尔", "查谟", "370条"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- latam_eu_market_access (21 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'latam_eu_market_access', 'latam_eu_market_access fn_anchor', '{"ar": ["ميركوسور", "إزالة الغابات"], "de": ["EFTA-Abkommen", "Entwaldungsverordnung"], "en": ["Mercosur", "Mercosul", "EFTA", "EUDR", "deforestation regulation"], "es": ["AELC", "reglamento de deforestación"], "fr": ["règlement sur la déforestation"], "hi": ["मर्कोसुर", "वनों की कटाई"], "it": ["regolamento sulla deforestazione"], "ja": ["メルコスール", "森林破壊防止"], "ru": ["Меркосур", "вырубк"], "zh": ["南方共同市场", "零毁林"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- latam_resource_access (93 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'latam_resource_access', 'latam_resource_access fn_anchor', '{"ar": ["المعادن الحرجة", "التعدين", "الليثيوم", "النحاس", "العناصر الأرضية النادرة", "الحزام والطريق", "هواوي", "السكك الحديدية"], "de": ["kritische Rohstoffe", "Bergbau", "Kupfer", "Seltene Erden", "Seidenstraße", "Eisenbahn"], "en": ["critical mineral", "mineral", "mining", "lithium", "copper", "rare earth", "Belt and Road", "BRI", "Huawei", "BYD", "Ganfeng", "Sinopec", "CNOOC", "COSCO", "Zijin", "Tianqi", "State Grid", "ByteDance", "Chancay", "panda bond", "railway", "railroad", "dredging"], "es": ["minerales críticos", "minera", "minería", "de litio", "cobre", "tierras raras", "Franja y la Ruta", "ferrocarril", "hidrovía"], "fr": ["minéraux critiques", "terres rares", "route de la soie", "chemin de fer"], "hi": ["महत्वपूर्ण खनिज", "खनन", "लिथियम", "तांबा", "दुर्लभ मृदा", "बेल्ट एंड रोड", "हुआवेई", "रेलवे"], "it": ["minerali critici", "estrazione mineraria", "terre rare", "via della seta", "ferrovia"], "ja": ["重要鉱物", "鉱山", "リチウム", "銅鉱", "レアアース", "一帯一路", "ファーウェイ", "鉄道"], "ru": ["критически важных минерал", "добыч", "литий", "медь", "редкозем", "Пояс и путь", "Хуавэй", "железнодорож"], "zh": ["关键矿产", "采矿", "锂矿", "铜矿", "稀土", "一带一路", "华为", "比亚迪", "赣锋", "紫金", "国家电网", "钱凯", "熊猫债", "铁路"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- latam_us_trade_pressure (35 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'latam_us_trade_pressure', 'latam_us_trade_pressure fn_anchor', '{"ar": ["تعريفة جمركية", "عقوبات"], "de": ["Zoll", "Strafzoll", "Sanktion"], "en": ["tariff", "sanction", "Magnitsky", "OFAC", "USTR", "Section 301", "countervailing", "antidumping", "anti-dumping", "decertif"], "es": ["arancel", "sanción", "sanciones", "derechos compensatorios", "descertificación"], "fr": ["droits de douane"], "hi": ["टैरिफ", "प्रतिबंध"], "it": ["dazio", "sanzione"], "ja": ["関税", "制裁", "反ダンピング"], "ru": ["пошлин", "санкц", "Магнитск"], "zh": ["关税", "制裁", "马格尼茨基", "反倾销"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- myanmar_civil_conflict (30 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'myanmar_civil_conflict', 'myanmar_civil_conflict fn_anchor', '{"ar": ["ميانمار", "بورما"], "de": ["Birma"], "en": ["Myanmar", "Burma", "Naypyidaw", "Naypyitaw", "Yangon", "Rangoon", "Rakhine", "Rohingya", "Tatmadaw", "Myawaddy", "Min Aung Hlaing", "Suu Kyi", "USDP"], "es": ["Birmania"], "fr": ["Birmanie"], "hi": ["म्यांमार", "म्यांमा", "बर्मा"], "it": ["Birmania"], "ja": ["ミャンマー", "ビルマ", "スーチー"], "ru": ["Мьянм", "Бирма"], "zh": ["缅甸", "敏昂莱", "昂山素季"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- pacific_island_contest (223 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'pacific_island_contest', 'pacific_island_contest fn_anchor', '{"ar": ["اتفاق أمني", "معاهدة أمنية", "اتفاقية دفاعية", "معاهدة دفاعية", "قاعدة عسكرية", "قاعدة بحرية", "وجود عسكري", "منتدى جزر المحيط الهادئ", "علاقات دبلوماسية", "مجال النفوذ", "نفوذ", "مساعدات تنموية", "فخ الديون", "معاهدة", "مذكرة تفاهم", "تصديق", "توقيع"], "de": ["Sicherheitspakt", "Sicherheitsabkommen", "Verteidigungspakt", "Verteidigungsabkommen", "Verteidigungsbündnis", "Militärbasis", "Militärstützpunkt", "Marinestützpunkt", "Militärpräsenz", "Hafenzugang", "diplomatische Beziehungen", "Einflusssphäre", "Einfluss", "Ausrichtung", "Hilfspaket", "Entwicklungshilfe", "Schuldenfalle", "Vertrag", "Absichtserklärung", "Ratifizierung", "Unterzeichnung"], "en": ["security pact", "security agreement", "security deal", "defence pact", "defense pact", "defence treaty", "defense treaty", "defence agreement", "defense agreement", "mutual defence", "mutual defense", "defence alliance", "defense alliance", "security cooperation", "policing", "military base", "naval base", "foreign base", "military presence", "basing", "port access", "wharf", "airstrip", "runway upgrade", "Pacific Islands Forum", "Melanesian Spearhead Group", "Pacific Policing Initiative", "policing initiative", "Falepili", "Boe Declaration", "Blue Pacific", "Compact of Free Association", "Nauru Agreement", "Forum Fisheries", "diplomatic ties", "switch recognition", "diplomatic recognition", "one-China", "Taiwan", "sphere of influence", "influence", "courting", "align", "alignment", "tilt", "pivot", "step up", "aid package", "development assistance", "medical team", "health aid", "budget support", "infrastructure loan", "debt trap", "seabed mineral", "co-op", "treaty", "pact", "memorandum of understanding", "ratify", "ratification", "signing ceremony", "communique"], "es": ["pacto de seguridad", "acuerdo de seguridad", "pacto de defensa", "tratado de defensa", "alianza de defensa", "base militar", "base naval", "presencia militar", "acceso portuario", "relaciones diplomáticas", "esfera de influencia", "influencia", "ayuda al desarrollo", "trampa de deuda", "tratado", "memorando de entendimiento", "ratificación", "firma"], "fr": ["pacte de sécurité", "accord de sécurité", "pacte de défense", "traité de défense", "alliance de défense", "base militaire", "base navale", "présence militaire", "accès portuaire", "relations diplomatiques", "sphère d''influence", "influence", "aide au développement", "piège de la dette", "traité", "protocole d''accord", "ratification", "signature"], "hi": ["सुरक्षा समझौता", "रक्षा समझौता", "रक्षा संधि", "सैन्य अड्डा", "नौसैनिक अड्डा", "सैन्य उपस्थिति", "प्रशांत द्वीप समूह मंच", "राजनयिक संबंध", "प्रभाव क्षेत्र", "प्रभाव", "विकास सहायता", "ऋण जाल", "संधि", "समझौता ज्ञापन", "अनुसमर्थन", "हस्ताक्षर"], "it": ["patto di sicurezza", "accordo di sicurezza", "patto di difesa", "trattato di difesa", "base militare", "base navale", "presenza militare", "relazioni diplomatiche", "sfera di influenza", "influenza", "aiuto allo sviluppo", "trappola del debito", "trattato", "memorandum d''intesa", "ratifica", "firma"], "ja": ["安全保障協定", "防衛協定", "安保協定", "軍事基地", "海軍基地", "軍事拠点", "太平洋諸島フォーラム", "外交関係", "勢力圏", "影響力", "開発援助", "債務の罠", "条約", "覚書", "批准", "署名"], "ru": ["пакт о безопасности", "соглашение о безопасности", "оборонный пакт", "договор об обороне", "военная база", "военно-морская база", "военное присутствие", "Форум тихоокеанских островов", "дипломатические отношения", "сфера влияния", "влияние", "помощь в развитии", "долговая ловушка", "договор", "меморандум о взаимопонимании", "ратификация", "подписание"], "zh": ["安全协议", "安全协定", "防务协议", "防卫协定", "共同防御", "军事基地", "海军基地", "军事存在", "港口准入", "太平洋岛国论坛", "蓝色太平洋", "外交关系", "势力范围", "影响力", "发展援助", "债务陷阱", "建交", "条约", "谅解备忘录", "批准", "签署"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- pakistan_afghanistan_border (79 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'pakistan_afghanistan_border', 'pakistan_afghanistan_border fn_anchor', '{"ar": ["طالبان", "تحريك طالبان", "كابول", "قندهار", "ننجرهار", "خط ديوراند", "غارة جوية", "الحدود", "مسلحين"], "de": ["Durand-Linie", "Luftangriff", "Grenzkonflikt", "Grenzgebiet", "Militante"], "en": ["Taliban", "TTP", "Tehreek-e-Taliban", "Haqqani", "ISPR", "Ghazab", "Kabul", "Kandahar", "Nangarhar", "Kunar", "Bajaur", "Torkham", "Khyber Pakhtunkhwa", "Angoor Adda", "Landi Kotal", "Durand", "airstrike", "strike", "cross-border", "border", "militant", "hideout", "clash", "retaliat", "checkpost", "ceasefire"], "es": ["Línea Durand", "ataque aéreo", "frontera", "milicianos"], "fr": ["ligne Durand", "frappe aérienne", "frontière"], "hi": ["तालिबान", "काबुल", "कंधार", "डूरंड रेखा", "हवाई हमला", "सीमा पार", "आतंकवादी"], "it": ["attacco aereo", "frontiera"], "ja": ["タリバン", "カブール", "カンダハル", "デュランド線", "空爆", "国境", "越境"], "ru": ["Талибан", "Техрик-е Талибан", "Кабул", "Кандагар", "линия Дюранда", "авиаудар", "боевик", "приграничн"], "zh": ["塔利班", "巴基斯坦塔利班", "喀布尔", "坎大哈", "杜兰德线", "空袭", "边境", "武装分子"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- thailand_cambodia_border (57 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'thailand_cambodia_border', 'thailand_cambodia_border fn_anchor', '{"ar": ["الحدود التايلاندية الكمبودية", "بريا فيهير"], "de": ["thailändisch-kambodschanisch", "kambodschanisch-thailändisch"], "en": ["Thai-Cambod", "Thailand-Cambod", "Cambodia-Thai", "Cambodian-Thai", "Cambodia-Thailand", "Thai-Khmer", "Khmer-Thai", "Thai–Cambod", "Thailand–Cambod", "Cambodia–Thai", "Cambodian–Thai", "Cambodia–Thailand", "Thai–Khmer", "Khmer–Thai", "Preah Vihear", "Ta Moan", "Ta Muen", "Ta Krabey", "Emerald Triangle", "Chong An Ma", "Chong Bok", "Chong Chom", "Chong Sa-Ngam", "Mom Bei", "Phu Makhuea", "MOU 44", "MOU44", "MOU 43", "MOU43", "Koh Kood", "Ko Kut", "Overlapping Claims Area", "Joint Boundary Committee", "General Border Committee", "Hun Manet", "Si Sa Ket", "Sisaket", "Oddar Meanchey"], "es": ["tailandés-camboyano", "camboyano-tailandés"], "fr": ["thaïlando-cambodgien"], "hi": ["थाईलैंड-कंबोडिया", "कंबोडिया-थाईलैंड", "प्रेह विहार"], "it": ["thailandese-cambogiano"], "ja": ["タイ・カンボジア", "カンボジアとタイ", "プレアビヒア"], "ru": ["таиландско-камбоджийск", "камбоджийско-таиландск", "Преа Вихеар"], "zh": ["泰柬", "柏威夏"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- us_canada_trade_coercion (139 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'us_canada_trade_coercion', 'us_canada_trade_coercion fn_anchor', '{"ar": ["USMCA", "تعريفة جمركية", "رسوم جمركية", "حرب تجارية", "مفاوضات تجارية", "إجراءات انتقامية", "سحب الاعتماد", "الأخشاب اللينة", "الصلب والألمنيوم", "رسوم تعويضية", "الحمائية", "الكانولا", "إدارة العرض"], "de": ["USMCA", "Zoll", "Zöll", "Handelskrieg", "Handelsgespräch", "Handelsabkommen", "Gegenzoll", "Zulassung entziehen", "Nadelholz", "Bauholz", "Stahl", "Aluminium", "Ausgleichszoll", "Antidumping", "Protektionis", "Rapsöl", "Angebotssteuerung"], "en": ["USMCA", "CUSMA", "tariff", "trade war", "trade talks", "trade deal", "trade negotiat", "trade agreement", "counter-tariff", "decertif", "softwood", "lumber", "steel", "aluminum", "aluminium", "countervail", "anti-dumping", "dumping", "surtax", "protectionis", "canola", "dairy", "supply management"], "es": ["T-MEC", "USMCA", "arancel", "guerra comercial", "negociaciones comerciales", "contra-arancel", "descertific", "madera blanda", "acero", "derechos compensatorios", "proteccionis", "colza", "gestión de la oferta"], "fr": ["ACEUM", "droits de douane", "guerre commerciale", "négociations commerciales", "contre-tarif", "décertific", "bois d''oeuvre", "acier", "droits compensateurs", "protectionnis", "canola", "gestion de l''offre"], "hi": ["USMCA", "टैरिफ", "व्यापार युद्ध", "व्यापार वार्ता", "जवाबी शुल्क", "प्रमाणन रद्द", "इमारती लकड़ी", "इस्पात", "प्रतिकारी शुल्क", "संरक्षणवाद", "कैनोला", "आपूर्ति प्रबंधन"], "it": ["USMCA", "dazio", "guerra commerciale", "negoziati commerciali", "contro-dazio", "decertific", "legname", "acciaio", "dazi compensativi", "protezionis", "colza", "gestione dell''offerta"], "ja": ["USMCA", "関税", "貿易戦争", "貿易交渉", "報復関税", "認証取り消し", "針葉樹材", "鉄鋼", "相殺関税", "保護主義", "カノーラ", "供給管理"], "ru": ["USMCA", "тариф", "пошлин", "торговая война", "торговые переговоры", "ответные пошлины", "отзыв сертификации", "пиломатериал", "сталь", "компенсационная пошлина", "протекционизм", "рапсовое", "регулирование поставок"], "zh": ["美墨加协定", "关税", "贸易战", "贸易谈判", "反制关税", "取消认证", "软木材", "钢铝", "反补贴税", "保护主义", "油菜籽", "供应管理"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- us_russia_arms_control (133 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'us_russia_arms_control', 'us_russia_arms_control fn_anchor', '{"ar": ["الحد من التسلح", "الاستقرار الاستراتيجي", "نزع السلاح", "سباق التسلح", "الترسانة النووية", "رأس نووي", "صاروخ عابر للقارات", "الدفاع الصاروخي", "تجربة نووية", "عمليات تفتيش"], "de": ["Neuer START", "Offener Himmel", "Rüstungskontrolle", "strategische Stabilität", "Abrüstung", "Wettrüsten", "Atomwaffenvertrag", "Atomarsenal", "Sprengkopf", "Hyperschall", "Raketenabwehr", "nukleare Triade", "Atomtest", "Inspektionen"], "en": ["New START", "INF", "CTBT", "Open Skies", "arms control", "strategic stability", "disarmament", "arms race", "nuclear treaty", "nuclear pact", "nuclear arsenal", "ICBM", "warhead", "Burevestnik", "Poseidon", "Sarmat", "Oreshnik", "hypersonic", "nuclear triad", "Golden Dome", "missile defence", "missile defense", "nuclear test", "inspections", "verification regime", "warhead limits"], "es": ["Nuevo START", "control de armas", "estabilidad estratégica", "desarme", "carrera armamentista", "arsenal nuclear", "ojiva", "hipersónico", "defensa antimisiles", "ensayo nuclear", "inspecciones"], "fr": ["Nouveau START", "contrôle des armements", "stabilité stratégique", "désarmement", "course aux armements", "arsenal nucléaire", "ogive", "hypersonique", "défense antimissile", "essai nucléaire", "inspections"], "hi": ["परमाणु निरस्त्रीकरण", "हथियार नियंत्रण", "हथियारों की होड़", "परमाणु हथियार", "मिसाइल रक्षा", "परमाणु परीक्षण"], "it": ["controllo degli armamenti", "stabilità strategica", "disarmo", "corsa agli armamenti", "arsenale nucleare", "testata", "ipersonico", "difesa antimissile", "test nucleare", "ispezioni"], "ja": ["新START", "軍備管理", "戦略的安定", "核軍縮", "軍拡競争", "核兵器庫", "大陸間弾道ミサイル", "核弾頭", "極超音速", "ミサイル防衛", "核実験", "査察"], "ru": ["СНВ", "ДСНВ", "Открытое небо", "Новый СНВ", "контроль над вооружениями", "стратегическая стабильность", "разоружени", "гонка вооружений", "ядерный арсенал", "нераспространени", "Буревестник", "Посейдон", "Сармат", "Орешник", "боеголовк", "гиперзвук", "ядерная триада", "противоракетн", "ядерные испытания", "инспекци"], "zh": ["新削减战略武器条约", "军控", "军备控制", "战略稳定", "核裁军", "军备竞赛", "核武库", "洲际导弹", "核弹头", "高超音速", "导弹防御", "核试验", "核查"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- us_venezuela_relations (195 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'us_venezuela_relations', 'us_venezuela_relations fn_anchor', '{"ar": ["تغيير النظام", "اعتقال", "اختطاف", "إطاحة", "انقلاب", "عملية عسكرية", "الولاية 51", "ضم", "الإكراه", "حصار", "أقصى ضغط", "احتلال", "قارب المخدرات", "تهريب المخدرات", "الاتجار بالمخدرات", "مصادرة ناقلة", "الكوكايين"], "de": ["Regimewechsel", "Festnahme", "Entführung", "Sturz", "Staatsstreich", "Kriegsvollmachten", "Militäroperation", "51. Bundesstaat", "annektieren", "Annexion", "Zwang", "Blockade", "maximaler Druck", "Besatzung", "Drogenboot", "Drogenschmuggel", "Drogenhandel", "Tankerbeschlagnahmung", "Kokain"], "en": ["Tren de Aragua", "Cartel de los Soles", "Cartel of the Suns", "SOUTHCOM", "Southern Command", "regime change", "capture", "abduct", "abduction", "detained Maduro", "seizure of Maduro", "ouster", "toppling", "coup", "extradition", "war powers", "military operation", "special forces", "51st state", "annex", "annexation", "coercion", "remote coercion", "blockade", "maximum pressure", "gunboat", "occupation", "drug boat", "drug vessel", "drug-boat strike", "narco", "narco-trafficking", "drug trafficking", "interdiction", "tanker seizure", "seized tanker", "drug smuggling", "cocaine", "narco-terror"], "es": ["cambio de régimen", "captura", "secuestro", "derrocamiento", "golpe", "operación militar", "poderes de guerra", "estado 51", "anexión", "anexar", "coerción", "bloqueo", "máxima presión", "ocupación", "narcolancha", "narcotráfico", "narcotraficante", "incautación de buque", "cocaína", "narcoterrorismo"], "fr": ["changement de régime", "capture", "enlèvement", "renversement", "coup d''État", "opération militaire", "51e État", "annexion", "annexer", "coercition", "blocus", "pression maximale", "occupation", "bateau de drogue", "narcotrafic", "trafic de drogue", "saisie de pétrolier", "cocaïne"], "hi": ["सत्ता परिवर्तन", "अपहरण", "तख्तापलट", "सैन्य अभियान", "51वां राज्य", "कब्जा", "नाकाबंदी", "अधिकतम दबाव", "ड्रग नाव", "मादक तस्करी", "कोकीन"], "it": ["cambio di regime", "cattura", "rapimento", "rovesciamento", "colpo di Stato", "operazione militare", "51º Stato", "annessione", "annettere", "coercizione", "blocco", "massima pressione", "occupazione", "barca della droga", "narcotraffico", "traffico di droga", "sequestro di petroliera", "cocaina"], "ja": ["体制転換", "拘束", "拉致", "転覆", "クーデター", "軍事作戦", "51番目の州", "併合", "強制", "封鎖", "最大限の圧力", "占領", "麻薬ボート", "麻薬密輸", "麻薬取引", "タンカー拿捕", "コカイン"], "ru": ["смена режима", "захват", "похищение", "свержение", "переворот", "военная операция", "51-й штат", "аннексия", "аннексировать", "принуждение", "блокада", "максимальное давление", "оккупация", "наркокатер", "наркотрафик", "наркоторговля", "захват танкера", "кокаин"], "zh": ["政权更迭", "抓捕", "绑架", "推翻", "政变", "军事行动", "第51州", "吞并", "兼并", "胁迫", "封锁", "极限施压", "占领", "贩毒船", "毒品走私", "贩毒", "扣押油轮", "可卡因"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- venezuela_political_transition (182 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'venezuela_political_transition', 'venezuela_political_transition fn_anchor', '{"ar": ["حكومة انتقالية", "الرئيس المؤقت", "انتقال السلطة", "الشرعية", "انتخابات", "المعارضة", "استفتاء", "مرشح", "تصويت", "احتجاجات", "اضطرابات", "قمع", "اعتقال", "إصلاح"], "de": ["Übergangsregierung", "Übergangspräsident", "Interimspräsident", "Machtübergabe", "Amtseinführung", "Legitimität", "Übergang", "Wahl", "Neuwahl", "Opposition", "Referendum", "Kandidat", "Stimmzettel", "Proteste", "Unruhen", "Razzia", "Festnahme", "Lohnerhöhung", "Repression"], "en": ["Delcy Rodríguez", "Delcy", "Jorge Rodríguez", "Padrino López", "chavismo", "chavista", "PSUV", "Miraflores", "Cabello", "Machado", "Edmundo González", "María Corina", "Vente Venezuela", "Guaidó", "Maduro", "interim government", "interim president", "acting president", "transitional government", "transition", "inauguration", "power transfer", "caretaker", "cabinet", "amnesty", "purge", "legitimacy", "mandate", "succession", "election", "snap election", "vote", "poll", "referendum", "opposition", "ballot", "candidate", "protest", "unrest", "crackdown", "detention", "wage increase", "reform", "repression", "strike wave"], "es": ["gobierno interino", "gobierno de transición", "presidente interino", "presidenta encargada", "transición", "traspaso de poder", "legitimidad", "amnistía", "elecciones", "oposición", "referéndum", "candidato", "comicios", "votación", "protestas", "disturbios", "represión", "detención", "aumento salarial", "reforma"], "fr": ["gouvernement intérimaire", "président par intérim", "transition", "transfert du pouvoir", "légitimité", "élections", "opposition", "référendum", "candidat", "scrutin", "manifestations", "troubles", "répression", "détention", "réforme"], "hi": ["अंतरिम सरकार", "कार्यवाहक राष्ट्रपति", "सत्ता हस्तांतरण", "चुनाव", "विपक्ष", "जनमत संग्रह", "उम्मीदवार", "विरोध", "अशांति", "दमन", "सुधार"], "it": ["governo ad interim", "presidente ad interim", "transizione", "legittimità", "elezioni", "opposizione", "referendum", "candidato", "proteste", "disordini", "repressione", "detenzione", "riforma"], "ja": ["暫定政府", "移行政府", "暫定大統領", "権力移譲", "正統性", "選挙", "野党", "国民投票", "候補", "投票", "抗議", "騒乱", "弾圧", "拘束", "改革"], "ru": ["временное правительство", "переходное правительство", "и.о. президента", "передача власти", "легитимность", "выборы", "оппозиция", "референдум", "кандидат", "голосование", "протесты", "беспорядки", "репрессии", "задержание", "реформа"], "zh": ["临时政府", "过渡政府", "代理总统", "权力交接", "合法性", "选举", "反对派", "公投", "候选人", "投票", "抗议", "骚乱", "镇压", "拘留", "改革"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- venezuela_sanctions_oil (189 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'venezuela_sanctions_oil', 'venezuela_sanctions_oil fn_anchor', '{"ar": ["النفط", "النفط الخام", "تصفية النفط", "صادرات النفط", "إنتاج النفط", "العقوبات", "رفع العقوبات", "تخفيف العقوبات", "الحظر", "إعادة هيكلة الديون", "التضخم المفرط", "الحد الأدنى للأجور", "الاستثمار الأجنبي"], "de": ["Öl", "Rohöl", "Ölförderung", "Ölexporte", "Raffinerie", "Ölgeschäft", "Ölfeld", "Sanktionen", "Sanktionslockerung", "Sanktionserleichterung", "Lizenz", "Embargo", "Schuldenumstrukturierung", "Hyperinflation", "Mindestlohn", "Wirtschaftsreform", "Auslandsinvestitionen"], "en": ["PDVSA", "Citgo", "Petrocedeño", "Petropiar", "Corpoelec", "Chevron", "ExxonMobil", "Exxon", "ConocoPhillips", "Conoco", "Repsol", "Eni", "Maurel", "Shell", "Orinoco", "Faja", "Paraguaná", "Jose terminal", "Lake Maracaibo", "Maracaibo", "Amuay", "Cardón", "El Palito", "oil", "crude", "barrel", "refinery", "refining", "refiner", "oilfield", "drilling", "oil rig", "output", "oil exports", "oil production", "oil law", "oil deal", "petrostate", "heavy crude", "condensate", "petroleum", "sanctions", "sanctions relief", "sanctions easing", "sanctions lifted", "delisting", "OFAC", "licence", "license", "waiver", "embargo", "secondary sanctions", "debt restructuring", "bondholders", "default", "hyperinflation", "dollarization", "bolívar", "minimum wage", "economic reform", "foreign investment", "arbitration award", "expropriation"], "es": ["petróleo", "crudo", "barril", "refinería", "petrolera", "exportaciones de crudo", "producción petrolera", "yacimiento", "sanciones", "alivio de sanciones", "levantamiento de sanciones", "licencia", "embargo", "reestructuración de deuda", "hiperinflación", "dolarización", "salario mínimo", "reforma económica", "inversión extranjera", "expropiación"], "fr": ["pétrole", "brut", "raffinerie", "baril", "pétrolier", "sanctions", "levée des sanctions", "allègement des sanctions", "licence", "embargo", "restructuration de la dette", "hyperinflation", "salaire minimum", "investissement étranger"], "hi": ["तेल", "कच्चा तेल", "तेल निर्यात", "प्रतिबंध", "प्रतिबंध हटाना", "ऋण पुनर्गठन", "विदेशी निवेश"], "it": ["petrolio", "greggio", "raffineria", "barile", "petrolifera", "sanzioni", "revoca delle sanzioni", "licenza", "embargo", "ristrutturazione del debito", "iperinflazione", "salario minimo", "investimenti esteri"], "ja": ["石油", "原油", "製油", "石油輸出", "制裁", "制裁解除", "制裁緩和", "禁輸", "債務再編", "ハイパーインフレ", "最低賃金", "外国投資"], "ru": ["нефть", "нефтяной", "нефтедобыча", "баррель", "нефтеэкспорт", "НПЗ", "санкции", "снятие санкций", "смягчение санкций", "лицензия", "эмбарго", "реструктуризация долга", "гиперинфляция", "минимальная зарплата", "иностранные инвестиции"], "zh": ["石油", "原油", "炼油", "石油出口", "石油产量", "重油", "制裁", "解除制裁", "放松制裁", "许可证", "禁运", "债务重组", "恶性通胀", "最低工资", "外国投资"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- ---------------------------------------------------------------------------
-- Parity fix: russia_sanctions_economy is INACTIVE in friction_nodes on both
-- local and Render, and its bundle is inactive locally -- but still active on
-- Render. Harmless today (an inactive FN never attributes) yet it is real
-- drift, and it is the only bundle Render has that local does not.
-- ---------------------------------------------------------------------------
UPDATE taxonomy_v3 SET is_active = false, updated_at = now()
WHERE taxonomy_function = 'fn_anchor' AND linked_id = 'russia_sanctions_economy' AND is_active = true;

-- ============================================================================
-- VERIFICATION (run before COMMIT)
-- ============================================================================

-- 1. Every ACTIVE atomic that still lacks a bundle. Expect 21 -- and every one
--    must be from an unbuilt theater (cuba/sahel/ethiopia/drc/balkans/somalia/
--    us domestic). Anything else appearing here is a genuine regression.
SELECT f.id
FROM friction_nodes f
WHERE f.fn_type = 'atomic' AND f.is_active
  AND NOT EXISTS (SELECT 1 FROM taxonomy_v3 x
                  WHERE x.taxonomy_function = 'fn_anchor' AND x.is_active AND x.linked_id = f.id)
ORDER BY f.id;

-- 2. Alias counts for the 22 -- must match the EXPECTED list in the header.
SELECT linked_id,
       (SELECT count(*) FROM jsonb_each(aliases) l, jsonb_array_elements_text(l.value)) AS alias_count
FROM taxonomy_v3
WHERE taxonomy_function = 'fn_anchor' AND is_active
  AND linked_id IN ('alberta_separatism_us_ties', 'aukus_alliance_reliability', 'australia_china_trade_leverage', 'balochistan_insurgency', 'canada_sovereignty_pressure', 'china_threat_assessment', 'essequibo_dispute', 'india_pakistan_militancy', 'indus_water_sharing', 'kashmir_dispute', 'latam_eu_market_access', 'latam_resource_access', 'latam_us_trade_pressure', 'myanmar_civil_conflict', 'pacific_island_contest', 'pakistan_afghanistan_border', 'thailand_cambodia_border', 'us_canada_trade_coercion', 'us_venezuela_relations', 'venezuela_political_transition', 'venezuela_sanctions_oil', 'us_russia_arms_control')
ORDER BY linked_id;

-- 3. No bundle may be orphaned (linked_id with no friction_nodes row). Expect 0.
SELECT count(*) AS orphaned_bundles
FROM taxonomy_v3 x
WHERE x.taxonomy_function = 'fn_anchor' AND x.is_active
  AND NOT EXISTS (SELECT 1 FROM friction_nodes f WHERE f.id = x.linked_id);

-- 4. Total active fn_anchor rows on Render.
--    Before: 81. Plus 22 inserted here, minus russia_sanctions_economy
--    deactivated above => EXPECT 102.
--    (Local reads 107 instead: 102 + the 3 colombia bundles and the 2
--    us_russia bundles that this file deliberately excludes. Local and Render
--    converge to 107 once the colombia and us_russia syncs are applied.)
SELECT count(*) AS active_fn_anchor_total
FROM taxonomy_v3 WHERE taxonomy_function = 'fn_anchor' AND is_active;

COMMIT;
