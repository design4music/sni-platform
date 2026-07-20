-- Great Lakes theater: greenfield structure (Phase 1 sign-off, 2026-07-20).
--
-- Theater was a blank shell -- 0 fn_anchor bundles, 0 narratives_v2 on all four
-- draft atomics, all description_*/editorial_summary_*/name_de NULL. The draft
-- decomposition was training-data-aged.
--
-- Grounded against 180d of real coverage: 417 titles carrying AFRICA-DRC
-- (Jan 20 -> Jul 20 2026), plus a system-wide probe for Great Lakes proper
-- nouns outside that centroid.
--
-- ---------------------------------------------------------------------------
-- CENTROID LAYER WAS 4/5 FICTION (found first, §4 / Horn-of-Africa lesson):
--
--   AFRICA-DRC            centroid_anchor row: YES    417 titles
--   AFRICA-RWANDA                              NO       0
--   AFRICA-UGANDA                              NO       0
--   AFRICA-BURUNDI                             NO       0
--   NON-STATE-M23                              NO       0
--
-- All four draft atomics were gated partly or wholly on centroids that have
-- never tagged a single title. Rwanda/Uganda/Burundi/Kigali/Kagame/Museveni and
-- the Rwandan Defence Forces all live inside AFRICA-EAST -- which also carries
-- Kenya, Tanzania, Zambia, Malawi, South Sudan, Mauritius, Seychelles and
-- Comoros, i.e. it is NOT co-extensive with this terrain.
--
-- Measured cost of NOT adding AFRICA-EAST: 11 titles/180d, of which 3 are a
-- Macron-Kagame genocide memorial in Paris and 1 is a Sri Lankan river project.
-- AFRICA-DRC's own anchor already carries M23, ADF and CODECO, so the insurgency
-- tags DRC natively. Per the Sahel lesson ("add the participant centroid" only
-- works when that centroid is co-extensive with the terrain), every atomic is
-- gated on AFRICA-DRC alone.
--
-- ---------------------------------------------------------------------------
-- Real-coverage theme map (§2a), 417 titles:
--   1. Ebola outbreak                    165 titles (40%)   -> NOT AN FN
--   2. M23 insurgency                     43 titles         -> KEEP, re-scope
--   3. Minerals / extraction competition  31 titles         -> KEEP
--   4. Mediation + sanctions track        ~25 titles        -> ADD
--   5. Humanitarian / displacement        16 titles         -> narrative layer
--   6. DRC domestic politics               5 titles         -> too thin
--   7. Non-M23 armed groups                1 title          -> MERGE away
--   8. MONUSCO / intervention forces       6 titles         -> RETIRE
--
-- ---------------------------------------------------------------------------
-- WHY EBOLA GETS NO ATOMIC (deliberate, signed off).
--
-- It is 40% of the corpus by title and dominates the event layer harder still:
-- 17 of the top 20 events by source_batch_count are Ebola (top event 38 sources);
-- the M23 war appears twice. It is nonetheless a SITUATION, not a friction node
-- -- see the fn_type='situation' backlog. There is a real friction subset inside
-- it (WHO ceasefire calls 21, border closures 15, USAID/CDC cuts 9, Chinese
-- medical diplomacy 7), but an atomic gated on AFRICA-DRC + Ebola vocabulary
-- would inhale all 165 titles regardless and read as 85% case-count reporting.
-- Accepted: ~40% of this theater's corpus stays unattributed until the situation
-- entity exists.
--
-- ---------------------------------------------------------------------------
-- WHY TWO ATOMICS ARE RETIRED, NOT RE-TUNED.
--
-- drc_intervention_forces: MONUSCO|SANDF|SAMIDRC|peacekeep|casque bleu = 6
-- titles/180d, and the story that exists is the WITHDRAWAL (South African
-- contingent departs, M23 publicly welcomes it, a new MONUSCO chief arrives to
-- "advance peace"). That is a beat in the M23 story, not a phenomenon. Its
-- surviving titles are absorbed by m23_conflict and drc_peace_process.
--
-- eastern_congo_armed_groups: non-M23 groups (CODECO|FDLR|Wazalendo|Mai-Mai|
-- Twirwaneho) = 1 title/180d; real ADF = 7. Worse, it is structurally REDUNDANT
-- with m23_conflict -- M23 *is* an armed group, so as drafted the two atomics
-- describe one phenomenon with one vocabulary, and aliases are OR'd. Merged.
--
-- ---------------------------------------------------------------------------
-- WHY MINERALS STAYS ONE ATOMIC.
--
-- The theme splits conceptually in two -- great-power extraction competition
-- (US-DRC minerals pact, Chemaf/Virtus, Gecamines leadership change, Chinese
-- cobalt incumbency, export controls) versus conflict financing ("Congo offers
-- tantalum deposit under M23 control to US", "Congo troops assault coltan-rich
-- town after site is offered to U.S. investors", Rubaya under M23, global brands
-- "likely using mineral that funds rebels"). Per §2 A2b they cannot be split:
-- both carry the identical alias set (coltan/cobalt/Rubaya/mining/pact) and an
-- OR'd bundle would make two atomics match the same titles. The conflict-
-- financing angle is carried in the NARRATIVE layer instead.
--
-- ---------------------------------------------------------------------------
-- ARCHETYPES. All three are null primary_target.
--   m23_conflict              §2 A2 -- `M23`/`AFC` and the east-Congo toponyms
--                             (Goma, Bukavu, Rubaya, Uvira, Beni) are self-
--                             gating names; no generic domain verbs.
--   drc_peace_process         §2 A2 on named accords/venues + the sanctions
--                             track. Named instruments carry the precision.
--   drc_minerals_competition  multilateral. AMERICAS-USA and ASIA-CHINA are
--                             DROPPED from centroid_ids: the participant gate is
--                             an OR, so keeping global centroids on an atomic
--                             whose bundle holds `cobalt`/`mining`/`copper`
--                             would admit every US/China commodity headline.
--
-- Theater keeps affected_asset_ids {katanga_copper_belt, bisie_tin_mine} (both
-- verified present in strategic_assets) and its anchor_point (29.2, -1.68, Goma)
-- so the homepage conflicts map is unaffected.
--
-- No DELETE; INSERT + UPDATE only. Reversible.

BEGIN;

-- ---------------------------------------------------------------------------
-- Theater: aggregator only. No fn_anchor bundle, never matches, null target.
-- Renamed: "Great Lakes mineral conflict zone" pre-judged the theater as
-- mineral-driven, which the corpus does not support (minerals 31 vs M23 43).
-- centroid_ids reduced to the one live centroid + the USA, which is a genuine
-- principal here (sanctions on Rwanda/Kabila, the minerals pact, the Washington
-- accords). Dropped: AFRICA-RWANDA, AFRICA-UGANDA, AFRICA-BURUNDI (dead refs)
-- and ASIA-CHINA (no longer needed once minerals is DRC-gated).
-- centroid_ids[0] stays AFRICA-DRC so navigation region assignment is correct.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET name_en = 'Eastern Congo conflict and mineral competition',
    name_de = 'Konflikt in Ostkongo und Konkurrenz um Rohstoffe',
    centroid_ids = ARRAY['AFRICA-DRC', 'AMERICAS-USA'],
    primary_target = NULL,
    member_fn_ids = ARRAY[
        'm23_conflict',
        'drc_peace_process',
        'drc_minerals_competition'
    ],
    updated_at = NOW()
WHERE id = 'great_lakes_theater';

-- ---------------------------------------------------------------------------
-- A. RE-SCOPE m23_conflict. Old name ("M23 insurgency and regional proxy
--    dynamics") baked the contested Rwandan-backing claim into the neutral FN
--    label; that belongs on the narrative axis, not here. Also absorbs the
--    merged eastern_congo_armed_groups (ADF at Beni, CODECO).
--    Corpus shows a de-escalation arc inside the window -- monthly M23 volume
--    Feb 22 -> Mar 9 -> Apr 6 -> May 5 -> Jun 1, with the army retaking ground
--    after an M23 withdrawal in May. Scope is the insurgency and the atrocity/
--    accountability record, NOT the mediation track (that is atomic B).
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET name_en = 'M23 insurgency in eastern Congo',
    name_de = 'M23-Aufstand im Osten der DR Kongo',
    centroid_ids = ARRAY['AFRICA-DRC'],
    primary_target = NULL,
    display_order = 82,
    is_active = true,
    updated_at = NOW()
WHERE id = 'm23_conflict';

-- ---------------------------------------------------------------------------
-- B. NEW -- the mediation and sanctions track. The theater's LIVE phase, and
--    before this migration it was homed nowhere in the system. M23 kinetic
--    coverage collapsed across the window while this track kept producing:
--    the Washington accords, Doha, a Swiss-brokered peace-monitoring deal, the
--    ceasefire and prisoner release, US sanctions on the Rwandan army and
--    officials, visa restrictions, Kabila sanctioned for M23 support, Kagame
--    calling the sanctions "insults", and "les accords de paix RDC-Rwanda
--    stagnent".
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope,
    centroid_ids, primary_target, display_order, is_active
) VALUES (
    'drc_peace_process',
    'Mediation and sanctions over eastern Congo',
    'Vermittlung und Sanktionen im Ostkongo-Konflikt',
    'atomic', 'regional',
    ARRAY['AFRICA-DRC'],
    NULL, 83, true
) ON CONFLICT (id) DO UPDATE
SET name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = true,
    updated_at = NOW();

-- ---------------------------------------------------------------------------
-- C. KEEP drc_minerals_competition, DRC-gated. See "WHY MINERALS STAYS ONE
--    ATOMIC" above for the no-split rationale.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET name_en = 'Cobalt and coltan extraction and supply competition',
    name_de = 'Kobalt- und Coltanabbau und Wettbewerb um Lieferketten',
    centroid_ids = ARRAY['AFRICA-DRC'],
    primary_target = NULL,
    display_order = 84,
    is_active = true,
    updated_at = NOW()
WHERE id = 'drc_minerals_competition';

-- ---------------------------------------------------------------------------
-- D. RETIRE -- non-M23 armed groups. 1 title/180d and redundant with atomic A.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET is_active = false,
    updated_at = NOW()
WHERE id = 'eastern_congo_armed_groups';

-- ---------------------------------------------------------------------------
-- E. RETIRE -- intervention forces. 6 titles/180d; the live story is withdrawal.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET is_active = false,
    updated_at = NOW()
WHERE id = 'drc_intervention_forces';

COMMIT;
