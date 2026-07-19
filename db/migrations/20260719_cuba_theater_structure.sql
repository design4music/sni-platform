-- Cuba theater: greenfield structure (Phase 1 sign-off, 2026-07-19).
--
-- Grounded against 180d of real coverage: 2,340 titles carrying AMERICAS-CUBA
-- (Jan 20 -> Jul 19 2026), 1,463 of them co-tagging AMERICAS-USA. Theater was a
-- blank shell -- 0 fn_anchor bundles, 0 narratives_v2, 0 attributed events,
-- 0 asset evidence on all three draft atomics.
--
-- Centroid corpus verified clean: AMERICAS-CUBA aliases are Cuba/Havana/
-- La Habana + translations. The one rule-6b risk (ru 'Куба' c 'Кубань'/'Кубок')
-- is immaterial -- 69 ru titles in the whole 180d window.
--
-- Real-coverage theme map (§2a):
--   1. Fuel/oil blockade + shipping        395 / 174 kw  -> split across A + B
--   2. Energy + humanitarian collapse      223 / 123 kw  -> ADD (largest, unhomed)
--   3. Embargo/sanctions instruments       276 kw        -> KEEP, re-scoped
--   4. External patrons & lifelines        ~250 (RU 156 / MX 118 / VZ 63 / CN 44,
--      third-party diplomacy 142)                        -> ADD (unhomed)
--   5. US military coercion / regime change ~140 (Nimitz to the Caribbean,
--      SOUTHCOM-Cuban generals, Hegseth at Guantanamo 20, war-powers votes,
--      "Cuba is next" 58, infiltration/speedboat/drone incidents 103) -> ADD
--   6. Repression, prisoners, dissidents   71 kw         -> KEEP, re-scoped
--   7. Leadership indictments + GAESA/Moa  81 / 11 kw    -> folded into A
--   8. MIGRATION / EXODUS                  ~12-19 (0.8%) -> DEACTIVATE
--
-- WHY MIGRATION DIES. The draft encodes the 2021-24 rafter/parole wave; it is
-- gone from this corpus. The probe's apparent hits are two OTHER stories:
-- Guantanamo-as-military-flashpoint (-> E) and US-domestic ICE detention deaths
-- (a US immigration story, not a Cuba friction node).
--
-- WHY COLLAPSE IS SEPARATE FROM SANCTIONS. Folding the blackouts/hunger/hotel
-- closures into the embargo atomic would merge a policy INSTRUMENT with its
-- CONTESTED OUTCOME -- and whether the collapse is caused by the blockade or by
-- regime mismanagement is precisely the narrative war this theater is about.
-- Separated by vocabulary (designation/licence/executive order vs blackout/grid/
-- ration/hospital), not by exclusion logic. Overlap to be measured at §4.
--
-- WHY MILITARY COERCION IS SEPARATE FROM THE SANCTIONS CAMPAIGN. Economic-legal
-- instruments and kinetic threat are orthogonal phenomena with sharply different
-- narrative axes (legitimacy of economic pressure vs legality of armed force).
--
-- ARCHETYPE: A2, anchor == subject (spec §2). 'Cuba'/'Havana'/'La Habana' is a
-- near-perfect gate on a well-populated centroid (2,340 titles), so all five
-- atomics take centroid_ids={AMERICAS-CUBA} alone. AMERICAS-USA on the OR-gate
-- buys nothing and would admit US-only titles that merely name a Cuban.
-- primary_target=AMERICAS-CUBA is redundant at TITLE level here but is set
-- deliberately: per the south_asia lesson, only primary_target activates the
-- 50%-of-event-titles rule at EVENT level, which is what suppresses the A2
-- mega-cluster contamination artifact.
--
-- Patron centroids (RUSSIA/CHINA/MEXICO/VENEZUELA) are deliberately NOT added to
-- cuba_external_lifelines -- they go in only if the §4 audit shows a real
-- centroid gap (spec §4: diagnose the gap before touching aliases).
--
-- Theater fix: primary_target cleared. Theaters carry no bundle and never match,
-- so a target on the aggregator is inert and misleading. Atomics also unhomed
-- from the inactive latam_theater so nothing is dual-homed.
--
-- Ids of the two survivors are kept: both still describe their re-scoped
-- content, and renaming buys nothing on a node with zero references.
--
-- No DELETE; INSERT + UPDATE only. Reversible.

BEGIN;

-- ---------------------------------------------------------------------------
-- Theater: pure aggregator. No fn_anchor bundle, never matches, null target.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET name_en = 'Cuba under maximum pressure',
    name_de = 'Kuba unter Maximaldruck',
    centroid_ids = ARRAY['AMERICAS-CUBA','AMERICAS-USA'],
    primary_target = NULL,
    member_fn_ids = ARRAY[
        'cuba_embargo_sanctions',
        'cuba_energy_collapse',
        'cuba_external_lifelines',
        'cuba_military_coercion',
        'cuba_regime_survival'
    ],
    updated_at = NOW()
WHERE id = 'cuba_theater';

-- Un-home the atomics from the inactive latam_theater (stale dual-home).
UPDATE friction_nodes
SET member_fn_ids = ARRAY(
        SELECT unnest(member_fn_ids) EXCEPT SELECT unnest(ARRAY[
            'cuba_embargo_sanctions','cuba_migration_exodus','cuba_regime_survival'
        ])),
    updated_at = NOW()
WHERE id = 'latam_theater';

-- ---------------------------------------------------------------------------
-- A. KEEP, re-scoped -- the 2026 instrument set, not the historical embargo.
--    Oil-blockade executive order, secondary sanctions on shippers/hoteliers,
--    GAESA / Moa Nickel designations, Helms-Burton property claims,
--    indictments of the leadership.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET name_en = 'US sanctions and blockade instruments',
    name_de = 'US-Sanktions- und Blockadeinstrumente',
    centroid_ids = ARRAY['AMERICAS-CUBA'],
    primary_target = 'AMERICAS-CUBA',
    scope = 'regional',
    display_order = 102,
    is_active = true,
    updated_at = NOW()
WHERE id = 'cuba_embargo_sanctions';

-- ---------------------------------------------------------------------------
-- B. NEW -- Energy and humanitarian collapse (largest unhomed theme).
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope,
    centroid_ids, primary_target, display_order, is_active
) VALUES (
    'cuba_energy_collapse',
    'Energy and humanitarian collapse',
    'Energie- und humanitärer Zusammenbruch',
    'atomic', 'regional',
    ARRAY['AMERICAS-CUBA'], 'AMERICAS-CUBA', 105, true
) ON CONFLICT (id) DO UPDATE
SET name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = true,
    updated_at = NOW();

-- ---------------------------------------------------------------------------
-- C. NEW -- External lifelines and patron competition.
--    Russian/Venezuelan tankers, China's fuel offer, Pemex halting then
--    resuming crude under US pressure, Mexico/Spain/Brazil/Canada aid tracks.
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope,
    centroid_ids, primary_target, display_order, is_active
) VALUES (
    'cuba_external_lifelines',
    'External lifelines and patron competition',
    'Äußere Rettungsleinen und Patronenkonkurrenz',
    'atomic', 'regional',
    ARRAY['AMERICAS-CUBA'], 'AMERICAS-CUBA', 106, true
) ON CONFLICT (id) DO UPDATE
SET name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = true,
    updated_at = NOW();

-- ---------------------------------------------------------------------------
-- D. NEW -- US military coercion and regime-change threat.
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope,
    centroid_ids, primary_target, display_order, is_active
) VALUES (
    'cuba_military_coercion',
    'Military coercion and regime-change threat',
    'Militärische Nötigung und Drohung eines Regimewechsels',
    'atomic', 'regional',
    ARRAY['AMERICAS-CUBA'], 'AMERICAS-CUBA', 107, true
) ON CONFLICT (id) DO UPDATE
SET name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = true,
    updated_at = NOW();

-- ---------------------------------------------------------------------------
-- E. KEEP, re-scoped -- internal legitimacy and control ONLY. The kinetic
--    threat half of the old catch-all moves to D; the US legal-warfare half
--    (indictments, GAESA) moves to A.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET name_en = 'Regime legitimacy and internal control',
    name_de = 'Legitimität des Regimes und innere Kontrolle',
    centroid_ids = ARRAY['AMERICAS-CUBA'],
    primary_target = 'AMERICAS-CUBA',
    scope = 'regional',
    display_order = 104,
    is_active = true,
    updated_at = NOW()
WHERE id = 'cuba_regime_survival';

-- ---------------------------------------------------------------------------
-- F. DEACTIVATE -- Migration/exodus. ~12-19 titles/180d (0.8%): a 2021-24-era
--    draft. See header for what the probe was actually catching.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes
SET is_active = false,
    updated_at = NOW()
WHERE id = 'cuba_migration_exodus';

COMMIT;
