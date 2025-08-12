-- CLUST-1 Results Analysis Queries for DBeaver
-- Run these queries to understand the clustering results

-- 1. WHY ONLY 912 ARTICLES? Check article date distribution
SELECT 
    DATE(published_at) as publish_date,
    COUNT(*) as articles_count,
    MIN(published_at) as earliest_time,
    MAX(published_at) as latest_time
FROM articles 
GROUP BY DATE(published_at)
ORDER BY publish_date DESC
LIMIT 10;

-- 2. Check the 168h window we used
SELECT 
    COUNT(*) as articles_in_168h_window,
    MIN(published_at) as window_start,
    MAX(published_at) as window_end
FROM articles 
WHERE published_at >= NOW() - INTERVAL '168 hours';

-- 3. CLUSTER OVERVIEW - See all clusters with sizes
SELECT 
    ac.cluster_id,
    ac.label,
    ac.size as cluster_size,
    ac.cohesion,
    ac.top_topics,
    ac.time_window,
    ac.lang
FROM article_clusters ac
ORDER BY ac.size DESC;

-- 4. DETAILED CLUSTER MEMBERS - Articles in each cluster
SELECT 
    ac.label as cluster_label,
    ac.size as cluster_size,
    a.title,
    a.source_name,
    a.published_at,
    acm.weight
FROM article_clusters ac
JOIN article_cluster_members acm ON ac.cluster_id = acm.cluster_id
JOIN articles a ON acm.article_id = a.id
ORDER BY ac.size DESC, a.published_at DESC;

-- 5. WHY NO SPORT CLUSTER? Check topics available
SELECT 
    tt.topic_id,
    tt.name as topic_name,
    tt.source,
    COUNT(at.article_id) as articles_mapped
FROM taxonomy_topics tt
LEFT JOIN article_topics at ON tt.topic_id = at.topic_id
GROUP BY tt.topic_id, tt.name, tt.source
ORDER BY articles_mapped DESC;

-- 6. Check article-topic mappings for sports
SELECT 
    a.title,
    a.source_name,
    a.published_at,
    tt.name as topic_name,
    at.score,
    at.source as mapping_source
FROM articles a
JOIN article_topics at ON a.id = at.article_id
JOIN taxonomy_topics tt ON at.topic_id = tt.topic_id
WHERE LOWER(tt.name) LIKE '%sport%' 
   OR LOWER(a.title) LIKE '%sport%'
   OR LOWER(a.title) LIKE '%football%'
   OR LOWER(a.title) LIKE '%basketball%'
   OR LOWER(a.title) LIKE '%soccer%'
ORDER BY a.published_at DESC
LIMIT 20;

-- 7. Check what articles have keywords but no topic mappings
SELECT 
    a.id,
    a.title,
    a.source_name,
    a.published_at,
    array_agg(k.keyword) as keywords,
    COUNT(at.topic_id) as topic_count
FROM articles a
LEFT JOIN article_keywords ak ON a.id = ak.article_id
LEFT JOIN keywords k ON ak.keyword_id = k.id
LEFT JOIN article_topics at ON a.id = at.article_id
WHERE a.published_at >= NOW() - INTERVAL '168 hours'
GROUP BY a.id, a.title, a.source_name, a.published_at
HAVING COUNT(k.keyword) > 0 AND COUNT(at.topic_id) = 0
ORDER BY a.published_at DESC
LIMIT 10;

-- 8. Topic combination statistics
SELECT 
    ac.top_topics,
    COUNT(*) as clusters_with_this_combo,
    SUM(ac.size) as total_articles,
    AVG(ac.cohesion) as avg_cohesion
FROM article_clusters ac
GROUP BY ac.top_topics
ORDER BY total_articles DESC;

-- 9. Source diversity in clusters
SELECT 
    ac.label,
    ac.size,
    COUNT(DISTINCT a.source_name) as unique_sources,
    array_agg(DISTINCT a.source_name) as sources
FROM article_clusters ac
JOIN article_cluster_members acm ON ac.cluster_id = acm.cluster_id
JOIN articles a ON acm.article_id = a.id
GROUP BY ac.cluster_id, ac.label, ac.size
ORDER BY ac.size DESC;

-- 10. Articles that were processed but not clustered
WITH clustered_articles AS (
    SELECT DISTINCT acm.article_id
    FROM article_cluster_members acm
),
processed_articles AS (
    SELECT DISTINCT at.article_id
    FROM article_topics at
    JOIN articles a ON at.article_id = a.id
    WHERE a.published_at >= NOW() - INTERVAL '168 hours'
)
SELECT 
    COUNT(pa.article_id) as total_processed,
    COUNT(ca.article_id) as total_clustered,
    COUNT(pa.article_id) - COUNT(ca.article_id) as unclustered_count
FROM processed_articles pa
LEFT JOIN clustered_articles ca ON pa.article_id = ca.article_id;