-- Migration: Add strip_patterns to feeds table
-- Date: 2026-01-26
-- Purpose: Store publisher name patterns to filter from extracted signals

-- Add strip_patterns column (array of strings, 1-3 patterns per feed)
ALTER TABLE feeds ADD COLUMN IF NOT EXISTS strip_patterns TEXT[];

-- Add comment
COMMENT ON COLUMN feeds.strip_patterns IS 'Patterns to filter from extracted orgs/signals (e.g., ["WSJ", "Wall Street Journal"])';
