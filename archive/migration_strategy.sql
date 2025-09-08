-- Strategic Narrative Intelligence Platform - Migration Strategy
-- This file contains the step-by-step migration plan and optimization guidelines

-- =============================================
-- MIGRATION EXECUTION ORDER
-- =============================================

/*
PHASE 1: Core Infrastructure Setup
1. Enable required PostgreSQL extensions
2. Create core domain tables (news_sources, narrative_actors)
3. Create partitioned tables with initial partitions
4. Set up basic indexes

PHASE 2: NSF-1 Schema Implementation
1. Create narratives table with NSF-1 fields
2. Create narrative_versions table
3. Create relationship tables
4. Add JSON field constraints and indexes

PHASE 3: Analytics and Performance
1. Create timeline and metrics tables
2. Create clustering tables
3. Add all performance indexes
4. Create functions and triggers

PHASE 4: Data Migration (if migrating from existing system)
1. Migrate news sources and articles
2. Transform existing narratives to NSF-1 format
3. Generate embeddings for existing content
4. Populate relationship tables
*/

-- =============================================
-- PARTITION MANAGEMENT STRATEGY
-- =============================================

-- Function to automatically create new monthly partitions for raw_articles
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name TEXT, start_date DATE)
RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    end_date DATE;
BEGIN
    partition_name := table_name || '_' || to_char(start_date, 'YYYY_MM');
    end_date := start_date + interval '1 month';
    
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I
                    FOR VALUES FROM (%L) TO (%L)',
                   partition_name, table_name, start_date, end_date);
    
    -- Create indexes on the new partition
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (source_id, published_at DESC)',
                   'idx_' || partition_name || '_source_published', partition_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I USING GIN (title_tsvector)',
                   'idx_' || partition_name || '_title_tsvector', partition_name);
END;
$$ LANGUAGE plpgsql;

-- Function to create partitions for the next 6 months
CREATE OR REPLACE FUNCTION setup_future_partitions()
RETURNS VOID AS $$
DECLARE
    current_month DATE;
    i INTEGER;
BEGIN
    current_month := date_trunc('month', CURRENT_DATE);
    
    FOR i IN 0..5 LOOP
        PERFORM create_monthly_partition('raw_articles', current_month + (i || ' months')::interval);
        PERFORM create_monthly_partition('narrative_daily_metrics', current_month + (i || ' months')::interval);
        PERFORM create_monthly_partition('narrative_timeline_events', current_month + (i || ' months')::interval);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Schedule this to run monthly
SELECT setup_future_partitions();

-- =============================================
-- PERFORMANCE OPTIMIZATION STRATEGIES
-- =============================================

-- 1. Connection Pooling Configuration (application level)
/*
Recommended PgBouncer configuration:
- pool_mode = transaction
- max_client_conn = 100
- default_pool_size = 25
- max_db_connections = 50
*/

-- 2. PostgreSQL Configuration Tuning
/*
Recommended postgresql.conf settings for narrative intelligence workload:

# Memory settings
shared_buffers = 4GB                    # 25% of RAM for dedicated server
work_mem = 256MB                        # For complex queries and sorts
maintenance_work_mem = 1GB              # For index creation and maintenance
effective_cache_size = 12GB             # 75% of RAM

# Query planner
random_page_cost = 1.1                  # For SSD storage
effective_io_concurrency = 200          # For SSD storage
seq_page_cost = 1.0

# WAL and checkpoints
wal_buffers = 64MB
checkpoint_completion_target = 0.9
checkpoint_timeout = 15min
max_wal_size = 2GB

# Parallel processing
max_parallel_workers = 8
max_parallel_workers_per_gather = 4
max_parallel_maintenance_workers = 4

# Vector extension settings (for embeddings)
vector.hnsw_ef_search = 100            # Search quality vs speed tradeoff
*/

-- 3. Materialized Views for Common Queries (Updated for Metrics Separation)
CREATE MATERIALIZED VIEW mv_narrative_trending_dashboard AS
SELECT 
    n.narrative_id,
    n.title,
    n.summary,
    m.trending_score,
    m.credibility_score,
    m.engagement_score,
    n.actor_origin,
    n.updated_at as last_updated_at,
    m.narrative_start_date,
    m.narrative_status,
    m.geographic_scope,
    m.keywords,
    
    -- Content-based metrics from NSF-1
    (n.source_stats->>'total_articles')::integer as total_articles,
    
    -- Aggregate metrics
    COALESCE(articles.article_count, 0) as recent_article_count,
    COALESCE(sources.source_diversity, 0) as source_diversity
    
FROM narratives n
JOIN narrative_metrics m ON n.id = m.narrative_uuid
LEFT JOIN (
    -- Recent article count in last 7 days
    SELECT 
        na.narrative_id,
        COUNT(DISTINCT na.article_id) as article_count
    FROM narrative_articles na
    JOIN raw_articles ra ON na.article_id = ra.article_id
    WHERE ra.published_at >= CURRENT_DATE - interval '7 days'
    GROUP BY na.narrative_id
) articles ON n.id = articles.narrative_id

LEFT JOIN (
    -- Source diversity metric
    SELECT 
        na.narrative_id,
        COUNT(DISTINCT ra.source_id)::decimal / NULLIF(COUNT(*), 0) as source_diversity
    FROM narrative_articles na
    JOIN raw_articles ra ON na.article_id = ra.article_id
    GROUP BY na.narrative_id
) sources ON n.id = sources.narrative_id

WHERE m.narrative_status = 'active';

-- Create indexes on materialized view
CREATE INDEX idx_mv_trending_dashboard_score ON mv_narrative_trending_dashboard 
    (trending_score DESC, last_updated_at DESC);
CREATE INDEX idx_mv_trending_dashboard_status ON mv_narrative_trending_dashboard 
    (narrative_status, trending_score DESC);
CREATE INDEX idx_mv_trending_dashboard_geographic ON mv_narrative_trending_dashboard 
    (geographic_scope, credibility_score DESC);

-- Refresh strategy for materialized view
CREATE OR REPLACE FUNCTION refresh_trending_dashboard()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_narrative_trending_dashboard;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- VECTOR EMBEDDING OPTIMIZATION
-- =============================================

-- Optimize vector indexes after bulk loading
CREATE OR REPLACE FUNCTION optimize_vector_indexes()
RETURNS VOID AS $$
BEGIN
    -- Rebuild vector indexes with optimal parameters after bulk loading
    DROP INDEX IF EXISTS idx_raw_articles_title_embedding;
    DROP INDEX IF EXISTS idx_raw_articles_content_embedding;
    DROP INDEX IF EXISTS idx_narratives_embedding;
    
    -- Recreate with optimized settings based on data size
    CREATE INDEX idx_raw_articles_title_embedding ON raw_articles 
        USING ivfflat (title_embedding vector_cosine_ops) 
        WITH (lists = GREATEST(LEAST((SELECT COUNT(*) FROM raw_articles) / 1000, 1000), 10));
        
    CREATE INDEX idx_raw_articles_content_embedding ON raw_articles 
        USING ivfflat (content_embedding vector_cosine_ops) 
        WITH (lists = GREATEST(LEAST((SELECT COUNT(*) FROM raw_articles) / 1000, 1000), 10));
        
    CREATE INDEX idx_narratives_embedding ON narratives 
        USING ivfflat (narrative_embedding vector_cosine_ops) 
        WITH (lists = GREATEST(LEAST((SELECT COUNT(*) FROM narratives) / 100, 100), 10));
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- DATA ARCHIVAL STRATEGY
-- =============================================

-- Function to archive old partitions
CREATE OR REPLACE FUNCTION archive_old_partitions(months_to_keep INTEGER DEFAULT 24)
RETURNS VOID AS $$
DECLARE
    partition_record RECORD;
    cutoff_date DATE;
BEGIN
    cutoff_date := date_trunc('month', CURRENT_DATE - (months_to_keep || ' months')::interval);
    
    -- Archive old article partitions
    FOR partition_record IN
        SELECT schemaname, tablename
        FROM pg_tables
        WHERE tablename LIKE 'raw_articles_%'
        AND tablename ~ '^raw_articles_\d{4}_\d{2}$'
        AND to_date(substring(tablename from 'raw_articles_(\d{4}_\d{2})'), 'YYYY_MM') < cutoff_date
    LOOP
        -- Move to archive schema or drop (depending on requirements)
        EXECUTE format('DROP TABLE IF EXISTS %I.%I CASCADE', 
                      partition_record.schemaname, partition_record.tablename);
        
        RAISE NOTICE 'Archived partition: %', partition_record.tablename;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- MONITORING AND MAINTENANCE
-- =============================================

-- Function to gather performance statistics
CREATE OR REPLACE FUNCTION get_narrative_db_stats()
RETURNS TABLE (
    table_name TEXT,
    row_count BIGINT,
    table_size TEXT,
    index_size TEXT,
    total_size TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.table_name::TEXT,
        t.row_count,
        pg_size_pretty(t.table_size) as table_size,
        pg_size_pretty(t.index_size) as index_size,
        pg_size_pretty(t.total_size) as total_size
    FROM (
        SELECT 
            schemaname||'.'||tablename as table_name,
            n_tup_ins + n_tup_upd + n_tup_del as row_count,
            pg_total_relation_size(schemaname||'.'||tablename) as total_size,
            pg_relation_size(schemaname||'.'||tablename) as table_size,
            pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename) as index_size
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
        AND tablename IN ('narratives', 'raw_articles', 'narrative_articles', 'narrative_daily_metrics')
        ORDER BY total_size DESC
    ) t;
END;
$$ LANGUAGE plpgsql;

-- Query to monitor slow queries
CREATE VIEW v_slow_narrative_queries AS
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements
WHERE query LIKE '%narratives%' OR query LIKE '%raw_articles%'
ORDER BY mean_time DESC;

-- =============================================
-- BACKUP AND RECOVERY STRATEGY
-- =============================================

/*
Recommended backup strategy:

1. Daily incremental backups using pg_dump or WAL-E/WAL-G
2. Weekly full backups
3. Point-in-time recovery capability
4. Cross-region backup replication for disaster recovery

Example backup commands:
# Full backup
pg_dump -h localhost -U postgres -d narrative_intelligence -F c -b -v -f "narrative_db_$(date +%Y%m%d).backup"

# Schema-only backup for version control
pg_dump -h localhost -U postgres -d narrative_intelligence -s -f "schema_$(date +%Y%m%d).sql"

# Specific table backup (for large tables)
pg_dump -h localhost -U postgres -d narrative_intelligence -t raw_articles -F c -f "articles_$(date +%Y%m%d).backup"
*/

-- =============================================
-- SECURITY CONSIDERATIONS
-- =============================================

-- Create read-only user for analytics
CREATE USER narrative_reader WITH PASSWORD 'secure_random_password';
GRANT CONNECT ON DATABASE narrative_intelligence TO narrative_reader;
GRANT USAGE ON SCHEMA public TO narrative_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO narrative_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO narrative_reader;

-- Create application user with limited permissions
CREATE USER narrative_app WITH PASSWORD 'secure_app_password';
GRANT CONNECT ON DATABASE narrative_intelligence TO narrative_app;
GRANT USAGE ON SCHEMA public TO narrative_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO narrative_app;
GRANT DELETE ON narrative_articles, narrative_actors_relation TO narrative_app; -- Limited delete permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO narrative_app;

-- Row Level Security (RLS) example for multi-tenant scenarios
-- ALTER TABLE narratives ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY narrative_tenant_policy ON narratives
--     FOR ALL TO narrative_app
--     USING (tenant_id = current_setting('app.tenant_id', true)::uuid);

-- =============================================
-- PERFORMANCE TESTING QUERIES
-- =============================================

/*
-- Test query performance for main dashboard
EXPLAIN ANALYZE
SELECT * FROM mv_narrative_trending_dashboard
ORDER BY trending_score DESC
LIMIT 20;

-- Test semantic search performance
EXPLAIN ANALYZE
SELECT narrative_id, title, narrative_embedding <=> $1::vector as distance
FROM narratives
WHERE narrative_embedding <=> $1::vector < 0.3
ORDER BY distance
LIMIT 50;

-- Test article ingestion performance
EXPLAIN ANALYZE
INSERT INTO raw_articles (source_id, title, content, published_at, language_code)
SELECT 
    (SELECT source_id FROM news_sources LIMIT 1),
    'Test Article ' || generate_series,
    'Test content for article ' || generate_series,
    CURRENT_TIMESTAMP - (generate_series || ' minutes')::interval,
    'en'
FROM generate_series(1, 1000);
*/