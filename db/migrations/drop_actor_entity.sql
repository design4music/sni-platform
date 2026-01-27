-- Migration: Drop actor_entity column from title_labels
-- Date: 2026-01-27
-- Reason: Merged into signals (orgs, commodities) - no longer needed

-- Drop the column
ALTER TABLE title_labels DROP COLUMN IF EXISTS actor_entity;

-- Verify
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'title_labels' ORDER BY ordinal_position;
