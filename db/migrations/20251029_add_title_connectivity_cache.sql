-- Migration: Add title connectivity cache for hybrid clustering
-- Date: 2025-10-29
-- Description: Cache Neo4j connectivity scores in Postgres for fast lookup during P3_v1 clustering

BEGIN;

-- Create connectivity cache table
CREATE TABLE IF NOT EXISTS title_connectivity_cache (
    title_id_1 UUID NOT NULL,
    title_id_2 UUID NOT NULL,
    co_occurs_score FLOAT DEFAULT 0.0,
    same_actor_score FLOAT DEFAULT 0.0,
    total_score FLOAT DEFAULT 0.0,
    shared_entities TEXT[] DEFAULT '{}',
    shared_actor TEXT,
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT connectivity_cache_pkey PRIMARY KEY (title_id_1, title_id_2),
    CONSTRAINT connectivity_title_order CHECK (title_id_1 < title_id_2),
    CONSTRAINT connectivity_title1_fkey FOREIGN KEY (title_id_1) REFERENCES titles(id) ON DELETE CASCADE,
    CONSTRAINT connectivity_title2_fkey FOREIGN KEY (title_id_2) REFERENCES titles(id) ON DELETE CASCADE
);

-- Indexes for fast lookup
CREATE INDEX idx_connectivity_title1 ON title_connectivity_cache(title_id_1);
CREATE INDEX idx_connectivity_title2 ON title_connectivity_cache(title_id_2);
CREATE INDEX idx_connectivity_score ON title_connectivity_cache(total_score DESC)
    WHERE total_score >= 0.3;  -- Only index significant connections

COMMENT ON TABLE title_connectivity_cache IS 'Precomputed connectivity scores from Neo4j for hybrid clustering (P3_v1)';
COMMENT ON COLUMN title_connectivity_cache.co_occurs_score IS 'Jaccard similarity from shared entities (0.0-1.0)';
COMMENT ON COLUMN title_connectivity_cache.same_actor_score IS 'AAT actor match score (0.0 or 1.0)';
COMMENT ON COLUMN title_connectivity_cache.total_score IS 'Combined connectivity score for clustering threshold';

COMMIT;

-- Verification
SELECT COUNT(*) as cache_entries FROM title_connectivity_cache;
