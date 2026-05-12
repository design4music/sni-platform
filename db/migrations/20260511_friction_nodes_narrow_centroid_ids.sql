-- Narrow friction_nodes.centroid_ids to actor-scope semantics.
-- 2026-05-11 — Phase 2 architectural decision (Option 2 in the design review).
--
-- Old meaning: every centroid touched by this FN's stories (actors + reactors
-- + affected parties). Used by frontend "Manifests in" sidebar.
--
-- New meaning: only the centroid(s) whose presence in a title qualifies the
-- title for this FN's actor scope. Used at attribution time as the centroid
-- gate combined with the fn_anchor topic gate.
--
-- For the Iran cluster, the actor is always Iran (MIDEAST-IRAN). For other
-- atomic FNs in future theaters the value will be that theater's actor scope.
--
-- Frontend "Manifests in" rendering is being removed in this changeset; the
-- broader "all involved parties" presentation will be derived from each FN's
-- linked narratives' actor_centroids when needed.

BEGIN;

-- Narrow the 5 Iran atomic FNs + theater to the Iran actor scope.
UPDATE friction_nodes
SET centroid_ids = ARRAY['MIDEAST-IRAN']
WHERE id IN (
    'iran_nuclear_program',
    'iran_proxy_network',
    'iran_regime_legitimacy_contest',
    'strait_of_hormuz_sovereignty',
    'gulf_attacks_on_arab_states',
    'iran_theater'
);

COMMENT ON COLUMN friction_nodes.centroid_ids IS
    'Actor scope (narrow). ANY-of semantics: a title qualifies for this FN only when its centroid_ids array overlaps this value. Iran cluster FNs are all anchored to MIDEAST-IRAN.';

COMMIT;
