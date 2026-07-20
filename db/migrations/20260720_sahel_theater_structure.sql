-- Sahel theater: greenfield structure (Phase 1 sign-off, 2026-07-20).
--
-- Theater was a blank shell: 4 draft atomics, 0 fn_anchor bundles,
-- 0 narratives_v2, 0 event_friction_nodes, 0 fn_asset_evidence.
--
-- Grounded against 180d of real coverage: 1,105 titles carrying AFRICA-SAHEL
-- (Jan 20 -> Jul 12 2026). Language mix en 556 / fr 302 -- francophone theater,
-- French desks (France 24, Le Monde, Le Figaro) carry a third of it.
--
-- CENTROID HEALTH (measured, not assumed). ~30% of the centroid is off-theater:
--   Senegal 196 titles, only 4 with any Sahel-security link (Sonko/Faye row,
--     IMF debt, anti-gay law, AFCON) -- a coastal democracy, not this conflict
--   Guinea 68 -- Equatorial Guinea (papal tour), Papua New Guinea, bauxite
--   'Niger' -> Nigerian geography ~39 (Niger State / Niger Delta / Niger Bridge,
--     Punch + Vanguard) -- genuine whole-word, real toponym ambiguity
--   'AES' -> AES Corp utility 11/14 (BlackRock/EQT $33.4bn buyout)
--   'mali' -> Serbo-Croatian "small" 23 (hr/sl/ca)
-- The word-start matcher trap was CHECKED and does NOT fire here: 'mali' is
-- 377/381 whole-word, 'niger' 137/139. The damage is centroid scope and toponym
-- ambiguity, not the matcher. Centroid scope is fixed in the companion
-- migration 20260720_sahel_centroid_scope.sql; the current 180d window is not
-- re-labelled, so bundle purity is what protects this build -- NO atomic below
-- carries Senegal/Guinea vocabulary, so those titles cannot attribute.
--
-- REAL-COVERAGE THEME MAP (§2a). One dominant story: a coordinated JNIM +
-- Tuareg offensive is breaking the Malian junta while Russia's Africa Corps
-- visibly retreats. Defence Minister Sadio Camara killed, Bamako attacked,
-- Kidal handed to Tuareg rebels "apres un accord avec les Russes", France
-- urging evacuation, Burkina cutting diplomatic ties with Paris.
--
--   1. Jihadist insurgency (JNIM 30 / IS-Sahel-ISWAP 25 / Boko Haram 74 /
--      fuel-blockade 32)                                  -> KEEP, re-scoped
--   2. Tuareg separatism  (Tuareg/Azawad/Kidal 52)        -> ADD (unhomed)
--   3. Junta consolidation (coup/junta 72, AES/ECOWAS 22) -> KEEP
--   4. Security-patron contest (Russia+Sahel 101,
--      Africa Corps 17, Turkiye ~30, Morocco 7, US)       -> ADD (retires 6)
--   5. France rupture (France+Sahel 68)                   -> ADD (retires 7)
--   6. sahel_wagner_presence                              -> DEACTIVATE
--   7. sahel_french_withdrawal                            -> DEACTIVATE
--
-- WHY sahel_wagner_presence DIES. Its premise has INVERTED. It is named
-- "Wagner and Russian military expansion"; the 2026 corpus is retreat --
-- "l'Africa Corps recule sous la pression des djihadistes" (Le Figaro),
-- "Russian Forces Withdraw from Rebel-Held Kidal", "la fiabilite du soutien
-- russe remise en question" (France 24), "Rusia se atasca en Mali: su modelo
-- de seguridad empieza a hundirse" (El Mundo), "Mali's militant attacks expose
-- limits of Putin's power in Africa" (Guardian), Tuareg rebels urging Russian
-- forces to withdraw. Wagner also folded into Africa Corps in 2024. An FN whose
-- NAME asserts the opposite of the coverage cannot be re-tuned into truth.
--
-- WHY sahel_french_withdrawal DIES -- stale, impure and redundant at once.
--   stale:     Barkhane|Serval|MINUSMA = 0 hits in 180 days. The operations
--              that define "withdrawal" are absent from the corpus.
--   impure:    "Post-French security vacuum AND great power competition" is
--              two orthogonal phenomena in one name.
--   redundant: its great-power half duplicated sahel_wagner_presence.
-- What is live is RUPTURE, not withdrawal: Burkina "rompre ses relations
-- diplomatiques" with France, a DGSE agent given 20 years in Bamako, Niger
-- blaming France for the Niamey airport attack, a junta cadre urging people to
-- "se preparer" for war with France, France pulling diplomats and urging
-- citizens out.
--
-- WHY TUAREG SEPARATISM IS SEPARATE FROM THE JIHADISTS. They are tactically
-- aligned in this offensive but are not the same phenomenon: the FLA/CSP are
-- secular northern separatists claiming self-determination over Azawad, JNIM is
-- an al-Qaeda affiliate seeking to topple the state. Folding them together
-- would make the largest atomic impure and would collapse two genuinely
-- different stance axes (self-determination vs territorial integrity) into one.
-- Separated by vocabulary (Kidal/Azawad/FLA/CSP vs JNIM/ISWAP/Ansaroul), not by
-- exclusion logic. Overlap to be measured at §4 -- some is expected and fine.
--
-- WHY THE PATRON CONTEST IS ONE ATOMIC, NOT FOUR. Turkiye (~30), Morocco (7)
-- and US re-engagement are individually far too thin to stand (spec §2a: a
-- theme with no volume is not an atomic). The coherent phenomenon is the
-- contest to become the Sahel's security patron after France; Russia is its
-- largest participant, not its subject. Accepted cost: less purity than a
-- Russia-only atomic. Flagged to the user at sign-off.
--
-- ARCHETYPE. This is a multi-dyad regional-instability theater (spec, south_asia
-- lesson): the acting party differs by atomic. Atomics 1-4 are terrain-gated on
-- AFRICA-SAHEL with primary_target NULL -- there is no single subject country to
-- target (the phenomenon spans Mali/Niger/Burkina/Chad and a target would delete
-- three quarters of it). sahel_france_rupture is the one dyad-AND atomic:
-- centroid_ids includes EUROPE-FRANCE and primary_target is AFRICA-SAHEL, so a
-- title must carry BOTH -- this is what stops it swallowing French domestic news.
--
-- Boko Haram / Lake Chad is folded into atomic 1: it is the same jihadist
-- phenomenon and 74 titles are otherwise homeless. NOTE for a later build:
-- there is no Nigeria FN anywhere in the system despite 2,514 Nigeria
-- titles/180d. Nigerian domestic banditry is a theater-sized gap, out of scope
-- here. sudan_civil_war keeps the Chad-Sudan spillover (20 titles); this
-- theater does not claim it.
--
-- Theater fix: AFRICA-NIGERIA dropped from the aggregator's centroid_ids. A
-- theater carries no bundle and never matches, so its centroids are display
-- scope only, and Nigeria would misrepresent the theater's terrain.
--
-- No DELETE; INSERT + UPDATE only. Reversible.

BEGIN;

-- ---------------------------------------------------------------------------
-- Theater: pure aggregator. No fn_anchor bundle, never matches, null target.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET name_en = 'Sahel military transition zone',
    name_de = 'Militärische Übergangszone Sahel',
    centroid_ids = ARRAY['AFRICA-SAHEL','EUROPE-FRANCE','EUROPE-RUSSIA','AMERICAS-USA'],
    primary_target = NULL,
    member_fn_ids = ARRAY[
        'sahel_jihadist_insurgency',
        'sahel_tuareg_separatism',
        'sahel_junta_consolidation',
        'sahel_security_patron_contest',
        'sahel_france_rupture'
    ],
    is_active = true,
    updated_at = NOW()
WHERE id = 'sahel_theater';

-- ---------------------------------------------------------------------------
-- 1. KEEP, re-scoped -- jihadist armed groups ONLY. The Tuareg half moves to 2.
--    Absorbs the Lake Chad basin (Boko Haram / ISWAP), previously unhomed.
--    NON-STATE-JIHADISTS and AFRICA-NIGERIA stay on the OR-gate: the Lake Chad
--    basin genuinely spans the Nigeria centroid.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET name_en = 'Jihadist insurgency and territorial contest',
    name_de = 'Dschihadistischer Aufstand und territorialer Wettstreit',
    centroid_ids = ARRAY['AFRICA-SAHEL','AFRICA-NIGERIA','NON-STATE-JIHADISTS'],
    primary_target = NULL,
    scope = 'regional',
    display_order = 101,
    is_active = true,
    updated_at = NOW()
WHERE id = 'sahel_jihadist_insurgency';

-- ---------------------------------------------------------------------------
-- 2. NEW -- Tuareg separatism and the northern Mali question.
--    Kidal, Azawad, FLA/CSP-DPA. 52 titles, co-principal in the offensive
--    that is destabilising Bamako, and homeless until now.
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope,
    centroid_ids, primary_target, display_order, is_active
) VALUES (
    'sahel_tuareg_separatism',
    'Tuareg separatism and the northern Mali question',
    'Tuareg-Separatismus und die Frage Nordmalis',
    'atomic', 'regional',
    ARRAY['AFRICA-SAHEL'], NULL, 102, true
) ON CONFLICT (id) DO UPDATE
SET name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = true,
    updated_at = NOW();

-- ---------------------------------------------------------------------------
-- 3. KEEP -- healthiest of the four drafts. Absorbs the AES-vs-ECOWAS
--    sovereignty rupture (~22), too thin to stand alone: party dissolutions in
--    Burkina, Niger's ICC withdrawal, the UN human-rights office closure,
--    "une junte qui se bunkerise". centroid_ids stays AFRICA-SAHEL alone --
--    this is a purely internal phenomenon and any external centroid on the
--    OR-gate would admit foreign-only titles.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET name_en = 'Junta consolidation and sovereigntist realignment',
    name_de = 'Junta-Konsolidierung und souveränistische Neuausrichtung',
    centroid_ids = ARRAY['AFRICA-SAHEL'],
    primary_target = NULL,
    scope = 'regional',
    display_order = 103,
    is_active = true,
    updated_at = NOW()
WHERE id = 'sahel_junta_consolidation';

-- ---------------------------------------------------------------------------
-- 4. NEW -- the contest to become the Sahel's security patron after France.
--    Africa Corps performance and retreat, Turkiye's drone/training model,
--    US re-engagement, Morocco's Atlantic access offer to the landlocked AES.
--    Retires sahel_wagner_presence (inverted premise -- see header).
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope,
    centroid_ids, primary_target, display_order, is_active
) VALUES (
    'sahel_security_patron_contest',
    'Contest for security patronage',
    'Wettstreit um die Sicherheitspatronage',
    'atomic', 'regional',
    ARRAY['AFRICA-SAHEL','EUROPE-RUSSIA'], NULL, 104, true
) ON CONFLICT (id) DO UPDATE
SET name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = true,
    updated_at = NOW();

-- ---------------------------------------------------------------------------
-- 5. NEW -- the France-Sahel rupture. Dyad AND: a title must carry BOTH
--    EUROPE-FRANCE (participant gate) and AFRICA-SAHEL (primary_target),
--    which is what keeps French domestic coverage out.
--    Retires sahel_french_withdrawal (stale + impure + redundant -- see header).
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope,
    centroid_ids, primary_target, display_order, is_active
) VALUES (
    'sahel_france_rupture',
    'Rupture with France',
    'Bruch mit Frankreich',
    'atomic', 'regional',
    ARRAY['AFRICA-SAHEL','EUROPE-FRANCE'], 'AFRICA-SAHEL', 105, true
) ON CONFLICT (id) DO UPDATE
SET name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = true,
    updated_at = NOW();

-- ---------------------------------------------------------------------------
-- 6/7. DEACTIVATE the two superseded drafts. Kept, not deleted: the rows are
--      the record of what was retired and why.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET is_active = false,
    updated_at = NOW()
WHERE id IN ('sahel_wagner_presence', 'sahel_french_withdrawal');

COMMIT;
