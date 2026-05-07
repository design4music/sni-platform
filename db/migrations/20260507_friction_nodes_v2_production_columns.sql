-- Production-readiness columns for friction nodes + narratives.
-- 2026-05-07
--
-- Replaces hardcoded FN-specific predicates in code with per-FN
-- configuration in the database. Adds:
--
--   friction_nodes.event_actor_markers TEXT[]
--   friction_nodes.event_topic_markers TEXT[]
--   friction_nodes.event_title_anchors TEXT[]
--     The event-FN linkage gate. An event qualifies if its canonical
--     title matches:
--       (any of event_actor_markers) AND (any of event_topic_markers)
--       OR
--       (any of event_title_anchors)
--     Example for Iran nuclear:
--       actor_markers = {Iran, Tehran}
--       topic_markers = {nuclear, enrichment, uranium, atomic, centrifuge}
--       title_anchors = {Natanz, Fordow, Bushehr, Arak, JCPOA}
--
--   narratives_v2.editorial_organ_publishers TEXT[]
--     Subset of `publishers` whose editorial stance is intrinsic
--     regardless of headline language (state media, ideological
--     organs). Stand-by narratives skip the framing-keyword gate for
--     these publishers. For all_in narratives the column is unused
--     (publisher is sufficient anyway).
--     Example for multipolar_systemic_alternative:
--       editorial_organ_publishers = {RT, RT News, TASS, TASS (EN),
--                                     Sputnik, RIA Novosti, Xinhua,
--                                     CGTN, China Daily, Global Times}

BEGIN;

-- friction_nodes
ALTER TABLE friction_nodes
    ADD COLUMN IF NOT EXISTS event_actor_markers text[],
    ADD COLUMN IF NOT EXISTS event_topic_markers text[],
    ADD COLUMN IF NOT EXISTS event_title_anchors text[];

-- narratives_v2
ALTER TABLE narratives_v2
    ADD COLUMN IF NOT EXISTS editorial_organ_publishers text[];

-- Populate FN2 with the gate currently hardcoded in lib/friction-nodes.ts
-- and scripts/bootstrap_fn2_demo_links.sql.
UPDATE friction_nodes
SET event_actor_markers = ARRAY['Iran', 'Tehran'],
    event_topic_markers = ARRAY['nuclear', 'enrichment', 'uranium', 'atomic', 'centrifuge'],
    event_title_anchors = ARRAY['Natanz', 'Fordow', 'Bushehr', 'Arak', 'JCPOA'],
    updated_at = now()
WHERE id = 'iran_nuclear_program';

-- Populate editorial organ lists. ALL_IN narratives already pass without
-- framing requirement so the column stays NULL/empty for them.
UPDATE narratives_v2
SET editorial_organ_publishers = ARRAY[
        'RT', 'RT News',
        'TASS', 'TASS (EN)',
        'Sputnik', 'RIA Novosti',
        'Xinhua', 'CGTN', 'China Daily', 'Global Times'
    ],
    updated_at = now()
WHERE id = 'multipolar_systemic_alternative';

-- EU diplomacy + Gulf hedging have no editorial-organ publishers — all
-- their listed outlets are aggregators that need framing-match evidence.
-- Column stays empty/null. Setting to empty array for consistency.
UPDATE narratives_v2
SET editorial_organ_publishers = ARRAY[]::text[],
    updated_at = now()
WHERE id IN ('eu_diplomatic_preservation_norm', 'gulf_regional_de_escalation');

COMMIT;
