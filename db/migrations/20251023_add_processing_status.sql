-- Migration: Add processing_status field for EF Generation v2.1
-- Date: 2025-10-23
-- Purpose: Support recycling bin for rejected titles in P3.5a seed validation

-- Add processing_status field to titles table
ALTER TABLE titles
ADD COLUMN IF NOT EXISTS processing_status VARCHAR(50) DEFAULT 'pending';

-- Valid statuses:
-- 'pending' = not yet processed
-- 'recycling' = rejected from cluster, awaiting re-clustering
-- 'assigned' = successfully assigned to an EF

CREATE INDEX IF NOT EXISTS idx_titles_processing_status
ON titles(processing_status)
WHERE processing_status = 'recycling';

COMMENT ON COLUMN titles.processing_status IS
  'Processing status for EF Generation v2.1: pending, recycling, assigned';

-- Update existing titles
UPDATE titles
SET processing_status = CASE
    WHEN event_family_id IS NOT NULL THEN 'assigned'
    ELSE 'pending'
END
WHERE processing_status IS NULL;
