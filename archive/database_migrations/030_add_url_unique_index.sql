-- Migration 030: Add unique index for URL normalization
-- Strategic Narrative Intelligence Platform
-- 
-- Purpose: Prevent duplicate articles by enforcing URL uniqueness
-- Supports UPSERT pattern for efficient deduplication

-- Create unique index on normalized URLs (case-insensitive)
-- This enables ON CONFLICT handling and prevents duplicate articles
CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_url_unique 
ON articles (LOWER(url));

-- Add comment for documentation
COMMENT ON INDEX idx_articles_url_unique IS 'Unique constraint on normalized URLs to prevent article duplicates';

-- Optional: Add index on processing_status for enrichment pipeline queries
CREATE INDEX IF NOT EXISTS idx_articles_processing_status_pending
ON articles (processing_status) 
WHERE processing_status = 'PENDING';

COMMENT ON INDEX idx_articles_processing_status_pending IS 'Optimization for enrichment pipeline queries on pending articles';