-- Retire narratives_v2.notes_en/de (never populated, no consumer) and
-- narratives_v2.scope_centroid_ids (override pattern is a smell under the
-- 1-to-1 FN<->narrative model: if a narrative needs a different scope, the
-- FN's own scope should be adjusted instead).
--
-- Pre-step: promote the per-narrative scope override on iran_theater to
-- the FN itself. Both ex-stand-by narratives (eu_diplomatic_preservation_norm
-- and multipolar_systemic_alternative) override iran_theater.centroid_ids
-- ({MIDEAST-IRAN, AMERICAS-USA, MIDEAST-ISRAEL}) to a 10-centroid set.
-- Widen the FN scope to that union so the 4 narratives share one rule.

BEGIN;

UPDATE friction_nodes SET
    centroid_ids = ARRAY[
        'MIDEAST-IRAN','AMERICAS-USA','MIDEAST-ISRAEL',
        'MIDEAST-SAUDI','MIDEAST-LEVANT','MIDEAST-PALESTINE',
        'MIDEAST-YEMEN','MIDEAST-IRAQ','EUROPE-UK','EUROPE-FRANCE'
    ]
WHERE id = 'iran_theater';

ALTER TABLE narratives_v2 DROP COLUMN IF EXISTS scope_centroid_ids;
ALTER TABLE narratives_v2 DROP COLUMN IF EXISTS notes_en;
ALTER TABLE narratives_v2 DROP COLUMN IF EXISTS notes_de;

COMMIT;
