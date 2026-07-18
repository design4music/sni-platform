-- Myanmar theater: greenfield structural re-carve (FN_THEATER_BUILD_SPEC 2a).
--
-- Draft atomics came from stale training data. Grounded against 470 titles /
-- 180d of real 2026 coverage:
--   * myanmar_ethnic_conflicts  -> ZERO corpus (Arakan Army 1, TNLA 0, MNDAA 0,
--     Kachin 0, Rakhine 0, Sagaing 0, Kokang 0). `Karen`/`KNU` are pure
--     collisions (Karen Bass, Knud Brix, knutpunkt). Deactivate.
--   * myanmar_china_influence   -> not an atomic: distinct core is 19 titles and
--     overlaps legitimation. China is the VALIDATOR in that story, not a
--     separate friction. Becomes a narrative on regime legitimation. Deactivate.
--   * myanmar_military_rule     -> half-stale. Resistance vocab dead (NUG 1,
--     PDF 2, Tatmadaw 1); the regime half is the dominant story but has changed
--     shape: legitimation via sham election, not "rule". Re-scope + rename.
--     Regime violence (55 titles) folds in here as counter-evidence to
--     legitimacy rather than standing as its own atomic.
--   * myanmar_transnational_crime -> NEW. 46 titles, orthogonal (overlap with
--     legitimation = 1 title, with violence = 2). Scam compounds, trafficking,
--     Chinese executions, US indictments.
--
-- Centroid fix: ASIA-SOUTHEAST has no centroid_anchor row at all; ASIA-SOUTHASIA's
-- anchor holds the ASEAN vocabulary, so 468/470 Myanmar titles tag ASIA-SOUTHASIA
-- and only 157 tag ASIA-SOUTHEAST. Gating on ASIA-SOUTHEAST alone loses 67% of the
-- corpus. Both atomics are Archetype A2 (the name `Myanmar` is ~95% on-topic), so
-- centroid_ids widen freely and primary_target stays null -- the name is the gate.
-- ASIA-SOUTHEAST stays first: getAllFrictionNodesByRegion reads centroid_ids[0].
--
-- Rare-earth corridor deliberately NOT built: `rare earth` appears in 313 titles
-- corpus-wide but only 3 that mention Myanmar. It has not earned coverage.

BEGIN;

-- 1. Re-scope + rename the surviving atomic. FK update rule is NO ACTION, but
--    this id has zero referencing rows in narratives_v2 / event_friction_nodes /
--    fn_asset_evidence, so the rename cannot orphan anything.
UPDATE friction_nodes
SET id           = 'myanmar_regime_legitimation',
    name_en      = 'Military regime legitimation and international recognition',
    centroid_ids = ARRAY['ASIA-SOUTHEAST', 'ASIA-SOUTHASIA', 'ASIA-CHINA'],
    primary_target = NULL,
    is_active    = TRUE,
    updated_at   = now()
WHERE id = 'myanmar_military_rule';

-- 2. New atomic: the transnational criminal economy.
INSERT INTO friction_nodes (
    id, name_en, fn_type, scope, centroid_ids, primary_target,
    affected_asset_ids, is_active, display_order, created_at, updated_at
) VALUES (
    'myanmar_transnational_crime',
    'Scam compounds and the transnational criminal economy',
    'atomic', 'regional',
    ARRAY['ASIA-SOUTHEAST', 'ASIA-SOUTHASIA', 'ASIA-CHINA'],
    NULL,
    ARRAY[]::text[],
    TRUE, 2, now(), now()
)
ON CONFLICT (id) DO UPDATE SET
    name_en      = EXCLUDED.name_en,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active    = TRUE,
    updated_at   = now();

UPDATE friction_nodes SET display_order = 1, updated_at = now()
WHERE id = 'myanmar_regime_legitimation';

-- 3. Deactivate the two atomics the corpus does not support. Deactivate, never
--    DELETE: every FK to friction_nodes is ON DELETE CASCADE (2026-07-07 incident).
UPDATE friction_nodes
SET is_active = FALSE, updated_at = now()
WHERE id IN ('myanmar_ethnic_conflicts', 'myanmar_china_influence');

-- 4. Theater aggregates only the two live atomics; widen its centroids to match.
UPDATE friction_nodes
SET member_fn_ids = ARRAY['myanmar_regime_legitimation', 'myanmar_transnational_crime'],
    centroid_ids  = ARRAY['ASIA-SOUTHEAST', 'ASIA-SOUTHASIA', 'ASIA-CHINA'],
    name_en       = 'Myanmar: military rule, legitimation and criminal economy',
    primary_target = NULL,
    updated_at    = now()
WHERE id = 'myanmar_theater';

COMMIT;
