-- ============================================================================
-- Insert MIDEAST-IRAQ Taxonomy Items
-- Cities and key organizations
-- Date: 2025-11-06
-- ============================================================================

BEGIN;

-- MIDEAST-IRAQ: Cities and organizations
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, is_active)
VALUES
  -- Cities
  ('Erbil', 'geo', '{MIDEAST-IRAQ}',
   '["أربيل", "هولير", "Arbela", "Arbil", "Hawler", "Arbèle", "अर्बिल", "एर्बिल", "エルビル", "アルビール", "Эрбиль", "Арбиль", "埃尔比勒", "艾尔比勒"]'::jsonb,
   true),

  ('Basra', 'geo', '{MIDEAST-IRAQ}',
   '["البصرة", "Al-Basrah", "Basrah", "Basora", "Bassora", "बसरा", "बस्रा", "バスラ", "Басра", "巴士拉", "巴斯拉"]'::jsonb,
   true),

  ('Mosul', 'geo', '{MIDEAST-IRAQ}',
   '["الموصل", "Al-Mawsil", "Mossoul", "मोसुल", "मूसिल", "モースル", "Мосул", "摩苏尔", "摩蘇爾"]'::jsonb,
   true),

  -- Organizations
  ('Popular Mobilization Forces', 'org', '{MIDEAST-IRAQ}',
   '["الحشد الشعبي", "قوات الحشد الشعبي", "Volksmobilisierungskräfte", "PMF", "Hashd al-Shaabi", "Popular Mobilization Units", "Fuerzas de Movilización Popular", "Forces de mobilisation populaire", "पॉपुलर मोबिलाइजेशन फोर्सेस", "पीएमएफ", "Forze di Mobilitazione Popolare", "人民動員隊", "Народные мобилизационные силы", "ПМС", "人民动员力量", "人民动员组织"]'::jsonb,
   true),

  ('Kurdistan Regional Government', 'org', '{MIDEAST-IRAQ}',
   '["حكومة إقليم كردستان", "Regionale Regierung Kurdistans", "KRG", "Kurdish Regional Government", "Gobierno Regional del Kurdistán", "Gouvernement régional du Kurdistan", "कुर्दिस्तान क्षेत्रीय सरकार", "केआरजी", "Governo Regionale del Kurdistan", "クルディスタン地域政府", "Региональное правительство Курдистана", "ПКК", "库尔德斯坦地区政府", "库区"]'::jsonb,
   true)
ON CONFLICT (id) DO NOTHING;

COMMIT;

-- Verification
SELECT COUNT(*) as iraq_items
FROM taxonomy_v3
WHERE 'MIDEAST-IRAQ' = ANY(centroid_ids);

SELECT item_type, COUNT(*) as count
FROM taxonomy_v3
WHERE 'MIDEAST-IRAQ' = ANY(centroid_ids)
GROUP BY item_type
ORDER BY item_type;
