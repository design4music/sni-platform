-- Strategic Narrative Intelligence Platform - Query Patterns with Metrics Separation
-- Updated to use narrative_metrics table for all analytics fields
-- NSF-1 JSON in narratives table stores content only

-- =============================================
-- DASHBOARD QUERIES (USING METRICS TABLE)
-- =============================================

-- Query Pattern 1: Main Dashboard - Trending Narratives
-- Uses metrics table for all trending and scoring data
WITH trending_narratives AS (
    SELECT 
        n.narrative_id,
        n.title,
        n.summary,
        n.alignment,
        n.actor_origin,
        n.updated_at,
        
        -- Metrics from separate table
        m.trending_score,
        m.credibility_score,
        m.engagement_score,
        m.narrative_status,
        m.narrative_priority,
        m.keywords,
        m.geographic_scope,
        m.sentiment_score,
        
        -- Calculate recency boost (newer narratives get slight boost)
        CASE 
            WHEN n.updated_at > CURRENT_TIMESTAMP - interval '24 hours' THEN m.trending_score * 1.2
            WHEN n.updated_at > CURRENT_TIMESTAMP - interval '72 hours' THEN m.trending_score * 1.1
            ELSE m.trending_score
        END as boosted_score,
        
        -- Get article count from source_stats JSONB
        (n.source_stats->>'total_articles')::integer as total_articles,
        
        -- Get latest activity from timeline
        (SELECT jsonb_array_elements(n.activity_timeline) 
         ORDER BY (jsonb_array_elements(n.activity_timeline)->>'timestamp') DESC 
         LIMIT 1) as latest_activity
        
    FROM narratives n
    JOIN narrative_metrics m ON n.id = m.narrative_uuid
    WHERE m.narrative_status = 'active'
    AND m.trending_score > 0.1  -- Filter out very low-trending narratives
)
SELECT 
    tn.*,
    -- Add source diversity metric from NSF-1 source_stats
    COALESCE(jsonb_object_keys_count(tn.source_stats->'sources'), 0) as unique_sources
FROM trending_narratives tn
ORDER BY tn.boosted_score DESC, tn.updated_at DESC
LIMIT 50;

-- Query Pattern 2: Narrative Detail Page
-- Comprehensive narrative information with metrics
CREATE OR REPLACE FUNCTION get_narrative_detail(p_narrative_id VARCHAR(50))
RETURNS TABLE (
    -- Core narrative data (NSF-1)
    id UUID,
    narrative_id VARCHAR(50),
    title VARCHAR(500),
    summary TEXT,
    origin_language CHAR(2),
    alignment JSONB,
    actor_origin JSONB,
    frame_logic JSONB,
    narrative_tension JSONB,
    activity_timeline JSONB,
    turning_points JSONB,
    media_spike_history JSONB,
    source_stats JSONB,
    top_excerpts JSONB,
    update_status JSONB,
    confidence_rating VARCHAR(20),
    data_quality_notes TEXT,
    version_history JSONB,
    rai_analysis JSONB,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Metrics data
    narrative_start_date TIMESTAMP WITH TIME ZONE,
    narrative_end_date TIMESTAMP WITH TIME ZONE,
    trending_score NUMERIC,
    credibility_score NUMERIC,
    engagement_score NUMERIC,
    sentiment_score NUMERIC,
    narrative_priority INTEGER,
    narrative_status TEXT,
    geographic_scope TEXT,
    keywords TEXT[],
    last_spike TIMESTAMP WITH TIME ZONE,
    
    -- Related data
    recent_articles JSONB,
    similar_narratives JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        -- Core narrative data
        n.id,
        n.narrative_id,
        n.title,
        n.summary,
        n.origin_language,
        n.alignment,
        n.actor_origin,
        n.frame_logic,
        n.narrative_tension,
        n.activity_timeline,
        n.turning_points,
        n.media_spike_history,
        n.source_stats,
        n.top_excerpts,
        n.update_status,
        n.confidence_rating,
        n.data_quality_notes,
        n.version_history,
        n.rai_analysis,
        n.created_at,
        n.updated_at,
        
        -- Metrics data
        m.narrative_start_date,
        m.narrative_end_date,
        m.trending_score,
        m.credibility_score,
        m.engagement_score,
        m.sentiment_score,
        m.narrative_priority,
        m.narrative_status,
        m.geographic_scope,
        m.keywords,
        m.last_spike,
        
        -- Recent high-relevance articles
        COALESCE(articles.article_data, '[]'::jsonb) as recent_articles,
        
        -- Similar narratives based on embeddings
        COALESCE(similar.similar_data, '[]'::jsonb) as similar_narratives
        
    FROM narratives n
    JOIN narrative_metrics m ON n.id = m.narrative_uuid
    LEFT JOIN (
        -- Get 10 most recent and relevant articles
        SELECT 
            na.narrative_id,
            jsonb_agg(
                jsonb_build_object(
                    'article_id', ra.article_id,
                    'title', ra.title,
                    'summary', ra.summary,
                    'published_at', ra.published_at,
                    'source_name', ns.source_name,
                    'url', ra.url,
                    'relevance_score', na.relevance_score,
                    'sentiment_score', ra.sentiment_score
                ) ORDER BY ra.published_at DESC
            ) as article_data
        FROM (
            SELECT narrative_id, article_id, relevance_score
            FROM narrative_articles
            WHERE narrative_id = (SELECT id FROM narratives WHERE narrative_id = p_narrative_id)
            AND relevance_score >= 0.5
            ORDER BY relevance_score DESC, assigned_at DESC
            LIMIT 10
        ) na
        JOIN raw_articles ra ON na.article_id = ra.article_id  
        JOIN news_sources ns ON ra.source_id = ns.source_id
        GROUP BY na.narrative_id
    ) articles ON n.id = articles.narrative_id
    
    LEFT JOIN (
        -- Get 5 most similar narratives using vector similarity
        SELECT 
            n_base.id as narrative_uuid,
            jsonb_agg(
                jsonb_build_object(
                    'narrative_id', similar_n.narrative_id,
                    'title', similar_n.title,
                    'summary', similar_n.summary,
                    'similarity_score', 1.0 - (n_base.narrative_embedding <=> similar_n.narrative_embedding),
                    'trending_score', similar_m.trending_score
                ) ORDER BY (n_base.narrative_embedding <=> similar_n.narrative_embedding) ASC
            ) as similar_data
        FROM narratives n_base
        CROSS JOIN LATERAL (
            SELECT 
                sn.id,
                sn.narrative_id,
                sn.title,
                sn.summary,
                sn.narrative_embedding
            FROM narratives sn
            JOIN narrative_metrics sm ON sn.id = sm.narrative_uuid
            WHERE sn.narrative_id != p_narrative_id
            AND sm.narrative_status = 'active'
            AND n_base.narrative_embedding <=> sn.narrative_embedding < 0.4
            ORDER BY n_base.narrative_embedding <=> sn.narrative_embedding
            LIMIT 5
        ) similar_n
        JOIN narrative_metrics similar_m ON similar_n.id = similar_m.narrative_uuid
        WHERE n_base.narrative_id = p_narrative_id
        GROUP BY n_base.id
    ) similar ON n.id = similar.narrative_uuid
    
    WHERE n.narrative_id = p_narrative_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- SEARCH AND FILTERING QUERIES WITH METRICS
-- =============================================

-- Query Pattern 3: Advanced Search with Metrics Filters
CREATE OR REPLACE FUNCTION search_narratives(
    p_search_text TEXT DEFAULT NULL,
    p_search_embedding vector(1536) DEFAULT NULL,
    p_actor_origins TEXT[] DEFAULT NULL,
    p_alignments TEXT[] DEFAULT NULL,
    p_date_from DATE DEFAULT NULL,
    p_date_to DATE DEFAULT NULL,
    p_min_credibility NUMERIC DEFAULT 0.0,
    p_narrative_status TEXT[] DEFAULT NULL,
    p_keywords TEXT[] DEFAULT NULL,
    p_geographic_scope TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 50,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    narrative_id VARCHAR(50),
    title VARCHAR(500),
    summary TEXT,
    alignment JSONB,
    trending_score NUMERIC,
    credibility_score NUMERIC,
    narrative_status TEXT,
    geographic_scope TEXT,
    keywords TEXT[],
    updated_at TIMESTAMP WITH TIME ZONE,
    search_rank DECIMAL(10,4),
    semantic_similarity DECIMAL(3,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        n.id,
        n.narrative_id,
        n.title,
        n.summary,
        n.alignment,
        m.trending_score,
        m.credibility_score,
        m.narrative_status,
        m.geographic_scope,
        m.keywords,
        n.updated_at,
        CASE 
            WHEN p_search_text IS NOT NULL THEN ts_rank(n.search_vector, plainto_tsquery('english', p_search_text))
            ELSE 0.0
        END::DECIMAL(10,4) as search_rank,
        CASE 
            WHEN p_search_embedding IS NOT NULL THEN (1.0 - (n.narrative_embedding <=> p_search_embedding))::DECIMAL(3,2)
            ELSE 0.0
        END as semantic_similarity
    FROM narratives n
    JOIN narrative_metrics m ON n.id = m.narrative_uuid
    WHERE 
        -- Status filter
        (p_narrative_status IS NULL OR m.narrative_status = ANY(p_narrative_status))
        
        -- Credibility filter
        AND m.credibility_score >= p_min_credibility
        
        -- Date range filter
        AND (p_date_from IS NULL OR m.narrative_start_date >= p_date_from)
        AND (p_date_to IS NULL OR m.narrative_start_date <= p_date_to)
        
        -- Geographic filter
        AND (p_geographic_scope IS NULL OR m.geographic_scope = p_geographic_scope)
        
        -- Keywords filter
        AND (p_keywords IS NULL OR m.keywords && p_keywords)
        
        -- Actor origins filter (NSF-1 JSONB)
        AND (p_actor_origins IS NULL OR EXISTS (
            SELECT 1 FROM jsonb_array_elements_text(n.actor_origin) AS actor
            WHERE actor = ANY(p_actor_origins)
        ))
        
        -- Alignments filter (NSF-1 JSONB)
        AND (p_alignments IS NULL OR EXISTS (
            SELECT 1 FROM jsonb_array_elements_text(n.alignment) AS align
            WHERE align = ANY(p_alignments)
        ))
        
        -- Text search filter
        AND (p_search_text IS NULL OR n.search_vector @@ plainto_tsquery('english', p_search_text))
        
        -- Semantic search filter
        AND (p_search_embedding IS NULL OR n.narrative_embedding <=> p_search_embedding < 0.5)
    
    ORDER BY 
        CASE 
            WHEN p_search_text IS NOT NULL AND p_search_embedding IS NOT NULL THEN
                (COALESCE(ts_rank(n.search_vector, plainto_tsquery('english', p_search_text)), 0) * 0.6 + 
                 (1.0 - COALESCE(n.narrative_embedding <=> p_search_embedding, 1.0)) * 0.4)
            WHEN p_search_text IS NOT NULL THEN
                ts_rank(n.search_vector, plainto_tsquery('english', p_search_text))
            WHEN p_search_embedding IS NOT NULL THEN
                (1.0 - (n.narrative_embedding <=> p_search_embedding))
            ELSE
                m.trending_score
        END DESC,
        n.updated_at DESC
    
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- ANALYTICS AND TRENDING QUERIES
-- =============================================

-- Query Pattern 4: Trending Analysis Dashboard
-- Pure metrics-based trending analysis
SELECT 
    n.narrative_id,
    n.title,
    n.summary,
    n.alignment,
    n.actor_origin,
    
    -- All metrics from metrics table
    m.trending_score,
    m.credibility_score,
    m.engagement_score,
    m.sentiment_score,
    m.narrative_priority,
    m.narrative_status,
    m.geographic_scope,
    m.keywords,
    m.narrative_start_date,
    m.last_spike,
    
    -- Content-based metrics from NSF-1
    (n.source_stats->>'total_articles')::integer as total_articles,
    (n.rai_analysis->>'adequacy_score')::numeric as rai_adequacy,
    
    -- Calculate composite score
    (m.trending_score * 0.4 + 
     m.credibility_score * 0.3 + 
     m.engagement_score * 10 * 0.2 +
     CASE WHEN m.last_spike >= CURRENT_TIMESTAMP - interval '24 hours' THEN 2.0 ELSE 0.0 END * 0.1
    ) as composite_score
     
FROM narratives n
JOIN narrative_metrics m ON n.id = m.narrative_uuid
WHERE m.narrative_status IN ('active', 'emerging')
ORDER BY composite_score DESC, m.trending_score DESC
LIMIT 25;

-- Query Pattern 5: Geographic and Status Analysis
-- Analyzes narrative distribution by region and status
SELECT 
    m.geographic_scope,
    m.narrative_status,
    COUNT(*) as narrative_count,
    AVG(m.trending_score) as avg_trending_score,
    AVG(m.credibility_score) as avg_credibility_score,
    AVG(m.engagement_score) as avg_engagement_score,
    
    -- Most common keywords by region/status
    array_agg(DISTINCT unnest(m.keywords)) as common_keywords,
    
    -- Sample narratives
    array_agg(n.narrative_id ORDER BY m.trending_score DESC) FILTER (WHERE rn <= 3) as top_narratives
    
FROM narratives n
JOIN narrative_metrics m ON n.id = m.narrative_uuid
CROSS JOIN LATERAL (
    SELECT ROW_NUMBER() OVER (PARTITION BY m.geographic_scope, m.narrative_status ORDER BY m.trending_score DESC) as rn
) ranked
WHERE m.narrative_status != 'archived'
GROUP BY m.geographic_scope, m.narrative_status
ORDER BY narrative_count DESC, avg_trending_score DESC;

-- Query Pattern 6: Keyword and Topic Analysis
-- Analyzes trending keywords and topics
WITH keyword_analysis AS (
    SELECT 
        unnest(m.keywords) as keyword,
        COUNT(*) as narrative_count,
        AVG(m.trending_score) as avg_trending_score,
        AVG(m.credibility_score) as avg_credibility_score,
        array_agg(DISTINCT m.geographic_scope) as regions,
        array_agg(n.narrative_id ORDER BY m.trending_score DESC) FILTER (WHERE rn <= 3) as top_narratives
    FROM narrative_metrics m
    JOIN narratives n ON n.id = m.narrative_uuid
    CROSS JOIN LATERAL (
        SELECT ROW_NUMBER() OVER (PARTITION BY unnest(m.keywords) ORDER BY m.trending_score DESC) as rn
    ) ranked
    WHERE m.narrative_status = 'active'
    AND m.keywords IS NOT NULL
    GROUP BY unnest(m.keywords)
    HAVING COUNT(*) >= 2  -- Keywords appearing in at least 2 narratives
)
SELECT 
    keyword,
    narrative_count,
    avg_trending_score,
    avg_credibility_score,
    regions,
    top_narratives
FROM keyword_analysis
ORDER BY avg_trending_score DESC, narrative_count DESC
LIMIT 20;

-- Query Pattern 7: Conflicts and Relationships Analysis
-- Analyzes narrative conflicts using NSF-1 data + metrics
SELECT 
    n1.narrative_id as source_narrative,
    n1.title as source_title,
    m1.trending_score as source_trending,
    m1.credibility_score as source_credibility,
    
    -- Conflicting narratives from NSF-1 conflicts_with field
    conflicts.conflicting_id,
    n2.title as conflicting_title,
    m2.trending_score as conflicting_trending,
    m2.credibility_score as conflicting_credibility,
    
    -- Shared keywords
    (m1.keywords && m2.keywords) as has_shared_keywords,
    (SELECT array_agg(k) FROM unnest(m1.keywords) k WHERE k = ANY(m2.keywords)) as shared_keywords,
    
    -- Geographic overlap
    (m1.geographic_scope = m2.geographic_scope) as same_region
    
FROM narratives n1
JOIN narrative_metrics m1 ON n1.id = m1.narrative_uuid
CROSS JOIN LATERAL jsonb_array_elements_text(n1.conflicts_with) conflicts(conflicting_id)
JOIN narratives n2 ON n2.narrative_id = conflicts.conflicting_id
JOIN narrative_metrics m2 ON n2.id = m2.narrative_uuid
WHERE m1.narrative_status = 'active' 
AND m2.narrative_status = 'active'
ORDER BY (m1.trending_score + m2.trending_score) DESC;

-- =============================================
-- PERFORMANCE MONITORING QUERIES
-- =============================================

-- Query to validate metrics separation
SELECT 
    'narratives' as table_name,
    COUNT(*) as total_rows,
    COUNT(CASE WHEN narrative_embedding IS NOT NULL THEN 1 END) as with_embeddings,
    AVG(jsonb_array_length(alignment)) as avg_alignment_count,
    COUNT(CASE WHEN rai_analysis->>'adequacy_score' IS NOT NULL THEN 1 END) as with_rai_analysis
FROM narratives
UNION ALL
SELECT 
    'narrative_metrics' as table_name,
    COUNT(*) as total_rows,
    COUNT(CASE WHEN trending_score > 0 THEN 1 END) as with_trending_score,
    AVG(array_length(keywords, 1)) as avg_keywords_count,
    COUNT(CASE WHEN credibility_score IS NOT NULL THEN 1 END) as with_credibility_score
FROM narrative_metrics;

-- Query to check join performance
EXPLAIN (ANALYZE, BUFFERS) 
SELECT n.narrative_id, n.title, m.trending_score, m.narrative_status
FROM narratives n
JOIN narrative_metrics m ON n.id = m.narrative_uuid
WHERE m.narrative_status = 'active'
ORDER BY m.trending_score DESC
LIMIT 10;

-- Query to monitor index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    CASE WHEN idx_scan = 0 THEN 'Never used' 
         WHEN idx_scan < 100 THEN 'Rarely used'
         ELSE 'Actively used' 
    END as usage_status
FROM pg_stat_user_indexes
WHERE tablename IN ('narratives', 'narrative_metrics', 'narrative_articles')
ORDER BY idx_scan DESC;