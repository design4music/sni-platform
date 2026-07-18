-- South Asia theater: structural re-carve (Phase 1 -> Phase 2 structure apply)
-- Greenfield: no bundles, no narratives, nothing attributed. Fully reversible.
--
-- Approved 2026-07-17 after §2a real-coverage grounding:
--   1. MERGE: india_china_theater retired; india_pakistan_theater re-scoped and
--      renamed south_asia_theater (regional-instability archetype, precedent:
--      sahel/horn_africa/balkan/great_lakes -- not a mis-shaped bilateral).
--   2. COVERAGE GAP: pakistan_afghanistan_border (NEW) -- 726 titles/180d, the
--      region's largest live conflict, previously unhomed anywhere in the system.
--   3. COVERAGE GAP: balochistan_insurgency (NEW) -- 92 titles/180d, unhomed.
--   4. STALENESS: india_pakistan_nuclear_balance retired (~9 titles; Pakistan's
--      "nuclear" coverage is mostly its US-Iran mediation, not the India dyad).
--   5. CENTROID ERROR + STALENESS: himalayan_strategic_competition retired --
--      ASIA-HIMALAYA is Nepal domestic politics, not the China border; Doklam=0.
--   6. STALENESS: ladakh_lac_dispute retired, NOT folded -- 6 clean titles/180d
--      (SCS-retirement class) and both natural anchors are poisoned: `LAC` in
--      this corpus is "Latin America and the Caribbean" (China-LAC cooperation),
--      `Ladakh` is Sonam Wangchuk's domestic statehood protests.
--
-- Centroid roles (§2): all atomics are A2 name-gated (null target) EXCEPT
-- pakistan_afghanistan_border, whose vocabulary is generic (airstrike, border,
-- Kabul) and therefore needs the dyad AND-gate. Sparser centroid goes in
-- primary_target (AFGHANISTAN 1420 < PAKISTAN 6345).
-- AND-gates were rejected for kashmir_dispute (only 48/107 Kashmir titles carry
-- PAK) and indus_water_sharing (drops 34->19) -- both would delete ~half.
--
-- id `india_pakistan_theater` -> `south_asia_theater`: FK update_rule is NO
-- ACTION, so the 2 dependent fn_asset_evidence rows are cleared first. They are
-- COMPUTED, not authored (compute_fn_asset_evidence.py regenerates them), and
-- are stale Strait-of-Hormuz co-mention artefacts.
--
-- Rich description_en/de + editorial_summary_en/de deferred to the §6
-- completeness step after narratives; names set bilingually now.

BEGIN;

-- ---------------------------------------------------------------------------
-- Clear stale COMPUTED asset evidence (regenerable) so the PK rename can pass
-- ---------------------------------------------------------------------------
DELETE FROM fn_asset_evidence
WHERE fn_id IN ('india_pakistan_theater', 'india_china_theater');

-- ---------------------------------------------------------------------------
-- RENAME + RESCOPE: india_pakistan_theater -> south_asia_theater
-- anchor_point moved from Srinagar (74.8, 34.1) to the Peshawar/Islamabad
-- corridor, central to all four frictions (Kashmir, Indus, Durand, Balochistan).
-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET
  id = 'south_asia_theater',
  centroid_ids = ARRAY['ASIA-INDIA', 'ASIA-PAKISTAN', 'ASIA-AFGHANISTAN'],
  member_fn_ids = ARRAY['pakistan_afghanistan_border', 'kashmir_dispute',
                        'balochistan_insurgency', 'indus_water_sharing',
                        'india_pakistan_militancy'],
  primary_target = NULL,
  anchor_point = '{"type":"Point","coordinates":[71.5,33.0]}'::jsonb,
  name_en = 'South Asia contested borders',
  name_de = 'Umstrittene Grenzen in Südasien',
  updated_at = now()
WHERE id = 'india_pakistan_theater';

-- ---------------------------------------------------------------------------
-- NEW ATOMIC: Pakistan-Afghanistan border conflict (the theater's largest)
-- Dyad AND-gate: participant PAKISTAN + target AFGHANISTAN = 726 titles/180d.
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes
  (id, fn_type, scope, is_active, display_order, primary_target, centroid_ids, name_en, name_de)
VALUES
  ('pakistan_afghanistan_border', 'atomic', 'regional', true, 61, 'ASIA-AFGHANISTAN',
   ARRAY['ASIA-PAKISTAN'],
   'Pakistan-Afghanistan border conflict',
   'Grenzkonflikt zwischen Pakistan und Afghanistan')
ON CONFLICT (id) DO UPDATE SET
  fn_type = EXCLUDED.fn_type, scope = EXCLUDED.scope, is_active = EXCLUDED.is_active,
  display_order = EXCLUDED.display_order, primary_target = EXCLUDED.primary_target,
  centroid_ids = EXCLUDED.centroid_ids, name_en = EXCLUDED.name_en,
  name_de = EXCLUDED.name_de, updated_at = now();

-- ---------------------------------------------------------------------------
-- NEW ATOMIC: Balochistan insurgency (A2 name-gate, Pakistan-internal)
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes
  (id, fn_type, scope, is_active, display_order, primary_target, centroid_ids, name_en, name_de)
VALUES
  ('balochistan_insurgency', 'atomic', 'regional', true, 64, NULL,
   ARRAY['ASIA-PAKISTAN'],
   'Balochistan insurgency',
   'Aufstand in Belutschistan')
ON CONFLICT (id) DO UPDATE SET
  fn_type = EXCLUDED.fn_type, scope = EXCLUDED.scope, is_active = EXCLUDED.is_active,
  display_order = EXCLUDED.display_order, primary_target = EXCLUDED.primary_target,
  centroid_ids = EXCLUDED.centroid_ids, name_en = EXCLUDED.name_en,
  name_de = EXCLUDED.name_de, updated_at = now();

-- ---------------------------------------------------------------------------
-- KEEP + A2 roles: Kashmir (name-gate; AND-gate would drop 59 of 107)
-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET
  centroid_ids = ARRAY['ASIA-INDIA', 'ASIA-PAKISTAN'],
  primary_target = NULL, display_order = 62,
  name_en = 'Kashmir dispute',
  name_de = 'Kaschmir-Konflikt',
  updated_at = now()
WHERE id = 'kashmir_dispute';

-- ---------------------------------------------------------------------------
-- KEEP + re-scope: India-Pakistan militancy (named groups only, A2)
-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET
  centroid_ids = ARRAY['ASIA-INDIA', 'ASIA-PAKISTAN'],
  primary_target = NULL, display_order = 63,
  name_en = 'Cross-border militancy and proxy accusations',
  name_de = 'Grenzüberschreitende Militanz und Stellvertretervorwürfe',
  updated_at = now()
WHERE id = 'india_pakistan_militancy';

-- ---------------------------------------------------------------------------
-- KEEP: Indus water sharing (A2; AND-gate would drop 34->19)
-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET
  centroid_ids = ARRAY['ASIA-INDIA', 'ASIA-PAKISTAN'],
  primary_target = NULL, display_order = 65,
  name_en = 'Indus waters treaty dispute',
  name_de = 'Streit um den Indus-Wasservertrag',
  updated_at = now()
WHERE id = 'indus_water_sharing';

-- ---------------------------------------------------------------------------
-- RETIRE: stale / dead / centroid-error atomics + the India-China theater
-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET is_active = false, member_fn_ids = ARRAY[]::text[], updated_at = now()
WHERE id = 'india_china_theater';

UPDATE friction_nodes SET is_active = false, updated_at = now()
WHERE id IN ('ladakh_lac_dispute', 'himalayan_strategic_competition',
             'india_pakistan_nuclear_balance');

COMMIT;
