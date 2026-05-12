-- Set per-FN actor-scope centroid_ids ("skin-in-the-game" actors only).
-- 2026-05-11 — supersedes the earlier flat MIDEAST-IRAN scope; safe commenters
-- (EU, Russia, China for far-away coverage) excluded. Each FN's scope is the
-- set of centroids whose presence in a title qualifies it for the FN's
-- attribution gate.

BEGIN;

-- Atomic FNs
UPDATE friction_nodes SET centroid_ids = ARRAY[
    'MIDEAST-IRAN',
    'AMERICAS-USA',
    'MIDEAST-ISRAEL'
] WHERE id = 'iran_nuclear_program';

UPDATE friction_nodes SET centroid_ids = ARRAY[
    'MIDEAST-IRAN',
    'MIDEAST-LEVANT',
    'MIDEAST-PALESTINE',
    'MIDEAST-YEMEN',
    'MIDEAST-IRAQ',
    'MIDEAST-ISRAEL',
    'AMERICAS-USA'
] WHERE id = 'iran_proxy_network';

UPDATE friction_nodes SET centroid_ids = ARRAY[
    'MIDEAST-IRAN',
    'AMERICAS-USA',
    'MIDEAST-ISRAEL'
] WHERE id = 'iran_regime_legitimacy_contest';

UPDATE friction_nodes SET centroid_ids = ARRAY[
    'MIDEAST-IRAN',
    'AMERICAS-USA',
    'EUROPE-UK',
    'EUROPE-FRANCE',
    'MIDEAST-SAUDI'
] WHERE id = 'strait_of_hormuz_sovereignty';

UPDATE friction_nodes SET centroid_ids = ARRAY[
    'MIDEAST-IRAN',
    'MIDEAST-YEMEN',
    'MIDEAST-SAUDI',
    'AMERICAS-USA',
    'MIDEAST-ISRAEL'
] WHERE id = 'gulf_attacks_on_arab_states';

-- iran_theater: union of all atomic FN scopes — the broad Iran-cluster scope.
UPDATE friction_nodes SET centroid_ids = ARRAY[
    'MIDEAST-IRAN',
    'AMERICAS-USA',
    'MIDEAST-ISRAEL',
    'MIDEAST-SAUDI',
    'MIDEAST-LEVANT',
    'MIDEAST-PALESTINE',
    'MIDEAST-YEMEN',
    'MIDEAST-IRAQ',
    'EUROPE-UK',
    'EUROPE-FRANCE'
] WHERE id = 'iran_theater';

COMMIT;
