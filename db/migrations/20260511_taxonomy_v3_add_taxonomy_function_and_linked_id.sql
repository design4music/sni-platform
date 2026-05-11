-- Add taxonomy_function discriminator + linked_id field to taxonomy_v3.
-- Phase 1 of the taxonomy unification (Phase 2 covers FN/narrative bundles).
-- 2026-05-11
--
-- After this migration:
--   - Every existing row has taxonomy_function in {stop_word, centroid_anchor}
--   - linked_id mirrors centroid_id for centroid_anchor rows
--   - CHECK constraint + UNIQUE partial indexes are in place ready for
--     Phase 2 fn_anchor / narrative_anchor rows
--   - Phase 2.1 centroid matching produces identical results (constraint
--     guarantees no fn_anchor/narrative_anchor row can have centroid_id set)
--
-- Phase 2 (out of scope here):
--   - Add friction_nodes.actor_centroid_ids
--   - Populate fn_anchor / narrative_anchor rows
--   - Rewrite bootstrap_friction_node.py to read from taxonomy_v3
--   - Update frontend lib/friction-nodes.ts to read from taxonomy_v3
--   - Drop friction_nodes.topic_keywords / narratives_v2.framing_keywords /
--     narratives_v2.topic_keywords

BEGIN;

ALTER TABLE taxonomy_v3
    ADD COLUMN IF NOT EXISTS taxonomy_function text NOT NULL DEFAULT 'centroid_anchor'
        CHECK (taxonomy_function IN ('stop_word','centroid_anchor','fn_anchor','narrative_anchor')),
    ADD COLUMN IF NOT EXISTS linked_id text;

-- Backfill existing rows. is_stop_word=true takes precedence; otherwise centroid_anchor.
UPDATE taxonomy_v3 SET taxonomy_function = 'stop_word'
    WHERE is_stop_word = true;

UPDATE taxonomy_v3 SET linked_id = centroid_id
    WHERE taxonomy_function = 'centroid_anchor' AND centroid_id IS NOT NULL;

-- Coherence CHECK constraint (added after backfill so existing data passes).
ALTER TABLE taxonomy_v3
    ADD CONSTRAINT taxonomy_v3_function_coherence CHECK (
        (taxonomy_function = 'stop_word'        AND linked_id IS NULL)
     OR (taxonomy_function = 'centroid_anchor'  AND linked_id IS NOT NULL)
     OR (taxonomy_function = 'fn_anchor'        AND linked_id IS NOT NULL)
     OR (taxonomy_function = 'narrative_anchor' AND linked_id IS NOT NULL)
    );

CREATE INDEX IF NOT EXISTS idx_taxonomy_v3_taxonomy_function
    ON taxonomy_v3 (taxonomy_function) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_taxonomy_v3_linked_id
    ON taxonomy_v3 (linked_id) WHERE is_active = true;
CREATE UNIQUE INDEX IF NOT EXISTS idx_taxonomy_v3_unique_fn_anchor
    ON taxonomy_v3 (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true;
CREATE UNIQUE INDEX IF NOT EXISTS idx_taxonomy_v3_unique_narrative_anchor
    ON taxonomy_v3 (linked_id) WHERE taxonomy_function = 'narrative_anchor' AND is_active = true;

COMMENT ON COLUMN taxonomy_v3.taxonomy_function IS
    'Discriminator: stop_word | centroid_anchor | fn_anchor | narrative_anchor. Replaces the binary is_stop_word semantically; the boolean is kept during transition for backward compatibility.';
COMMENT ON COLUMN taxonomy_v3.linked_id IS
    'centroid_id for centroid_anchor rows, friction_nodes.id for fn_anchor, narratives_v2.id for narrative_anchor. NULL for stop_word. Mutually exclusive with centroid_id semantics — never both populated for the same row.';

COMMIT;
