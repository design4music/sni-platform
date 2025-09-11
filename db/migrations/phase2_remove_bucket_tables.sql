-- Phase 2 Cleanup: Remove bucket-related tables and columns
-- The bucketless architecture no longer needs these components

-- Drop bucket-related tables
DROP TABLE IF EXISTS bucket_members CASCADE;
DROP TABLE IF EXISTS buckets CASCADE;

-- Remove bucket-related columns from titles table  
-- (Note: The titles table may have bucket_id references that need cleanup)
ALTER TABLE titles DROP COLUMN IF EXISTS bucket_id;

-- Remove bucket-related columns from event_families if they exist
ALTER TABLE event_families DROP COLUMN IF EXISTS source_bucket_ids;

-- Remove bucket-related indexes (these will be dropped automatically with tables)
-- No manual index cleanup needed

-- Update any views that might reference bucket tables
-- The main schema doesn't have views referencing buckets, but check legacy views
DROP VIEW IF EXISTS bucket_summary;
DROP VIEW IF EXISTS bucket_activity;

-- Add comment for migration tracking
INSERT INTO runs (phase, prompt_version, input_ref, output_ref) 
VALUES (
    'cleanup', 
    'phase2_bucketless', 
    'remove_bucket_tables', 
    '{"tables_dropped": ["buckets", "bucket_members"], "columns_dropped": ["titles.bucket_id", "event_families.source_bucket_ids"]}'
);

COMMENT ON DATABASE CURRENT_DATABASE IS 'SNI Phase 2: Bucketless Direct Title Processing Architecture';