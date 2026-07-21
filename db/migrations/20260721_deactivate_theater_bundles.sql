-- Deactivate the 5 fn_anchor bundles that theaters carry directly
-- (iran_theater, israel_theater, syria_theater, turkey_theater,
-- yemen_red_sea_theater), violating FN_THEATER_BUILD_SPEC.md 1 ("theaters
-- carry no taxonomy, never participate in matching"). Pre-existing, from
-- builds predating the spec (audited 2026-07-18, see
-- lessons_fn_bundle_deploy_gap memory).
--
-- Effect: at the next bootstrap, these 5 theaters stop matching headlines
-- directly and behave like every other theater (rolled up from their
-- atomics' title_narratives only, via THEATER_ROLLUP_SQL). Their existing
-- theater-level title_narratives rows (Iran 14,883, Israel 12,797, etc.)
-- were never read by the frontend -- THEATER_ROLLUP_SQL filters to
-- afn.fn_type = 'atomic' -- so this is dead-weight cleanup, not a visible
-- change. The 4 atomics under each theater keep their own bundles and are
-- unaffected.
--
-- linked_id is stable across local/Render; the taxonomy_v3.id UUID is not
-- (see lessons_render_structural_drift), so match on linked_id.

BEGIN;

UPDATE taxonomy_v3 SET is_active = false, updated_at = NOW()
 WHERE taxonomy_function = 'fn_anchor' AND is_active = true
   AND linked_id IN ('iran_theater', 'israel_theater', 'syria_theater',
                      'turkey_theater', 'yemen_red_sea_theater');

COMMIT;
