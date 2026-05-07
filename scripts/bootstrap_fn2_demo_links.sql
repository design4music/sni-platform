-- Bootstrap demo data for FN2 (Iran nuclear program).
-- 2026-05-07
-- One-off mechanical-keyword script. NOT pipeline-integrated.
-- Idempotent via ON CONFLICT DO NOTHING.
--
-- Strategy:
--   Step 1 (event_friction_nodes): events whose member titles match any FN
--   topic_keyword, ranked by recency, capped per FN.
--   Step 2 (title_narratives): titles matching any narrative framing_keyword,
--   ranked by recency, capped per narrative. One title can attach to multiple
--   narratives (article quotes both frames).

BEGIN;

-- ============================================================
-- Step 1: event_friction_nodes for FN2
-- ============================================================
-- Match titles_v3 against FN2 topic_keywords (case-insensitive substring).
-- Then link every event whose member titles include >=1 matching title.
-- UNCAPPED — the chart needs full coverage to show realistic activity.

DELETE FROM event_friction_nodes WHERE fn_id = 'iran_nuclear_program';

WITH fn AS (
    SELECT id AS fn_id, topic_keywords
    FROM friction_nodes WHERE id = 'iran_nuclear_program'
),
matching_titles AS (
    SELECT t.id AS title_id
    FROM titles_v3 t, fn
    WHERE EXISTS (
        SELECT 1 FROM unnest(fn.topic_keywords) kw
        WHERE t.title_display ILIKE '%' || kw || '%'
    )
    AND t.pubdate_utc > NOW() - INTERVAL '180 days'
),
candidate_events AS (
    SELECT DISTINCT et.event_id
    FROM event_v3_titles et
    JOIN matching_titles mt ON mt.title_id = et.title_id
)
INSERT INTO event_friction_nodes (event_id, fn_id)
SELECT ce.event_id, 'iran_nuclear_program'
FROM candidate_events ce
ON CONFLICT (event_id, fn_id) DO NOTHING;

-- ============================================================
-- Step 2: title_narratives for the 5 narratives on FN2
-- ============================================================
-- Architecture (post-publisher-stance refactor):
--   1. FN-topic gate: title contains >=1 of FN.topic_keywords
--      (tight: only Iran-nuclear-specific terms; excludes generic
--       "uranium enrichment" / "centrifuge" / NK headlines)
--   2. Publisher-stance bucket: title's publisher is in narrative.publishers
--      (editorially curated per-narrative list)
--
-- The framing_keywords no longer gate membership — they're repurposed as
-- a SAMPLE-QUALITY RANKER in the page query so cards display headlines
-- with the strongest visible framing within their bucket.
--
-- A title from a publisher in zero narratives (wire services, neutral
-- regional outlets) is left unattributed. A title from a publisher in
-- multiple narratives (rare) attaches to all of them.

DELETE FROM title_narratives WHERE narrative_id IN (
    'west_iran_nuclear_threat',
    'iran_nuclear_sovereign_right',
    'eu_diplomatic_preservation_norm',
    'multipolar_systemic_alternative',
    'gulf_regional_de_escalation'
);

WITH fn_topic AS (
    SELECT topic_keywords FROM friction_nodes WHERE id = 'iran_nuclear_program'
)
INSERT INTO title_narratives (title_id, narrative_id)
SELECT t.id AS title_id, n.id AS narrative_id
FROM narratives_v2 n
JOIN friction_node_narratives fnn ON fnn.narrative_id = n.id
JOIN fn_topic ON fnn.fn_id = 'iran_nuclear_program'
JOIN titles_v3 t
    ON t.publisher_name = ANY(n.publishers)
   AND EXISTS (
        SELECT 1 FROM unnest(fn_topic.topic_keywords) kw
        WHERE t.title_display ILIKE '%' || kw || '%'
    )
WHERE n.id IN (
    'west_iran_nuclear_threat',
    'iran_nuclear_sovereign_right',
    'eu_diplomatic_preservation_norm',
    'multipolar_systemic_alternative',
    'gulf_regional_de_escalation'
)
AND t.pubdate_utc > NOW() - INTERVAL '180 days'
ON CONFLICT (title_id, narrative_id) DO NOTHING;

COMMIT;

-- ============================================================
-- Verification
-- ============================================================
SELECT 'event_friction_nodes count for FN2' AS metric, COUNT(*)::text AS value
FROM event_friction_nodes WHERE fn_id = 'iran_nuclear_program'
UNION ALL
SELECT 'title_narratives count by narrative: ' || narrative_id, COUNT(*)::text
FROM title_narratives
WHERE narrative_id IN (SELECT narrative_id FROM friction_node_narratives WHERE fn_id = 'iran_nuclear_program')
GROUP BY narrative_id;
