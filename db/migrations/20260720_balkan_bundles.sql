
-- serbia_government_legitimacy (42 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'serbia_government_legitimacy', 'serbia_government_legitimacy fn_anchor', '{"ar": ["فوتشيتش", "بلغراد", "صربيا"], "de": ["Belgrad", "Serbien"], "en": ["Vučić", "Vucic", "SNS", "Brnabić", "Brnabic", "Šapić", "naprednj", "opozicij", "Skupštin", "Beograd", "Belgrade", "Novi Sad", "nadstrešnic", "NIS", "Gazprom", "TurkStream", "gasovod", "rafinerij"], "es": ["serbio"], "fr": ["serbe"], "hi": ["वुचिच", "बेलग्रेड", "सर्बिया"], "it": ["serbo"], "ja": ["ブチッチ", "ベオグラード", "セルビア"], "ru": ["Вучич", "Скупщин", "Белград", "Газпром", "нефтяно", "Сербии", "Сербия"], "zh": ["武契奇", "贝尔格莱德", "塞尔维亚"]}'::jsonb, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- balkan_foreign_capital (20 aliases)
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'balkan_foreign_capital', 'balkan_foreign_capital fn_anchor', '{"ar": ["كوشنر", "منتجع"], "de": ["Luxusresort", "Ferienanlage"], "en": ["Kushner", "Jared", "Fincantieri", "resort", "Sazan"], "es": ["turístico"], "fr": ["touristique"], "hi": ["कुशनर", "रिसॉर्ट"], "it": ["turistico"], "ja": ["クシュナー", "リゾート"], "ru": ["Кушнер", "курорт"], "zh": ["库什纳", "度假村"]}'::jsonb, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();
