\set LIBWINDOW '30 days'

-- A) daily volume (EN)
WITH days AS (
  SELECT date_trunc('day', a.published_at) AS d, COUNT(*) AS n
  FROM articles a
  WHERE a.language_code='en' AND a.published_at >= now()-interval :'LIBWINDOW'
  GROUP BY 1
),
-- choose an active-day threshold = max(30, 40th percentile of nonzero days)
thr AS (
  SELECT GREATEST(30, COALESCE(PERCENTILE_CONT(0.4) WITHIN GROUP (ORDER BY n) FILTER (WHERE n>0),0)) AS min_n
  FROM days
),
active_days AS (
  SELECT d FROM days, thr WHERE n >= thr.min_n
),
-- token occurrences per day (canonical)
ak AS (
  SELECT
    a.id AS article_id,
    COALESCE(kc.canon_text, LOWER(k.keyword_text)) AS tok,
    date_trunc('day', a.published_at) AS d
  FROM article_keywords ak
  JOIN keywords k ON k.id=ak.keyword_id
  JOIN articles a ON a.id=ak.article_id
  LEFT JOIN keyword_canon_map m ON m.token_norm=LOWER(k.keyword_text)
  LEFT JOIN keyword_canon kc ON kc.canon_id=m.canon_id
  WHERE a.language_code='en' AND a.published_at >= now()-interval :'LIBWINDOW'
),
stats AS (
  SELECT
    tok,
    COUNT(DISTINCT article_id)            AS doc_freq,
    COUNT(DISTINCT d)                     AS days_present,
    COUNT(DISTINCT d) FILTER (WHERE d IN (SELECT d FROM active_days)) AS active_days_present
  FROM ak GROUP BY tok
)
-- B) Library rule (batch-aware):
-- keep tokens that appear on >=2 active days (any volume) OR total doc_freq >= 12
DROP MATERIALIZED VIEW IF EXISTS shared_keywords_lib_norm_30d;
CREATE MATERIALIZED VIEW shared_keywords_lib_norm_30d AS
SELECT tok, doc_freq, days_present, active_days_present
FROM stats
WHERE active_days_present >= 2 OR doc_freq >= 12;