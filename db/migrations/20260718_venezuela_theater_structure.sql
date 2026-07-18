-- Venezuela theater: greenfield structural fixes (Phase 1 sign-off, 2026-07-18).
--
-- Grounded against 180d of real coverage (3,445 titles on AMERICAS-VENEZUELA,
-- Jan 18 -> Jul 7 2026). Scenario: US Jan-2026 operation captured Maduro; VP
-- Delcy Rodriguez runs a US-blessed interim government; sanctions easing drove
-- an oil-major restart (Exxon/Chevron/Eni, 7-yr-high exports); opposition
-- (Machado) frozen out; 51st-state annexation rhetoric; recurring drug-boat /
-- Tren de Aragua strikes; Essequibo ICJ hearings; then a late-June earthquake
-- (3,535 dead) now dominates recent coverage.
--
-- Structure sign-off (four atomics kept, re-scoped):
--   A venezuela_sanctions_oil       -> "Oil restart & economic opening"
--   B venezuela_political_transition -> keep (3-stance own-goal topic)
--   C us_venezuela_relations         -> "US coercion & military action"
--                                       (absorbs drug-boat / Tren de Aragua strikes)
--   D essequibo_dispute              -> keep, thin A2 toponym atomic
-- Earthquake aid-competition -> theater-level narrative card only (no atomic).
--
-- CRITICAL centroid fix: AMERICAS-COLOMBIA and AMERICAS-GUYANA DO NOT EXIST as
-- centroids (0 titles system-wide). Colombia folds into AMERICAS-ANDEAN; Guyana
-- splits ANDEAN(25)/CARIBBEAN(8)/VENEZUELA(16). Every reference to the two dead
-- centroids silently collapsed gating to VEN(+USA). Drop them; Essequibo gates
-- on the toponym (A2) + VEN + ANDEAN + CARIBBEAN.
--
-- Archetype: single-subject theater (like iran_/cuba_/turkey_theater). All
-- atomics target-centric on Venezuela -> primary_target=AMERICAS-VENEZUELA
-- (makes generic domain verbs safe), except Essequibo (A2, null target).
-- Theater carries no bundle and never matches -> primary_target=null.
--
-- No DELETE; UPDATEs only. Reversible.

BEGIN;

-- A/B/C target-centric on Venezuela. centroid_ids = {VEN} ONLY: with
-- primary_target=VEN the participant gate already requires VEN, so USA in the
-- set is inert for attribution but massively inflates the alias auditor (USA is
-- 126k titles -> shows Iran/Gulf oil "leak" that primary_target actually
-- filters). Dropping USA makes the audit meaningful and attribution identical.

-- A. Oil restart & economic opening
UPDATE friction_nodes
SET name_en = 'Oil restart and economic opening',
    name_de = 'Wiederanlauf der Ölförderung und wirtschaftliche Öffnung',
    centroid_ids = ARRAY['AMERICAS-VENEZUELA'],
    primary_target = 'AMERICAS-VENEZUELA',
    updated_at = NOW()
WHERE id = 'venezuela_sanctions_oil';

-- B. Post-intervention political transition (drop dead COLOMBIA + marginal
--    BRAZIL -- VEN gate already carries everything)
UPDATE friction_nodes
SET centroid_ids = ARRAY['AMERICAS-VENEZUELA'],
    primary_target = 'AMERICAS-VENEZUELA',
    updated_at = NOW()
WHERE id = 'venezuela_political_transition';

-- C. US coercion & military action (capture aftermath, annexation rhetoric,
--    drug-boat / Tren de Aragua strikes; bare troops/deploy/warship kept OUT of
--    the bundle so June earthquake-relief coverage does not bleed in)
UPDATE friction_nodes
SET name_en = 'US coercion and military action',
    name_de = 'US-Zwangsmaßnahmen und Militäraktionen',
    centroid_ids = ARRAY['AMERICAS-VENEZUELA'],
    primary_target = 'AMERICAS-VENEZUELA',
    updated_at = NOW()
WHERE id = 'us_venezuela_relations';

-- D. Essequibo territorial dispute (A2 toponym gate; drop dead GUYANA, gate on
--    the centroids where Guyana coverage actually lands)
UPDATE friction_nodes
SET centroid_ids = ARRAY['AMERICAS-VENEZUELA','AMERICAS-ANDEAN','AMERICAS-CARIBBEAN'],
    primary_target = NULL,
    updated_at = NOW()
WHERE id = 'essequibo_dispute';

-- Theater: aggregator only. Keep VEN first (drives map region); drop dead
-- COLOMBIA/GUYANA; keep ANDEAN (Colombia/Guyana context) + BRAZIL (region).
-- Null the primary_target -- theaters never participate in matching.
UPDATE friction_nodes
SET centroid_ids = ARRAY['AMERICAS-VENEZUELA','AMERICAS-USA','AMERICAS-ANDEAN','AMERICAS-BRAZIL'],
    primary_target = NULL,
    updated_at = NOW()
WHERE id = 'venezuela_theater';

COMMIT;
