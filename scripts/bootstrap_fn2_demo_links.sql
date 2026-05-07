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
-- Per architecture: title must pass THREE gates:
--   1. Topic-relevance: title contains >=1 narrative.topic_keyword
--   2. Frame-relevance: title contains >=1 narrative.framing_keyword
--      (loaded vocabulary diagnostic)
--   3. Centroid-relevance (NEW): title contains >=1 identifier from
--      narrative.actor_centroids ∪ FN.centroid_ids ("manifests in").
--      Stops cross-FN bleed: "N. Korea uranium enrichment facility
--      complete" no longer matches the Iran-nuclear narratives because
--      no Iran/Israel/Saudi/USA/EU identifier appears.
--
-- The centroid_alias_lookup CTE is hardcoded for the demo. In production
-- this would live in a centroids_v3.aliases column or a dedicated
-- centroid_aliases table.

DELETE FROM title_narratives WHERE narrative_id IN (
    'west_iran_nuclear_threat',
    'iran_nuclear_sovereign_right',
    'eu_diplomatic_preservation_norm',
    'multipolar_systemic_alternative',
    'gulf_regional_de_escalation'
);

WITH centroid_alias_lookup(cid, kw) AS (VALUES
    ('AMERICAS-USA',     ARRAY['United States','American','Washington','Trump','Biden','Vance','Witkoff','Rubio','White House','US administration','U.S. ','US '] ),
    ('MIDEAST-ISRAEL',   ARRAY['Israel','Israeli','IDF','Mossad','Netanyahu','Katz','Tel Aviv','Jerusalem','Barnea']),
    ('MIDEAST-SAUDI',    ARRAY['Saudi','Riyadh','MBS','Mohammed bin Salman']),
    ('MIDEAST-IRAN',     ARRAY['Iran','Iranian','Tehran','Khamenei','Pezeshkian','Araghchi','Larijani','Baqaei','Gharibabadi','Eslami','IRGC']),
    ('NON-STATE-EU',     ARRAY['EU ','European Union','Europe','Brussels','E3','Borrell','Kallas','von der Leyen']),
    ('EUROPE-FRANCE',    ARRAY['France','French','Macron','Paris','Quai d''Orsay','Barrot']),
    ('EUROPE-GERMANY',   ARRAY['Germany','German','Berlin','Scholz','Merz','Baerbock','FAZ ']),
    ('EUROPE-UK',        ARRAY['UK ','U.K.','British','London','Starmer','Lammy']),
    ('EUROPE-RUSSIA',    ARRAY['Russia','Russian','Moscow','Putin','Lavrov','Kremlin']),
    ('ASIA-CHINA',       ARRAY['China','Chinese','Beijing','Xi Jinping','Wang Yi']),
    ('ASIA-NORKOREA',    ARRAY['North Korea','DPRK','Kim Jong-un','Pyongyang','Hwasong'])
),
-- For each narrative on FN2, build the union set of allowed centroid
-- aliases: coalition (narrative.actor_centroids) + manifests-in (fn.centroid_ids).
narrative_allowed_aliases AS (
    SELECT
        n.id AS narrative_id,
        ARRAY(
            SELECT DISTINCT k
            FROM (
                SELECT unnest(cal.kw) AS k
                FROM friction_node_narratives fnn
                JOIN friction_nodes fn ON fn.id = fnn.fn_id
                JOIN centroid_alias_lookup cal
                  ON cal.cid = ANY(n.actor_centroids)
                  OR cal.cid = ANY(fn.centroid_ids)
                WHERE fnn.narrative_id = n.id
            ) sub
        ) AS aliases
    FROM narratives_v2 n
    WHERE n.id IN (
        'west_iran_nuclear_threat',
        'iran_nuclear_sovereign_right',
        'eu_diplomatic_preservation_norm',
        'multipolar_systemic_alternative',
        'gulf_regional_de_escalation'
    )
)
INSERT INTO title_narratives (title_id, narrative_id)
SELECT t.id AS title_id, n.id AS narrative_id
FROM narratives_v2 n
JOIN narrative_allowed_aliases naa ON naa.narrative_id = n.id
JOIN titles_v3 t
    ON EXISTS (
        SELECT 1 FROM unnest(n.topic_keywords) kw
        WHERE t.title_display ILIKE '%' || kw || '%'
    )
   AND EXISTS (
        SELECT 1 FROM unnest(n.framing_keywords) kw
        WHERE t.title_display ILIKE '%' || kw || '%'
    )
   AND EXISTS (
        SELECT 1 FROM unnest(naa.aliases) kw
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
