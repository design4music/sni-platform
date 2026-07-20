-- Horn of Africa theater: greenfield structure (Phase 1 sign-off, 2026-07-20).
--
-- Theater was a blank shell -- 0 fn_anchor bundles, 0 narratives_v2 on all four
-- draft atomics. Draft decomposition was training-data-aged (2023/24 vintage).
--
-- Grounded against 180d of real coverage: 622 titles carrying AFRICA-HORN, plus
-- a 697-title wide scope (AFRICA-HORN OR Horn proper nouns in title). All theme
-- counts below are from that scope, Jan 20 -> Jul 20 2026.
--
-- ---------------------------------------------------------------------------
-- CENTROID LAYER WAS MOSTLY DEAD REFS (the first thing found, §4 / Venezuela
-- lesson). AFRICA-HORN is the ONLY Horn centroid that exists and is populated:
--
--   AFRICA-HORN                          centroid_anchor row: YES   622 titles
--   AFRICA-ETHIOPIA                      centroid_anchor row: NO    129 (legacy)
--   AFRICA-SOMALIA / -ERITREA / -DJIBOUTI            NO              0
--   NON-STATE-AL-SHABAAB                             NO              0
--   NON-STATE-OROMIA-LIBERATION-FRONT                NO              0
--
-- All four draft atomics were gated on centroids that do not exist. AFRICA-HORN's
-- anchor already carries Ethiopia/Djibouti/Somalia/Eritrea/Addis/Mogadishu/
-- Asmara/Bab-el-Mandeb/Gulf of Aden, so it is the correct single participant gate.
--
-- Second centroid finding: 30% of Horn-name content (75/247 titles) sits OUTSIDE
-- AFRICA-HORN, dominated by MIDEAST-ISRAEL (52) -- the Somaliland recognition
-- story, i.e. the theater's single largest theme was leaking out of scope.
-- MIDEAST-ISRAEL is therefore added as a participant on that atomic only.
--
-- ---------------------------------------------------------------------------
-- Real-coverage theme map (§2a):
--   1. Somaliland recognition contest   118 titles (17% of corpus)     -> ADD
--      (Israeli recognition + first ambassador, Jerusalem embassy, Somaliland
--       president in the Knesset, US minerals-and-bases offers, UAE-built base
--       at Berbera, AU "null and void", Erdogan/Egypt/Saudi/Iran/12-state
--       condemnations, Somalia vowing to block an Israeli base)
--   2. Ethiopia vs its neighbours        ~90 titles                    -> RE-SCOPE
--      (Tigray 36 + Eritrea 37 + Egypt encirclement 21 + sea access 7)
--   3. Somali state security             ~73 titles                    -> RE-SCOPE
--      (al-Shabaab 22 + piracy 23 + Mogadishu crisis 9 + Turkey patronage 30
--       + US blocking UN support for the AU mission)
--   4. Amhara / Oromo insurgency          0 titles                     -> RETIRE
--   5. Ethiopia-Somaliland port MoU       0 titles                     -> RETIRE
--
-- ---------------------------------------------------------------------------
-- WHY TWO ATOMICS ARE RETIRED, NOT RE-TUNED.
--
-- ethiopia_amhara_conflict: `Amhara` = 0 titles system-wide/180d. `Oromo`/
-- `Oromia` = 1 (an AFP fact-check). `Fano` = 1 real out of 26 matches -- the
-- other 25 are pure rule-6b substring garbage (Stefano, Fanone, Troufanov,
-- orfano, Stefanovic). Empty AND a collision minefield.
--
-- ethiopia_somaliland_access: titles carrying `Somaliland` AND Ethiopia/Abiy = 0.
-- The entire Ethiopian sea-access theme is 7 titles and its live axis has moved
-- to ERITREA/Assab ("Abiy's vision of Ethiopia includes a seaport in Eritrea"),
-- not Somaliland. The 2024 MoU premise is gone from the feed. The 7 surviving
-- titles are absorbed by ethiopia_regional_confrontation, where they belong.
--
-- ---------------------------------------------------------------------------
-- WHY ONLY THREE ATOMICS (generous slices, per sign-off).
--
-- Two further candidates were measured and deliberately FOLDED rather than cut
-- as their own atomics, to avoid micro-fragmentation on a mid-volume theater
-- with no superpower as a direct principal:
--
--   * Somali piracy resurgence (23 titles: UKMTO, Garacad, hijacked tanker,
--     "Pirates on the prowl again") -> folded into somalia_state_security.
--     Piracy, al-Shabaab, the AU mission and the Mogadishu election crisis are
--     one phenomenon: Somali state capacity and control of its own coast.
--
--   * Egypt-Ethiopia rivalry (21-39 titles: Egypt-Eritrea maritime deal,
--     Sisi-Afwerki in Cairo, Egypt-Djibouti and Egypt-Somalia coordination,
--     "Egypt seeks to isolate Ethiopia", "rejects parallel entities in the Horn
--     of Africa") -> folded into ethiopia_regional_confrontation. Egypt's
--     courtship of Eritrea/Somalia/Djibouti IS the encirclement that drives the
--     Eritrea war risk; Eritrea is the hinge actor in both. Note GERD/Nile is
--     nearly ABSENT from 2026 coverage (3 hits) -- the rivalry has moved off
--     water and onto alignment, which is why no water atomic is proposed.
--
-- ethiopia_political_order (Abiy's 90%-of-seats win, boycotts, locked-out
-- regions, "throttling free expression", 24 titles) was also considered and
-- dropped as an atomic: it is closer to domestic-politics coverage than a
-- friction node. Its Tigray-exclusion strand is already inside atomic B.
--
-- ---------------------------------------------------------------------------
-- ARCHETYPES.
--   A. somaliland_recognition_contest   -- §2 A2, anchor == subject. `Somaliland`
--      is a near-perfect toponym gate (118 titles, ~100% on-topic). Null target,
--      widened participants (AFRICA-HORN + MIDEAST-ISRAEL) per A2: a title cannot
--      carry the name without being on-topic, so wider scope only helps recall.
--      CAVEAT for step 3: the EN matcher is word-START, so `Somali` would swallow
--      every Somaliland title. Atomic C must NOT carry a bare `Somali` alias.
--   B/C. multilateral -- null primary_target. There is no single subject centroid
--      to target (AFRICA-ETHIOPIA/-SOMALIA do not exist), and the phenomena act
--      in several directions, so alias purity is the only lever (§2 Archetype B).
--
-- ---------------------------------------------------------------------------
-- Theater keeps affected_asset_ids {bab_el_mandeb, gerd_dam} and its anchor_point
-- so the homepage conflicts map is unaffected.
--
-- No DELETE; INSERT + UPDATE only. Reversible.

BEGIN;

-- ---------------------------------------------------------------------------
-- Theater: aggregator only. No fn_anchor bundle, never matches, null target.
-- centroid_ids reduced to the one live centroid + the two external principals
-- that actually carry Horn coverage (Israel via Somaliland, Turkey via Somalia).
-- Dropped: AFRICA-ETHIOPIA, AFRICA-ERITREA, AFRICA-SOMALIA, AFRICA-KENYA,
-- AFRICA-DJIBOUTI (all dead or near-dead refs).
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET name_en = 'Horn of Africa realignment',
    name_de = 'Neuordnung am Horn von Afrika',
    centroid_ids = ARRAY[
        'AFRICA-HORN',
        'MIDEAST-ISRAEL',
        'MIDEAST-EGYPT',
        'MIDEAST-TURKEY',
        'AMERICAS-USA'
    ],
    primary_target = NULL,
    member_fn_ids = ARRAY[
        'somaliland_recognition_contest',
        'ethiopia_regional_confrontation',
        'somalia_state_security'
    ],
    updated_at = NOW()
WHERE id = 'horn_africa_theater';

-- ---------------------------------------------------------------------------
-- A. NEW -- Somaliland recognition contest. The theater's dominant theme
--    (118 titles/180d) and, before this migration, homed nowhere in the system.
--    §2 A2: anchor == subject, null target, wide participants.
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope,
    centroid_ids, primary_target, display_order, is_active
) VALUES (
    'somaliland_recognition_contest',
    'Somaliland recognition contest',
    'Der Streit um die Anerkennung Somalilands',
    'atomic', 'regional',
    ARRAY['AFRICA-HORN','MIDEAST-ISRAEL','AMERICAS-USA','MIDEAST-EGYPT','MIDEAST-TURKEY'],
    NULL, 74, true
) ON CONFLICT (id) DO UPDATE
SET name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = true,
    updated_at = NOW();

-- ---------------------------------------------------------------------------
-- B. RE-SCOPE of ethiopia_tigray_aftermath.
--    Old scope ("aftermath and war crimes accountability") is a finished phase.
--    2026 corpus is renewed-war RISK plus interstate encirclement: TPLF
--    restoring the pre-war administration, drone strikes in Tigray, Ethiopia
--    demanding Eritrean troop withdrawal, Eritrea calling the claims
--    "fabricated", "Ethiopia and Eritrea are on the brink of war again", Tigray
--    excluded from the June election, Abiy "at the war front", Egypt-Eritrea
--    maritime deal, Abiy's Assab seaport ambition.
--    Absorbs the 7 surviving sea-access titles from the retired access atomic.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET id = 'ethiopia_regional_confrontation',
    name_en = 'Ethiopia''s confrontation with its neighbours',
    name_de = 'Äthiopiens Konfrontation mit seinen Nachbarn',
    centroid_ids = ARRAY['AFRICA-HORN','MIDEAST-EGYPT'],
    primary_target = NULL,
    display_order = 75,
    is_active = true,
    updated_at = NOW()
WHERE id = 'ethiopia_tigray_aftermath';

-- ---------------------------------------------------------------------------
-- C. RE-SCOPE of somalia_al_shabaab -- broadened from insurgency-only to the
--    Somali state-capacity file. al-Shabaab alone is 22 titles/180d: too thin
--    to stand as its own atomic. Broadened it carries ~73: al-Shabaab and US
--    airstrikes, the AU mission funding crisis (US blocking UN support), the
--    Mogadishu clashes over the election delay, the piracy resurgence off
--    Garacad, and Turkey's patronage (spaceport, offshore drilling, mediation).
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET id = 'somalia_state_security',
    name_en = 'Somali state security and coastal control',
    name_de = 'Somalias Staatssicherheit und Kontrolle der Küste',
    centroid_ids = ARRAY['AFRICA-HORN','MIDEAST-TURKEY','AMERICAS-USA'],
    primary_target = NULL,
    display_order = 76,
    is_active = true,
    updated_at = NOW()
WHERE id = 'somalia_al_shabaab';

-- ---------------------------------------------------------------------------
-- D. RETIRE -- Amhara insurgency. 0 titles system-wide/180d.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET is_active = false,
    updated_at = NOW()
WHERE id = 'ethiopia_amhara_conflict';

-- ---------------------------------------------------------------------------
-- E. RETIRE -- Ethiopian sea access via Somaliland. 0 titles carry both.
--    Live sea-access axis moved to Eritrea; absorbed by atomic B.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET is_active = false,
    updated_at = NOW()
WHERE id = 'ethiopia_somaliland_access';

COMMIT;
