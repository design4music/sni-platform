
-- m23_conflict (44 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'm23_conflict', 'm23_conflict fn_anchor', '{"ar": ["حركة إم23", "تحالف نهر الكونغو", "القوات الديمقراطية المتحالفة", "غوما", "كيفو", "بوكافو"], "de": [], "en": ["M23", "AFC", "Alliance Fleuve Congo", "CODECO", "FDLR", "FARDC", "Wazalendo", "Allied Democratic Forces", "Nangaa", "Twirwaneho", "Goma", "Bukavu", "Kivu", "Rubaya", "Uvira", "Beni", "Masisi", "Rutshuru", "Walikale", "Kisangani"], "es": [], "fr": [], "hi": ["एम23", "गोमा", "किवु"], "it": [], "ja": ["コンゴ川同盟", "北キブ", "南キブ"], "ru": ["М23", "Альянс реки Конго", "КОДЕКО", "Гома", "Киву", "Букаву"], "zh": ["M23运动", "刚果河联盟", "民主同盟军", "戈马", "基伍", "布卡武"]}'::jsonb, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- drc_peace_process (46 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'drc_peace_process', 'drc_peace_process fn_anchor', '{"ar": ["وقف إطلاق النار", "اتفاق سلام", "مفاوضات", "عقوبات", "كاغامي", "كابيلا"], "de": [], "en": ["ceasefire", "truce", "mediat", "negotiat", "peace", "Doha", "Luanda", "MONUSCO", "sanction", "embargo", "visa restriction", "Kabila", "Kagame", "ICJ", "war crimes"], "es": [], "fr": ["accord", "paix", "cessez-le-feu", "médiation", "trêve", "sanctionn", "restrictions de visa"], "hi": ["संघर्ष विराम", "शांति समझौता", "प्रतिबंध"], "it": [], "ja": ["停戦", "和平合意", "制裁"], "ru": ["перемирие", "переговоры", "мирное соглашение", "МООНСДРК", "санкции", "Кагаме", "Кабила"], "zh": ["停火", "和平协议", "谈判", "制裁", "卡加梅"]}'::jsonb, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- drc_minerals_competition (65 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'drc_minerals_competition', 'drc_minerals_competition fn_anchor', '{"ar": ["الكوبالت", "الكولتان", "النحاس", "كاتانغا", "سلسلة التوريد", "حظر التصدير"], "de": [], "en": ["cobalt", "coltan", "tantalum", "cassiterite", "lithium", "copper", "mine", "Gecamines", "Gécamines", "Chemaf", "Kamoa", "Tenke", "Katanga", "Kolwezi", "Lualaba", "Bisie", "Rubaya", "KoBold", "CMOC", "ERG", "Zijin", "Virtus", "artisanal", "smelter", "export ban", "export control", "supply chain", "refinery", "quota"], "es": [], "fr": ["minerai", "cuivre", "étain", "artisanale", "chaîne d''approvisionnement", "exportation"], "hi": ["कोबाल्ट", "कोल्टन", "कटंगा", "आपूर्ति श्रृंखला"], "it": [], "ja": ["コバルト", "コルタン", "カタンガ", "サプライチェーン"], "ru": ["кобальт", "колтан", "медь", "тантал", "Жекамин", "Катанга", "цепочка поставок", "экспортные ограничения"], "zh": ["钴", "钶钽铁矿", "铜矿", "锂", "卡莫阿", "紫金矿业", "供应链", "出口管制"]}'::jsonb, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();
