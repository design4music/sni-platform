-- Korea theater: structural re-carve (greenfield, approved 2026-07-16).
--
-- Grounded against 180d of real coverage. The theater's real universe is the
-- 1,216 titles on ASIA-NORKOREA; ASIA-SOUTHKOREA looks larger (4,801) but is
-- dominated by off-theater content (~1,055 Samsung/chips/tariffs/shipbuilding,
-- ~206 domestic politics), so atomics scoped loosely to the South drown in
-- earnings noise.
--
-- Measured theme volumes (180d, titles):
--   missile/nuclear programme     301   -> north_korea_missile_program
--   China-DPRK                    189   -> north_korea_china_patronage
--   inter-Korean relations        108   -> inter_korean_relations       (NEW)
--   Russia-DPRK alignment         106   -> north_korea_russia_alignment (NEW)
--   US-ROK alliance modernisation  83   -> korea_peninsula_deterrence
--   reunification                  38   -> retired (see below)
--   sanctions/pressure             15   -> retired (see below)
--   national identity               0
--
-- Retirements:
--
-- korea_reunification_identity -- the phenomenon is being formally abolished,
--   not contested: North Korea deleted reunification from its constitution and
--   Seoul's unification white paper pivoted to "two-state coexistence". The
--   identity half returns 0 titles. 'unification' is also a homograph trap --
--   roughly a third of its hits are the Japanese Unification Church dissolution
--   case. The live phenomenon underneath is inter-Korean relations, which gets
--   its own atomic below rather than inheriting a dead frame.
--
-- north_korea_international_pressure -- 15 titles in 180d, and they are a
--   grab-bag (UNSC humanitarian waivers, a UK sanction on a children's camp,
--   Lazarus crypto heists). Below viability, per the SCS precedent. The
--   denuclearisation/UNSC pressure content folds into the missile programme
--   atomic (that is what the pressure is about); sanctions-evasion folds into
--   the China patronage atomic (that is where non-enforcement happens).
--
-- Re-scope of north_korea_china_leverage -> north_korea_china_patronage:
--   China's leverage does not appear as sanctions enforcement. The 189 China
--   titles are Xi's state visit, the Wang Yi visit, Air China flights and the
--   Beijing-Pyongyang rail link resuming after six years, "How China keeps
--   North Korea's economy alive", and Xi declining to press Kim on nuclear
--   weapons despite a US request. The phenomenon is patronage and sanctions
--   dissolution, so the node is renamed to match what it actually captures.
--
-- Russia and China are kept as separate atomics, not merged into one
-- "external patronage" node: measured co-occurrence on ASIA-NORKOREA is 3
-- titles carrying both against 106 Russia-only and 184 China-only. They are
-- distinct phenomena (combat participation vs economic/diplomatic lifeline)
-- with distinct stance axes.
--
-- Deactivations only; no DELETE, so no cascade risk to event_friction_nodes.
-- Reversible by flipping is_active back and restoring member_fn_ids.

BEGIN;

-- 1. Retire the two dead atomics.
UPDATE friction_nodes
SET is_active = false,
    updated_at = NOW()
WHERE id IN (
    'korea_reunification_identity',      -- phenomenon abolished; 0 identity titles
    'north_korea_international_pressure'  -- 15 titles; below viability
);

-- 2. Re-scope the China node: patronage, not enforcement.
UPDATE friction_nodes
SET id = 'north_korea_china_patronage',
    name_en = 'China''s patronage of North Korea',
    centroid_ids = ARRAY['ASIA-NORKOREA', 'ASIA-CHINA'],
    primary_target = 'ASIA-NORKOREA',
    updated_at = NOW()
WHERE id = 'north_korea_china_leverage';

-- 3. Missile programme: target-centric on the DPRK. The target gate is what
--    makes the generic domain vocabulary (missile, enrichment, warhead) safe.
UPDATE friction_nodes
SET centroid_ids = ARRAY['ASIA-NORKOREA', 'ASIA-SOUTHKOREA', 'AMERICAS-USA', 'ASIA-JAPAN'],
    primary_target = 'ASIA-NORKOREA',
    updated_at = NOW()
WHERE id = 'north_korea_missile_program';

-- 4. Deterrence: re-scoped to the US-ROK alliance and its modernisation
--    (OPCON transfer, USFK posture, the nuclear-submarine bid, extended
--    deterrence). Target-centric on the South -- the alliance is about the ROK,
--    and the gate keeps generic alliance/drill vocabulary off other theaters.
UPDATE friction_nodes
SET name_en = 'US-ROK alliance and peninsula deterrence',
    centroid_ids = ARRAY['ASIA-SOUTHKOREA', 'AMERICAS-USA', 'ASIA-NORKOREA', 'ASIA-JAPAN'],
    primary_target = 'ASIA-SOUTHKOREA',
    updated_at = NOW()
WHERE id = 'korea_peninsula_deterrence';

-- 5. NEW: Russia-DPRK alignment. Target-centric on the DPRK. Overlaps
--    ukraine_battlefield slightly via the shared EUROPE-RUSSIA participant on
--    Kursk stories; that is acceptable structural overlap (spec section 1),
--    not a defect -- the subject here is what the DPRK is becoming.
INSERT INTO friction_nodes (
    id, name_en, fn_type, centroid_ids, primary_target,
    is_active, scope, affected_asset_ids, display_order
) VALUES (
    'north_korea_russia_alignment',
    'North Korea''s alignment with Russia',
    'atomic',
    ARRAY['ASIA-NORKOREA', 'EUROPE-RUSSIA', 'EUROPE-UKRAINE', 'EUROPE-BELARUS'],
    'ASIA-NORKOREA',
    true, 'regional', ARRAY[]::text[], 3
) ON CONFLICT (id) DO NOTHING;

-- 6. NEW: inter-Korean relations. Bilateral archetype -- the engagement and
--    hostility track runs in both directions (Seoul's overtures, Pyongyang's
--    responses, incidents on the line), so no valid primary_target.
INSERT INTO friction_nodes (
    id, name_en, fn_type, centroid_ids, primary_target,
    is_active, scope, affected_asset_ids, display_order
) VALUES (
    'inter_korean_relations',
    'Inter-Korean relations',
    'atomic',
    ARRAY['ASIA-NORKOREA', 'ASIA-SOUTHKOREA'],
    NULL,
    true, 'regional', ARRAY[]::text[], 4
) ON CONFLICT (id) DO NOTHING;

-- 7. Theater membership: pure aggregator, no bundle, no target.
UPDATE friction_nodes
SET member_fn_ids = ARRAY[
        'north_korea_missile_program',
        'north_korea_china_patronage',
        'north_korea_russia_alignment',
        'inter_korean_relations',
        'korea_peninsula_deterrence'
    ],
    centroid_ids = ARRAY['ASIA-NORKOREA', 'ASIA-SOUTHKOREA', 'AMERICAS-USA', 'ASIA-CHINA', 'ASIA-JAPAN', 'EUROPE-RUSSIA'],
    primary_target = NULL,
    updated_at = NOW()
WHERE id = 'korea_theater';

COMMIT;
