-- Strategic Narrative Intelligence Platform - PostgreSQL Database Schema
-- CANONICAL SOURCE OF TRUTH - Complete production schema with partitioning and performance optimizations
-- This schema implements the NSF-1 format for narrative intelligence
-- 
-- NOTE: This is the official schema file. ~nsf1_corrected_schema.sql has been archived as a duplicate.

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector"; -- For pgvector extension
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search optimization
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For composite indexes

-- =============================================
-- CORE DOMAIN TABLES
-- =============================================

-- News sources and feeds configuration
CREATE TABLE news_sources (
    source_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(255) NOT NULL,
    source_url TEXT NOT NULL,
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('rss', 'api', 'scraper', 'manual')),
    country_code CHAR(2),
    language_code CHAR(2) NOT NULL,
    political_alignment VARCHAR(50),
    credibility_score DECIMAL(3,2) CHECK (credibility_score >= 0.0 AND credibility_score <= 10.0),
    update_frequency_minutes INTEGER DEFAULT 60,
    is_active BOOLEAN DEFAULT true,
    last_crawled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_source_url UNIQUE (source_url)
);

-- Raw articles from news feeds (partitioned by date)
CREATE TABLE raw_articles (
    article_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL REFERENCES news_sources(source_id),
    external_id VARCHAR(255), -- Original article ID from source
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    author VARCHAR(255),
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    url TEXT,
    language_code CHAR(2) NOT NULL,
    
    -- Article metadata
    word_count INTEGER,
    sentiment_score DECIMAL(3,2) CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0),
    
    -- Vector embeddings for semantic similarity
    title_embedding vector(1536), -- OpenAI ada-002 dimensions
    content_embedding vector(1536),
    
    -- Full-text search vectors
    title_tsvector tsvector GENERATED ALWAYS AS (to_tsvector('english', title)) STORED,
    content_tsvector tsvector GENERATED ALWAYS AS (to_tsvector('english', COALESCE(content, ''))) STORED,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (published_at);

-- Create partitions for raw_articles (monthly partitions for 2 years)
CREATE TABLE raw_articles_2024_01 PARTITION OF raw_articles
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE raw_articles_2024_02 PARTITION OF raw_articles
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
CREATE TABLE raw_articles_2024_03 PARTITION OF raw_articles
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');
CREATE TABLE raw_articles_2024_04 PARTITION OF raw_articles
    FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');
CREATE TABLE raw_articles_2024_05 PARTITION OF raw_articles
    FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');
CREATE TABLE raw_articles_2024_06 PARTITION OF raw_articles
    FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');
CREATE TABLE raw_articles_2024_07 PARTITION OF raw_articles
    FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');
CREATE TABLE raw_articles_2024_08 PARTITION OF raw_articles
    FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');
CREATE TABLE raw_articles_2024_09 PARTITION OF raw_articles
    FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');
CREATE TABLE raw_articles_2024_10 PARTITION OF raw_articles
    FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');
CREATE TABLE raw_articles_2024_11 PARTITION OF raw_articles
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');
CREATE TABLE raw_articles_2024_12 PARTITION OF raw_articles
    FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');
CREATE TABLE raw_articles_2025_01 PARTITION OF raw_articles
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE raw_articles_2025_02 PARTITION OF raw_articles
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
CREATE TABLE raw_articles_2025_03 PARTITION OF raw_articles
    FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');
CREATE TABLE raw_articles_2025_04 PARTITION OF raw_articles
    FOR VALUES FROM ('2025-04-01') TO ('2025-05-01');
CREATE TABLE raw_articles_2025_05 PARTITION OF raw_articles
    FOR VALUES FROM ('2025-05-01') TO ('2025-06-01');
CREATE TABLE raw_articles_2025_06 PARTITION OF raw_articles
    FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');
CREATE TABLE raw_articles_2025_07 PARTITION OF raw_articles
    FOR VALUES FROM ('2025-07-01') TO ('2025-08-01');
CREATE TABLE raw_articles_2025_08 PARTITION OF raw_articles
    FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');
CREATE TABLE raw_articles_2025_09 PARTITION OF raw_articles
    FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');
CREATE TABLE raw_articles_2025_10 PARTITION OF raw_articles
    FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
CREATE TABLE raw_articles_2025_11 PARTITION OF raw_articles
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
CREATE TABLE raw_articles_2025_12 PARTITION OF raw_articles
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- =============================================
-- NSF-1 NARRATIVE SCHEMA - CORRECTED TO MATCH SPECIFICATION
-- =============================================

-- Main narratives table implementing exact NSF-1 schema
CREATE TABLE narratives (
    -- PRIMARY KEY - UUID for internal use
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- DISPLAY ID - Used by API and frontend (e.g., "EN-002-A")
    narrative_id VARCHAR(50) NOT NULL UNIQUE,
    
    -- CORE NSF-1 FIELDS (exact match to specification)
    title VARCHAR(500) NOT NULL,
    summary TEXT NOT NULL,
    origin_language CHAR(2) NOT NULL,
    
    -- ARRAY FIELDS - stored as JSONB arrays for PostgreSQL
    dominant_source_languages JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of language codes
    alignment JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of alignment strings
    actor_origin JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of actor origins
    conflict_alignment JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of conflict alignments
    frame_logic JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of logic strings
    nested_within JSONB DEFAULT '[]'::jsonb, -- Array of parent narrative IDs
    conflicts_with JSONB DEFAULT '[]'::jsonb, -- Array of conflicting narrative IDs  
    logical_strain JSONB DEFAULT '[]'::jsonb, -- Array of strain descriptions
    
    -- STRUCTURED OBJECT FIELDS
    narrative_tension JSONB DEFAULT '[]'::jsonb, -- Array of {type, description} objects
    activity_timeline JSONB DEFAULT '{}'::jsonb, -- Object with date keys and event descriptions
    turning_points JSONB DEFAULT '[]'::jsonb, -- Array of {date, description} objects
    media_spike_history JSONB DEFAULT '{}'::jsonb, -- Object with date keys and count values
    source_stats JSONB DEFAULT '{}'::jsonb, -- Object with total_articles and sources breakdown
    top_excerpts JSONB DEFAULT '[]'::jsonb, -- Array of {source, language, original, translated} objects
    
    -- UPDATE STATUS OBJECT
    update_status JSONB DEFAULT '{}'::jsonb, -- Object with {last_updated, update_trigger}
    
    -- QUALITY AND CONFIDENCE
    confidence_rating VARCHAR(20) CHECK (confidence_rating IN ('low', 'medium', 'high', 'very_high')),
    data_quality_notes TEXT,
    
    -- VERSION HISTORY
    version_history JSONB DEFAULT '[]'::jsonb, -- Array of {version, date, change} objects
    
    -- RAI ANALYSIS - Complex structured object
    rai_analysis JSONB DEFAULT '{}'::jsonb, -- Object with adequacy_score, final_synthesis, key_conflicts, blind_spots, radical_shifts, last_analyzed
    
    -- SEARCH AND PERFORMANCE FIELDS
    narrative_embedding vector(1536), -- For semantic similarity
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', title || ' ' || summary)
    ) STORED,
    
    -- METADATA
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- JSON SCHEMA VALIDATION CONSTRAINTS
-- =============================================

-- Validate array fields are arrays
ALTER TABLE narratives ADD CONSTRAINT valid_dominant_source_languages 
    CHECK (jsonb_typeof(dominant_source_languages) = 'array');

ALTER TABLE narratives ADD CONSTRAINT valid_alignment 
    CHECK (jsonb_typeof(alignment) = 'array');

ALTER TABLE narratives ADD CONSTRAINT valid_actor_origin 
    CHECK (jsonb_typeof(actor_origin) = 'array');

ALTER TABLE narratives ADD CONSTRAINT valid_conflict_alignment 
    CHECK (jsonb_typeof(conflict_alignment) = 'array');

ALTER TABLE narratives ADD CONSTRAINT valid_frame_logic 
    CHECK (jsonb_typeof(frame_logic) = 'array');

ALTER TABLE narratives ADD CONSTRAINT valid_nested_within 
    CHECK (jsonb_typeof(nested_within) = 'array');

ALTER TABLE narratives ADD CONSTRAINT valid_conflicts_with 
    CHECK (jsonb_typeof(conflicts_with) = 'array');

ALTER TABLE narratives ADD CONSTRAINT valid_logical_strain 
    CHECK (jsonb_typeof(logical_strain) = 'array');

ALTER TABLE narratives ADD CONSTRAINT valid_narrative_tension 
    CHECK (jsonb_typeof(narrative_tension) = 'array');

ALTER TABLE narratives ADD CONSTRAINT valid_turning_points 
    CHECK (jsonb_typeof(turning_points) = 'array');

ALTER TABLE narratives ADD CONSTRAINT valid_top_excerpts 
    CHECK (jsonb_typeof(top_excerpts) = 'array');

ALTER TABLE narratives ADD CONSTRAINT valid_version_history 
    CHECK (jsonb_typeof(version_history) = 'array');

-- Validate object fields are objects
ALTER TABLE narratives ADD CONSTRAINT valid_activity_timeline 
    CHECK (jsonb_typeof(activity_timeline) = 'object');

ALTER TABLE narratives ADD CONSTRAINT valid_media_spike_history 
    CHECK (jsonb_typeof(media_spike_history) = 'object');

ALTER TABLE narratives ADD CONSTRAINT valid_source_stats 
    CHECK (jsonb_typeof(source_stats) = 'object');

ALTER TABLE narratives ADD CONSTRAINT valid_update_status 
    CHECK (jsonb_typeof(update_status) = 'object');

ALTER TABLE narratives ADD CONSTRAINT valid_rai_analysis 
    CHECK (jsonb_typeof(rai_analysis) = 'object');

-- =============================================
-- NARRATIVE METRICS TABLE (SEPARATE FROM NSF-1 CONTENT)
-- =============================================

-- narrative_metrics table stores all analytics and scoring data
-- NSF-1 JSON in narratives table stores narrative content only
CREATE TABLE narrative_metrics (
    -- Foreign key to narratives table (UUID primary key)
    narrative_uuid UUID PRIMARY KEY REFERENCES narratives(id) ON DELETE CASCADE,
    
    -- TEMPORAL FIELDS
    narrative_start_date TIMESTAMP WITH TIME ZONE,
    narrative_end_date TIMESTAMP WITH TIME ZONE,
    last_spike TIMESTAMP WITH TIME ZONE,
    
    -- SCORING FIELDS
    trending_score NUMERIC DEFAULT 0.0 CHECK (trending_score >= 0),
    credibility_score NUMERIC CHECK (credibility_score >= 0.0 AND credibility_score <= 10.0),
    engagement_score NUMERIC CHECK (engagement_score >= 0.0 AND engagement_score <= 1.0),
    sentiment_score NUMERIC CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0),
    
    -- PRIORITY AND STATUS
    narrative_priority INTEGER DEFAULT 5 CHECK (narrative_priority >= 1 AND narrative_priority <= 10),
    narrative_status TEXT DEFAULT 'active' CHECK (narrative_status IN ('active', 'emerging', 'declining', 'dormant', 'archived')),
    
    -- METADATA
    geographic_scope TEXT, -- e.g., 'global', 'europe', 'us-domestic'
    update_frequency INTERVAL DEFAULT '15 minutes',
    version_number INTEGER DEFAULT 1,
    
    -- KEYWORDS FOR QUICK FILTERING
    keywords TEXT[], -- Simple array of core tags for filtering and search
    
    -- TIMESTAMPS
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- CONSTRAINTS
    CONSTRAINT chk_narrative_metrics_dates CHECK (
        narrative_start_date IS NULL OR narrative_end_date IS NULL OR narrative_start_date <= narrative_end_date
    )
);

-- =============================================
-- RELATIONSHIP TABLES
-- =============================================

-- Link articles to narratives (many-to-many)
CREATE TABLE narrative_articles (
    narrative_id UUID NOT NULL REFERENCES narratives(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES raw_articles(article_id) ON DELETE CASCADE,
    relevance_score DECIMAL(3,2) NOT NULL DEFAULT 0.5 
        CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(50) DEFAULT 'auto', -- 'auto' or 'manual'
    
    PRIMARY KEY (narrative_id, article_id)
);

-- =============================================
-- PERFORMANCE INDEXES
-- =============================================

-- News sources indexes
CREATE INDEX idx_news_sources_active ON news_sources (is_active, last_crawled_at);
CREATE INDEX idx_news_sources_country_lang ON news_sources (country_code, language_code);

-- Raw articles indexes
CREATE INDEX idx_raw_articles_source_published ON raw_articles (source_id, published_at DESC);
CREATE INDEX idx_raw_articles_language_published ON raw_articles (language_code, published_at DESC);
CREATE INDEX idx_raw_articles_title_tsvector ON raw_articles USING GIN (title_tsvector);
CREATE INDEX idx_raw_articles_content_tsvector ON raw_articles USING GIN (content_tsvector);
CREATE INDEX idx_raw_articles_title_embedding ON raw_articles USING ivfflat (title_embedding vector_cosine_ops);
CREATE INDEX idx_raw_articles_content_embedding ON raw_articles USING ivfflat (content_embedding vector_cosine_ops);

-- Core narrative indexes
CREATE INDEX idx_narratives_origin_language ON narratives (origin_language);
CREATE INDEX idx_narratives_confidence ON narratives (confidence_rating);
CREATE INDEX idx_narratives_created ON narratives (created_at DESC);
CREATE INDEX idx_narratives_updated ON narratives (updated_at DESC);

-- Full-text search
CREATE INDEX idx_narratives_search_vector ON narratives USING GIN (search_vector);

-- Vector similarity search
CREATE INDEX idx_narratives_embedding ON narratives USING ivfflat (narrative_embedding vector_cosine_ops);

-- JSONB field indexes for common queries
CREATE INDEX idx_narratives_alignment_gin ON narratives USING GIN (alignment);
CREATE INDEX idx_narratives_actor_origin_gin ON narratives USING GIN (actor_origin);
CREATE INDEX idx_narratives_frame_logic_gin ON narratives USING GIN (frame_logic);
CREATE INDEX idx_narratives_nested_within_gin ON narratives USING GIN (nested_within);
CREATE INDEX idx_narratives_conflicts_with_gin ON narratives USING GIN (conflicts_with);
CREATE INDEX idx_narratives_dominant_source_languages_gin ON narratives USING GIN (dominant_source_languages);
CREATE INDEX idx_narratives_conflict_alignment_gin ON narratives USING GIN (conflict_alignment);

-- Narrative metrics indexes (for dashboard and trending queries)
CREATE INDEX idx_narrative_metrics_trending_score ON narrative_metrics (trending_score DESC);
CREATE INDEX idx_narrative_metrics_status ON narrative_metrics (narrative_status);
CREATE INDEX idx_narrative_metrics_priority ON narrative_metrics (narrative_priority);
CREATE INDEX idx_narrative_metrics_credibility ON narrative_metrics (credibility_score DESC);
CREATE INDEX idx_narrative_metrics_engagement ON narrative_metrics (engagement_score DESC);
CREATE INDEX idx_narrative_metrics_start_date ON narrative_metrics (narrative_start_date DESC);
CREATE INDEX idx_narrative_metrics_keywords ON narrative_metrics USING GIN (keywords);
CREATE INDEX idx_narrative_metrics_geographic_scope ON narrative_metrics (geographic_scope);

-- Composite indexes for common dashboard queries
CREATE INDEX idx_narrative_metrics_status_trending ON narrative_metrics (narrative_status, trending_score DESC);
CREATE INDEX idx_narrative_metrics_active_priority ON narrative_metrics (narrative_status, narrative_priority) WHERE narrative_status = 'active';

-- Relationship indexes
CREATE INDEX idx_narrative_articles_narrative_id ON narrative_articles (narrative_id);
CREATE INDEX idx_narrative_articles_article_id ON narrative_articles (article_id);
CREATE INDEX idx_narrative_articles_relevance ON narrative_articles (narrative_id, relevance_score DESC);

-- =============================================
-- FUNCTIONS AND TRIGGERS
-- =============================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply the trigger to relevant tables
CREATE TRIGGER update_news_sources_updated_at BEFORE UPDATE ON news_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_raw_articles_updated_at BEFORE UPDATE ON raw_articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_narratives_updated_at BEFORE UPDATE ON narratives
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_narrative_metrics_updated_at BEFORE UPDATE ON narrative_metrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- SAMPLE NSF-1 DATA INSERTION
-- =============================================

-- Insert the example narrative from the specification
INSERT INTO narratives (
    narrative_id,
    title,
    summary,
    origin_language,
    dominant_source_languages,
    alignment,
    actor_origin,
    conflict_alignment,
    frame_logic,
    narrative_tension,
    nested_within,
    conflicts_with,
    activity_timeline,
    turning_points,
    logical_strain,
    media_spike_history,
    source_stats,
    top_excerpts,
    update_status,
    confidence_rating,
    data_quality_notes,
    version_history,
    rai_analysis
) VALUES (
    'EN-002-A',
    'Energy Independence as Security Strategy',
    'Brief framing of narrative, 2-3 sentences.',
    'en',
    '["en", "de", "fr"]'::jsonb,
    '["Western governments", "EU policy"]'::jsonb,
    '["EU Commission", "U.S. energy agencies"]'::jsonb,
    '["Europe vs Supplier Dependence"]'::jsonb,
    '["Reducing import reliance increases security", "Green transition framed as sovereignty defense"]'::jsonb,
    '[
        {"type": "Internal", "description": "Green goals vs temporary fossil fuel expansion"},
        {"type": "External", "description": "Critics argue U.S. LNG dependence contradicts autonomy narrative"}
    ]'::jsonb,
    '["EN-CORE-001"]'::jsonb,
    '["EN-004"]'::jsonb,
    '{"2025-Q3": "Narrative spike after EU energy summit"}'::jsonb,
    '[{"date": "2025-07-15", "description": "Framing shift: renewables as autonomy"}]'::jsonb,
    '["Claim of independence vs rising LNG imports", "Security framing vs energy cost protests"]'::jsonb,
    '{"2025-07": 42}'::jsonb,
    '{
        "total_articles": 42,
        "sources": {
            "Reuters": 14,
            "Politico EU": 10,
            "Tagesschau": 7,
            "Bloomberg": 6,
            "Le Monde": 5
        }
    }'::jsonb,
    '[
        {
            "source": "Politico EU",
            "language": "en",
            "original": "Energy policy is now defense policy — Europe must act accordingly.",
            "translated": null
        },
        {
            "source": "Tagesschau",
            "language": "de",
            "original": "Neue Gasterminals sind notwendig, um unsere Unabhängigkeit zu sichern.",
            "translated": "New gas terminals are necessary to secure our independence."
        }
    ]'::jsonb,
    '{
        "last_updated": "2025-07-22",
        "update_trigger": "EU summit announcement and media spike"
    }'::jsonb,
    'high',
    'Based on 42 articles from 5 sources; alignment consistent.',
    '[
        {
            "version": "1.0",
            "date": "2025-07-22",
            "change": "Initial narrative entry created"
        }
    ]'::jsonb,
    '{
        "adequacy_score": 0.74,
        "final_synthesis": "Overall, the narrative presents a coherent framing of energy independence as security strategy, though blind spots remain around rare earth dependencies and economic trade-offs.",
        "key_conflicts": [
            "Narrative claims victory yet reports rising energy imports",
            "Shift from climate to security framing not explicitly acknowledged"
        ],
        "blind_spots": [
            "No acknowledgment of rare earth dependency in independence framing"
        ],
        "radical_shifts": [
            {
                "date": "2025-08-01",
                "description": "Pivot from renewables as climate policy to renewables as defense policy"
            }
        ],
        "last_analyzed": "2025-08-01"
    }'::jsonb
);

-- Insert corresponding metrics for the sample narrative
INSERT INTO narrative_metrics (
    narrative_uuid,
    narrative_start_date,
    narrative_end_date,
    trending_score,
    credibility_score,
    engagement_score,
    sentiment_score,
    narrative_priority,
    narrative_status,
    geographic_scope,
    update_frequency,
    version_number,
    keywords
) VALUES (
    (SELECT id FROM narratives WHERE narrative_id = 'EN-002-A'),
    '2025-07-01 00:00:00+00'::timestamp with time zone,
    NULL, -- Ongoing narrative
    8.5, -- High trending score
    7.2, -- Good credibility
    0.74, -- From RAI analysis adequacy score
    0.15, -- Slightly positive sentiment
    2, -- High priority (1-10 scale, lower = higher priority)
    'active',
    'europe',
    '15 minutes'::interval,
    1,
    ARRAY['energy', 'independence', 'security', 'EU', 'renewables', 'autonomy']
);

-- =============================================
-- MIGRATION STRATEGY - BACKFILL EXISTING NARRATIVES
-- =============================================

-- Function to backfill narrative_metrics for existing narratives
CREATE OR REPLACE FUNCTION backfill_narrative_metrics()
RETURNS void AS $$
BEGIN
    INSERT INTO narrative_metrics (narrative_uuid)
    SELECT id FROM narratives
    WHERE id NOT IN (SELECT narrative_uuid FROM narrative_metrics)
    ON CONFLICT (narrative_uuid) DO NOTHING;
    
    RAISE NOTICE 'Backfilled narrative_metrics for % narratives', 
        (SELECT COUNT(*) FROM narratives WHERE id NOT IN (SELECT narrative_uuid FROM narrative_metrics WHERE narrative_uuid IS NOT NULL));
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- SAMPLE QUERIES FOR NSF-1 DATA WITH METRICS SEPARATION
-- =============================================

/*
-- Query 1: Get trending narratives for dashboard (using metrics table)
SELECT n.narrative_id, n.title, n.summary, m.trending_score, m.narrative_status, m.credibility_score
FROM narratives n
JOIN narrative_metrics m ON n.id = m.narrative_uuid
WHERE m.narrative_status = 'active'
ORDER BY m.trending_score DESC, m.credibility_score DESC
LIMIT 20;

-- Query 2: Find narratives by alignment and high credibility
SELECT n.narrative_id, n.title, n.alignment, m.credibility_score, m.engagement_score
FROM narratives n
JOIN narrative_metrics m ON n.id = m.narrative_uuid
WHERE n.alignment @> '["EU policy"]'::jsonb 
  AND m.credibility_score >= 7.0
ORDER BY m.credibility_score DESC;

-- Query 3: Get narratives that conflict with specific narrative
SELECT n.narrative_id, n.title, m.trending_score, m.narrative_status
FROM narratives n
JOIN narrative_metrics m ON n.id = m.narrative_uuid
WHERE n.conflicts_with @> '["EN-004"]'::jsonb
  AND m.narrative_status IN ('active', 'emerging')
ORDER BY m.trending_score DESC;

-- Query 4: Search by keywords and geographic scope
SELECT n.narrative_id, n.title, m.keywords, m.geographic_scope, m.trending_score
FROM narratives n
JOIN narrative_metrics m ON n.id = m.narrative_uuid
WHERE m.keywords && ARRAY['energy', 'security']
  AND m.geographic_scope = 'europe'
  AND m.narrative_status = 'active'
ORDER BY m.trending_score DESC;

-- Query 5: Get high-priority active narratives with recent activity
SELECT n.narrative_id, n.title, m.narrative_priority, m.last_spike, m.trending_score
FROM narratives n
JOIN narrative_metrics m ON n.id = m.narrative_uuid
WHERE m.narrative_status = 'active'
  AND m.narrative_priority <= 3
  AND m.last_spike >= NOW() - INTERVAL '7 days'
ORDER BY m.narrative_priority, m.trending_score DESC;

-- Query 6: Find narratives with high RAI analysis scores and good credibility
SELECT n.narrative_id, n.title, 
       (n.rai_analysis->>'adequacy_score')::numeric as rai_score,
       m.credibility_score, m.engagement_score
FROM narratives n
JOIN narrative_metrics m ON n.id = m.narrative_uuid
WHERE (n.rai_analysis->>'adequacy_score')::numeric >= 0.7
  AND m.credibility_score >= 6.0
ORDER BY (n.rai_analysis->>'adequacy_score')::numeric DESC, m.credibility_score DESC;

-- Query 7: Get narratives by time range and sentiment
SELECT n.narrative_id, n.title, m.narrative_start_date, m.sentiment_score, m.trending_score
FROM narratives n
JOIN narrative_metrics m ON n.id = m.narrative_uuid
WHERE m.narrative_start_date >= '2025-07-01'
  AND m.narrative_start_date <= '2025-08-01'
  AND m.sentiment_score IS NOT NULL
ORDER BY m.narrative_start_date DESC;

-- Query 8: Complex dashboard query - trending with content analysis
SELECT 
    n.narrative_id,
    n.title,
    n.alignment,
    n.frame_logic,
    m.trending_score,
    m.credibility_score,
    m.engagement_score,
    m.narrative_priority,
    m.keywords,
    (n.source_stats->>'total_articles')::integer as article_count,
    (n.rai_analysis->>'adequacy_score')::numeric as rai_adequacy
FROM narratives n
JOIN narrative_metrics m ON n.id = m.narrative_uuid
WHERE m.narrative_status = 'active'
  AND m.trending_score >= 5.0
  AND m.credibility_score >= 6.0
ORDER BY m.trending_score DESC, m.credibility_score DESC
LIMIT 10;

-- Query 9: Find related narratives (same keywords, different alignment)
SELECT 
    n1.narrative_id as source_narrative,
    n1.title as source_title,
    n1.alignment as source_alignment,
    n2.narrative_id as related_narrative,
    n2.title as related_title,
    n2.alignment as related_alignment,
    m1.keywords as shared_keywords
FROM narratives n1
JOIN narrative_metrics m1 ON n1.id = m1.narrative_uuid
JOIN narrative_metrics m2 ON m1.keywords && m2.keywords
JOIN narratives n2 ON n2.id = m2.narrative_uuid
WHERE n1.id != n2.id
  AND NOT (n1.alignment @> n2.alignment OR n2.alignment @> n1.alignment)
  AND m1.narrative_status = 'active'
  AND m2.narrative_status = 'active'
ORDER BY n1.narrative_id;

-- Query 10: Migration validation - ensure all narratives have metrics
SELECT 
    COUNT(n.id) as total_narratives,
    COUNT(m.narrative_uuid) as narratives_with_metrics,
    COUNT(n.id) - COUNT(m.narrative_uuid) as missing_metrics
FROM narratives n
LEFT JOIN narrative_metrics m ON n.id = m.narrative_uuid;
*/