-- US domestic theater: greenfield structure (Phase 1 sign-off, 2026-07-19).
--
-- Theater was a blank shell: 0 fn_anchor bundles, 0 narratives_v2, 0 attributed
-- events, 0 completeness fields on the theater and all four draft atomics. The
-- draft decomposition was training-data-aged and is substantially replaced.
--
-- Grounded against 180d of real coverage (Jan 20 -> Jul 19 2026) on the
-- AMERICAS-USA centroid.
--
-- WHY THE DRAFT'S federal_state_authority DIES. Its premise was federal troop
-- deployments to cities. Measured: 'National Guard' 14 titles, 'Insurrection
-- Act' 4, 'federalize' 1, 'sanctuary city' 9, 'troop deployment' 24 of which
-- only 4 are USA-only (the rest are Iran/Germany). There is no city-deployment
-- story in this corpus quarter. What the draft was reaching for is real but is
-- three separate phenomena -- courts, cabinet personnel, and the central bank --
-- carved below as C/D/E.
--
-- WHY THOSE THREE ARE NOT ONE ATOMIC. Measured pairwise co-occurrence over the
-- window: judicial n fed = 10 titles (the Lisa Cook ruling, correctly dual),
-- judicial n loyalty = 1, fed n loyalty = 0, all three = 0. They are
-- empirically orthogonal, not redundant. Different actors, different stakes.
--
-- WHY culture_wars DIES. Its largest clusters are Kimmel 34 / Obama video 49 /
-- Pope 34 -- small, spiky, low external legibility, and it is the one atomic
-- that would have needed a bare-country gate. The institutionally legible half
-- of its content (broadcast-licence review, NPR/PBS defunding) is carved out as
-- H, which is anchored on the regulator and the First Amendment rather than on
-- the culture-war topic.
--
-- WHY immigration_border BECOMES INTERIOR ENFORCEMENT, AND HOW IT STAYS CLEAR OF
-- mexico_theater. These are two phenomena, not one. mexico_theater owns the
-- bilateral border, cartels and tariff leverage, and all three of its atomics
-- carry primary_target = AMERICAS-MEXICO. This atomic owns ICE interior
-- operations -- raids, detention deaths, judges ordering releases, ICE at
-- airports/stadiums/voting sites, Abbott vs Houston, Minnesota charging an ICE
-- officer. Dropping AMERICAS-MEXICO and AMERICAS-CENTRAL from centroid_ids is
-- what separates them mechanically. At 2,446 titles / 534 non-English / 137
-- publishers it is the most externally legible US domestic story in the corpus.
-- The id is renamed because 'border' now names exactly what is out of scope;
-- safe here because the row has 0 event_friction_nodes / 0 narratives_v2 /
-- 0 fn_asset_evidence children.
--
-- WHY EPSTEIN LIVES HERE. 3,105 titles / 966 non-English / 157 publishers, the
-- largest theme in the corpus and previously unhomed anywhere in the system.
-- The centroid gate already requires AMERICAS-USA, so these titles are
-- US-anchored by construction; the Mandelson, Jack Lang, Norwegian-royals,
-- Prince Andrew and Slim/Salinas threads reach the corpus through the US files
-- release and US court process. One network with a US centre.
--
-- ARCHETYPE: all eight atomics take centroid_ids = {AMERICAS-USA} with
-- primary_target = AMERICAS-USA. The target is redundant at TITLE level (the
-- participant gate already means "carries USA") but is set deliberately: per the
-- south_asia and cuba lessons, only primary_target activates the
-- 50%-of-event-titles rule at EVENT level. On a centroid this large that rule is
-- what suppresses mega-cluster contamination -- the Iran-war and Big-Tech events
-- run to 100-400 titles each and would otherwise drag in whole foreign events on
-- a single stray alias match.
--
-- Because the participant gate is a bare country, alias purity is the ONLY
-- precision lever (spec §2). Every bundle at §3 is built from institution-
-- specific proper nouns and fixed compounds -- no bare domain verbs, and no bare
-- Trump / Congress / Senate / Supreme Court.
--
-- Collisions already measured, to encode at §3 (do not re-derive):
--   Warsh    c warship/warships  -- 698 raw matches, ~150 real. Use 'Kevin Warsh'.
--   Bondi    c Bondi Beach       -- Australian mass shooting.  Use 'Pam Bondi'.
--   Supreme Court (bare)         -- 1,798 raw; India/Korea/Nigeria/Estonia/AU.
--   special counsel              -- resolves to Korea (Yoon).
--   Hegseth                      -- resolves to the Iran war, not domestic.
--   impeach                      -- 509 raw, only 129 USA-only.
--   militia                      -- 69 raw, only 3 USA-only.
--   FCC (bare)                   -- SpaceX/Amazon/Charter spectrum business.
--   assassination (bare)         -- Khamenei / Charlie Kirk / Peter Obi (NG).
--   ICE                          -- clean, but ONLY via the case-sensitive
--                                   all-caps acronym path (<=4 chars). Verify
--                                   apply_fn_anchor_bundle.py preserves case.
--
-- Theater name drops "polarisation": a framing word does not belong in neutral
-- FN prose (it belongs in narratives_v2).
--
-- No DELETE anywhere; INSERT + UPDATE only. Reversible.

BEGIN;

-- ---------------------------------------------------------------------------
-- Theater: pure aggregator. No fn_anchor bundle, never matches, null target.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET name_en = 'United States domestic governance conflict',
    name_de = 'Innenpolitischer Machtkonflikt in den USA',
    centroid_ids = ARRAY['AMERICAS-USA'],
    primary_target = NULL,
    scope = 'global',
    member_fn_ids = ARRAY[
        'us_electoral_legitimacy',
        'us_judicial_constraint',
        'us_executive_loyalty',
        'us_fed_independence',
        'us_interior_immigration_enforcement',
        'us_epstein_elite_network',
        'us_political_violence',
        'us_press_freedom'
    ],
    is_active = true,
    updated_at = NOW()
WHERE id = 'us_domestic_theater';

-- ---------------------------------------------------------------------------
-- A. KEEP -- Electoral legitimacy. 685 titles / 68 publishers.
--    Redistricting war (TX/FL/CA/VA/UT/SC), mail-in ballot restriction fight
--    and the Postal Service order blocked by federal judges, proof-of-
--    citizenship and voter-ID pushes, SCOTUS on the Voting Rights Act, the FBI
--    raid on an Ohio voting-rights group.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET name_en = 'Electoral legitimacy and the midterm contest',
    name_de = 'Wahllegitimität und der Midterm-Wettstreit',
    centroid_ids = ARRAY['AMERICAS-USA'],
    primary_target = 'AMERICAS-USA',
    scope = 'regional',
    display_order = 101,
    is_active = true,
    updated_at = NOW()
WHERE id = 'us_electoral_legitimacy';

-- ---------------------------------------------------------------------------
-- B. RE-SCOPE + RENAME -- Interior immigration enforcement. 2,446 titles.
--    Border/cartel/tariff content stays with mexico_theater (see header).
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET id = 'us_interior_immigration_enforcement'
WHERE id = 'us_immigration_border';

UPDATE friction_nodes
SET name_en = 'Interior immigration enforcement',
    name_de = 'Einwanderungsdurchsetzung im Landesinneren',
    centroid_ids = ARRAY['AMERICAS-USA'],
    primary_target = 'AMERICAS-USA',
    scope = 'regional',
    display_order = 105,
    is_active = true,
    updated_at = NOW()
WHERE id = 'us_interior_immigration_enforcement';

-- ---------------------------------------------------------------------------
-- C. NEW -- Judicial constraint on executive power. 488 titles.
--    Birthright citizenship rejected, the tariff-authority ruling, TPS and
--    southern-border decisions, federal judges blocking executive orders.
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope,
    centroid_ids, primary_target, display_order, is_active
) VALUES (
    'us_judicial_constraint',
    'Judicial constraint on executive power',
    'Gerichtliche Schranken der Exekutivgewalt',
    'atomic', 'regional',
    ARRAY['AMERICAS-USA'], 'AMERICAS-USA', 102, true
) ON CONFLICT (id) DO UPDATE
SET name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = true,
    updated_at = NOW();

-- ---------------------------------------------------------------------------
-- D. NEW -- Cabinet turnover and executive loyalty. 546 titles.
--    Bondi removal, Noem ouster, Gabbard resignation, Patel, inspectors general.
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope,
    centroid_ids, primary_target, display_order, is_active
) VALUES (
    'us_executive_loyalty',
    'Cabinet turnover and executive loyalty',
    'Kabinettsumbau und Loyalität in der Exekutive',
    'atomic', 'regional',
    ARRAY['AMERICAS-USA'], 'AMERICAS-USA', 103, true
) ON CONFLICT (id) DO UPDATE
SET name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = true,
    updated_at = NOW();

-- ---------------------------------------------------------------------------
-- E. NEW -- Federal Reserve independence. 470 titles / 84 non-English.
--    Warsh nomination, the blocked removal of governor Lisa Cook, "totally
--    independent" framing. Highest market read-through of the set, which is why
--    the foreign business press carries it.
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope,
    centroid_ids, primary_target, display_order, is_active
) VALUES (
    'us_fed_independence',
    'Federal Reserve independence',
    'Unabhängigkeit der US-Notenbank',
    'atomic', 'regional',
    ARRAY['AMERICAS-USA'], 'AMERICAS-USA', 104, true
) ON CONFLICT (id) DO UPDATE
SET name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = true,
    updated_at = NOW();

-- ---------------------------------------------------------------------------
-- F. NEW -- Epstein files and elite networks. 3,105 titles / 966 non-English.
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope,
    centroid_ids, primary_target, display_order, is_active
) VALUES (
    'us_epstein_elite_network',
    'Epstein files and elite networks',
    'Epstein-Akten und Elitennetzwerke',
    'atomic', 'regional',
    ARRAY['AMERICAS-USA'], 'AMERICAS-USA', 106, true
) ON CONFLICT (id) DO UPDATE
SET name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = true,
    updated_at = NOW();

-- ---------------------------------------------------------------------------
-- G. NEW -- Political violence and protective security. 350 titles.
--    The Correspondents' Dinner shooting and the Cole Allen prosecution,
--    Mar-a-Lago, gunfire near the White House, the Vance motorcade, the
--    Omar town hall attack.
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope,
    centroid_ids, primary_target, display_order, is_active
) VALUES (
    'us_political_violence',
    'Political violence and protective security',
    'Politische Gewalt und Personenschutz',
    'atomic', 'regional',
    ARRAY['AMERICAS-USA'], 'AMERICAS-USA', 107, true
) ON CONFLICT (id) DO UPDATE
SET name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = true,
    updated_at = NOW();

-- ---------------------------------------------------------------------------
-- H. NEW -- Press freedom and broadcast regulation. 221 titles.
--    The Kimmel/ABC licence review, NPR and PBS defunding blocked on First
--    Amendment grounds, the Comey prosecution, revoked visas of a Costa Rican
--    newspaper's executives. Anchored on the regulator and the constitutional
--    claim, NOT on the culture-war topic.
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope,
    centroid_ids, primary_target, display_order, is_active
) VALUES (
    'us_press_freedom',
    'Press freedom and broadcast regulation',
    'Pressefreiheit und Rundfunkaufsicht',
    'atomic', 'regional',
    ARRAY['AMERICAS-USA'], 'AMERICAS-USA', 108, true
) ON CONFLICT (id) DO UPDATE
SET name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = true,
    updated_at = NOW();

-- ---------------------------------------------------------------------------
-- I. DEACTIVATE -- draft atomics replaced above. Rows kept (no DELETE, no
--    cascade); they simply fall out of every roll-up and matching path.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET is_active = false,
    updated_at = NOW()
WHERE id IN ('us_culture_wars', 'us_federal_state_authority');

COMMIT;
