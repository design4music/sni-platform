-- Migration: Drop processing_status column and related indexes
-- Date: 2025-10-08
-- Reason: Legacy field no longer used for queue selection (gate_keep used instead)
-- Impact: Reduces schema complexity, removes unused indexes

-- Drop indexes first
DROP INDEX IF EXISTS idx_titles_processing_status;
DROP INDEX IF EXISTS idx_titles_pending_gate;

-- Drop column
ALTER TABLE titles DROP COLUMN IF EXISTS processing_status;
ALTER TABLE titles DROP COLUMN IF EXISTS processed_at;

-- Verify cleanup
DO $$
BEGIN
    RAISE NOTICE 'Migration complete: processing_status column and indexes dropped';
END $$;
