-- ============================================================================
-- Insert MIDEAST-SUDAN Taxonomy Items
-- Locations, military forces, and key leaders
-- Date: 2025-11-06
-- ============================================================================

BEGIN;

-- MIDEAST-SUDAN: Locations, forces, and leaders
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, is_active)
VALUES
  -- Locations
  ('Darfur', 'geo', '{MIDEAST-SUDAN}',
   '["دارفور", "Darfour", "दारफुर", "ダルフール", "Дарфур", "达尔富尔"]'::jsonb,
   true),

  ('Port Sudan', 'geo', '{MIDEAST-SUDAN}',
   '["بورتسودان", "Port-Soudan", "पोर्ट सूडान", "ポートスーダン", "Порт-Судан", "苏丹港"]'::jsonb,
   true),

  -- Military Forces
  ('Sudanese Armed Forces', 'org', '{MIDEAST-SUDAN}',
   '["القوات المسلحة السودانية", "Sudanesische Streitkräfte", "SAF", "Fuerzas Armadas de Sudán", "Forces armées soudanaises", "सूडानी सशस्त्र बल", "Forze Armate Sudanesi", "スーダン軍", "Суданские вооруженные силы", "苏丹武装部队"]'::jsonb,
   true),

  ('Rapid Support Forces', 'org', '{MIDEAST-SUDAN}',
   '["قوات الدعم السريع", "Schnelle Unterstützungskräfte", "RSF", "Fuerzas de Apoyo Rápido", "Forces de soutien rapide", "रैपिड सपोर्ट फोर्सेस", "Forze di Supporto Rapido", "迅速支援部隊", "Силы быстрой поддержки", "快速支援部队"]'::jsonb,
   true),

  -- Leaders
  ('Abdel Fattah al-Burhan', 'person', '{MIDEAST-SUDAN}',
   '["عبد الفتاح البرهان", "General al-Burhan", "Abdel Fattah al-Bourhane", "अब्देल फतह अल-बुरहान", "アブデルファタハ・アルブルハン", "Абдель Фаттах аль-Бурхан", "阿卜杜勒·法塔赫·布尔汉"]'::jsonb,
   true),

  ('Mohamed Hamdan Dagalo', 'person', '{MIDEAST-SUDAN}',
   '["محمد حمدان دقلو", "Hemedti", "मोहम्मद हमदान दागालो", "モハメド・ハムダン・ダガロ", "Мохамед Хамдан Дагало", "穆罕默德·哈姆丹·达加洛"]'::jsonb,
   true)
ON CONFLICT (id) DO NOTHING;

COMMIT;

-- Verification
SELECT COUNT(*) as sudan_items
FROM taxonomy_v3
WHERE 'MIDEAST-SUDAN' = ANY(centroid_ids);

SELECT item_type, COUNT(*) as count
FROM taxonomy_v3
WHERE 'MIDEAST-SUDAN' = ANY(centroid_ids)
GROUP BY item_type
ORDER BY item_type;
