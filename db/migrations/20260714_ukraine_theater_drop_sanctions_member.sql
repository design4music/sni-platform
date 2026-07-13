-- Ukraine theater: drop russia_sanctions_regime from membership (2026-07-14)
--
-- Reconciliation of an untracked local change. The May seed
-- (20260519_friction_node_ukraine_war_theater_seed.sql) put
-- russia_sanctions_regime in ukraine_war_theater. The 2026-07 Europe review
-- re-homed it to russia_europe_theater, but no migration file removed it from
-- ukraine_war_theater -- that edit lived only in the working DB. This codifies
-- it so both DBs converge. russia_sanctions_regime remains a member of
-- russia_europe_theater (its correct home); this only removes the stale
-- Ukraine membership, so the theater's 5 members are exactly the Ukraine
-- atomics (battlefield, aid, peace, corruption, infrastructure_war).
-- Idempotent: array_remove is a no-op when the element is absent.

BEGIN;

UPDATE friction_nodes
   SET member_fn_ids = array_remove(member_fn_ids, 'russia_sanctions_regime'),
       updated_at = NOW()
 WHERE id = 'ukraine_war_theater';

COMMIT;
