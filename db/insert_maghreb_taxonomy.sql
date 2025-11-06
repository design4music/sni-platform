-- ============================================================================
-- Insert MIDEAST-MAGHREB Taxonomy Items
-- North Africa: Algeria, Tunisia, Morocco, Libya, Mauritania
-- Date: 2025-11-04
-- ============================================================================

BEGIN;

-- MIDEAST-MAGHREB: Countries, cities, leaders, and infrastructure
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, iso_code, is_active)
VALUES
  -- Algeria
  ('Algeria', 'geo', '{MIDEAST-MAGHREB}', '["Algerian"]', 'DZ', true),
  ('Algiers', 'geo', '{MIDEAST-MAGHREB}', '[]', 'DZ', true),
  ('Oran', 'geo', '{MIDEAST-MAGHREB}', '[]', 'DZ', true),
  ('Constantine', 'geo', '{MIDEAST-MAGHREB}', '[]', 'DZ', true),
  ('Hassi Messaoud', 'geo', '{MIDEAST-MAGHREB}', '[]', 'DZ', true),
  ('Abdelmadjid Tebboune', 'person', '{MIDEAST-MAGHREB}', '["Tebboune"]', 'DZ', true),
  ('Sonatrach', 'org', '{MIDEAST-MAGHREB}', '[]', 'DZ', true),

  -- Tunisia
  ('Tunisia', 'geo', '{MIDEAST-MAGHREB}', '["Tunisian"]', 'TN', true),
  ('Tunis', 'geo', '{MIDEAST-MAGHREB}', '[]', 'TN', true),
  ('Sfax', 'geo', '{MIDEAST-MAGHREB}', '[]', 'TN', true),
  ('Sousse', 'geo', '{MIDEAST-MAGHREB}', '[]', 'TN', true),
  ('Kais Saied', 'person', '{MIDEAST-MAGHREB}', '[]', 'TN', true),

  -- Morocco
  ('Morocco', 'geo', '{MIDEAST-MAGHREB}', '["Moroccan"]', 'MA', true),
  ('Rabat', 'geo', '{MIDEAST-MAGHREB}', '[]', 'MA', true),
  ('Casablanca', 'geo', '{MIDEAST-MAGHREB}', '[]', 'MA', true),
  ('Western Sahara', 'geo', '{MIDEAST-MAGHREB}', '[]', 'MA', true),
  ('Laayoune', 'geo', '{MIDEAST-MAGHREB}', '["Laâyoune"]', 'MA', true),
  ('Mohammed VI', 'person', '{MIDEAST-MAGHREB}', '["King Mohammed VI"]', 'MA', true),
  ('OCP Group', 'org', '{MIDEAST-MAGHREB}', '["Office Chérifien des Phosphates"]', 'MA', true),

  -- Libya
  ('Libya', 'geo', '{MIDEAST-MAGHREB}', '["Libyan"]', 'LY', true),
  ('Tripoli', 'geo', '{MIDEAST-MAGHREB}', '[]', 'LY', true),
  ('Benghazi', 'geo', '{MIDEAST-MAGHREB}', '[]', 'LY', true),
  ('Misrata', 'geo', '{MIDEAST-MAGHREB}', '[]', 'LY', true),
  ('Sirte', 'geo', '{MIDEAST-MAGHREB}', '[]', 'LY', true),
  ('Khalifa Haftar', 'person', '{MIDEAST-MAGHREB}', '["General Haftar"]', 'LY', true),

  -- Mauritania
  ('Mauritania', 'geo', '{MIDEAST-MAGHREB}', '["Mauritanian"]', 'MR', true),
  ('Nouakchott', 'geo', '{MIDEAST-MAGHREB}', '[]', 'MR', true),

  -- Organizations
  ('Polisario Front', 'org', '{MIDEAST-MAGHREB}', '["Polisario"]', NULL, true),
  ('LNA', 'org', '{MIDEAST-MAGHREB}', '["Libyan National Army"]', 'LY', true),
  ('GNA', 'org', '{MIDEAST-MAGHREB}', '["Government of National Accord"]', 'LY', true),

  -- Infrastructure & Strategic Assets
  ('Mediterranean shipping', 'domain', '{MIDEAST-MAGHREB}', '[]', NULL, true),
  ('Maghreb-Europe Pipeline', 'anchor', '{MIDEAST-MAGHREB}', '["GME Pipeline"]', NULL, true),
  ('Trans-Saharan Pipeline', 'anchor', '{MIDEAST-MAGHREB}', '["NIGAL Pipeline"]', NULL, true),
  ('Phosphate exports', 'domain', '{MIDEAST-MAGHREB}', '[]', NULL, true),
  ('Strait of Gibraltar', 'geo', '{MIDEAST-MAGHREB}', '["Gibraltar Strait"]', NULL, true),
  ('Gulf of Sidra', 'geo', '{MIDEAST-MAGHREB}', '[]', 'LY', true)
ON CONFLICT (id) DO NOTHING;

COMMIT;

-- Verification
SELECT COUNT(*) as maghreb_items
FROM taxonomy_v3
WHERE 'MIDEAST-MAGHREB' = ANY(centroid_ids);

SELECT item_type, COUNT(*) as count
FROM taxonomy_v3
WHERE 'MIDEAST-MAGHREB' = ANY(centroid_ids)
GROUP BY item_type
ORDER BY item_type;
