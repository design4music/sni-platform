-- Move EU diplomatic + multipolar (cross-cluster stand-by narratives) from
-- the 5 atomic Iran FNs onto iran_theater. Path A semantics: the theater is
-- the home of cross-cluster narratives; atomic FNs host only the FN-specific
-- coalitions.
-- 2026-05-11

BEGIN;

-- Remove old per-FN links for these two stand-by narratives
DELETE FROM friction_node_narratives
WHERE narrative_id IN (
    'eu_diplomatic_preservation_norm',
    'multipolar_systemic_alternative'
)
AND fn_id IN (
    'iran_nuclear_program',
    'iran_proxy_network',
    'iran_regime_legitimacy_contest',
    'strait_of_hormuz_sovereignty',
    'gulf_attacks_on_arab_states'
);

-- Add theater-level links with canonical stance labels
INSERT INTO friction_node_narratives (fn_id, narrative_id, stance_label_en, stance_label_de, display_order)
VALUES
    ('iran_theater', 'eu_diplomatic_preservation_norm', 'Preserve diplomacy', 'Diplomatie bewahren', 1),
    ('iran_theater', 'multipolar_systemic_alternative', 'Anti-imperial alternative', 'Anti-imperiale Alternative', 2);

COMMIT;
