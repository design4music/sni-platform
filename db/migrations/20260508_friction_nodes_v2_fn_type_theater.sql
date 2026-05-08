-- Add fn_type discriminator + member_fn_ids to friction_nodes.
-- 2026-05-08
--
-- Single table holds both atomic friction nodes (the standard contested-
-- phenomenon entry we've been building) AND theaters (groupings of atomic
-- FNs sharing a common subject — e.g. the Iran theater = nuclear + proxy
-- + regime legitimacy + Hormuz + Gulf attacks all united by being "what
-- about Iran's X").
--
-- Per the user's schema preference (memory: feedback_db_schema_preferences):
-- prefer expanding existing tables to creating new ones; use a discriminator
-- field when content is semantically related but has variant-specific
-- fields. Atomic FNs and theaters share most fields (name, description,
-- editorial_summary, centroid_ids); they differ only in:
--
--   - atomic FNs use topic_keywords + event_*_markers/anchors for matching
--   - theaters use member_fn_ids for grouping (no matching needed —
--     theaters have no events of their own; their events are the union
--     of their atomic members')

BEGIN;

ALTER TABLE friction_nodes
    ADD COLUMN IF NOT EXISTS fn_type text NOT NULL DEFAULT 'atomic'
        CHECK (fn_type IN ('atomic', 'theater')),
    ADD COLUMN IF NOT EXISTS member_fn_ids text[];

CREATE INDEX IF NOT EXISTS idx_friction_nodes_fn_type ON friction_nodes (fn_type);
CREATE INDEX IF NOT EXISTS idx_friction_nodes_member_fn_ids
    ON friction_nodes USING gin (member_fn_ids);

COMMENT ON COLUMN friction_nodes.fn_type IS
    'atomic = single contested phenomenon (standard FN). theater = grouping of atomic FNs sharing a common subject.';
COMMENT ON COLUMN friction_nodes.member_fn_ids IS
    'For fn_type=theater: list of atomic friction_nodes.id values bundled in this theater. NULL for atomic FNs.';

COMMIT;
