-- Create anchor_triads_30d materialized view for triad-based seed enhancement
-- Triads over last 30 days (non-hub, library tokens only)

DROP MATERIALIZED VIEW IF EXISTS anchor_triads_30d;

CREATE MATERIALIZED VIEW anchor_triads_30d AS
WITH ak AS (
  SELECT a.id AS article_id,
         COALESCE(m.canon_text, LOWER(k.keyword)) AS tok
  FROM article_keywords ak
  JOIN keywords k   ON k.id = ak.keyword_id
  JOIN articles a   ON a.id = ak.article_id
  LEFT JOIN keyword_canon_map m ON m.token_norm = LOWER(k.keyword)
  WHERE a.language = 'EN' AND a.created_at >= now() - interval '30 days'
),
lib AS (SELECT tok FROM shared_keywords_lib_norm_30d),
nonhub AS (
  SELECT tok FROM lib
  EXCEPT 
  SELECT tok FROM keyword_hubs_30d
),
triples AS (
  SELECT a1.article_id, a1.tok t1, a2.tok t2, a3.tok t3
  FROM ak a1
  JOIN ak a2 ON a2.article_id = a1.article_id AND a2.tok > a1.tok
  JOIN ak a3 ON a3.article_id = a1.article_id AND a3.tok > a2.tok
  WHERE a1.tok IN (SELECT tok FROM nonhub)
    AND a2.tok IN (SELECT tok FROM nonhub)
    AND a3.tok IN (SELECT tok FROM nonhub)
)
SELECT LEAST(t1, t2, t3) AS t1,
       -- Pick middle value: sort array, take element 2
       (SELECT val FROM unnest(ARRAY[t1, t2, t3]) val ORDER BY val LIMIT 1 OFFSET 1) AS t2,
       GREATEST(t1, t2, t3) AS t3,
       COUNT(DISTINCT article_id) AS co_doc
FROM triples
GROUP BY t1, t2, t3
HAVING COUNT(DISTINCT article_id) >= 2;   -- threshold; use 3 if too many

-- Index for fast lookups
CREATE UNIQUE INDEX IF NOT EXISTS idx_anchor_triads_30d ON anchor_triads_30d(t1, t2, t3);

-- Quick stats query for verification
-- SELECT COUNT(*) AS triads, SUM(co_doc) AS total_codoc FROM anchor_triads_30d;