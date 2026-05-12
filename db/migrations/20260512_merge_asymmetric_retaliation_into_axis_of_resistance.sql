-- Merge iran_asymmetric_retaliation_doctrine into iran_axis_of_resistance.
-- Justification: same 9 publishers, 100% title overlap (47/47), both all_in
-- with the same Iran/Yemen coalition. Conceptual difference (movement vs
-- doctrine) was real but irrelevant for attribution.
-- 2026-05-12.

BEGIN;

-- Merge asymmetric's framing keywords into axis (union, deduped). Keep the
-- doctrinal-tactical vocabulary as additional rhetorical fingerprints in
-- iran_axis_of_resistance.
UPDATE narratives_v2 a
SET framing_keywords = (
    SELECT array_agg(DISTINCT kw ORDER BY kw)
    FROM unnest(a.framing_keywords || ARRAY[
        'legitimate retaliation', 'legitimate response',
        'asymmetric retaliation', 'asymmetric response',
        'asymmetric warfare', 'asymmetric deterrence',
        'proportionate response', 'proportionate to aggression',
        'complicit Gulf states', 'complicit states', 'host states',
        'launch points', 'staging ground',
        'US base as legitimate target', 'US bases are targets',
        'response to aggression', 'eye for an eye',
        'Yemeni resistance', 'Houthi solidarity', 'Palestine solidarity',
        'punishing Saudi participation',
        'imposing costs', 'cost imposition',
        'cannot match conventional', 'asymmetric calculus',
        'higher cost', 'will be answered'
    ]) AS kw
)
WHERE a.id = 'iran_axis_of_resistance';

-- Drop friction_node_narratives link
DELETE FROM friction_node_narratives
WHERE narrative_id = 'iran_asymmetric_retaliation_doctrine';

-- Drop title_narratives rows
DELETE FROM title_narratives
WHERE narrative_id = 'iran_asymmetric_retaliation_doctrine';

-- Drop the narrative row itself
DELETE FROM narratives_v2
WHERE id = 'iran_asymmetric_retaliation_doctrine';

COMMIT;
