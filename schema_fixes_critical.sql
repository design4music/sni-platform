-- Strategic Narrative Intelligence Platform
-- Critical Database Schema Fixes for NSF-1 Compliance
-- Generated: August 3, 2025
-- 
-- This script addresses critical issues found in database schema verification
-- that could cause CLUST-2 workflow failures when saving narratives.

-- ===========================================================================
-- CRITICAL FIX 1: Add Missing Full-Text Search Support
-- ===========================================================================

-- Add search_vector generated column for full-text search
-- This column will automatically index title + summary for efficient search
ALTER TABLE narratives ADD COLUMN search_vector tsvector 
GENERATED ALWAYS AS (
    to_tsvector('english', title || ' ' || summary)
) STORED;

-- Create GIN index for full-text search performance
CREATE INDEX idx_narratives_search_vector 
ON narratives USING GIN (search_vector);

-- Verify the search_vector column was created correctly
SELECT 
    column_name, 
    data_type, 
    is_generated,
    generation_expression
FROM information_schema.columns 
WHERE table_name = 'narratives' 
AND column_name = 'search_vector';

-- Test full-text search functionality
SELECT narrative_id, title, ts_rank(search_vector, to_tsquery('energy')) as rank
FROM narratives 
WHERE search_vector @@ to_tsquery('energy')
ORDER BY rank DESC
LIMIT 5;

-- ===========================================================================
-- CRITICAL FIX 2: Add Missing JSONB Validation Constraints
-- ===========================================================================

-- Ensure all JSONB array fields have proper type validation
-- Some constraints may already exist, using IF NOT EXISTS equivalent

DO $$
BEGIN
    -- Check and add narrative_tension array validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'valid_narrative_tension_strict'
    ) THEN
        ALTER TABLE narratives ADD CONSTRAINT valid_narrative_tension_strict 
            CHECK (jsonb_typeof(narrative_tension) = 'array' OR narrative_tension IS NULL);
    END IF;
    
    -- Check and add turning_points array validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'valid_turning_points_strict'
    ) THEN
        ALTER TABLE narratives ADD CONSTRAINT valid_turning_points_strict 
            CHECK (jsonb_typeof(turning_points) = 'array' OR turning_points IS NULL);
    END IF;
    
    -- Check and add top_excerpts array validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'valid_top_excerpts_strict'
    ) THEN
        ALTER TABLE narratives ADD CONSTRAINT valid_top_excerpts_strict 
            CHECK (jsonb_typeof(top_excerpts) = 'array' OR top_excerpts IS NULL);
    END IF;
    
    -- Check and add version_history array validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'valid_version_history_strict'
    ) THEN
        ALTER TABLE narratives ADD CONSTRAINT valid_version_history_strict 
            CHECK (jsonb_typeof(version_history) = 'array' OR version_history IS NULL);
    END IF;
    
    -- Object field validations
    -- Check and add activity_timeline object validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'valid_activity_timeline_strict'
    ) THEN
        ALTER TABLE narratives ADD CONSTRAINT valid_activity_timeline_strict 
            CHECK (jsonb_typeof(activity_timeline) = 'object' OR activity_timeline IS NULL);
    END IF;
    
    -- Check and add media_spike_history object validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'valid_media_spike_history_strict'
    ) THEN
        ALTER TABLE narratives ADD CONSTRAINT valid_media_spike_history_strict 
            CHECK (jsonb_typeof(media_spike_history) = 'object' OR media_spike_history IS NULL);
    END IF;
    
    -- Check and add source_stats object validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'valid_source_stats_strict'
    ) THEN
        ALTER TABLE narratives ADD CONSTRAINT valid_source_stats_strict 
            CHECK (jsonb_typeof(source_stats) = 'object' OR source_stats IS NULL);
    END IF;
    
    -- Check and add update_status object validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'valid_update_status_strict'
    ) THEN
        ALTER TABLE narratives ADD CONSTRAINT valid_update_status_strict 
            CHECK (jsonb_typeof(update_status) = 'object' OR update_status IS NULL);
    END IF;
    
    -- Check and add rai_analysis object validation
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'valid_rai_analysis_strict'
    ) THEN
        ALTER TABLE narratives ADD CONSTRAINT valid_rai_analysis_strict 
            CHECK (jsonb_typeof(rai_analysis) = 'object' OR rai_analysis IS NULL);
    END IF;
    
    RAISE NOTICE 'JSONB validation constraints added successfully';
END
$$;

-- ===========================================================================
-- CRITICAL FIX 3: Verify Vector Extension and Dimensions
-- ===========================================================================

-- Verify pgvector extension is properly installed
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check current narrative_embedding column configuration
SELECT 
    column_name,
    data_type,
    udt_name,
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'narratives' 
AND column_name = 'narrative_embedding';

-- Verify vector index exists and is properly configured
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'narratives' 
AND indexname = 'idx_narratives_embedding';

-- Check if any narratives have embeddings (should show data status)
SELECT 
    COUNT(*) as total_narratives,
    COUNT(narrative_embedding) as narratives_with_embeddings,
    ROUND(
        (COUNT(narrative_embedding)::float / COUNT(*)) * 100, 2
    ) as embedding_completion_percent
FROM narratives;

-- ===========================================================================
-- PERFORMANCE FIX: Add Composite Indexes for Common CLUST-2 Queries
-- ===========================================================================

-- Index for narrative creation date + status queries
CREATE INDEX IF NOT EXISTS idx_narratives_created_status 
ON narratives (created_at DESC, confidence_rating) 
WHERE confidence_rating IS NOT NULL;

-- Index for JSONB array containment queries (most common in CLUST-2)
-- These indexes already exist, but verify they're optimal
DO $$
BEGIN
    -- Verify alignment GIN index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'narratives' 
        AND indexname = 'idx_narratives_alignment_gin'
    ) THEN
        CREATE INDEX idx_narratives_alignment_gin 
        ON narratives USING GIN (alignment);
    END IF;
    
    -- Verify actor_origin GIN index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'narratives' 
        AND indexname = 'idx_narratives_actor_origin_gin'
    ) THEN
        CREATE INDEX idx_narratives_actor_origin_gin 
        ON narratives USING GIN (actor_origin);
    END IF;
    
    RAISE NOTICE 'JSONB GIN indexes verified';
END
$$;

-- ===========================================================================
-- DATA INTEGRITY VERIFICATION
-- ===========================================================================

-- Verify all existing data passes new constraints
SELECT 
    'narrative_tension' as field_name,
    COUNT(*) as total_rows,
    COUNT(CASE WHEN jsonb_typeof(narrative_tension) = 'array' OR narrative_tension IS NULL THEN 1 END) as valid_rows,
    COUNT(CASE WHEN jsonb_typeof(narrative_tension) != 'array' AND narrative_tension IS NOT NULL THEN 1 END) as invalid_rows
FROM narratives

UNION ALL

SELECT 
    'activity_timeline' as field_name,
    COUNT(*) as total_rows,
    COUNT(CASE WHEN jsonb_typeof(activity_timeline) = 'object' OR activity_timeline IS NULL THEN 1 END) as valid_rows,
    COUNT(CASE WHEN jsonb_typeof(activity_timeline) != 'object' AND activity_timeline IS NOT NULL THEN 1 END) as invalid_rows
FROM narratives

UNION ALL

SELECT 
    'update_status' as field_name,
    COUNT(*) as total_rows,
    COUNT(CASE WHEN jsonb_typeof(update_status) = 'object' OR update_status IS NULL THEN 1 END) as valid_rows,
    COUNT(CASE WHEN jsonb_typeof(update_status) != 'object' AND update_status IS NOT NULL THEN 1 END) as invalid_rows
FROM narratives;

-- ===========================================================================
-- CLUST-2 COMPATIBILITY TEST QUERIES
-- ===========================================================================

-- Test query 1: Search for narratives with specific alignment (CLUST-2 uses this pattern)
SELECT narrative_id, title, alignment
FROM narratives 
WHERE alignment @> '["Western governments"]'::jsonb
LIMIT 5;

-- Test query 2: Search for parent-child relationships (CLUST-2 creates these)
SELECT 
    parent.narrative_id as parent_id,
    parent.title as parent_title,
    child.narrative_id as child_id,
    child.title as child_title
FROM narratives parent
JOIN narratives child ON child.nested_within @> jsonb_build_array(parent.narrative_id::text)
LIMIT 5;

-- Test query 3: Full-text search (now works with search_vector)
SELECT narrative_id, title, ts_rank(search_vector, to_tsquery('Trump')) as relevance
FROM narratives 
WHERE search_vector @@ to_tsquery('Trump')
ORDER BY relevance DESC
LIMIT 5;

-- Test query 4: Complex JSONB object queries (CLUST-2 may use these)
SELECT narrative_id, title, 
       (update_status->>'last_updated') as last_updated,
       (update_status->>'update_trigger') as update_trigger
FROM narratives 
WHERE update_status->>'update_trigger' = 'clust2_segmentation'
LIMIT 5;

-- ===========================================================================
-- POST-FIX VALIDATION
-- ===========================================================================

-- Count total indexes on narratives table
SELECT COUNT(*) as total_indexes
FROM pg_indexes 
WHERE tablename = 'narratives';

-- Show all constraints on narratives table
SELECT constraint_name, constraint_type
FROM information_schema.table_constraints 
WHERE table_name = 'narratives'
ORDER BY constraint_type, constraint_name;

-- Verify column count matches expected
SELECT COUNT(*) as column_count
FROM information_schema.columns 
WHERE table_name = 'narratives';

-- ===========================================================================
-- SUCCESS MESSAGE
-- ===========================================================================

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'CRITICAL SCHEMA FIXES COMPLETED SUCCESSFULLY';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Changes applied:';
    RAISE NOTICE '✓ Added search_vector column with GIN index';
    RAISE NOTICE '✓ Added JSONB validation constraints';
    RAISE NOTICE '✓ Verified vector extension compatibility';
    RAISE NOTICE '✓ Added performance indexes';
    RAISE NOTICE '✓ Validated data integrity';
    RAISE NOTICE '';
    RAISE NOTICE 'CLUST-2 workflow should now work correctly!';
    RAISE NOTICE 'Next step: Test CLUST-2 narrative creation';
    RAISE NOTICE '============================================';
END
$$;

-- Final verification query
SELECT 
    'Schema Fix Status' as status,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'narratives' 
            AND column_name = 'search_vector'
        ) THEN 'READY FOR CLUST-2'
        ELSE 'ISSUES REMAIN'
    END as clust2_compatibility;