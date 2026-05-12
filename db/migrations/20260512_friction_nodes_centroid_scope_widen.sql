-- Widen centroid scope on the 5 Iran FNs: add back non-MIDEAST actors with
-- direct stake in each FN's phenomenon. Particularly USA — the primary
-- external party across all five files.
-- 2026-05-12.

BEGIN;

-- iran_theater (umbrella catch-all). Core triad: Iran + USA + Israel.
UPDATE friction_nodes SET centroid_ids = ARRAY[
    'MIDEAST-IRAN',
    'AMERICAS-USA',
    'MIDEAST-ISRAEL'
] WHERE id = 'iran_theater';

-- Nuclear: Iran target, USA + Israel strikers, E3 + EU diplomatic actors.
UPDATE friction_nodes SET centroid_ids = ARRAY[
    'MIDEAST-IRAN',
    'AMERICAS-USA',
    'MIDEAST-ISRAEL',
    'NON-STATE-EU'
] WHERE id = 'iran_nuclear_program';

-- Proxy network: Iran sponsor, proxy fronts (Levant/Palestine/Yemen/Iraq),
-- Israel target, USA forces deployed in the region.
UPDATE friction_nodes SET centroid_ids = ARRAY[
    'MIDEAST-IRAN',
    'MIDEAST-LEVANT',
    'MIDEAST-PALESTINE',
    'MIDEAST-YEMEN',
    'MIDEAST-IRAQ',
    'MIDEAST-ISRAEL',
    'AMERICAS-USA'
] WHERE id = 'iran_proxy_network';

-- Hormuz: Iran + Gulf states + foreign naval coalition (US Fifth Fleet,
-- UK/French escorts).
UPDATE friction_nodes SET centroid_ids = ARRAY[
    'MIDEAST-IRAN',
    'MIDEAST-SAUDI',
    'MIDEAST-GULF',
    'AMERICAS-USA',
    'EUROPE-UK',
    'EUROPE-FRANCE'
] WHERE id = 'strait_of_hormuz_sovereignty';

-- Gulf attacks: Iran + Yemen attackers, Saudi/UAE/Gulf-states + USA bases as
-- targets, Israel co-targeted in war periods.
UPDATE friction_nodes SET centroid_ids = ARRAY[
    'MIDEAST-IRAN',
    'MIDEAST-YEMEN',
    'MIDEAST-SAUDI',
    'MIDEAST-GULF',
    'MIDEAST-ISRAEL',
    'AMERICAS-USA'
] WHERE id = 'gulf_attacks_on_arab_states';

COMMIT;
