DROP MATERIALIZED VIEW IF EXISTS keyword_hubs_30d;
CREATE MATERIALIZED VIEW keyword_hubs_30d AS
SELECT tok,
       doc_freq::float / NULLIF(active_days_present,0) AS df_per_active_day
FROM shared_keywords_lib_norm_30d
ORDER BY df_per_active_day DESC
LIMIT 12;  -- keep 12 hubs