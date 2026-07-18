-- South China Sea: retire the theater, keep one standalone atomic.
--
-- Grounded against 365d of real coverage (2026-07-16). The SCS corpus is
-- ~135 titles/180d and flat. Three of the four atomics have no corpus at all:
-- fisheries/maritime-militia return 0, nine-dash returns 0, and the named-reef
-- vocabulary is empty (Mischief Reef 1, Fiery Cross 0, Spratly 5, Paracel 6).
--
-- The split into claims vs freedom-of-navigation is also not expressible with
-- the available data levers: bundle aliases are OR'd, there is no AND, and no
-- SCS centroid exists for primary_target to gate on. Freedom-of-navigation has
-- no distinctive vocabulary of its own -- FONOP/Seventh Fleet/Talisman Sabre
-- return 0, 'freedom of navigation' resolves to Hormuz, 'Nimitz' to the
-- Caribbean, 'George Washington' to the president. Both atomics would have had
-- to carry the same toponym set and would have matched the identical titles.
--
-- So the dispute supports exactly one atomic. It keeps the whole phenomenon
-- (claims, law, incidents, features, external presence) and stands alone --
-- no theater, since nesting a single atomic under one is a wrapper with no
-- roll-up to do. Frontend support for theater-less atomics added alongside
-- this migration (lib/friction-nodes.ts + FrictionNodesBrowser.tsx).
--
-- Deactivations only; no DELETE, so no cascade risk to event_friction_nodes.
-- Reversible by flipping is_active back.

BEGIN;

UPDATE friction_nodes
SET is_active = false,
    updated_at = NOW()
WHERE id IN (
    'scs_theater',              -- one atomic left; nothing to aggregate
    'scs_freedom_of_navigation',-- no vocabulary distinct from the claims atomic
    'scs_reef_militarisation',  -- named-reef corpus is empty
    'scs_fisheries_conflict'    -- 0 titles: no fisheries/militia coverage
);

-- Archetype A2 (anchor == subject): the toponym carries the precision, so no
-- target gate. Participants stay China + the ASEAN claimants + the US.
-- ASIA-SOUTHEAST is currently unmatchable (it has no centroid_anchor row in
-- taxonomy_v3 -- tracked separately); it is kept here because it is correct,
-- and recall improves on its own once that is fixed.
UPDATE friction_nodes
SET primary_target = NULL,
    centroid_ids = ARRAY['ASIA-CHINA', 'ASIA-SOUTHEAST', 'AMERICAS-USA'],
    updated_at = NOW()
WHERE id = 'south_china_sea_claims';

COMMIT;
