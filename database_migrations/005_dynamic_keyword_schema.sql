-- Dynamic Keyword Discovery Schema Migration
-- Strategic Narrative Intelligence Platform
-- Migration 005: Data-driven keyword extraction and lifecycle management

-- Core keywords table - dynamically discovered from content
CREATE TABLE keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword TEXT NOT NULL UNIQUE,
    keyword_type TEXT NOT NULL CHECK (keyword_type IN ('entity', 'phrase', 'keyphrase')),
    entity_label TEXT, -- For entities: PERSON, ORG, GPE, EVENT, etc.
    
    -- Strategic scoring (learned dynamically)
    strategic_score FLOAT NOT NULL DEFAULT 0.0,
    base_frequency INTEGER NOT NULL DEFAULT 0, -- Total appearances across all articles
    recent_frequency INTEGER NOT NULL DEFAULT 0, -- Appearances in last 30 days
    
    -- Lifecycle management
    first_seen TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    lifecycle_stage TEXT NOT NULL DEFAULT 'active' CHECK (lifecycle_stage IN ('active', 'warm', 'cold', 'archived')),
    
    -- Trend detection
    trending_score FLOAT NOT NULL DEFAULT 0.0, -- Spike detection multiplier
    peak_frequency INTEGER NOT NULL DEFAULT 0, -- Highest frequency in any 7-day window
    peak_date TIMESTAMP WITHOUT TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Article-keyword relationships with dynamic scoring
CREATE TABLE article_keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    keyword_id UUID NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
    
    -- Extraction metadata
    extraction_method TEXT NOT NULL CHECK (extraction_method IN ('spacy', 'yake', 'keybert', 'combined')),
    extraction_score FLOAT NOT NULL DEFAULT 0.0, -- Raw extraction confidence
    strategic_score FLOAT NOT NULL DEFAULT 0.0, -- Calculated strategic relevance
    keyword_rank INTEGER NOT NULL, -- Importance rank within article
    
    -- Context information
    appears_in_title BOOLEAN NOT NULL DEFAULT FALSE,
    appears_in_summary BOOLEAN NOT NULL DEFAULT FALSE,
    position_importance FLOAT NOT NULL DEFAULT 0.0,
    
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Ensure unique keyword per article
    UNIQUE(article_id, keyword_id)
);

-- Keyword trend tracking for spike detection
CREATE TABLE keyword_trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword_id UUID NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    daily_frequency INTEGER NOT NULL DEFAULT 0,
    spike_factor FLOAT NOT NULL DEFAULT 1.0, -- Multiplier vs baseline frequency
    baseline_frequency FLOAT NOT NULL DEFAULT 0.0, -- 7-day rolling average
    
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Ensure one record per keyword per day
    UNIQUE(keyword_id, date)
);

-- Keyword co-occurrence patterns for clustering
CREATE TABLE keyword_cooccurrence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword1_id UUID NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
    keyword2_id UUID NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
    
    cooccurrence_count INTEGER NOT NULL DEFAULT 1,
    cooccurrence_score FLOAT NOT NULL DEFAULT 0.0, -- Normalized co-occurrence strength
    
    first_seen TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Prevent duplicate pairs and self-references
    CHECK (keyword1_id != keyword2_id),
    UNIQUE(keyword1_id, keyword2_id)
);

-- Indexes for performance
CREATE INDEX idx_keywords_strategic_score ON keywords (strategic_score DESC);
CREATE INDEX idx_keywords_frequency ON keywords (base_frequency DESC);
CREATE INDEX idx_keywords_recent_frequency ON keywords (recent_frequency DESC);
CREATE INDEX idx_keywords_trending ON keywords (trending_score DESC);
CREATE INDEX idx_keywords_lifecycle ON keywords (lifecycle_stage, last_seen);
CREATE INDEX idx_keywords_type ON keywords (keyword_type);
CREATE INDEX idx_keywords_entity_label ON keywords (entity_label) WHERE entity_label IS NOT NULL;

CREATE INDEX idx_article_keywords_article ON article_keywords (article_id);
CREATE INDEX idx_article_keywords_keyword ON article_keywords (keyword_id);
CREATE INDEX idx_article_keywords_strategic_score ON article_keywords (strategic_score DESC);
CREATE INDEX idx_article_keywords_rank ON article_keywords (keyword_rank);
CREATE INDEX idx_article_keywords_method ON article_keywords (extraction_method);

CREATE INDEX idx_keyword_trends_date ON keyword_trends (date DESC);
CREATE INDEX idx_keyword_trends_spike ON keyword_trends (spike_factor DESC);
CREATE INDEX idx_keyword_trends_keyword_date ON keyword_trends (keyword_id, date DESC);

CREATE INDEX idx_keyword_cooccurrence_score ON keyword_cooccurrence (cooccurrence_score DESC);
CREATE INDEX idx_keyword_cooccurrence_count ON keyword_cooccurrence (cooccurrence_count DESC);

-- Functions for keyword lifecycle management
CREATE OR REPLACE FUNCTION update_keyword_lifecycle()
RETURNS TRIGGER AS $$
BEGIN
    -- Update lifecycle stage based on last_seen
    IF NEW.last_seen < NOW() - INTERVAL '365 days' THEN
        NEW.lifecycle_stage = 'archived';
    ELSIF NEW.last_seen < NOW() - INTERVAL '30 days' THEN
        IF NEW.strategic_score > 0.7 THEN
            NEW.lifecycle_stage = 'warm'; -- Keep important keywords longer
        ELSE
            NEW.lifecycle_stage = 'cold';
        END IF;
    ELSE
        NEW.lifecycle_stage = 'active';
    END IF;
    
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic lifecycle management
CREATE TRIGGER trigger_keyword_lifecycle
    BEFORE UPDATE ON keywords
    FOR EACH ROW
    EXECUTE FUNCTION update_keyword_lifecycle();

-- Function to calculate trending scores
CREATE OR REPLACE FUNCTION calculate_trending_score(
    current_frequency INTEGER,
    baseline_frequency FLOAT
) RETURNS FLOAT AS $$
BEGIN
    -- Spike detection: current vs baseline
    IF baseline_frequency > 0 THEN
        RETURN current_frequency / baseline_frequency;
    ELSIF current_frequency > 0 THEN
        RETURN 2.0; -- New keywords get moderate trending score
    ELSE
        RETURN 1.0; -- Baseline
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Views for common queries
CREATE VIEW strategic_keywords AS
SELECT 
    k.*,
    ak_stats.article_count,
    ak_stats.avg_strategic_score
FROM keywords k
LEFT JOIN (
    SELECT 
        keyword_id,
        COUNT(*) as article_count,
        AVG(strategic_score) as avg_strategic_score
    FROM article_keywords
    GROUP BY keyword_id
) ak_stats ON k.id = ak_stats.keyword_id
WHERE k.strategic_score > 0.5
ORDER BY k.strategic_score DESC;

CREATE VIEW trending_keywords AS
SELECT 
    k.*,
    kt.spike_factor,
    kt.daily_frequency as recent_frequency,
    kt.date as trend_date
FROM keywords k
JOIN keyword_trends kt ON k.id = kt.keyword_id
WHERE kt.date >= CURRENT_DATE - INTERVAL '7 days'
  AND kt.spike_factor > 1.5
ORDER BY kt.spike_factor DESC;

-- Comments for documentation
COMMENT ON TABLE keywords IS 'Dynamically discovered keywords with no predefined lists';
COMMENT ON TABLE article_keywords IS 'Keywords extracted from articles with context and scoring';
COMMENT ON TABLE keyword_trends IS 'Daily trend tracking for spike detection';
COMMENT ON TABLE keyword_cooccurrence IS 'Co-occurrence patterns for keyword-based clustering';

COMMENT ON COLUMN keywords.strategic_score IS 'Dynamic strategic relevance score (0.0-1.0) learned from data';
COMMENT ON COLUMN keywords.lifecycle_stage IS 'Automatic lifecycle: active (30d) -> warm (1y) -> cold -> archived';
COMMENT ON COLUMN keywords.trending_score IS 'Spike detection multiplier vs baseline frequency';
COMMENT ON COLUMN article_keywords.position_importance IS 'Importance based on position in title/summary/body';

-- Migration verification query
/*
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('keywords', 'article_keywords', 'keyword_trends', 'keyword_cooccurrence')
ORDER BY table_name, ordinal_position;

-- Test keyword lifecycle stages
SELECT lifecycle_stage, COUNT(*) 
FROM keywords 
GROUP BY lifecycle_stage;
*/