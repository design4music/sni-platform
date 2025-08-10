-- CLUST-3 Narrative Consolidation Schema Migration
-- Strategic Narrative Intelligence Platform
-- Migration 004: Add consolidation and archival fields

-- Add consolidation_stage field
ALTER TABLE narratives
ADD COLUMN consolidation_stage TEXT DEFAULT 'raw'
CHECK (consolidation_stage IN ('raw', 'consolidated', 'archived'));

-- Add archive_reason field for tracking merge history
ALTER TABLE narratives
ADD COLUMN archive_reason JSONB DEFAULT NULL;

-- Create composite index for consolidation queries
CREATE INDEX idx_narratives_consolidation_stage
ON narratives (consolidation_stage, created_at DESC);

-- Create index for similarity queries (if narrative_embedding exists)
-- This assumes narrative_embedding field exists for vector similarity
-- CREATE INDEX idx_narratives_embedding_similarity 
-- ON narratives USING ivfflat (narrative_embedding vector_cosine_ops);

-- Update existing narratives to have 'raw' status
UPDATE narratives 
SET consolidation_stage = 'raw' 
WHERE consolidation_stage IS NULL;

-- Add comment for documentation
COMMENT ON COLUMN narratives.consolidation_stage IS 'Stage of narrative consolidation: raw (new), consolidated (canonical), archived (merged/obsolete)';
COMMENT ON COLUMN narratives.archive_reason IS 'JSONB metadata explaining why narrative was archived, including merge target and confidence';

-- Migration verification query
-- Run this to verify migration worked correctly:
/*
SELECT 
    consolidation_stage,
    COUNT(*) as count,
    MIN(created_at) as earliest,
    MAX(created_at) as latest
FROM narratives 
GROUP BY consolidation_stage 
ORDER BY consolidation_stage;
*/