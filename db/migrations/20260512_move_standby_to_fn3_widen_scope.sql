-- Move EU diplomatic + multipolar stand-by narratives from iran_theater to
-- iran_regime_legitimacy_contest (FN3), widen FN3's centroid scope to
-- theater-wide, narrow iran_theater's centroid scope to its primary region.
-- 2026-05-12.
--
-- Architectural revision: theater is a region summary, not a narrative host.
-- FN3 is the "core" friction node of the Iran cluster — the regime/sovereignty
-- contest that all other contested phenomena orbit. Stand-by narratives
-- (EU diplomatic preservation + multipolar alternative) attach to FN3.
-- Theater scope is manually curated; for Iran cluster it starts at MIDEAST-IRAN
-- (the heart of the theater) and can expand if editorial judgment changes.

BEGIN;

-- Remove stand-by-on-theater links (the 2026-05-11 placement)
DELETE FROM friction_node_narratives
WHERE fn_id = 'iran_theater'
  AND narrative_id IN (
      'eu_diplomatic_preservation_norm',
      'multipolar_systemic_alternative'
  );

-- Attach stand-bys to FN3 with FN3-context stance labels
INSERT INTO friction_node_narratives
    (fn_id, narrative_id, stance_label_en, stance_label_de, display_order)
VALUES
    ('iran_regime_legitimacy_contest',
     'eu_diplomatic_preservation_norm',
     'Engage and criticise',
     'Engagieren und kritisieren',
     3),
    ('iran_regime_legitimacy_contest',
     'multipolar_systemic_alternative',
     'Sovereignty principle',
     'Souveraenitaetsprinzip',
     4);

-- Widen FN3's actor scope to theater-wide. Regime/sovereignty discourse
-- genuinely spans the war: strikes on Iran, retaliation against US/Israel,
-- proxy operations from Lebanon/Palestine/Yemen/Iraq, naval theater UK/France.
UPDATE friction_nodes
SET centroid_ids = ARRAY[
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
WHERE id = 'iran_regime_legitimacy_contest';

-- Narrow iran_theater to its primary region (the heart of the action).
-- Manual curation: editorial judgment, not derived. Adjustable later.
UPDATE friction_nodes
SET centroid_ids = ARRAY['MIDEAST-IRAN']
WHERE id = 'iran_theater';

COMMIT;
