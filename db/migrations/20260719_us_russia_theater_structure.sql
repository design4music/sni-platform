-- US-Russia theater: greenfield structure (Phase 1 sign-off, 2026-07-19).
--
-- Grounded against 180d of real coverage: 4,132 titles carrying BOTH
-- AMERICAS-USA and EUROPE-RUSSIA (Jan 20 -> Jul 19 2026); 130 dyad-dominant
-- events read. Theater was a blank shell -- 0 fn_anchor bundles, 0 narratives_v2,
-- 0 attributed events on both draft atomics.
--
-- Real-coverage theme map (§2a):
--   1. US sanctions relief as leverage    ~355 kw, largest event cluster  -> ADD
--      (oil waivers, OFAC licences, India 30-day waiver, Rosneft German ops
--       exemption, Lukoil->Carlyle, Cuba tanker)
--   2. Trump-Putin bilateral channel      229 channel-vocab titles        -> ADD
--      (Abu Dhabi, Alaska, envoy trips, mil-to-mil talks resumed, Dmitriev
--       investment pitch, G20 Miami, congratulation calls)
--   3. Nuclear arms control               89 kw, New START EXPIRED 2026-02-04 -> KEEP
--   4. Russia-Iran alignment vs US        525 titles -- NOT homed here, see below
--   5. Russia-China-US triangle           229 kw -- co-mention of 2/3, no atomic
--   6. Election interference / info war   3 titles/180d                   -> DEACTIVATE
--   7. Tech/platform decoupling           ~4 events -- too thin, no atomic
--
-- WHY IRAN IS NOT AN ATOMIC HERE. Russia's role in the US-Iran war (525 titles:
-- targeting intel on US bases, UN vetoes, Lavrov "abandon ultimatums") is a real
-- unhomed gap, but every alignment FN in the system is homed on the TERRAIN /
-- ALIGNING PARTY, never on the great power: north_korea_russia_alignment->NK,
-- armenia_western_pivot->Caucasus, colombia_us_alignment->Andean,
-- pacific_island_contest->the islands, sahel_wagner_presence->Sahel,
-- eu_right_realignment->EU. A great power appears in EVERY theater, so homing by
-- great power turns a theater into a grab-bag. Recommended as a follow-up atomic
-- on iran_theater (which already gates MIDEAST-IRAN and has no Russia actor).
--
-- WHY SANCTIONS ARE NOT LEFT TO russia_sanctions_regime. That atomic (1,100
-- events, russia_europe_theater) is dominated by EUROPEAN enforcement --
-- shadow-fleet seizures by France/UK, Bulgarian Lukoil refinery supply. The US
-- instrument story (waiver/licence/carve-out/OFAC) is a different phenomenon:
-- sanctions relief as a bargaining chip with Moscow. Separated by vocabulary,
-- not by exclusion logic -- the new bundle carries US instruments only and no
-- shadow-fleet/seizure/interception terms.
--
-- Archetype: dyad-AND on all three atomics, exactly the us_china_theater shape
-- (centroid_ids={AMERICAS-USA} + primary_target=EUROPE-RUSSIA). Russia is the
-- subject in all three (sanctions ON Russia, channel WITH Russia, arms control
-- WITH Russia), so the target gate is the general substitute for AND-logic and
-- makes generic domain verbs (waiver, talks, treaty) safe. Known caveat
-- (spec §4): audit_fn_anchor_aliases.py applies the participant gate but NOT
-- primary_target, so %foreign will be OVERSTATED here -- read it as a
-- promiscuity ranking, not a leak rate.
--
-- Theater centroid fix: AMERICAS-CANADA matched 8 titles/180d (training-data-aged
-- draft); EUROPE-UKRAINE on the theater's OR-gate would drag the entire Ukraine
-- war in. Reduced to the clean dyad, matching us_china_theater.
--
-- Theater rename: "strategic rivalry" is contradicted by the corpus -- 2026
-- coverage is as much rapprochement (sanctions relief, warm calls, resumed
-- mil-to-mil) as rivalry.
--
-- No DELETE; INSERT + UPDATE only. Reversible.

BEGIN;

-- ---------------------------------------------------------------------------
-- Theater: aggregator only. No fn_anchor bundle, never matches, null target.
-- Keeps its existing energy affected_asset_ids (yamal_lng, west_siberian_basin,
-- samotlor_field) -- they belong to the sanctions-leverage story.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET name_en = 'US-Russia strategic relationship',
    name_de = 'Das strategische Verhältnis zwischen den USA und Russland',
    centroid_ids = ARRAY['AMERICAS-USA','EUROPE-RUSSIA'],
    primary_target = NULL,
    member_fn_ids = ARRAY[
        'us_russia_sanctions_leverage',
        'us_russia_bilateral_channel',
        'us_russia_arms_control'
    ],
    updated_at = NOW()
WHERE id = 'us_russia_theater';

-- ---------------------------------------------------------------------------
-- A. NEW -- US sanctions relief as leverage (largest theme)
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope,
    centroid_ids, primary_target, display_order, is_active
) VALUES (
    'us_russia_sanctions_leverage',
    'Sanctions relief as leverage',
    'Sanktionslockerung als Druckmittel',
    'atomic', 'regional',
    ARRAY['AMERICAS-USA'], 'EUROPE-RUSSIA', 92, true
) ON CONFLICT (id) DO UPDATE
SET name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = true,
    updated_at = NOW();

-- ---------------------------------------------------------------------------
-- B. NEW -- Trump-Putin bilateral channel (relationship management axis).
--    Bundle deliberately EXCLUDES ceasefire / peace-plan verbs: those stay with
--    ukraine_peace_negotiations (808 events). This atomic is the channel itself.
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope,
    centroid_ids, primary_target, display_order, is_active
) VALUES (
    'us_russia_bilateral_channel',
    'Bilateral channel and normalisation',
    'Bilateraler Gesprächskanal und Normalisierung',
    'atomic', 'regional',
    ARRAY['AMERICAS-USA'], 'EUROPE-RUSSIA', 93, true
) ON CONFLICT (id) DO UPDATE
SET name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = true,
    updated_at = NOW();

-- ---------------------------------------------------------------------------
-- C. KEEP, re-scoped -- Nuclear arms control. Was null-target Archetype B;
--    moved onto the dyad-AND gate like its siblings.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET name_en = 'Nuclear arms control and strategic stability',
    name_de = 'Nukleare Rüstungskontrolle und strategische Stabilität',
    centroid_ids = ARRAY['AMERICAS-USA'],
    primary_target = 'EUROPE-RUSSIA',
    is_active = true,
    updated_at = NOW()
WHERE id = 'us_russia_arms_control';

-- ---------------------------------------------------------------------------
-- D. DEACTIVATE -- Election interference. 3 titles/180d: a 2016/2020-era draft.
--    The live disinformation residual (Epstein fakes, Macron claims) is
--    Russia->Europe and already sits in russia_hybrid_warfare.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET is_active = false,
    updated_at = NOW()
WHERE id = 'us_russia_election_interference';

COMMIT;
