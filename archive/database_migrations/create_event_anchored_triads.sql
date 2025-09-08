-- Create event_anchored_triads_30d materialized view
-- CLUST-1 Phase A Enhancement: Hub-hub-event pattern detection for triad seeding

-- Drop existing view if it exists
DROP MATERIALIZED VIEW IF EXISTS event_anchored_triads_30d CASCADE;

-- Create the materialized view
CREATE MATERIALIZED VIEW event_anchored_triads_30d AS
WITH ak AS (
    -- Get article-token relationships from last 30 days
    SELECT 
        ack.article_id,
        ack.token AS tok
    FROM article_core_keywords ack
    JOIN articles a ON a.id = ack.article_id
    WHERE a.language = 'EN' 
      AND a.published_at >= NOW() - INTERVAL '30 days'
),
hubs AS (
    -- Load hub tokens 
    SELECT tok FROM keyword_hubs_30d
),
events AS (
    -- Load strategic event tokens only (filter noise)
    SELECT token AS tok FROM event_tokens_30d
    WHERE token IN ('sanctions', 'tariffs', 'war', 'peace', 'election', 'summit', 'talks', 'negotiations', 'conflict', 'missile', 'oil', 'gas', 'ceasefire', 'referendum', 'drone', 'treaty', 'meeting')
),
triples AS (
    -- Generate all 3-token combinations per article
    SELECT 
        a1.article_id,
        a1.tok AS t1,
        a2.tok AS t2, 
        a3.tok AS t3
    FROM ak a1
    JOIN ak a2 ON a2.article_id = a1.article_id AND a2.tok > a1.tok
    JOIN ak a3 ON a3.article_id = a1.article_id AND a3.tok > a2.tok
),
tri AS (
    -- Aggregate triples and count co-occurrences
    SELECT 
        LEAST(t1, t2, t3) AS x,
        CASE 
            WHEN t1 NOT IN (LEAST(t1,t2,t3), GREATEST(t1,t2,t3)) THEN t1
            WHEN t2 NOT IN (LEAST(t1,t2,t3), GREATEST(t1,t2,t3)) THEN t2  
            ELSE t3
        END AS y,
        GREATEST(t1, t2, t3) AS z,
        COUNT(DISTINCT article_id) AS co_doc
    FROM triples
    GROUP BY 1, 2, 3
),
filtered AS (
    -- Filter for patterns with exactly 2 hubs + 1 event (any order)
    SELECT x, y, z, co_doc
    FROM tri
    WHERE (
        -- Pattern 1: hub, hub, event
        (x IN (SELECT tok FROM hubs) AND y IN (SELECT tok FROM hubs) AND z IN (SELECT tok FROM events))
        OR
        -- Pattern 2: hub, event, hub  
        (x IN (SELECT tok FROM hubs) AND y IN (SELECT tok FROM events) AND z IN (SELECT tok FROM hubs))
        OR
        -- Pattern 3: event, hub, hub
        (x IN (SELECT tok FROM events) AND y IN (SELECT tok FROM hubs) AND z IN (SELECT tok FROM hubs))
    )
    AND co_doc >= 3  -- Minimum co-occurrence threshold
),
pmi AS (
    -- Calculate PMI scores for triads
    SELECT 
        f.*,
        LN(co_doc::float) 
        - 0.5 * LN(GREATEST(1, (SELECT COUNT(DISTINCT article_id) FROM ak WHERE tok = f.x)))
        - 0.5 * LN(GREATEST(1, (SELECT COUNT(DISTINCT article_id) FROM ak WHERE tok = f.y)))  
        - 0.5 * LN(GREATEST(1, (SELECT COUNT(DISTINCT article_id) FROM ak WHERE tok = f.z))) AS pmi_score
    FROM filtered f
)
-- Final output: normalize to hub1, hub2, event format
SELECT 
    CASE 
        WHEN x IN (SELECT tok FROM hubs) AND y IN (SELECT tok FROM hubs) THEN LEAST(x, y)
        WHEN x IN (SELECT tok FROM hubs) AND z IN (SELECT tok FROM hubs) THEN LEAST(x, z)
        ELSE LEAST(y, z)
    END AS hub1,
    CASE 
        WHEN x IN (SELECT tok FROM hubs) AND y IN (SELECT tok FROM hubs) THEN GREATEST(x, y)
        WHEN x IN (SELECT tok FROM hubs) AND z IN (SELECT tok FROM hubs) THEN GREATEST(x, z)
        ELSE GREATEST(y, z)
    END AS hub2,
    CASE 
        WHEN x IN (SELECT tok FROM events) THEN x
        WHEN y IN (SELECT tok FROM events) THEN y
        ELSE z
    END AS event_tok,
    co_doc,
    pmi_score
FROM pmi
WHERE pmi_score >= 1.5;  -- Lower threshold for Phase A

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
    AVG(pmi_score) AS avg_pmi
FROM event_anchored_triads_30d;