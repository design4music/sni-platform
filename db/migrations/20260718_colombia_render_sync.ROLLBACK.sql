-- ROLLBACK for 20260718_colombia_render_sync.sql
--
-- DESTRUCTIVE. Only valid while the Colombia bootstrap has NOT been run --
-- pre-flight on 2026-07-18 confirmed these ids did not exist on Render, so
-- this removes exactly what the forward migration added and nothing else.
--
-- If bootstrap HAS since run, event_friction_nodes rows will exist for these
-- fn_ids; check before running, because friction_nodes is the parent of
-- event_friction_nodes, fn_asset_evidence and narratives_v2 (which in turn
-- parents title_narratives).
--
-- Order matters: FKs are NO ACTION, so children must go first.

BEGIN;

-- Guard: refuse to run if attribution exists (i.e. bootstrap already ran).
DO $$
DECLARE n int;
BEGIN
    SELECT count(*) INTO n FROM event_friction_nodes WHERE fn_id LIKE 'colombia%';
    IF n > 0 THEN
        RAISE EXCEPTION 'Refusing rollback: % event_friction_nodes rows exist for colombia%%. Re-evaluate before deleting.', n;
    END IF;
END $$;

DELETE FROM narratives_v2  WHERE fn_id LIKE 'colombia%';
DELETE FROM taxonomy_v3    WHERE taxonomy_function = 'fn_anchor' AND linked_id LIKE 'colombia%';
DELETE FROM friction_nodes WHERE id LIKE 'colombia%';

-- Expect 0 | 0 | 0
SELECT
    (SELECT count(*) FROM friction_nodes WHERE id LIKE 'colombia%') AS fn_rows,
    (SELECT count(*) FROM taxonomy_v3 WHERE taxonomy_function='fn_anchor' AND linked_id LIKE 'colombia%') AS bundles,
    (SELECT count(*) FROM narratives_v2 WHERE fn_id LIKE 'colombia%') AS narratives;

COMMIT;
