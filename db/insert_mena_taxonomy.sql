-- ============================================================================
-- Insert MENA Taxonomy Items with Centroid Linkages
-- Date: 2025-11-04
-- ============================================================================

BEGIN;

-- MIDEAST-PALESTINE: Palestine and related entities
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, is_active)
VALUES
  -- Countries/Territories
  ('Palestine', 'geo', '{MIDEAST-PALESTINE}', '["Palestinian"]', true),
  ('Gaza', 'geo', '{MIDEAST-PALESTINE}', '["Gaza Strip"]', true),
  ('West Bank', 'geo', '{MIDEAST-PALESTINE, MIDEAST-ISRAEL}', '["Judea and Samaria"]', true),

  -- Cities
  ('Gaza City', 'geo', '{MIDEAST-PALESTINE}', '["Gaza"]', true),
  ('Ramallah', 'geo', '{MIDEAST-PALESTINE}', '[]', true),
  ('Hebron', 'geo', '{MIDEAST-PALESTINE}', '[]', true),
  ('Jenin', 'geo', '{MIDEAST-PALESTINE}', '[]', true),
  ('Nablus', 'geo', '{MIDEAST-PALESTINE}', '[]', true),

  -- Organizations
  ('Hamas', 'org', '{MIDEAST-PALESTINE}', '["Islamic Resistance Movement"]', true),
  ('Palestinian Authority', 'org', '{MIDEAST-PALESTINE}', '["PA"]', true),
  ('Fatah', 'org', '{MIDEAST-PALESTINE}', '[]', true),
  ('Islamic Jihad', 'org', '{MIDEAST-PALESTINE}', '["Palestinian Islamic Jihad"]', true),
  ('PLO', 'org', '{MIDEAST-PALESTINE}', '["Palestine Liberation Organization"]', true),

  -- Key Persons
  ('Ismail Haniyeh', 'person', '{MIDEAST-PALESTINE}', '[]', true),
  ('Yahya Sinwar', 'person', '{MIDEAST-PALESTINE}', '[]', true),
  ('Mahmoud Abbas', 'person', '{MIDEAST-PALESTINE}', '["Abu Mazen"]', true),
  ('Mohammed Deif', 'person', '{MIDEAST-PALESTINE}', '[]', true)
ON CONFLICT (id) DO NOTHING;

-- MIDEAST-IRAN: Iran and related entities
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, iso_code, is_active)
VALUES
  -- Countries
  ('Iran', 'geo', '{MIDEAST-IRAN}', '["Iranian", "Islamic Republic of Iran"]', 'IR', true),

  -- Capitals & Cities
  ('Tehran', 'geo', '{MIDEAST-IRAN}', '[]', 'IR', true),
  ('Isfahan', 'geo', '{MIDEAST-IRAN}', '[]', 'IR', true),
  ('Mashhad', 'geo', '{MIDEAST-IRAN}', '[]', 'IR', true),

  -- Key Persons
  ('Ali Khamenei', 'person', '{MIDEAST-IRAN}', '["Ayatollah Khamenei"]', 'IR', true),
  ('Ebrahim Raisi', 'person', '{MIDEAST-IRAN}', '["President Raisi"]', 'IR', true),
  ('Qasem Soleimani', 'person', '{MIDEAST-IRAN}', '["General Soleimani"]', 'IR', true),
  ('Mohammad Bagheri', 'person', '{MIDEAST-IRAN}', '[]', 'IR', true),

  -- Organizations & Military
  ('IRGC', 'org', '{MIDEAST-IRAN}', '["Islamic Revolutionary Guard Corps", "Revolutionary Guards"]', 'IR', true),
  ('Quds Force', 'org', '{MIDEAST-IRAN}', '[]', 'IR', true),
  ('Basij', 'org', '{MIDEAST-IRAN}', '[]', 'IR', true),
  ('Iranian Army', 'org', '{MIDEAST-IRAN}', '[]', 'IR', true)
ON CONFLICT (id) DO NOTHING;

-- MIDEAST-SAUDI: Saudi Arabia and related entities
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, iso_code, is_active)
VALUES
  -- Countries
  ('Saudi Arabia', 'geo', '{MIDEAST-SAUDI}', '["Saudi", "KSA"]', 'SA', true),

  -- Capitals & Cities
  ('Riyadh', 'geo', '{MIDEAST-SAUDI}', '[]', 'SA', true),
  ('Jeddah', 'geo', '{MIDEAST-SAUDI}', '[]', 'SA', true),
  ('Mecca', 'geo', '{MIDEAST-SAUDI}', '["Makkah"]', 'SA', true),
  ('Medina', 'geo', '{MIDEAST-SAUDI}', '["Al-Madinah"]', 'SA', true),
  ('Dhahran', 'geo', '{MIDEAST-SAUDI}', '[]', 'SA', true),

  -- Key Persons
  ('Mohammed bin Salman', 'person', '{MIDEAST-SAUDI}', '["MBS", "Crown Prince Mohammed"]', 'SA', true),
  ('Salman of Saudi Arabia', 'person', '{MIDEAST-SAUDI}', '["King Salman"]', 'SA', true),

  -- Organizations
  ('Saudi Aramco', 'org', '{MIDEAST-SAUDI}', '["Aramco"]', 'SA', true),
  ('OPEC', 'org', '{MIDEAST-SAUDI}', '["Organization of Petroleum Exporting Countries"]', NULL, true)
ON CONFLICT (id) DO NOTHING;

-- MIDEAST-EGYPT: Egypt and related entities
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, iso_code, is_active)
VALUES
  -- Countries
  ('Egypt', 'geo', '{MIDEAST-EGYPT}', '["Egyptian"]', 'EG', true),

  -- Capitals & Cities
  ('Cairo', 'geo', '{MIDEAST-EGYPT}', '[]', 'EG', true),
  ('Alexandria', 'geo', '{MIDEAST-EGYPT}', '[]', 'EG', true),
  ('Suez', 'geo', '{MIDEAST-EGYPT}', '[]', 'EG', true),
  ('Port Said', 'geo', '{MIDEAST-EGYPT}', '[]', 'EG', true),

  -- Key Persons
  ('Abdel Fattah el-Sisi', 'person', '{MIDEAST-EGYPT}', '["Sisi", "President Sisi"]', 'EG', true),

  -- Organizations
  ('Egyptian Military', 'org', '{MIDEAST-EGYPT}', '["Egyptian Army"]', 'EG', true),
  ('Suez Canal Authority', 'org', '{MIDEAST-EGYPT}', '[]', 'EG', true)
ON CONFLICT (id) DO NOTHING;

-- MIDEAST-TURKEY
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, iso_code, is_active)
VALUES
  ('Turkey', 'geo', '{MIDEAST-TURKEY}', '["Turkish", "Türkiye"]', 'TR', true),
  ('Ankara', 'geo', '{MIDEAST-TURKEY}', '[]', 'TR', true),
  ('Istanbul', 'geo', '{MIDEAST-TURKEY}', '[]', 'TR', true),
  ('Izmir', 'geo', '{MIDEAST-TURKEY}', '[]', 'TR', true),
  ('Recep Tayyip Erdogan', 'person', '{MIDEAST-TURKEY}', '["Erdogan", "President Erdogan"]', 'TR', true),
  ('Turkish Armed Forces', 'org', '{MIDEAST-TURKEY}', '["Turkish Military"]', 'TR', true)
ON CONFLICT (id) DO NOTHING;

-- MIDEAST-YEMEN
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, iso_code, is_active)
VALUES
  ('Yemen', 'geo', '{MIDEAST-YEMEN}', '["Yemeni"]', 'YE', true),
  ('Sanaa', 'geo', '{MIDEAST-YEMEN}', '["Sana''a"]', 'YE', true),
  ('Aden', 'geo', '{MIDEAST-YEMEN}', '[]', 'YE', true),
  ('Houthis', 'org', '{MIDEAST-YEMEN}', '["Ansar Allah"]', 'YE', true),
  ('Abdul-Malik al-Houthi', 'person', '{MIDEAST-YEMEN}', '[]', 'YE', true)
ON CONFLICT (id) DO NOTHING;

-- MIDEAST-SYRIA
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, iso_code, is_active)
VALUES
  ('Syria', 'geo', '{MIDEAST-SYRIA}', '["Syrian"]', 'SY', true),
  ('Damascus', 'geo', '{MIDEAST-SYRIA}', '[]', 'SY', true),
  ('Aleppo', 'geo', '{MIDEAST-SYRIA}', '[]', 'SY', true),
  ('Bashar al-Assad', 'person', '{MIDEAST-SYRIA}', '["Assad", "President Assad"]', 'SY', true),
  ('Syrian Army', 'org', '{MIDEAST-SYRIA}', '[]', 'SY', true)
ON CONFLICT (id) DO NOTHING;

-- MIDEAST-LEBANON
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, iso_code, is_active)
VALUES
  ('Lebanon', 'geo', '{MIDEAST-LEBANON}', '["Lebanese"]', 'LB', true),
  ('Beirut', 'geo', '{MIDEAST-LEBANON}', '[]', 'LB', true),
  ('Hezbollah', 'org', '{MIDEAST-LEBANON, MIDEAST-ISRAEL}', '["Party of God"]', 'LB', true),
  ('Hassan Nasrallah', 'person', '{MIDEAST-LEBANON}', '[]', 'LB', true)
ON CONFLICT (id) DO NOTHING;

-- MIDEAST-GULF: Gulf States
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, iso_code, is_active)
VALUES
  -- UAE
  ('UAE', 'geo', '{MIDEAST-GULF}', '["United Arab Emirates", "Emirati"]', 'AE', true),
  ('Abu Dhabi', 'geo', '{MIDEAST-GULF}', '[]', 'AE', true),
  ('Dubai', 'geo', '{MIDEAST-GULF}', '[]', 'AE', true),
  ('Mohammed bin Zayed', 'person', '{MIDEAST-GULF}', '["MBZ"]', 'AE', true),

  -- Qatar
  ('Qatar', 'geo', '{MIDEAST-GULF}', '["Qatari"]', 'QA', true),
  ('Doha', 'geo', '{MIDEAST-GULF}', '[]', 'QA', true),
  ('Tamim bin Hamad', 'person', '{MIDEAST-GULF}', '["Emir Tamim"]', 'QA', true),

  -- Other Gulf States
  ('Bahrain', 'geo', '{MIDEAST-GULF}', '["Bahraini"]', 'BH', true),
  ('Kuwait', 'geo', '{MIDEAST-GULF}', '["Kuwaiti"]', 'KW', true),
  ('Oman', 'geo', '{MIDEAST-GULF}', '["Omani"]', 'OM', true),

  -- Organizations
  ('GCC', 'org', '{MIDEAST-GULF}', '["Gulf Cooperation Council"]', NULL, true)
ON CONFLICT (id) DO NOTHING;

COMMIT;

-- ============================================================================
-- Verification queries
-- ============================================================================

-- Count items per centroid
SELECT
    unnest(centroid_ids) as centroid_id,
    COUNT(*) as item_count
FROM taxonomy_v3
WHERE centroid_ids IS NOT NULL
GROUP BY unnest(centroid_ids)
ORDER BY centroid_id;

-- Total new items
SELECT COUNT(*) as total_mena_items
FROM taxonomy_v3
WHERE centroid_ids && ARRAY[
    'MIDEAST-PALESTINE', 'MIDEAST-IRAN', 'MIDEAST-SAUDI',
    'MIDEAST-EGYPT', 'MIDEAST-TURKEY', 'MIDEAST-YEMEN',
    'MIDEAST-SYRIA', 'MIDEAST-LEBANON', 'MIDEAST-GULF'
]::TEXT[];
