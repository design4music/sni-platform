-- Create KPI view excluding macros from success metrics
-- Only count 'final' clusters as CLUST-1 success

DROP VIEW IF EXISTS clust1_final_kpis CASCADE;

CREATE VIEW clust1_final_kpis AS
WITH recent_run AS (
    -- Get most recent clustering run
    SELECT 
        MAX(created_at) as latest_run,
        COUNT(*) as total_clusters,
        COUNT(*) FILTER (WHERE cluster_type = 'final') as final_clusters,
        COUNT(*) FILTER (WHERE cluster_type = 'macro') as macro_clusters
    FROM article_clusters
    WHERE created_at >= NOW() - INTERVAL '24 hours'
),
final_members AS (
    -- Count unique articles in final clusters only
    SELECT 
        COUNT(DISTINCT acm.article_id) as final_articles,
        COUNT(*) as final_memberships,
        ROUND(AVG(cluster_sizes.size), 1) as avg_final_cluster_size
    FROM article_cluster_members acm
    JOIN article_clusters ac ON ac.cluster_id = acm.cluster_id
    JOIN (
        SELECT cluster_id, COUNT(*) as size 
        FROM article_cluster_members 
        GROUP BY cluster_id
    ) cluster_sizes ON cluster_sizes.cluster_id = ac.cluster_id
    WHERE ac.created_at >= NOW() - INTERVAL '24 hours'
      AND ac.cluster_type = 'final'
),
final_entropy AS (
    -- Calculate entropy for final clusters only
    SELECT 
        CASE WHEN COUNT(*) > 0 THEN 
            ROUND(AVG(-1 * sizes.size_ratio * LN(sizes.size_ratio))::numeric, 3)
        ELSE 0 END as final_entropy
    FROM (
        SELECT 
            acm.cluster_id,
            COUNT(*)::float / SUM(COUNT(*)) OVER () as size_ratio
        FROM article_cluster_members acm
        JOIN article_clusters ac ON ac.cluster_id = acm.cluster_id
        WHERE ac.created_at >= NOW() - INTERVAL '24 hours'
          AND ac.cluster_type = 'final'
        GROUP BY acm.cluster_id
    ) sizes
),
strategic_baseline AS (
    -- Strategic candidates baseline (approximate)
    SELECT COUNT(DISTINCT a.id) as strategic_candidates
    FROM articles a
    WHERE a.language = 'EN' 
      AND a.published_at >= NOW() - INTERVAL '72 hours'
)
SELECT 
    rr.latest_run,
    rr.total_clusters,
    rr.final_clusters,
    rr.macro_clusters,
    ROUND(100.0 * rr.macro_clusters / GREATEST(rr.total_clusters, 1), 1) as macro_pct,
    
    fm.final_articles,
    fm.final_memberships, 
    fm.avg_final_cluster_size,
    
    fe.final_entropy,
    
    sb.strategic_candidates,
    ROUND(100.0 * fm.final_articles / GREATEST(sb.strategic_candidates, 1), 1) as pct_clustered_final_over_candidates,
    
    -- Success criteria flags
    CASE WHEN fe.final_entropy <= 2.40 THEN 'PASS' ELSE 'FAIL' END as entropy_check,
    CASE WHEN rr.macro_clusters::float / GREATEST(rr.total_clusters, 1) <= 0.30 THEN 'PASS' ELSE 'FAIL' END as macro_check,
    CASE WHEN fm.final_articles::float / GREATEST(sb.strategic_candidates, 1) >= 0.05 THEN 'PASS' ELSE 'FAIL' END as coverage_check
    
FROM recent_run rr
CROSS JOIN final_members fm  
CROSS JOIN final_entropy fe
CROSS JOIN strategic_baseline sb;

-- Verify the view
SELECT * FROM clust1_final_kpis;