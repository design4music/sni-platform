-- Migration: Add 'rejected' status to processing_status field
-- Date: 2025-10-24
-- Purpose: Support permanent rejection of old recycled titles

-- Update comment to include new 'rejected' status
COMMENT ON COLUMN titles.processing_status IS
  'Processing status: pending, recycling, assigned, rejected';
