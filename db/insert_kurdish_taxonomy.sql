-- ============================================================================
-- Insert Kurdish Cross-Regional Taxonomy Items
-- Items spanning Iraq, Syria, and Turkey centroids
-- Date: 2025-11-06
-- ============================================================================

BEGIN;

-- Kurdish cross-regional items with multi-centroid assignments
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, is_active)
VALUES
  -- Geographic/Identity terms spanning multiple regions
  ('Kurdistan', 'geo', '{MIDEAST-IRAQ,MIDEAST-SYRIA,MIDEAST-TURKEY}',
   '["كردستان", "Kurdish region", "Kurdish lands", "Kurdistán", "कुर्दिस्तान", "クルディスタン", "Курдистан", "库尔德斯坦"]'::jsonb,
   true),

  ('Kurds', 'domain', '{MIDEAST-IRAQ,MIDEAST-SYRIA,MIDEAST-TURKEY}',
   '["الأكراد", "Kurden", "Kurdish people", "kurdos", "Kurdes", "कुर्द", "curdi", "クルド人", "курды", "库尔德人"]'::jsonb,
   true),

  ('Kurdish', 'domain', '{MIDEAST-IRAQ,MIDEAST-SYRIA,MIDEAST-TURKEY}',
   '["كردي", "kurdisch", "kurdo", "kurde", "कुर्दिश", "curdo", "クルドの", "курдский", "库尔德的"]'::jsonb,
   true),

  -- Kurdish military/political organizations
  ('PKK', 'org', '{MIDEAST-TURKEY,MIDEAST-SYRIA,MIDEAST-IRAQ}',
   '["حزب العمال الكردستاني", "Arbeiterpartei Kurdistans", "Kurdistan Workers'' Party", "Partido de los Trabajadores de Kurdistán", "Parti des travailleurs du Kurdistan", "पीकेके", "कुर्दिस्तान वर्कर्स पार्टी", "Partito dei Lavoratori del Kurdistan", "クルディスタン労働者党", "ПКК", "Курдская рабочая партия", "库尔德工人党"]'::jsonb,
   true),

  ('YPG', 'org', '{MIDEAST-SYRIA,MIDEAST-TURKEY}',
   '["وحدات حماية الشعب", "Volksschutzeinheiten", "People''s Protection Units", "Unidades de Protección Popular", "Unités de protection du peuple", "वाईपीजी", "पीपल्स प्रोटेक्शन यूनिट्स", "Unità di Protezione Popolare", "人民防衛部隊", "ЮПГ", "Отряды народной самообороны", "人民保护部队"]'::jsonb,
   true),

  ('Peshmerga', 'org', '{MIDEAST-IRAQ,MIDEAST-SYRIA}',
   '["البشمركة", "Peschmerga", "Kurdish fighters", "पेशमर्गा", "ペシュメルガ", "пешмерга", "佩什梅格"]'::jsonb,
   true),

  -- Syrian Kurdistan
  ('Rojava', 'geo', '{MIDEAST-SYRIA,MIDEAST-TURKEY}',
   '["روجافا", "Syrian Kurdistan", "Western Kurdistan", "रोजावा", "ロジャヴァ", "Рожава", "罗贾瓦"]'::jsonb,
   true)
ON CONFLICT (id) DO NOTHING;

COMMIT;

-- Verification
SELECT 'Total Kurdish items' as description, COUNT(*) as count
FROM taxonomy_v3
WHERE item_raw IN ('Kurdistan', 'Kurds', 'Kurdish', 'PKK', 'YPG', 'Peshmerga', 'Rojava');

-- Show distribution across centroids
SELECT
    unnest(centroid_ids) as centroid_id,
    COUNT(*) as items
FROM taxonomy_v3
WHERE item_raw IN ('Kurdistan', 'Kurds', 'Kurdish', 'PKK', 'YPG', 'Peshmerga', 'Rojava')
GROUP BY unnest(centroid_ids)
ORDER BY centroid_id;
