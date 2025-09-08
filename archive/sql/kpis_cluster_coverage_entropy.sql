-- KPIs: Cluster Coverage, Quality, and Entropy Analysis
-- Strategic Narrative Intelligence - CLUST-1 Performance Metrics

\echo '=== CLUST-1 KPI REPORT ==='
\echo 'Generated:' :DATE

-- 1. COVERAGE FUNNEL ANALYSIS
\echo ''
\echo '1. COVERAGE FUNNEL (300h window)'

WITH funnel AS (
  -- Total articles in window
  SELECT 
    COUNT(*) as total_articles,
    COUNT(*) FILTER (WHERE language = 'EN') as en_articles
  FROM articles 
  WHERE published_at >= now() - interval '300 hours'
),
keywords_funnel AS (
  -- Articles with keywords  
  SELECT 
    COUNT(DISTINCT a.id) as articles_with_keywords,
    COUNT(DISTINCT ck.article_id) as articles_with_core_keywords
  FROM articles a
  LEFT JOIN article_keywords ak ON ak.article_id = a.id
  LEFT JOIN article_core_keywords ck ON ck.article_id = a.id
  WHERE a.language = 'EN' 
  AND a.published_at >= now() - interval '300 hours'
),
clustering_funnel AS (
  -- Clustered articles
  SELECT 
    COUNT(DISTINCT ac.cluster_id) as total_clusters,
    COUNT(DISTINCT acm.article_id) as clustered_articles,
    AVG(ac.size) as avg_cluster_size,
    AVG(ac.cohesion) as avg_cohesion
  FROM article_clusters ac
  LEFT JOIN article_cluster_members acm ON acm.cluster_id = ac.cluster_id
)
SELECT 
  f.total_articles,
  f.en_articles,
  kf.articles_with_keywords,
  kf.articles_with_core_keywords,
  cf.total_clusters,
  cf.clustered_articles,
  ROUND(cf.clustered_articles::float / NULLIF(kf.articles_with_core_keywords, 0) * 100, 1) as recall_pct,
  ROUND(kf.articles_with_core_keywords::float / NULLIF(f.en_articles, 0) * 100, 1) as coverage_pct,
  ROUND(cf.avg_cluster_size, 1) as avg_cluster_size,
  ROUND(cf.avg_cohesion, 3) as avg_cohesion
FROM funnel f, keywords_funnel kf, clustering_funnel cf;

-- 2. CLUSTER QUALITY DISTRIBUTION  
\echo ''
\echo '2. CLUSTER QUALITY DISTRIBUTION'

SELECT 
  CASE 
    WHEN cohesion >= 0.80 THEN '0.80+ (Excellent)'
    WHEN cohesion >= 0.70 THEN '0.70-0.79 (Very Good)' 
    WHEN cohesion >= 0.60 THEN '0.60-0.69 (Good)'
    WHEN cohesion >= 0.50 THEN '0.50-0.59 (Fair)'
    ELSE '< 0.50 (Poor)'
  END as quality_tier,
  COUNT(*) as cluster_count,
  ROUND(AVG(size), 1) as avg_size,
  ROUND(MIN(cohesion), 3) as min_cohesion,
  ROUND(MAX(cohesion), 3) as max_cohesion
FROM article_clusters 
WHERE cohesion IS NOT NULL
GROUP BY 1
ORDER BY min_cohesion DESC;

-- 3. TOP PERFORMING CLUSTERS
\echo ''
\echo '3. TOP PERFORMING CLUSTERS (by size and quality)'

SELECT 
  COALESCE(label, 'Unlabeled') as cluster_label,
  size as articles,
  ROUND(cohesion, 3) as cohesion,
  CASE 
    WHEN top_topics IS NOT NULL THEN array_to_string(top_topics[1:3], ', ')
    ELSE 'No topics'
  END as top_keywords
FROM article_clusters 
ORDER BY size DESC, cohesion DESC
LIMIT 15;

-- 4. ENTROPY AND DIVERSITY ANALYSIS
\echo ''
\echo '4. CLUSTER ENTROPY ANALYSIS'

WITH entropy_calc AS (
  SELECT 
    ac.cluster_id,
    ac.size,
    ac.cohesion,
    -- Calculate keyword diversity entropy
    CASE 
      WHEN ac.top_topics IS NOT NULL THEN array_length(ac.top_topics, 1)
      ELSE 0 
    END as keyword_diversity,
    -- Size-based entropy tier
    CASE 
      WHEN ac.size >= 10 THEN 'Large (10+)'
      WHEN ac.size >= 5 THEN 'Medium (5-9)'  
      WHEN ac.size >= 3 THEN 'Small (3-4)'
      ELSE 'Tiny (1-2)'
    END as size_tier
  FROM article_clusters ac
)
SELECT 
  size_tier,
  COUNT(*) as cluster_count,
  ROUND(AVG(size), 1) as avg_size,
  ROUND(AVG(cohesion), 3) as avg_cohesion,
  ROUND(AVG(keyword_diversity), 1) as avg_keyword_diversity,
  SUM(size) as total_articles_in_tier
FROM entropy_calc
GROUP BY size_tier
ORDER BY 
  CASE size_tier
    WHEN 'Large (10+)' THEN 1
    WHEN 'Medium (5-9)' THEN 2  
    WHEN 'Small (3-4)' THEN 3
    ELSE 4
  END;

-- 5. TEMPORAL CLUSTERING PERFORMANCE
\echo ''
\echo '5. TEMPORAL CLUSTERING PATTERNS (last 7 days)'

WITH daily_stats AS (
  SELECT 
    date_trunc('day', a.published_at) as day,
    COUNT(DISTINCT a.id) as daily_articles,
    COUNT(DISTINCT CASE WHEN acm.article_id IS NOT NULL THEN a.id END) as daily_clustered,
    COUNT(DISTINCT CASE WHEN ck.article_id IS NOT NULL THEN a.id END) as daily_eligible
  FROM articles a
  LEFT JOIN article_cluster_members acm ON acm.article_id = a.id
  LEFT JOIN article_core_keywords ck ON ck.article_id = a.id
  WHERE a.language = 'EN'
  AND a.published_at >= now() - interval '7 days'
  GROUP BY 1
)
SELECT 
  TO_CHAR(day, 'YYYY-MM-DD Dy') as date,
  daily_articles as articles,
  daily_eligible as eligible,  
  daily_clustered as clustered,
  CASE 
    WHEN daily_eligible > 0 THEN ROUND(daily_clustered::float / daily_eligible * 100, 1)
    ELSE 0 
  END as daily_recall_pct
FROM daily_stats
ORDER BY day DESC
LIMIT 7;

-- 6. BIGRAM CANONICALIZATION IMPACT
\echo ''
\echo '6. CANONICALIZATION IMPACT (bigrams and entities)'

SELECT 
  concept_cluster,
  COUNT(*) as mapping_count,
  ROUND(AVG(confidence), 3) as avg_confidence,
  array_agg(canon_text ORDER BY confidence DESC LIMIT 5) as top_canonical_terms
FROM keyword_canon_map
WHERE concept_cluster IS NOT NULL
GROUP BY concept_cluster
ORDER BY mapping_count DESC
LIMIT 10;

-- 7. LIBRARY EFFICIENCY METRICS  
\echo ''
\echo '7. BATCH-AWARE LIBRARY EFFICIENCY'

SELECT 
  COUNT(*) as total_library_tokens,
  COUNT(*) FILTER (WHERE active_days_present >= 2) as multi_day_tokens,
  COUNT(*) FILTER (WHERE doc_freq >= 12) as high_freq_tokens,
  COUNT(*) FILTER (WHERE active_days_present >= 2 AND doc_freq < 12) as batch_rescued_tokens,
  ROUND(AVG(doc_freq), 1) as avg_doc_freq,
  ROUND(AVG(days_present), 1) as avg_days_present,
  ROUND(AVG(active_days_present), 1) as avg_active_days
FROM shared_keywords_lib_norm_30d;

\echo ''
\echo '=== END KPI REPORT ==='