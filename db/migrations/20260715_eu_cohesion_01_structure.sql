-- eu_cohesion_theater — Phase 2 structure (FN_THEATER_BUILD_SPEC §2/§2a).
-- Greenfield theater; the 8 draft atomics were built on stale training data.
-- Structural re-assessment against real 2026 coverage (see session notes):
--   * Orban defeated -> hungary re-scoped (transition + EU relationship), kept.
--   * Brexit dead (~63 hits) -> post_brexit_realignment DEACTIVATED; EUROPE-UK
--     dropped from the theater (removed large non-cohesion UK domestic noise).
--   * Meloni-vs-Brussels friction dissolved -> italian_populist_government
--     DEACTIVATED; southern content flows to migration/budget/realignment.
--   * Slovakia coverage is ~85% "Fico blocks Ukraine aid" (owned by
--     ukraine_war_theater / russia_europe_theater) -> slovakia_alignment
--     DEACTIVATED; its errant EUROPE-RUSSIA centroid removed with it.
--   * NEW eu_right_realignment: the EU-institutional realignment of the
--     parliamentary right (EPP/ECR/PfE groups, the cordon sanitaire, cross-
--     border coordination) — the biggest genuine coverage gap.
-- Net: 8 draft atomics -> 6 active. No DELETE (deactivate via is_active=false),
-- so nothing cascades. Names/descriptions/editorial land in migration 02.
SET client_encoding TO 'UTF8';

-- ---- 1. Deactivate the three stale atomics (reversible; no data wiped) ----
UPDATE friction_nodes SET is_active = false, updated_at = NOW()
WHERE id IN ('slovakia_alignment', 'post_brexit_realignment', 'italian_populist_government');

-- ---- 2. Insert the new atomic (shell; prose in migration 02) ----
INSERT INTO friction_nodes
  (id, name_en, name_de, fn_type, centroid_ids, primary_target, scope, display_order, is_active)
VALUES
  ('eu_right_realignment',
   'Realignment of Europe''s parliamentary right',
   'Neuordnung der europäischen Rechten',
   'atomic',
   ARRAY['NON-STATE-EU','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-SOUTH','EUROPE-VISEGRAD'],
   NULL, 'regional', 40, true)
ON CONFLICT (id) DO UPDATE SET
  centroid_ids = EXCLUDED.centroid_ids,
  primary_target = EXCLUDED.primary_target,
  is_active = true,
  updated_at = NOW();

-- ---- 3. Centroid fixes on retained atomics ----
-- Budget/sovereignty: drop errant EUROPE-UKRAINE; broaden to the net-payer /
-- cohesion-fund / CAP member states so their resistance attributes.
UPDATE friction_nodes SET
  centroid_ids = ARRAY['NON-STATE-EU','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-SOUTH','EUROPE-VISEGRAD'],
  updated_at = NOW()
WHERE id = 'eu_budget_sovereignty';

-- Migration/asylum: broaden from NON-STATE-EU only to the member states whose
-- national disputes (Spain amnesty, Italy Albania, German returns) are the story.
UPDATE friction_nodes SET
  centroid_ids = ARRAY['NON-STATE-EU','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-SOUTH','EUROPE-VISEGRAD'],
  updated_at = NOW()
WHERE id = 'eu_migration_burden_sharing';

-- Hungary: keep VISEGRAD + NON-STATE-EU (no per-country centroid exists;
-- attribution is name-gated, archetype A2). Slovakia's EUROPE-RUSSIA is gone
-- with its deactivation. No change needed here beyond confirming.

-- ---- 4. Theater aggregation: drop EUROPE-UK, refresh membership ----
UPDATE friction_nodes SET
  centroid_ids = ARRAY['EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-SOUTH','EUROPE-VISEGRAD','NON-STATE-EU'],
  member_fn_ids = ARRAY['hungary_rule_of_law','eu_migration_burden_sharing','eu_budget_sovereignty','afd_and_german_polarisation','french_nationalist_challenge','eu_right_realignment'],
  updated_at = NOW()
WHERE id = 'eu_cohesion_theater';
