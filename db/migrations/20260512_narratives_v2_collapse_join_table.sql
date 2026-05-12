-- Collapse friction_node_narratives join table into narratives_v2.
-- Architectural decision (2026-05-12): narratives are 1-to-1 with FNs.
-- The strategic-narrative library is retired; each narrative is FN-specific.
-- Meta narratives may resurface later as a parent layer.
--
-- This migration:
--   1. Adds fn_id, display_order, stance_label_*, notes_*, scope_centroid_ids
--      to narratives_v2 (formerly on friction_node_narratives).
--   2. Splits iran_axis_of_resistance (currently linked to BOTH
--      gulf_attacks_on_arab_states and iran_proxy_network) into two
--      distinct narratives so the 1-to-1 invariant holds.
--   3. Drops gulf_regional_de_escalation (orphan, zero attributions, no FN).
--   4. Drops deprecated columns: tier, narrative_type, topic_keywords,
--      editorial_organ_publishers.
--   5. Drops the join table.

BEGIN;

ALTER TABLE narratives_v2 ADD COLUMN IF NOT EXISTS fn_id              text;
ALTER TABLE narratives_v2 ADD COLUMN IF NOT EXISTS display_order      int DEFAULT 0;
ALTER TABLE narratives_v2 ADD COLUMN IF NOT EXISTS stance_label_en    text;
ALTER TABLE narratives_v2 ADD COLUMN IF NOT EXISTS stance_label_de    text;
ALTER TABLE narratives_v2 ADD COLUMN IF NOT EXISTS notes_en           text;
ALTER TABLE narratives_v2 ADD COLUMN IF NOT EXISTS notes_de           text;
ALTER TABLE narratives_v2 ADD COLUMN IF NOT EXISTS scope_centroid_ids text[];

-- Split iran_axis_of_resistance BEFORE backfill so the new narrative
-- carries the gulf attachment and the original carries proxy.
INSERT INTO narratives_v2 (
    id, name_en, name_de, claim_en, claim_de,
    actor_centroids, stance, framing_keywords, publishers,
    is_active
)
SELECT 'iran_gulf_resistance_solidarity',
       name_en, name_de, claim_en, claim_de,
       actor_centroids, stance, framing_keywords, publishers,
       true
FROM narratives_v2
WHERE id = 'iran_axis_of_resistance';

-- Backfill from the join table. For iran_axis_of_resistance keep only
-- the iran_proxy_network row; the gulf row is satisfied by the new
-- iran_gulf_resistance_solidarity narrative below.
UPDATE narratives_v2 n
SET fn_id              = fnn.fn_id,
    display_order      = fnn.display_order,
    stance_label_en    = fnn.stance_label_en,
    stance_label_de    = fnn.stance_label_de,
    notes_en           = fnn.notes_en,
    notes_de           = fnn.notes_de,
    scope_centroid_ids = fnn.scope_centroid_ids
FROM friction_node_narratives fnn
WHERE fnn.narrative_id = n.id
  AND NOT (n.id = 'iran_axis_of_resistance' AND fnn.fn_id = 'gulf_attacks_on_arab_states');

UPDATE narratives_v2
SET fn_id              = 'gulf_attacks_on_arab_states',
    display_order      = 3,
    stance_label_en    = 'Resistance solidarity'
WHERE id = 'iran_gulf_resistance_solidarity';

-- Drop orphan (no FN link, no title attributions).
DELETE FROM narratives_v2 WHERE id = 'gulf_regional_de_escalation';

-- Sanity: every active narrative must now have fn_id + stance_label_en + display_order.
-- (Will raise a constraint violation here if any narrative was missed.)
ALTER TABLE narratives_v2 ALTER COLUMN fn_id           SET NOT NULL;
ALTER TABLE narratives_v2 ALTER COLUMN display_order   SET NOT NULL;
ALTER TABLE narratives_v2 ALTER COLUMN stance_label_en SET NOT NULL;

ALTER TABLE narratives_v2 ADD CONSTRAINT narratives_v2_fn_id_fkey
    FOREIGN KEY (fn_id) REFERENCES friction_nodes(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_narratives_v2_fn_id
    ON narratives_v2 (fn_id, display_order);

-- Deprecated columns — see decision note above.
ALTER TABLE narratives_v2 DROP COLUMN IF EXISTS tier;
ALTER TABLE narratives_v2 DROP COLUMN IF EXISTS narrative_type;
ALTER TABLE narratives_v2 DROP COLUMN IF EXISTS topic_keywords;
ALTER TABLE narratives_v2 DROP COLUMN IF EXISTS editorial_organ_publishers;

DROP TABLE friction_node_narratives;

COMMENT ON COLUMN narratives_v2.fn_id IS
    '1-to-1 link to friction_nodes.id (replaces the friction_node_narratives join).';
COMMENT ON COLUMN narratives_v2.scope_centroid_ids IS
    'Optional override of the FN attribution scope. NULL = inherit parent FN.centroid_ids.';

COMMIT;
