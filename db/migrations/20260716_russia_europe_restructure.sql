-- Russia-Europe theater structural re-carve (Phase 2, step 2 + centroid roles step 4)
-- Approved decomposition 2026-07-16. LOCAL, reversible.
-- Retire 2 stale atomics; add 2 new; re-scope kept atomics + theater.
-- Bundles + narratives are applied separately (see docs/context/RUSSIA_EUROPE_THEATER_BUILD.md).

-- 1. Retire stale atomics (deactivate, do NOT delete -- reversible).
--    baltic_security  = geography-not-phenomenon, redundant with deterrence.
--    russia_gas_leverage = defunct 2022 energy-war frame; content splits to hybrid/sanctions.
UPDATE friction_nodes SET is_active = false, updated_at = now()
WHERE id IN ('baltic_security', 'russia_gas_leverage');

-- 2. New atomics (multilateral / gray-zone; null primary_target; alias-purity driven).
INSERT INTO friction_nodes (id, name_en, name_de, fn_type, centroid_ids, primary_target, scope, is_active)
VALUES
 ('russia_hybrid_warfare',
  'Russian hybrid and gray-zone operations against Europe',
  'Russische hybride Kriegsfuehrung gegen Europa',
  'atomic',
  ARRAY['EUROPE-RUSSIA','EUROPE-BALTIC','EUROPE-NORDIC','EUROPE-VISEGRAD','EUROPE-GERMANY','EUROPE-UK','NON-STATE-EU'],
  NULL, 'regional', true),
 ('russia_airspace_incursions',
  'Airspace incursions and NATO air-defence on the Eastern flank',
  'Luftraumverletzungen und NATO-Luftverteidigung an der Ostflanke',
  'atomic',
  ARRAY['EUROPE-RUSSIA','EUROPE-BALTIC','EUROPE-VISEGRAD','EUROPE-NORDIC','NON-STATE-NATO'],
  NULL, 'regional', true)
ON CONFLICT (id) DO UPDATE SET
  name_en = EXCLUDED.name_en, name_de = EXCLUDED.name_de,
  centroid_ids = EXCLUDED.centroid_ids, primary_target = EXCLUDED.primary_target,
  is_active = true, updated_at = now();

-- 3. Re-scope kept atomics.
--    deterrence: widen to full Eastern-flank participant set; stays bilateral/multilateral (null target).
UPDATE friction_nodes SET
  centroid_ids = ARRAY['EUROPE-RUSSIA','EUROPE-BALTIC','EUROPE-NORDIC','EUROPE-VISEGRAD','NON-STATE-NATO','AMERICAS-USA','EUROPE-GERMANY'],
  primary_target = NULL, updated_at = now()
WHERE id = 'russia_nato_deterrence';

--    sanctions: target-centric on Russia; widen to include EU as the imposing actor.
UPDATE friction_nodes SET
  centroid_ids = ARRAY['EUROPE-RUSSIA','NON-STATE-EU'],
  primary_target = 'EUROPE-RUSSIA', updated_at = now()
WHERE id = 'russia_sanctions_regime';

-- 4. Theater: new membership + union centroid set (add NON-STATE-NATO).
UPDATE friction_nodes SET
  member_fn_ids = ARRAY['russia_nato_deterrence','russia_hybrid_warfare','russia_airspace_incursions','russia_sanctions_regime'],
  centroid_ids = ARRAY['EUROPE-RUSSIA','NON-STATE-EU','NON-STATE-NATO','EUROPE-BALTIC','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-VISEGRAD','EUROPE-NORDIC','AMERICAS-USA'],
  updated_at = now()
WHERE id = 'russia_europe_theater';
