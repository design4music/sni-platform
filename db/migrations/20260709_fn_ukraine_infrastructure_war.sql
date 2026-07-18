-- New atomic FN: ukraine_infrastructure_war (2026-07-09)
-- The mutual campaign against energy and infrastructure: Ukrainian deep
-- strikes on Russian refineries/depots/terminals, Russian strikes on the
-- Ukrainian grid, Zaporizhzhia NPP safety, Kerch Bridge, export facilities.
-- Corpus evidence (90d, UA/RU-centroid titles): refinery/oil depot 261 hits,
-- ZNPP/IAEA 82, power grid 22 -- the largest untracked phenomenon in the
-- Ukraine theater. Closes the ZNPP/Kerch asset-attribution gap via
-- affected_asset_ids with demonstrated-strike mechanisms (D-090 rule 2).
--
-- Narrative publishers are copied from the ukraine_battlefield pair --
-- identical coalition voices, different stance axis.
-- Idempotent: ON CONFLICT DO NOTHING / guarded UPDATE throughout.

BEGIN;

-- 1. FN row
INSERT INTO friction_nodes (
    id, name_en, name_de, description_en, description_de,
    editorial_summary_en, editorial_summary_de,
    centroid_ids, fn_type, affected_asset_ids, is_active, display_order
) VALUES (
    'ukraine_infrastructure_war',
    'Energy and infrastructure war',
    'Energie- und Infrastrukturkrieg',
    'The mutual campaign against energy and infrastructure: Ukrainian long-range strikes on Russian refineries, fuel depots and export terminals; Russian strikes on Ukraine''s power system and fuel storage; and the contested safety of the Zaporizhzhia nuclear plant. Energy is dual-use by nature -- each side presents its own strikes as military necessity and the other side''s as terror, and that contest over intent is part of the phenomenon itself.',
    'Der wechselseitige Feldzug gegen Energie und Infrastruktur: ukrainische Langstreckenangriffe auf russische Raffinerien, Treibstofflager und Exportterminals; russische Angriffe auf das ukrainische Stromsystem und Treibstofflager; dazu die umkaempfte Sicherheit des Kernkraftwerks Saporischschja. Energie ist ihrem Wesen nach dual-use -- jede Seite stellt eigene Angriffe als militaerische Notwendigkeit dar und die der Gegenseite als Terror; dieser Streit um die Absicht ist Teil des Phaenomens selbst.',
    'Since 2024 the war''s most distinctive strategic layer has moved off the front line and onto the energy map. Ukraine''s deep-strike campaign reaches refineries, depots and export terminals far inside Russia; Russia''s missile and drone campaign works through Ukraine''s grid, generation and fuel storage. Both campaigns hit systems that are irreducibly dual-use: the same refinery fuels tanks and tractors, the same grid powers arms plants and apartment blocks. Each side states a military-economic rationale for its own strikes -- degrading the enemy''s fuel supply, logistics and defence industry -- and frames the other''s as terror against civilians; adjudicating between those readings is the narratives'' job, not this node''s. The Zaporizhzhia plant sits at the centre as a standing nuclear-safety flashpoint, with the IAEA as the only institutional referee on site. The contest is fought as much over legitimacy as over megawatts.',
    'Seit 2024 hat sich die praegendste strategische Ebene des Krieges von der Front auf die Energiekarte verlagert. Die ukrainische Tiefschlag-Kampagne erreicht Raffinerien, Lager und Exportterminals weit im russischen Hinterland; die russische Raketen- und Drohnenkampagne richtet sich gegen das ukrainische Stromnetz, die Erzeugung und die Treibstofflager. Beide Kampagnen treffen Systeme, die unaufloeslich dual-use sind: dieselbe Raffinerie betankt Panzer und Traktoren, dasselbe Netz versorgt Ruestungswerke und Wohnbloecke. Jede Seite nennt fuer die eigenen Angriffe eine militaerisch-oekonomische Begruendung -- Schwaechung von Treibstoffversorgung, Logistik und Ruestungsindustrie des Gegners -- und rahmt die der Gegenseite als Terror gegen Zivilisten; zwischen diesen Lesarten zu entscheiden ist Aufgabe der Narrative, nicht dieses Knotens. Das Kernkraftwerk Saporischschja steht im Zentrum als permanenter nuklearer Gefahrenherd, mit der IAEO als einzigem institutionellen Schiedsrichter vor Ort. Der Konflikt wird ebenso um Legitimitaet wie um Megawatt gefuehrt.',
    ARRAY['EUROPE-UKRAINE','EUROPE-RUSSIA'],
    'atomic',
    -- D-090 rule 2 (demonstrated reach), all with repeated documented strikes
    -- or direct fire: ZNPP (shelling/occupation, IAEA-documented), Kerch
    -- Strait (bridge struck repeatedly), Omsk refinery + Primorsk/Ust-Luga
    -- terminals (Ukrainian long-range drone strikes), Novorossiysk port
    -- (naval drone + missile strikes), Druzhba West (strikes + pumping halts).
    ARRAY['zaporizhzhia_npp','kerch_strait','omsk_refinery',
          'primorsk_ust_luga_terminals','novorossiysk_port',
          'druzhba_pipeline_west'],
    true,
    5
) ON CONFLICT (id) DO NOTHING;

-- 2. Theater membership
UPDATE friction_nodes
   SET member_fn_ids = member_fn_ids || ARRAY['ukraine_infrastructure_war'],
       updated_at = NOW()
 WHERE id = 'ukraine_war_theater'
   AND NOT member_fn_ids @> ARRAY['ukraine_infrastructure_war'];

-- 3. Narratives (publishers copied from the battlefield coalition pair)
INSERT INTO narratives_v2 (
    id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de,
    actor_centroids, publishers, framing_keywords, is_active
)
SELECT
    'infrastructure_war_economy_strikes', 'ukraine_infrastructure_war', 1, 2,
    'Legitimate strikes on the war economy',
    'Legitime Schlaege gegen die Kriegswirtschaft',
    'Ukraine-aligned: precision degradation of Russia''s war economy; Russian grid strikes are terror',
    'Ukraine-orientiert: praezise Zermuerbung der russischen Kriegswirtschaft; russische Netzangriffe sind Terror',
    'Strikes on refineries, depots and export terminals are lawful pressure on the aggressor''s war economy and export revenue. It is Russia that weaponises winter by destroying Ukraine''s power grid and holds Europe hostage at the Zaporizhzhia plant.',
    'Angriffe auf Raffinerien, Treibstofflager und Exportterminals sind rechtmaessiger Druck auf die Kriegswirtschaft und Exporterloese des Aggressors. Es ist Russland, das den Winter zur Waffe macht, indem es das ukrainische Stromnetz zerstoert und Europa am Kernkraftwerk Saporischschja in Geiselhaft haelt.',
    ARRAY['EUROPE-UKRAINE','AMERICAS-USA','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','NON-STATE-EU'],
    (SELECT publishers FROM narratives_v2 WHERE id = 'ukrainian_defense_and_deep_strikes'),
    ARRAY['war economy','legitimate military target','fuel shortage','gasoline crisis',
          'kinetic sanctions','export revenue','weaponising winter','nuclear blackmail',
          'refinery fire','deep strike'],
    true
WHERE EXISTS (SELECT 1 FROM narratives_v2 WHERE id = 'ukrainian_defense_and_deep_strikes')
ON CONFLICT (id) DO NOTHING;

INSERT INTO narratives_v2 (
    id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de,
    actor_centroids, publishers, framing_keywords, is_active
)
SELECT
    'infrastructure_war_energy_terror', 'ukraine_infrastructure_war', 2, -2,
    'Terror against civilian infrastructure',
    'Terror gegen zivile Infrastruktur',
    'Russia-aligned: Kyiv attacks civilian energy and endangers nuclear safety',
    'Russland-orientiert: Kiew greift zivile Energie an und gefaehrdet die nukleare Sicherheit',
    'Ukrainian drone and missile attacks on refineries, pipelines and the Zaporizhzhia plant are terrorism against civilian infrastructure, enabled by Western targeting support. Russian strikes on energy facilities serve a military purpose: undermining Ukraine''s military-industrial complex, its logistics and the fuel supply to the front.',
    'Ukrainische Drohnen- und Raketenangriffe auf Raffinerien, Pipelines und das Kernkraftwerk Saporischschja sind Terror gegen zivile Infrastruktur, ermoeglicht durch westliche Zielunterstuetzung. Russische Schlaege gegen Energieanlagen dienen einem militaerischen Zweck: der Schwaechung des ukrainischen militaerisch-industriellen Komplexes, seiner Logistik und der Treibstoffversorgung der Front.',
    ARRAY['EUROPE-RUSSIA'],
    (SELECT publishers FROM narratives_v2 WHERE id = 'russian_smo_operations'),
    ARRAY['terrorist attack','civilian infrastructure','energy terror','provocation',
          'nuclear catastrophe','Kyiv regime','Western targeting data','retaliatory strike'],
    true
WHERE EXISTS (SELECT 1 FROM narratives_v2 WHERE id = 'russian_smo_operations')
ON CONFLICT (id) DO NOTHING;

-- 4. fn_anchor bundle. Per FN_ANCHOR_VOCABULARY_SPEC: country-neutral,
-- atoms not phrases, no generic combat vocabulary (that is battlefield's
-- axis), Latin-identical tokens en-only. "refiner"/"raffiner" are
-- deliberate stems: the word-start matcher covers refinery/refineries/
-- refineria and Raffinerie/raffinerie/raffineria. Bare "pipeline" is
-- deliberately excluded (would pull gas-diplomacy stories that belong to
-- russia_gas_leverage); named pipelines and "pumping station" carry it.
INSERT INTO taxonomy_v3 (item_raw, aliases, is_active, taxonomy_function, linked_id)
SELECT 'ukraine_infrastructure_war fn_anchor', '{
  "en": ["IAEA", "Grossi", "Energoatom", "Ukrenergo", "Naftogaz", "DTEK",
         "Rosatom", "Transneft",
         "ZNPP", "Enerhodar", "Kerch Bridge", "Crimean Bridge", "Druzhba",
         "Ust-Luga", "Primorsk", "Novorossiysk", "Ryazan", "Kirishi",
         "Tuapse", "Omsk", "Volgograd", "Syzran", "Caspian Pipeline",
         "reactor", "power unit", "spent fuel", "nuclear safety",
         "refiner", "raffiner", "oil depot", "fuel depot", "oil terminal",
         "pumping station", "substation", "power grid", "blackout",
         "energy infrastructure", "thermal power"],
  "de": ["Stromnetz", "Stromausfall", "Umspannwerk", "Atomkraftwerk",
         "Kernkraftwerk", "AKW", "Öldepot", "Treibstofflager",
         "Energieinfrastruktur", "Pumpstation"],
  "es": ["apagón", "red eléctrica", "oleoducto", "central nuclear",
         "planta nuclear", "depósito de petróleo"],
  "fr": ["oléoduc", "réseau électrique", "centrale nucléaire",
         "dépôt pétrolier", "sûreté nucléaire"],
  "it": ["oleodotto", "rete elettrica", "centrale nucleare",
         "deposito petrolifero"],
  "ru": ["НПЗ", "нефтебаз", "нефтеперераб", "энергосистем", "подстанци",
         "отключени", "блэкаут", "ЗАЭС", "Энергодар", "МАГАТЭ", "Гросси",
         "энергоблок", "АЭС", "Усть-Луга", "Приморск", "Новороссийск",
         "Транснефть", "Росатом", "Укрэнерго", "ДТЭК",
         "энергетическая инфраструктура"],
  "zh": ["炼油厂", "输油管道", "电网", "停电", "扎波罗热核电站",
         "国际原子能机构", "核电站", "变电站", "能源基础设施"],
  "ar": ["مصفاة", "مستودع نفط", "شبكة الكهرباء", "انقطاع الكهرباء",
         "محطة زابوريجيا النووية", "الوكالة الدولية للطاقة الذرية",
         "محطة نووية", "غروسي", "البنية التحتية للطاقة"],
  "ja": ["製油所", "石油貯蔵施設", "送電網", "停電", "ザポリージャ原発",
         "原発", "変電所", "エネルギーインフラ", "グロッシ"],
  "hi": ["रिफाइनरी", "तेल डिपो", "बिजली ग्रिड", "परमाणु संयंत्र",
         "ज़ापोरिज्जिया", "ऊर्जा बुनियादी ढांचा"]
}'::jsonb, true, 'fn_anchor', 'ukraine_infrastructure_war'
WHERE NOT EXISTS (
    SELECT 1 FROM taxonomy_v3
    WHERE taxonomy_function = 'fn_anchor'
      AND linked_id = 'ukraine_infrastructure_war'
);

COMMIT;
