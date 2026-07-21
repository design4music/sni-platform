-- Restore primary_target on 23 atomics that had it nulled by an untracked
-- edit -- discovered during the 2026-07-20 Render full-parity sync, which
-- propagated local's NULL to Render. No calibration migration ever nulled
-- these (they are all Middle East / EU FNs; every real "primary_target =
-- NULL" migration in this repo belongs to a different theater's archetype
-- calibration). Values match the original seed
-- (20260621_set_primary_target_friction_nodes.sql) and were verified against
-- each FN's current centroid_ids before restoring (every target is a member
-- of its own FN's scope).
--
-- Without this, re-running bootstrap_friction_node.py on these FNs widens
-- title attribution by +41% on average (measured: red_sea_shipping_security
-- +350%, israel_iran_strikes +254%, gaza_war +102%), because the target gate
-- is what makes the multi-centroid ME atomics precise (spec Archetype A).
--
-- Apply to BOTH local (source of truth) and Render, in that order, so a
-- future full-parity sync does not re-null Render.

BEGIN;

UPDATE friction_nodes SET primary_target = 'MIDEAST-IRAN', updated_at = NOW() WHERE id = 'strait_of_hormuz_sovereignty';
UPDATE friction_nodes SET primary_target = 'MIDEAST-ISRAEL', updated_at = NOW() WHERE id = 'israel_lebanon_border';
UPDATE friction_nodes SET primary_target = 'MIDEAST-ISRAEL', updated_at = NOW() WHERE id = 'gaza_war';
UPDATE friction_nodes SET primary_target = 'MIDEAST-IRAN', updated_at = NOW() WHERE id = 'iran_proxy_network';
UPDATE friction_nodes SET primary_target = 'MIDEAST-IRAN', updated_at = NOW() WHERE id = 'iran_nuclear_program';
UPDATE friction_nodes SET primary_target = 'MIDEAST-YEMEN', updated_at = NOW() WHERE id = 'red_sea_shipping_security';
UPDATE friction_nodes SET primary_target = 'MIDEAST-ISRAEL', updated_at = NOW() WHERE id = 'west_bank_settlements';
UPDATE friction_nodes SET primary_target = 'MIDEAST-ISRAEL', updated_at = NOW() WHERE id = 'israel_iran_strikes';
UPDATE friction_nodes SET primary_target = 'MIDEAST-LEVANT', updated_at = NOW() WHERE id = 'syria_kurdish_question';
UPDATE friction_nodes SET primary_target = 'MIDEAST-IRAN', updated_at = NOW() WHERE id = 'gulf_attacks_on_arab_states';
UPDATE friction_nodes SET primary_target = 'MIDEAST-TURKEY', updated_at = NOW() WHERE id = 'turkey_mediator_role';
UPDATE friction_nodes SET primary_target = 'MIDEAST-YEMEN', updated_at = NOW() WHERE id = 'houthi_strikes_on_israel';
UPDATE friction_nodes SET primary_target = 'MIDEAST-LEVANT', updated_at = NOW() WHERE id = 'syria_counter_terror';
UPDATE friction_nodes SET primary_target = 'MIDEAST-TURKEY', updated_at = NOW() WHERE id = 'turkey_kurdish_question';
UPDATE friction_nodes SET primary_target = 'MIDEAST-LEVANT', updated_at = NOW() WHERE id = 'syria_recognition_and_normalisation';
UPDATE friction_nodes SET primary_target = 'MIDEAST-YEMEN', updated_at = NOW() WHERE id = 'saudi_houthi_war';
UPDATE friction_nodes SET primary_target = 'NON-STATE-EU', updated_at = NOW() WHERE id = 'eu_migration_burden_sharing';
UPDATE friction_nodes SET primary_target = 'MIDEAST-TURKEY', updated_at = NOW() WHERE id = 'turkey_democratic_backsliding';
UPDATE friction_nodes SET primary_target = 'MIDEAST-TURKEY', updated_at = NOW() WHERE id = 'turkey_iran_war_spillover';
UPDATE friction_nodes SET primary_target = 'EUROPE-RUSSIA', updated_at = NOW() WHERE id = 'russia_sanctions_economy';
UPDATE friction_nodes SET primary_target = 'MIDEAST-LEVANT', updated_at = NOW() WHERE id = 'syria_israeli_strikes';
UPDATE friction_nodes SET primary_target = 'NON-STATE-EU', updated_at = NOW() WHERE id = 'hungary_rule_of_law';
UPDATE friction_nodes SET primary_target = 'NON-STATE-EU', updated_at = NOW() WHERE id = 'eu_budget_sovereignty';

COMMIT;
