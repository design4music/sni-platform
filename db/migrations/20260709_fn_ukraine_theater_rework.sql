-- FN Europe review, phase 2: Ukraine theater full rework (2026-07-09)
-- Decisions: centroid_ids narrowed to actual actor scope ("where things
-- happen"), primary_target added as a structural guard where donor/
-- multilateral centroids must stay broad, fn_anchor bundles pruned of
-- generic legal-process vocabulary, narrative "coalition" display fixed.
-- See conversation for full evidence (Bolton/Weinstein/Castro pollution
-- traced to AMERICAS-USA/EUROPE-UK in ukraine_official_corruption.centroid_ids;
-- NATO-Ankara-summit pollution traced to bare "NATO" alias + broad donor
-- centroids in western_aid_to_ukraine).
--
-- link_titles() in scripts/bootstrap_friction_node.py was extended in the
-- prior commit to respect primary_target symmetrically with link_events()
-- -- this migration is the data half of that pairing.

BEGIN;

-- ukraine_official_corruption: domestic phenomenon, money origin irrelevant.
-- Single centroid removes the AMERICAS-USA/EUROPE-UK leak entirely.
UPDATE friction_nodes
   SET centroid_ids = ARRAY['EUROPE-UKRAINE'],
       updated_at = NOW()
 WHERE id = 'ukraine_official_corruption';

UPDATE taxonomy_v3
   SET aliases = '{"ar": ["NABU", "SAP", "HACC", "NACP", "فساد", "رشوة", "اختلاس", "عمولة", "نهب", "مكافحة الفساد", "شفافية", "مشتريات دفاعية", "فضيحة مشتريات", "فضيحة فساد", "اقرار ذمة مالية", "اثراء غير مشروع", "استرداد اصول", "مصادرة اصول", "شروط الاتحاد الاوروبي", "شروط صندوق النقد", "تقدم الاصلاح", "محكمة مكافحة الفساد", "مكتب مكافحة الفساد"], "de": ["NABU", "SAP", "HACC", "NACP", "ARMA", "Korruption", "Bestechung", "Schmiergeld", "Unterschlagung", "Veruntreuung", "Antikorruption", "Transparenz", "Ruestungsbeschaffung", "Beschaffungsskandal", "Vermoegenserklaerung", "Vermoegensrueckfuehrung", "EU-Konditionalitaet", "IWF-Konditionalitaet", "Reformfortschritt", "Antikorruptionsgericht", "Antikorruptionsbuero"], "en": ["NABU", "SAP", "SAPO", "HACC", "VAKS", "NACP", "ARMA", "PGO", "SBI", "DBR", "corruption", "bribery", "bribe", "embezzlement", "kickback", "anti-corruption", "transparency", "defence procurement", "defense procurement", "procurement scandal", "procurement fraud", "asset declaration", "illicit enrichment", "undeclared assets", "asset recovery", "asset seizure", "asset forfeiture", "EU conditionality", "IMF conditionality", "reform progress", "reform track", "High Anti-Corruption Court", "Anti-Corruption Action Centre", "AntAC", "Yermak"], "es": ["NABU", "SAP", "HACC", "NACP", "corrupcion", "soborno", "malversacion", "desfalco", "anticorrupcion", "transparencia", "adquisicion de defensa", "escandalo de adquisicion", "declaracion de patrimonio", "enriquecimiento ilicito", "condicionalidad de la UE", "condicionalidad del FMI", "progreso de reforma", "tribunal anticorrupcion", "oficina anticorrupcion"], "fr": ["NABU", "SAP", "HACC", "NACP", "corruption", "pot-de-vin", "detournement", "malversation", "anti-corruption", "anticorruption", "transparence", "marche public de defense", "scandale de marche", "declaration de patrimoine", "enrichissement illicite", "conditionnalite de l''UE", "conditionnalite du FMI", "progres de reforme", "tribunal anticorruption", "bureau anticorruption"], "hi": ["NABU", "SAP", "HACC", "NACP", "भ्रष्टाचार", "रिश्वत", "गबन", "घोटाला", "भ्रष्टाचार विरोधी", "पारदर्शिता", "रक्षा खरीद", "खरीद घोटाला", "संपत्ति घोषणा", "अवैध संवर्धन", "भ्रष्टाचार विरोधी न्यायालय", "भ्रष्टाचार विरोधी ब्यूरो"], "it": ["NABU", "SAP", "HACC", "NACP", "corruzione", "tangente", "appropriazione indebita", "peculato", "anticorruzione", "trasparenza", "appalto della difesa", "scandalo appalti", "dichiarazione patrimoniale", "arricchimento illecito", "condizionalita UE", "condizionalita FMI", "progresso di riforma", "tribunale anticorruzione", "ufficio anticorruzione"], "ja": ["NABU", "SAP", "HACC", "NACP", "汚職", "収賄", "贈収賄", "横領", "着服", "キックバック", "反汚職", "透明性", "防衛調達", "調達スキャンダル", "汚職スキャンダル", "資産申告", "違法蓄財", "EU条件", "IMF条件", "改革の進展", "反汚職裁判所", "反汚職局"], "ru": ["НАБУ", "САП", "ВАКС", "НАЗК", "АРМА", "коррупция", "взятка", "взяточничество", "хищение", "растрата", "откат", "антикоррупция", "антикоррупционный", "прозрачность", "оборонзаказ", "госзакупки", "закупочный скандал", "коррупционный скандал", "декларация о доходах", "незаконное обогащение", "необъявленные активы", "возврат активов", "конфискация активов", "условия ЕС", "условия МВФ", "прогресс реформ", "антикоррупционный суд", "антикоррупционное бюро", "Ермак"], "zh": ["NABU", "SAP", "HACC", "NACP", "腐败", "贪腐", "贪污", "受贿", "行贿", "挪用公款", "回扣", "反腐败", "反腐", "透明度", "国防采购", "采购丑闻", "腐败丑闻", "资产申报", "非法致富", "欧盟条件", "国际货币基金组织条件", "改革进展", "反腐败法院", "反腐败局"]}'::jsonb
 WHERE taxonomy_function='fn_anchor' AND linked_id='ukraine_official_corruption';

-- ukraine_battlefield / ukraine_war_theater: fighting happens in Ukraine
-- and Russia only. AMERICAS-USA, EUROPE-BALTIC were bundling in unrelated
-- US/Baltic-centroid news (EUROPE-BALTIC already flagged DEAD in
-- out/fn_audit_EUROPE.md; AMERICAS-USA's "HOT" flag was the pollution
-- itself, not evidence it belongs).
UPDATE friction_nodes
   SET centroid_ids = ARRAY['EUROPE-UKRAINE','EUROPE-RUSSIA'],
       updated_at = NOW()
 WHERE id = 'ukraine_battlefield';

UPDATE friction_nodes
   SET centroid_ids = ARRAY['EUROPE-UKRAINE','EUROPE-RUSSIA'],
       primary_target = 'EUROPE-UKRAINE',
       updated_at = NOW()
 WHERE id = 'ukraine_war_theater';

-- western_aid_to_ukraine / ukraine_peace_negotiations: donor capitals
-- (US/UK/FR/DE) and negotiation venues are structurally legitimate actor
-- scope -- aid decisions ARE made in Washington/Brussels, peace talks ARE
-- Trump/Witkoff-led. Instead of stripping legitimate breadth, add
-- primary_target so the SAME title must also carry EUROPE-UKRAINE --
-- kills NATO-Ankara-summit-style false positives without narrowing the
-- centroid list.
UPDATE friction_nodes
   SET primary_target = 'EUROPE-UKRAINE',
       updated_at = NOW()
 WHERE id = 'western_aid_to_ukraine';

UPDATE friction_nodes
   SET primary_target = 'EUROPE-UKRAINE',
       updated_at = NOW()
 WHERE id = 'ukraine_peace_negotiations';

UPDATE taxonomy_v3
   SET aliases = '{"ar": ["مساعدات عسكرية", "مساعدات اقتصادية", "توريد اسلحة", "تدريب", "مساعدات امنية", "حزمة مساعدات", "تصنيع دفاعي", "ذخيرة", "قذائف", "اصول مجمدة", "صندوق اوكرانيا", "مبادرة تشيكية", "رامشتاين", "باتريوت", "هايمارس", "تاوروس", "ابرامز"], "de": ["Ramstein", "Ukraine-Verteidigungsgruppe", "Waffenlieferung", "Militaerhilfe", "Wirtschaftshilfe", "Sicherheitsunterstuetzung", "Hilfspaket", "Ausbildungsmission", "Ruestungsproduktion", "Joint Venture", "Munition", "Granaten", "Artilleriegranaten", "eingefrorene Vermoegen", "Ukraine-Fazilitaet", "Friedensfazilitaet", "Leopard", "tschechische Munitions-Initiative", "Sondervermoegen"], "en": ["Ramstein", "UDCG", "Ukraine Defense Contact Group", "EU Council", "Taurus", "HIMARS", "ATACMS", "Storm Shadow", "SCALP", "Patriot", "F-16", "Leopard", "Abrams", "Bradley", "Stinger", "Javelin", "IRIS-T", "NASAMS", "Caesar", "Archer", "AMX-10", "PzH 2000", "Marder", "Rheinmetall", "BAE", "Lockheed", "Raytheon", "KMW", "Nexter", "Saab", "Norinco", "ERA loan", "Ukraine Facility", "REPO Act", "Lend-Lease", "European Peace Facility", "EPF", "macro-financial assistance", "MFA", "frozen assets", "immobilised assets", "aid package", "military aid", "economic aid", "weapons delivery", "security assistance", "training mission", "defence production", "defense production", "joint venture", "ammunition supply", "155mm", "shells", "artillery shells", "Czech initiative", "extraordinary revenue acceleration", "windfall profits"], "es": ["Ramstein", "ayuda militar", "ayuda economica", "entrega de armas", "asistencia de seguridad", "paquete de ayuda", "mision de entrenamiento", "produccion de defensa", "municion", "proyectiles de artilleria", "activos congelados", "servicio Ucrania", "iniciativa checa"], "fr": ["Ramstein", "aide militaire", "aide economique", "livraison d''armes", "assistance de securite", "plan d''aide", "mission de formation", "production de defense", "munitions", "obus d''artillerie", "avoirs geles", "facilite Ukraine", "initiative tcheque", "facilite europeenne de paix"], "hi": ["सैन्य सहायता", "आर्थिक सहायता", "हथियार आपूर्ति", "पैट्रियट", "हाईमार्स", "तौरस", "गोला बारूद", "जमे हुए संपत्ति"], "it": ["Ramstein", "aiuti militari", "aiuti economici", "consegna di armi", "assistenza di sicurezza", "pacchetto di aiuti", "missione di addestramento", "produzione di difesa", "munizioni", "proietti d''artiglieria", "beni congelati", "Strumento Ucraina", "iniziativa ceca"], "ja": ["ラムシュタイン", "軍事援助", "経済援助", "武器供与", "安全保障支援", "援助パッケージ", "訓練ミッション", "防衛生産", "合弁事業", "弾薬", "砲弾", "凍結資産", "ウクライナ・ファシリティー", "チェコ・イニシアチブ", "タウルス", "ハイマース", "パトリオット", "レオパルト", "ラインメタル"], "ru": ["Рамштайн", "Таурус", "Хаймарс", "АТАКМС", "Шторм Шэдоу", "Пэтриот", "Леопард", "Абрамс", "Брэдли", "Стингер", "Джавелин", "IRIS-T", "NASAMS", "военная помощь", "экономическая помощь", "поставка оружия", "учебная миссия", "оборонное производство", "совместное предприятие", "боеприпасы", "снаряды", "артиллерийские снаряды", "замороженные активы", "чешская инициатива", "фонд мира", "REPO", "ленд-лиз", "Рейнметалл"], "zh": ["军事援助", "经济援助", "武器交付", "安全援助", "援助计划", "训练任务", "国防生产", "合资企业", "弹药", "炮弹", "冻结资产", "乌克兰基金", "莱茵金属", "洛克希德", "拉姆施泰因"]}'::jsonb
 WHERE taxonomy_function='fn_anchor' AND linked_id='western_aid_to_ukraine';

-- Cosmetic "Coalition" badge fix: EU is not a coalition partner in the
-- RU/CN "Zelensky is corrupt" framing. actor_centroids is display-only,
-- not part of the attribution query.
UPDATE narratives_v2
   SET actor_centroids = ARRAY['EUROPE-RUSSIA','ASIA-CHINA'],
       updated_at = NOW()
 WHERE id = 'zelensky_regime_corruption';

COMMIT;
