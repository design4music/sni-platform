-- SNI-v2 Database Schema: Headlines-Only Multilingual Pipeline
-- Based on the Context Document specifications
-- Updated: 2025-09-07 with CLUST-1 Strategic Gate columns

-- Enable pgvector extension if available
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS cluster_members CASCADE;
DROP TABLE IF EXISTS narratives CASCADE; 
DROP TABLE IF EXISTS clusters CASCADE;
DROP TABLE IF EXISTS titles CASCADE;
DROP TABLE IF EXISTS feeds CASCADE;
DROP TABLE IF EXISTS runs CASCADE;

-- Core feed management
CREATE TABLE feeds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL UNIQUE,
    language_code VARCHAR(5) NOT NULL,  -- 'en', 'es', 'fr', 'de', 'ru', 'zh'
    country_code VARCHAR(3),            -- 'US', 'DE', 'FR', etc.
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 1,
    fetch_interval_minutes INTEGER DEFAULT 60,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- RSS ingestion metadata
    source_domain TEXT,                 -- Source domain for feed categorization
    etag TEXT,                         -- ETag for conditional GET requests
    last_modified TEXT,                -- Last-Modified header for conditional GET
    last_pubdate_utc TIMESTAMP WITH TIME ZONE, -- Latest article pubdate seen
    last_run_at TIMESTAMP WITH TIME ZONE       -- Last successful fetch timestamp
);

-- Headlines-only articles (massively simplified from original SNI)
CREATE TABLE titles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feed_id UUID REFERENCES feeds(id),
    
    -- Core content (from Context Document section 5)
    title_original TEXT NOT NULL,       -- Raw title from RSS
    title_display TEXT NOT NULL,        -- Cleaned for display
    title_norm TEXT,                    -- Normalized for matching (CLUST-1)
    url_gnews TEXT NOT NULL,            -- Google News URL
    publisher_name VARCHAR(255),        -- Publisher name
    publisher_domain VARCHAR(255),      -- Publisher domain
    publisher_country_code VARCHAR(3),  -- Publisher country (heuristic, nullable)
    pubdate_utc TIMESTAMP,              -- UTC publication date
    lang VARCHAR(5),                    -- Language code
    content_hash VARCHAR(64),           -- Hash for deduplication
    
    -- Language processing
    detected_language VARCHAR(5),      -- Auto-detected language
    language_confidence FLOAT,         -- Detection confidence
    
    -- Strategic filtering (legacy columns)
    is_strategic BOOLEAN,
    strategic_confidence FLOAT,
    strategic_signals JSONB DEFAULT '{}', -- Strategic indicators found
    
    -- Strategic Gate filtering (CLUST-1)
    gate_keep BOOLEAN NOT NULL DEFAULT false,     -- Gate decision: keep/reject
    gate_reason TEXT,                             -- Reason: actor_hit/anchor_sim/below_threshold
    gate_score REAL,                              -- Similarity score (0-1)
    gate_anchor_labels TEXT[],                    -- Matching anchor labels for mechanism
    gate_actor_hit TEXT,                          -- Actor alias that matched
    gate_at TIMESTAMP WITH TIME ZONE,             -- Gate processing timestamp
    
    -- Entities (multilingual NER)
    entities JSONB DEFAULT '{}',        -- Extracted entities
    entity_count INTEGER DEFAULT 0,
    
    -- Embeddings (using pgvector if available, otherwise JSON)
    title_embedding vector(384),        -- all-MiniLM-L6-v2 embeddings
    title_embedding_json JSONB,         -- Fallback if no pgvector
    
    -- Processing status
    processing_status VARCHAR(20) DEFAULT 'pending',  -- pending/gated/completed/failed
    processed_at TIMESTAMP,
    
    -- Metadata
    ingested_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(content_hash, feed_id)  -- Prevent duplicates
);

-- Buckets (pre-LLM clustering from Context Document section 8)
CREATE TABLE buckets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bucket_id VARCHAR(64) NOT NULL UNIQUE,  -- e.g., "B-2025-09-01-US-CN-TW"
    date_window_start TIMESTAMP NOT NULL,
    date_window_end TIMESTAMP NOT NULL,
    top_actors JSONB DEFAULT '[]',      -- Canonical actor IDs
    mechanism_hint VARCHAR(50),         -- Optional mechanism classification
    members_count INTEGER DEFAULT 0,
    members_checksum VARCHAR(64),       -- For change detection
    created_at TIMESTAMP DEFAULT NOW()
);

-- Events (from Context Document section 8)
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bucket_id UUID REFERENCES buckets(id),
    
    -- Versioning for updates
    version INTEGER DEFAULT 1,         -- Version number for updates
    
    -- Event content (from GEN-1 phase output)
    title_neutral TEXT NOT NULL,       -- Neutral event description
    shared_facts JSONB DEFAULT '[]',   -- Facts true for all titles
    actors JSONB DEFAULT '[]',         -- Canonical actor list
    mechanism VARCHAR(50),             -- From frozen taxonomy (MVP Core-20)
    time_window JSONB DEFAULT '{}',    -- {start, end}
    geography JSONB DEFAULT '[]',      -- Geographic scope
    categories JSONB DEFAULT '[]',     -- Content categories
    consistency_note TEXT,             -- LLM consistency observations
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Narratives (from Context Document section 8)  
CREATE TABLE narratives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES events(id),
    
    -- Versioning for updates
    version INTEGER DEFAULT 1,         -- Version number for updates
    
    -- Narrative content
    title TEXT NOT NULL,
    thesis TEXT NOT NULL,              -- 1-2 sentence narrative summary
    framing_vector JSONB DEFAULT '{}', -- Structured framing analysis
    lexicon_markers JSONB DEFAULT '{}',-- verbs/hedges/evaluatives  
    representative_sources JSONB DEFAULT '[]', -- Source domains
    representative_headlines JSONB DEFAULT '[]', -- Title IDs
    why_different TEXT,                -- If 2 narratives, why they differ
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Arcs (from Context Document section 8)
CREATE TABLE arcs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Versioning for updates
    version INTEGER DEFAULT 1,         -- Version number for updates
    
    -- Arc identity  
    title TEXT NOT NULL,
    thesis TEXT NOT NULL,              -- Cross-event pattern description
    framing_pattern JSONB DEFAULT '{}', -- Abstract framing pattern
    member_event_ids JSONB DEFAULT '[]', -- Full list of event IDs
    featured_event_ids JSONB DEFAULT '[]', -- UI preview events
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Runs (provenance tracking from Context Document section 8)
CREATE TABLE runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phase VARCHAR(20) NOT NULL,        -- ingest|clust1|gen1|merge|arc
    prompt_version VARCHAR(50),        -- For LLM phases
    input_ref TEXT,                    -- Reference to input (e.g., bucket IDs)
    output_ref JSONB,                  -- Output data or references
    tokens_used INTEGER DEFAULT 0,     -- LLM token usage
    cost_usd DECIMAL(10,4) DEFAULT 0,  -- Cost tracking
    bucket_token_count INTEGER,        -- Tokens per bucket (for budgeting)
    bucket_cost_estimate DECIMAL(10,4), -- Cost estimate per bucket
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_feeds_active ON feeds(is_active) WHERE is_active = true;
CREATE INDEX idx_feeds_language ON feeds(language_code);

CREATE INDEX idx_titles_feed ON titles(feed_id);
CREATE INDEX idx_titles_strategic ON titles(is_strategic) WHERE is_strategic = true;
CREATE INDEX idx_titles_language ON titles(detected_language);
CREATE INDEX idx_titles_published ON titles(pubdate_utc);
CREATE INDEX idx_titles_hash ON titles(content_hash);

-- Strategic Gate indexes (CLUST-1)
CREATE INDEX idx_titles_processing_status ON titles(processing_status);
CREATE INDEX idx_titles_gate_keep ON titles(gate_keep) WHERE gate_keep = true;
CREATE INDEX idx_titles_gate_reason ON titles(gate_reason);
CREATE INDEX idx_titles_gate_at ON titles(gate_at);
CREATE INDEX idx_titles_pending_gate ON titles(processing_status, gate_at) WHERE processing_status = 'pending' AND gate_at IS NULL;

CREATE INDEX idx_buckets_date ON buckets(date_window_start, date_window_end);
CREATE INDEX idx_events_bucket ON events(bucket_id);
CREATE INDEX idx_events_mechanism ON events(mechanism);
CREATE INDEX idx_narratives_event ON narratives(event_id);
CREATE INDEX idx_runs_phase ON runs(phase, created_at);

-- Views for common queries (from Context Document)
CREATE VIEW strategic_titles AS
SELECT 
    t.*,
    f.name as feed_name,
    f.language_code as feed_language,
    f.country_code as feed_country
FROM titles t
JOIN feeds f ON t.feed_id = f.id
WHERE t.gate_keep = true;  -- Updated to use Strategic Gate results

-- Legacy view for backward compatibility
CREATE VIEW legacy_strategic_titles AS
SELECT 
    t.*,
    f.name as feed_name,
    f.language_code as feed_language,
    f.country_code as feed_country
FROM titles t
JOIN feeds f ON t.feed_id = f.id
WHERE t.is_strategic = true;

CREATE VIEW recent_activity AS  
SELECT 
    'title' as entity_type,
    t.id::text as entity_id,
    t.title_display as description,
    t.created_at
FROM titles t
WHERE t.created_at > NOW() - INTERVAL '24 hours'

UNION ALL

SELECT 
    'event' as entity_type,
    e.id::text as entity_id, 
    e.title_neutral as description,
    e.created_at
FROM events e
WHERE e.created_at > NOW() - INTERVAL '24 hours'

ORDER BY created_at DESC;

-- Initial data: Basic mechanism taxonomy (from Context Document Appendix B)
-- Note: This is a simplified version - full taxonomy would be inserted via migration
INSERT INTO runs (phase, prompt_version, input_ref, output_ref) 
VALUES ('setup', 'v1.0', 'schema_creation', '{"tables_created": 8, "indexes_created": 12}');

COMMENT ON DATABASE CURRENT_DATABASE IS 'SNI-v2: Headlines-Only Multilingual Narrative Intelligence';
COMMENT ON TABLE titles IS 'Headlines-only articles with multilingual processing';
COMMENT ON TABLE events IS 'Event families generated from buckets by LLM';  
COMMENT ON TABLE narratives IS 'Framed narratives for events showing competing storylines';
COMMENT ON TABLE arcs IS 'Structural arcs linking multiple events by recurring patterns';