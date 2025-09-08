-- Create simplified event_anchored_triads_30d materialized view for Phase A
-- Focus on basic hub-hub-event pattern detection

-- Drop existing view if it exists
DROP MATERIALIZED VIEW IF EXISTS event_anchored_triads_30d CASCADE;

-- Create simplified materialized view
CREATE MATERIALIZED VIEW event_anchored_triads_30d AS
WITH strategic_events AS (
    -- Use event_tokens_30d as-is (no hardcoding)
    SELECT token AS event_tok FROM event_tokens_30d
),
hubs AS (
    -- Hub tokens from materialized view
    SELECT tok FROM keyword_hubs_30d
),
article_tokens AS (
    -- Recent article tokens
    SELECT 
        ack.article_id,
        ack.token
    FROM article_core_keywords ack
    JOIN articles a ON a.id = ack.article_id
    WHERE a.language = 'EN' 
      AND a.published_at >= NOW() - INTERVAL '30 days'
),
candidate_articles AS (
    -- Articles with 2+ hubs and 1+ events
    SELECT 
        at.article_id,
        ARRAY_AGG(DISTINCT at.token) FILTER (WHERE at.token IN (SELECT tok FROM hubs)) AS hub_tokens,
        ARRAY_AGG(DISTINCT at.token) FILTER (WHERE at.token IN (SELECT event_tok FROM strategic_events)) AS event_tokens
    FROM article_tokens at
    GROUP BY at.article_id
    HAVING 
        COUNT(DISTINCT at.token) FILTER (WHERE at.token IN (SELECT tok FROM hubs)) >= 2
        AND COUNT(DISTINCT at.token) FILTER (WHERE at.token IN (SELECT event_tok FROM strategic_events)) >= 1
),
triads AS (
    -- Generate hub1-hub2-event combinations from each candidate article
    SELECT 
        h1.hub AS hub1,
        h2.hub AS hub2, 
        e.event AS event_tok,
        COUNT(DISTINCT ca.article_id) AS co_doc
    FROM candidate_articles ca
    CROSS JOIN LATERAL UNNEST(ca.hub_tokens) AS h1(hub)
    CROSS JOIN LATERAL UNNEST(ca.hub_tokens) AS h2(hub)
    CROSS JOIN LATERAL UNNEST(ca.event_tokens) AS e(event)
    WHERE h1.hub < h2.hub  -- Ensure hub1 < hub2 for uniqueness
    GROUP BY h1.hub, h2.hub, e.event
    HAVING COUNT(DISTINCT ca.article_id) >= 3  -- Minimum co-occurrence
)
SELECT 
    hub1,
    hub2,
    event_tok,
    co_doc,
    LN(co_doc::float) AS pmi_score  -- Simplified PMI
FROM triads
ORDER BY co_doc DESC;

-- Create unique index for fast lookups
CREATE UNIQUE INDEX IF NOT EXISTS idx_event_anchored_triads_30d_unique 
ON event_anchored_triads_30d(hub1, hub2, event_tok);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_event_anchored_triads_30d_codoc 
ON event_anchored_triads_30d(co_doc DESC);

-- Verify the view was created
SELECT 
    COUNT(*) AS total_triads,
    AVG(co_doc) AS avg_codoc,
    MAX(co_doc) AS max_codoc
FROM event_anchored_triads_30d;