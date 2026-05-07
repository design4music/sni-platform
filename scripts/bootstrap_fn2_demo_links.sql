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
-- An event-FN link means the event is SUBSTANTIVELY about the FN's
-- contested phenomenon — not just that one of its many member titles
-- happens to mention it. Test: the event's OWN canonical title must
-- carry both an Iran-marker AND a nuclear-domain word, OR a name that's
-- inherently Iran-nuclear (Natanz, Fordow, Bushehr, Arak, JCPOA).
--
-- Earlier loose rule (any member-title mentions topic kw) attached events
-- like "US submarine sinks Iranian warship" — has 187 member titles,
-- maybe 5 mention nuclear in passing, but the event isn't ABOUT nuclear.
-- The strict rule cuts ~239 -> ~142 events for FN2; surviving set is
-- substantively on-topic.
--
-- Hardcoded predicate per FN. When more FNs land we'll move this to a
-- per-FN JSONB "title-match grammar" column on friction_nodes.

DELETE FROM event_friction_nodes WHERE fn_id = 'iran_nuclear_program';

INSERT INTO event_friction_nodes (event_id, fn_id)
SELECT e.id, 'iran_nuclear_program'
FROM events_v3 e
WHERE e.is_promoted = true
  AND e.merged_into IS NULL
  AND e.date > (CURRENT_DATE - INTERVAL '180 days')
  AND (
    -- Iran-marker AND nuclear-domain word
    (
      (e.title ILIKE '%Iran%' OR e.title ILIKE '%Tehran%')
      AND (
        e.title ILIKE '%nuclear%' OR e.title ILIKE '%enrichment%'
        OR e.title ILIKE '%uranium%' OR e.title ILIKE '%atomic%'
        OR e.title ILIKE '%centrifuge%'
      )
    )
    -- Iran-specific site/program names (no other co-marker needed)
    OR e.title ILIKE '%Natanz%'
    OR e.title ILIKE '%Fordow%'
    OR e.title ILIKE '%Bushehr%'
    OR e.title ILIKE '%Arak%'
    OR e.title ILIKE '%JCPOA%'
  )
ON CONFLICT (event_id, fn_id) DO NOTHING;

-- ============================================================
-- Step 2: title_narratives for the 5 narratives on FN2
-- ============================================================
-- Architecture (post-publisher-stance + per-type strictness):
--   1. FN-topic gate: title contains >=1 of FN.topic_keywords
--   2. Publisher-stance bucket: title's publisher is in narrative.publishers
--   3. Framing gate (CONDITIONAL): for narrative_type='stand_by' narratives
--      ONLY, title must also contain >=1 of narrative.framing_keywords.
--
-- Why the conditional: ALL_IN narratives have publisher lists that are
-- ideological organs (Press TV, IRNA, Jerusalem Post, Times of Israel)
-- — every headline they publish on this FN frames from their stance,
-- so publisher alone is sufficient. STAND_BY narratives have publisher
-- lists that include news-aggregator outlets (BBC, Le Monde, Al Arabiya,
-- Al-Ahram, Gulf News) which cover the FN broadly without consistent
-- frame; those need framing-keyword evidence to confirm the stand-by
-- frame is actually present in the headline.
--
-- This is what stops "UAE air defences intercept Iranian missiles" from
-- being attributed to gulf_regional_de_escalation just because Gulf News
-- is a Gulf-hedging publisher.

DELETE FROM title_narratives WHERE narrative_id IN (
    'west_iran_nuclear_threat',
    'iran_nuclear_sovereign_right',
    'eu_diplomatic_preservation_norm',
    'multipolar_systemic_alternative'
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
   AND (
        -- ALL_IN: publisher stance is sufficient.
        n.narrative_type = 'all_in'
        OR
        -- STAND_BY editorial-organ exception: state-media publishers
        -- are intrinsically on-frame regardless of headline (RT/TASS
        -- always anti-Western; Xinhua/CGTN always Chinese-multipolar;
        -- Press TV always Iran POV — though that one only appears in
        -- all_in lists). Letting these through without framing match
        -- preserves their coverage.
        t.publisher_name = ANY(ARRAY[
            'RT', 'RT News',
            'TASS', 'TASS (EN)',
            'Sputnik', 'RIA Novosti',
            'Xinhua', 'CGTN', 'China Daily', 'Global Times'
        ])
        OR
        -- STAND_BY non-editorial: require framing-keyword evidence.
        -- For aggregator publishers (BBC, Le Monde, Al Arabiya, Gulf News,
        -- Al Jazeera, Anadolu, etc.), the publisher covers broadly so we
        -- need the framing language as confirmation that THIS specific
        -- headline carries the narrative's frame.
        EXISTS (
            SELECT 1 FROM unnest(n.framing_keywords) kw
            WHERE t.title_display ILIKE '%' || kw || '%'
        )
   )
WHERE n.id IN (
    'west_iran_nuclear_threat',
    'iran_nuclear_sovereign_right',
    'eu_diplomatic_preservation_norm',
    'multipolar_systemic_alternative'
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
