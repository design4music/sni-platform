-- SNI-v2 Database Schema: Title-Only Multilingual
-- Uses v2_ prefix to coexist with existing SNI tables

-- Core feed management (simplified)
CREATE TABLE v2_feeds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL UNIQUE,
    language_code VARCHAR(5) NOT NULL,  -- 'en', 'de', 'fr', 'es', etc.
    country_code VARCHAR(3),            -- 'US', 'DE', 'FR', etc.
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 1,
    fetch_interval_minutes INTEGER DEFAULT 60,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Title-only articles (massively simplified)
CREATE TABLE v2_titles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feed_id UUID REFERENCES v2_feeds(id),
    
    -- Core content
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    published_at TIMESTAMP,
    
    -- Language processing
    detected_language VARCHAR(5),      -- Auto-detected language
    language_confidence FLOAT,         -- Detection confidence
    
    -- Strategic filtering
    is_strategic BOOLEAN,
    strategic_confidence FLOAT,
    strategic_signals JSONB,           -- Strategic indicators found
    
    -- Entities (multilingual)
    entities JSONB,                    -- Extracted entities
    entity_count INTEGER DEFAULT 0,
    
    -- Embeddings (using pgvector)
    title_embedding VECTOR(384),       -- all-MiniLM-L6-v2 embeddings
    
    -- Processing status
    processing_status VARCHAR(20) DEFAULT 'pending',  -- pending/completed/failed
    processed_at TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(url, feed_id)  -- Prevent duplicates per feed
);

-- Multilingual clusters (CLUST-2)
CREATE TABLE v2_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Cluster metadata
    cluster_key VARCHAR(64) NOT NULL UNIQUE,   -- Deterministic hash
    primary_language VARCHAR(5),               -- Most common language in cluster
    languages VARCHAR[] DEFAULT '{}',          -- All languages in cluster
    
    -- Cluster characteristics
    member_count INTEGER DEFAULT 0,
    avg_strategic_confidence FLOAT,
    
    -- Semantic properties
    cluster_embedding VECTOR(384),      -- Centroid embedding
    coherence_score FLOAT,              -- Internal cluster coherence
    
    -- Geographic/Entity focus
    primary_entities JSONB DEFAULT '{}', -- Top entities in cluster
    geographic_focus VARCHAR[] DEFAULT '{}', -- Countries/regions involved
    
    -- Temporal properties
    first_seen TIMESTAMP,
    last_updated TIMESTAMP,
    time_span_hours INTEGER,
    
    -- Narrative association
    narrative_id UUID,                  -- Link to broader narrative
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Title-cluster membership (many-to-many)
CREATE TABLE v2_cluster_members (
    title_id UUID REFERENCES v2_titles(id) ON DELETE CASCADE,
    cluster_id UUID REFERENCES v2_clusters(id) ON DELETE CASCADE,
    membership_strength FLOAT DEFAULT 1.0,  -- How strongly title belongs
    added_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (title_id, cluster_id)
);

-- Cross-lingual narratives (LLM-assisted)
CREATE TABLE v2_narratives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Narrative identity
    narrative_key VARCHAR(128) UNIQUE,  -- Persistent across updates
    title TEXT NOT NULL,               -- Human-readable narrative title
    summary TEXT,                      -- LLM-generated summary
    
    -- Multilingual properties
    primary_language VARCHAR(5),
    involved_languages VARCHAR[] DEFAULT '{}',
    
    -- Temporal properties  
    first_detected TIMESTAMP,
    last_activity TIMESTAMP,
    estimated_duration_days INTEGER,
    
    -- Importance metrics
    cluster_count INTEGER DEFAULT 0,
    total_titles INTEGER DEFAULT 0,
    strategic_importance FLOAT,
    
    -- Geographic scope
    involved_countries VARCHAR[] DEFAULT '{}',
    geographic_scope VARCHAR(20),       -- 'local', 'regional', 'global'
    
    -- LLM processing
    llm_last_processed TIMESTAMP,
    llm_processing_cost FLOAT DEFAULT 0.0, -- Track LLM usage costs
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_v2_titles_language ON v2_titles(detected_language);
CREATE INDEX idx_v2_titles_strategic ON v2_titles(is_strategic) WHERE is_strategic = true;
CREATE INDEX idx_v2_titles_published ON v2_titles(published_at);
CREATE INDEX idx_v2_titles_embedding ON v2_titles USING ivfflat (title_embedding vector_cosine_ops);
CREATE INDEX idx_v2_clusters_language ON v2_clusters(primary_language);
CREATE INDEX idx_v2_clusters_updated ON v2_clusters(last_updated);
CREATE INDEX idx_v2_cluster_members_title ON v2_cluster_members(title_id);
CREATE INDEX idx_v2_cluster_members_cluster ON v2_cluster_members(cluster_id);

-- Views for easy querying
CREATE VIEW v2_strategic_titles AS
SELECT t.*, f.name as feed_name, f.language_code as feed_language
FROM v2_titles t
JOIN v2_feeds f ON t.feed_id = f.id
WHERE t.is_strategic = true;

CREATE VIEW v2_cluster_overview AS
SELECT 
    c.*,
    COUNT(cm.title_id) as actual_member_count,
    ARRAY_AGG(DISTINCT t.detected_language) as actual_languages
FROM v2_clusters c
LEFT JOIN v2_cluster_members cm ON c.id = cm.cluster_id
LEFT JOIN v2_titles t ON cm.title_id = t.id
GROUP BY c.id;