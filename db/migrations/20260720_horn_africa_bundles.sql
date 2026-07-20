
-- somaliland_recognition_contest (7 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'somaliland_recognition_contest', 'somaliland_recognition_contest fn_anchor', '{"ar": ["أرض الصومال"], "de": [], "en": ["Somaliland", "Hargeisa"], "es": [], "fr": [], "hi": ["सोमालीलैंड"], "it": [], "ja": ["ソマリランド"], "ru": ["Сомалиленд"], "zh": ["索马里兰"]}'::jsonb, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- ethiopia_regional_confrontation (23 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'ethiopia_regional_confrontation', 'ethiopia_regional_confrontation fn_anchor', '{"ar": ["تيغراي", "إريتريا", "سد النهضة"], "de": ["Eritreas", "Äthiopien"], "en": ["Tigray", "TPLF", "Aksum", "Eritrea", "Asmara", "Afwerki", "Abiy", "GERD", "sea access"], "es": [], "fr": ["Tigré", "Érythrée", "Éthiopie"], "hi": [], "it": [], "ja": ["ティグレ", "エリトリア"], "ru": ["Тиграй", "Эритрея"], "zh": ["提格雷", "厄立特里亚"]}'::jsonb, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- somalia_state_security (16 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'somalia_state_security', 'somalia_state_security fn_anchor', '{"ar": ["الصومالي", "مقديشو"], "de": ["Mogadischu", "Piraten"], "en": ["Somalia", "Shabaab", "Mogadishu", "Puntland", "Garacad"], "es": [], "fr": [], "hi": ["सोमालिया"], "it": [], "ja": ["ソマリア", "アル・シャバブ", "モガディシュ"], "ru": ["Сомалийск", "Могадишо"], "zh": ["摩加迪沙"]}'::jsonb, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();
