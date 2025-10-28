-- Migration: Add action_triple JSONB column to titles table
-- Date: 2025-10-28
-- Purpose: Store Actor-Action-Target triples for graph-pattern clustering

-- Add action_triple column
ALTER TABLE titles ADD COLUMN IF NOT EXISTS action_triple JSONB;

-- Create GIN index for efficient JSONB querying
CREATE INDEX IF NOT EXISTS idx_titles_action_triple ON titles USING GIN (action_triple);

-- Add comment for documentation
COMMENT ON COLUMN titles.action_triple IS 'Actor-Action-Target triple extracted from title: {"actor": "US", "action": "sanctions", "target": "Russia"}';
