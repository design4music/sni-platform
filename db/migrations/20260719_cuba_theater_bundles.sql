
-- cuba_embargo_sanctions (39 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'cuba_embargo_sanctions', 'cuba_embargo_sanctions fn_anchor', '{"ar": ["عقوبات", "حصار"], "de": ["Blockade", "Sanktion"], "en": ["embargo", "blockade", "sanction", "OFAC", "Treasury", "blacklist", "license", "executive order", "waiver", "GAESA", "Moa Nickel", "Hapag-Lloyd", "CMA CGM", "Iberostar", "Melia", "expropriat", "nationalis", "confiscat", "compensation", "indict", "Exxon"], "es": ["bloqueo", "sanciones", "Meliá", "expropia", "confisca", "indemniza", "imputa"], "fr": ["blocus", "expropriation"], "hi": ["प्रतिबंध"], "it": [], "ja": ["制裁", "禁輸"], "ru": ["санкции против Кубы"], "zh": ["制裁"]}'::jsonb, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- cuba_energy_collapse (53 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'cuba_energy_collapse', 'cuba_energy_collapse fn_anchor', '{"ar": ["انقطاع الكهرباء", "نقص الوقود", "مجاعة"], "de": ["Stromausfall", "Versorgungskrise", "Hunger"], "en": ["blackout", "power grid", "power cut", "outage", "electricity", "electrical", "generator", "fuel", "gasoline", "diesel", "petrol", "shortage", "ration", "scarcity", "hunger", "malnutrition", "medicine", "medical supplies", "hospital", "rubbish", "garbage", "collapse"], "es": ["apagón", "apagones", "red eléctrica", "combustible", "escasez", "desabasto", "hambre"], "fr": ["panne de courant", "carburant", "pénurie", "rationnement"], "hi": ["बिजली कटौती", "ईंधन संकट", "भुखमरी"], "it": ["carburante"], "ja": ["停電", "電力網", "燃料不足", "食料不足"], "ru": ["отключение электричества", "топливо", "гуманитарный кризис"], "zh": ["停电", "燃料短缺", "缺粮"]}'::jsonb, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- cuba_external_lifelines (37 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'cuba_external_lifelines', 'cuba_external_lifelines fn_anchor', '{"ar": ["ناقلة نفط", "مساعدات إنسانية"], "de": ["Tanker", "Lieferung", "Hilfsgüter"], "en": ["tanker", "shipment", "crude", "delivery", "deliver", "shipping", "vessel", "convoy", "humanitarian aid", "donate", "relief", "solidarity", "Pemex", "CELAC", "SPIEF"], "es": ["petrolero", "buque", "cargamento", "envío", "crudo", "ayuda humanitaria"], "fr": ["aide humanitaire"], "hi": ["तेल टैंकर", "मानवीय सहायता"], "it": ["petroliera"], "ja": ["タンカー", "人道支援"], "ru": ["нефть", "танкер", "гуманитарная помощь"], "zh": ["油轮", "人道主义援助"]}'::jsonb, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- cuba_military_coercion (40 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'cuba_military_coercion', 'cuba_military_coercion fn_anchor', '{"ar": ["حاملة طائرات", "غزو"], "de": [], "en": ["Guantanamo", "Guantánamo", "Pentagon", "Bay of Pigs", "Nimitz", "carrier", "naval", "surveillance flight", "reconnaissance", "drone", "invasion", "intervention", "military action", "war powers", "mobilisation", "mobilization", "speedboat", "infiltration", "infiltrate", "incursion", "Autodefensas"], "es": ["Comando Sur", "portaaviones", "invasión", "intervención militar", "ataque militar", "infiltración", "lancha rápida"], "fr": ["porte-avions"], "hi": ["विमानवाहक", "सैन्य हस्तक्षेप"], "it": ["portaerei"], "ja": ["空母", "軍事介入"], "ru": ["авианосец", "военная интервенция"], "zh": ["航母", "军事干预"]}'::jsonb, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- cuba_regime_survival (35 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'cuba_regime_survival', 'cuba_regime_survival fn_anchor', '{"ar": ["الحزب الشيوعي", "سجناء سياسيين", "إصلاح"], "de": ["Gefangene"], "en": ["Díaz-Canel", "Diaz-Canel", "Communist Party", "protest", "prisoner", "political prisoner", "release", "human rights", "reform", "private sector"], "es": ["castrismo", "disidente", "oposición", "protesta", "preso político", "excarcela", "detención", "represión", "reforma"], "fr": [], "hi": ["कम्युनिस्ट पार्टी", "राजनीतिक कैदी", "सुधार"], "it": [], "ja": ["共産党", "政治犯", "改革"], "ru": ["компартия", "политзаключённые", "реформа"], "zh": ["共产党", "政治犯", "改革"]}'::jsonb, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();
