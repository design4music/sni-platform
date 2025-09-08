-- Keyword Canonical Mapping Schema Migration
-- Strategic Narrative Intelligence Platform
-- Migration 008: Canonical keyword mapping cache

-- Canonical keyword mapping cache
CREATE TABLE keyword_canon_map (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_norm TEXT NOT NULL UNIQUE,     -- Normalized token
    canon_text TEXT NOT NULL,            -- Canonical form  
    confidence FLOAT NOT NULL DEFAULT 0.0, -- Mapping confidence (0.0-1.0)
    concept_cluster TEXT,                -- Concept cluster for overlap counting
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Core keywords materialized view (will be populated later)
CREATE TABLE article_core_keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    token TEXT NOT NULL,                 -- Canonical token
    score FLOAT NOT NULL,                -- Strategic score
    doc_freq INTEGER NOT NULL,           -- Document frequency
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    
    UNIQUE(article_id, token)
);

-- Indexes for performance
CREATE INDEX idx_keyword_canon_map_token ON keyword_canon_map (token_norm);
CREATE INDEX idx_keyword_canon_map_canon ON keyword_canon_map (canon_text);
CREATE INDEX idx_keyword_canon_map_cluster ON keyword_canon_map (concept_cluster);

CREATE INDEX idx_article_core_keywords_article ON article_core_keywords (article_id);
CREATE INDEX idx_article_core_keywords_token ON article_core_keywords (token);
CREATE INDEX idx_article_core_keywords_score ON article_core_keywords (score DESC);
CREATE INDEX idx_article_core_keywords_doc_freq ON article_core_keywords (doc_freq);

-- Function to refresh canonical mappings
CREATE OR REPLACE FUNCTION refresh_canonical_mappings() RETURNS INTEGER AS $$
DECLARE
    processed_count INTEGER := 0;
BEGIN
    -- This will be populated by the Python normalizer
    -- Placeholder for future batch updates
    RETURN processed_count;
END;
$$ LANGUAGE plpgsql;

-- Comments
COMMENT ON TABLE keyword_canon_map IS 'Cache of normalized tokens to canonical forms';
COMMENT ON TABLE article_core_keywords IS 'Top 6 canonical concepts per EN article with df in [3..250]';
COMMENT ON COLUMN keyword_canon_map.confidence IS 'Mapping confidence: 1.0=exact match, 0.8=normalized form';
COMMENT ON COLUMN article_core_keywords.doc_freq IS 'Document frequency of canonical token across corpus';