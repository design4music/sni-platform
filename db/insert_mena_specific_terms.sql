-- ============================================================================
-- Insert Specific High-Signal MENA Taxonomy Items
-- These are specific units, systems, and entities (not generic terms)
-- Date: 2025-11-04
-- ============================================================================

BEGIN;

-- MIDEAST-SYRIA: Specific military and conflict entities only
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, is_active)
VALUES
  -- Specific Russian military bases (strong signals)
  ('Khmeimim', 'org', '{MIDEAST-SYRIA}', '["Khmeimim Air Base", "Hmeimim"]', true),
  ('Tartus', 'geo', '{MIDEAST-SYRIA}', '["Tartus Naval Base"]', true),

  -- Specific militant leaders (not generic "Syrian Army")
  ('Abu Mohammad al-Julani', 'person', '{MIDEAST-SYRIA}', '["Ahmed Hussein al-Sharaa", "al-Julani"]', true),

  -- Specific rebel/terrorist groups
  ('Hayat Tahrir al-Sham', 'org', '{MIDEAST-SYRIA}', '["HTS"]', true),
  ('Syrian Democratic Forces', 'org', '{MIDEAST-SYRIA}', '["SDF"]', true),

  -- Specific military units (not generic)
  ('Tiger Forces', 'org', '{MIDEAST-SYRIA}', '["Tiger Division"]', true),
  ('Republican Guard', 'org', '{MIDEAST-SYRIA}', '["Syrian Republican Guard"]', true),

  -- Key cities with strategic significance
  ('Idlib', 'geo', '{MIDEAST-SYRIA}', '[]', true),
  ('Homs', 'geo', '{MIDEAST-SYRIA}', '[]', true),
  ('Raqqa', 'geo', '{MIDEAST-SYRIA}', '[]', true),
  ('Deir ez-Zor', 'geo', '{MIDEAST-SYRIA}', '["Deir al-Zor"]', true)
ON CONFLICT (id) DO NOTHING;

-- MIDEAST-ISRAEL: Specific military units and systems
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, is_active)
VALUES
  -- Specific Israeli military units
  ('Unit 8200', 'org', '{MIDEAST-ISRAEL}', '[]', true),
  ('Sayeret Matkal', 'org', '{MIDEAST-ISRAEL}', '[]', true),
  ('Golani Brigade', 'org', '{MIDEAST-ISRAEL}', '[]', true),
  ('Givati Brigade', 'org', '{MIDEAST-ISRAEL}', '[]', true),

  -- Specific defense systems (models)
  ('Iron Dome', 'model', '{MIDEAST-ISRAEL}', '[]', true),
  ('David''s Sling', 'model', '{MIDEAST-ISRAEL}', '[]', true),
  ('Arrow 3', 'model', '{MIDEAST-ISRAEL}', '["Arrow III"]', true),

  -- Intelligence/Security agencies
  ('Shin Bet', 'org', '{MIDEAST-ISRAEL}', '["Shabak"]', true),
  ('Aman', 'org', '{MIDEAST-ISRAEL}', '["Military Intelligence Directorate"]', true),

  -- Key locations
  ('Tel Aviv', 'geo', '{MIDEAST-ISRAEL}', '[]', true),
  ('Haifa', 'geo', '{MIDEAST-ISRAEL}', '[]', true),
  ('Golan Heights', 'geo', '{MIDEAST-ISRAEL, MIDEAST-SYRIA}', '[]', true)
ON CONFLICT (id) DO NOTHING;

-- MIDEAST-IRAN: Specific systems and facilities
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, is_active)
VALUES
  -- Specific Iranian weapons systems
  ('Shahed', 'model', '{MIDEAST-IRAN}', '["Shahed-136", "Shahed drone", "Shahed drones"]', true),
  ('Fateh-110', 'model', '{MIDEAST-IRAN}', '[]', true),
  ('Kheibar Shekan', 'model', '{MIDEAST-IRAN}', '["Khorramshahr"]', true),

  -- Nuclear facilities (specific)
  ('Natanz', 'org', '{MIDEAST-IRAN}', '["Natanz Nuclear Facility"]', true),
  ('Fordow', 'org', '{MIDEAST-IRAN}', '["Fordow Nuclear Facility"]', true),
  ('Arak', 'org', '{MIDEAST-IRAN}', '["Arak Heavy Water Reactor"]', true),

  -- Specific ports/facilities
  ('Bandar Abbas', 'geo', '{MIDEAST-IRAN}', '[]', true),
  ('Chabahar', 'geo', '{MIDEAST-IRAN}', '[]', true)
ON CONFLICT (id) DO NOTHING;

-- MIDEAST-PALESTINE: Specific locations and groups
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, is_active)
VALUES
  -- Specific locations (not generic cities)
  ('Rafah', 'geo', '{MIDEAST-PALESTINE}', '[]', true),
  ('Khan Yunis', 'geo', '{MIDEAST-PALESTINE}', '["Khan Younis"]', true),
  ('Jabaliya', 'geo', '{MIDEAST-PALESTINE}', '["Jabalia"]', true),

  -- Specific military wings
  ('Qassam Brigades', 'org', '{MIDEAST-PALESTINE}', '["Izz ad-Din al-Qassam Brigades"]', true),
  ('al-Quds Brigades', 'org', '{MIDEAST-PALESTINE}', '["Saraya al-Quds"]', true)
ON CONFLICT (id) DO NOTHING;

-- MIDEAST-LEBANON: Specific Hezbollah units and locations
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, is_active)
VALUES
  -- Hezbollah units
  ('Radwan Forces', 'org', '{MIDEAST-LEBANON}', '["Radwan Unit"]', true),

  -- Strategic locations
  ('Litani River', 'geo', '{MIDEAST-LEBANON}', '[]', true),
  ('South Lebanon', 'geo', '{MIDEAST-LEBANON}', '[]', true),
  ('Bekaa Valley', 'geo', '{MIDEAST-LEBANON}', '[]', true)
ON CONFLICT (id) DO NOTHING;

-- MIDEAST-YEMEN: Specific Houthi systems and locations
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, is_active)
VALUES
  -- Houthi weapons
  ('Burkan', 'model', '{MIDEAST-YEMEN}', '["Burkan missile"]', true),
  ('Quds', 'model', '{MIDEAST-YEMEN}', '["Quds cruise missile"]', true),

  -- Strategic locations
  ('Hodeidah', 'geo', '{MIDEAST-YEMEN}', '["Hudaydah", "Hodeida"]', true),
  ('Taiz', 'geo', '{MIDEAST-YEMEN}', '[]', true),
  ('Marib', 'geo', '{MIDEAST-YEMEN}', '[]', true),

  -- Red Sea locations
  ('Bab al-Mandab', 'geo', '{MIDEAST-YEMEN}', '["Bab el-Mandeb"]', true)
ON CONFLICT (id) DO NOTHING;

-- MIDEAST-SAUDI: Specific facilities and systems
INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, is_active)
VALUES
  -- Oil infrastructure (specific)
  ('Abqaiq', 'org', '{MIDEAST-SAUDI}', '["Abqaiq oil facility"]', true),
  ('Khurais', 'org', '{MIDEAST-SAUDI}', '["Khurais oil field"]', true),

  -- Defense systems
  ('Patriot', 'model', '{MIDEAST-SAUDI}', '["Patriot missile"]', true),
  ('THAAD', 'model', '{MIDEAST-SAUDI}', '["Terminal High Altitude Area Defense"]', true)
ON CONFLICT (id) DO NOTHING;

COMMIT;

-- Verification
SELECT
    unnest(centroid_ids) as centroid_id,
    COUNT(*) as new_items
FROM taxonomy_v3
WHERE item_raw IN (
    -- Check a few key items
    'Iron Dome', 'Shahed', 'Khmeimim', 'Qassam Brigades', 'Radwan Forces'
)
GROUP BY unnest(centroid_ids);
