-- Drop event_actor_markers, event_topic_markers, event_title_anchors from
-- friction_nodes. Replaced by fn_anchor bundle (taxonomy_v3) + centroid scope
-- (friction_nodes.centroid_ids). Bootstrap's link_events now reads the unified
-- attribution gate instead of the (actor AND topic) OR anchor pattern.
-- 2026-05-12.

BEGIN;

ALTER TABLE friction_nodes
    DROP COLUMN IF EXISTS event_actor_markers,
    DROP COLUMN IF EXISTS event_topic_markers,
    DROP COLUMN IF EXISTS event_title_anchors;

COMMIT;
