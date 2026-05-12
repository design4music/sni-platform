-- Add per-(FN, narrative) link scope override.
-- 2026-05-12.
--
-- friction_node_narratives.scope_centroid_ids holds an explicit centroid scope
-- for this particular link. When NULL, attribution falls back to the FN's
-- centroid_ids (friction_nodes.centroid_ids). When set, this overrides.
--
-- Use case: FN3 (iran_regime_legitimacy_contest) hosts both regime-specific
-- all-in narratives (which want narrow Iran-core scope) AND cross-cluster
-- stand-by narratives (EU diplomatic, multipolar) which want broad theater
-- scope. Without per-link override, both would inherit the same FN scope.
--
-- Companion migration: narrow FN3.centroid_ids back to the regime-core actor
-- set [Iran, USA, Israel]. Stand-bys get explicit theater-wide override.

BEGIN;

ALTER TABLE friction_node_narratives
    ADD COLUMN IF NOT EXISTS scope_centroid_ids TEXT[];

COMMENT ON COLUMN friction_node_narratives.scope_centroid_ids IS
    'Centroid scope override for this (fn, narrative) link. NULL = inherit from friction_nodes.centroid_ids. Used for stand-by narratives that need a broader scope than the host FN.';

-- Narrow FN3 scope back to its regime-core actors. All-in narratives on FN3
-- inherit this narrow scope; stand-bys override below.
UPDATE friction_nodes
SET centroid_ids = ARRAY[
    'MIDEAST-IRAN',
    'AMERICAS-USA',
    'MIDEAST-ISRAEL'
]
WHERE id = 'iran_regime_legitimacy_contest';

-- Stand-bys on FN3: explicit theater-wide scope (the full 10-centroid Iran
-- cluster). EU diplomatic + multipolar care about every front of the war.
UPDATE friction_node_narratives
SET scope_centroid_ids = ARRAY[
    'MIDEAST-IRAN',
    'AMERICAS-USA',
    'MIDEAST-ISRAEL',
    'MIDEAST-SAUDI',
    'MIDEAST-LEVANT',
    'MIDEAST-PALESTINE',
    'MIDEAST-YEMEN',
    'MIDEAST-IRAQ',
    'EUROPE-UK',
    'EUROPE-FRANCE'
]
WHERE fn_id = 'iran_regime_legitimacy_contest'
  AND narrative_id IN (
      'eu_diplomatic_preservation_norm',
      'multipolar_systemic_alternative'
  );

COMMIT;
