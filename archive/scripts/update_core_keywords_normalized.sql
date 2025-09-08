\set RUNWINDOW '300 hours'

DROP MATERIALIZED VIEW IF EXISTS article_core_keywords;
CREATE MATERIALIZED VIEW article_core_keywords AS
WITH base AS (
  SELECT a.id AS article_id,
         COALESCE(kc.canon_text, LOWER(k.keyword_text)) AS token,
         ak.strategic_score
  FROM articles a
  JOIN article_keywords ak ON ak.article_id=a.id
  JOIN keywords k ON k.id=ak.keyword_id
  LEFT JOIN keyword_canon_map m ON m.token_norm=LOWER(k.keyword_text)
  LEFT JOIN keyword_canon kc ON kc.canon_id=m.canon_id
  WHERE a.language_code='en' AND a.published_at >= now()-interval :'RUNWINDOW'
),
filtered AS (
  SELECT b.*
  FROM base b
  JOIN shared_keywords_lib_norm_30d s ON s.tok = b.token
),
ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY article_id ORDER BY strategic_score DESC) rnk
  FROM filtered
)
SELECT article_id, token, strategic_score FROM ranked WHERE rnk <= 8;