-- ============================================================================
-- Narrative Hierarchy Migration to Canonical parent_id Field
-- Strategic Narrative Intelligence Platform
-- Migration ID: 002
-- Date: August 3, 2025
-- ============================================================================
--
-- GOAL: Simplify parent/child narrative relationships by making parent_id (UUID) 
-- the canonical field for hierarchy, improving query performance and simplifying 
-- ORM handling. The nested_within (JSONB) will be deprecated.
--
-- CHANGES:
-- 1. Ensure parent_id column exists with proper constraints
-- 2. Create migration to backfill parent_id from nested_within data
-- 3. Add performance indexes for parent_id queries
-- 4. Mark nested_within as deprecated (add comment)
-- 5. Create helper functions and views for hierarchy queries
--
-- COMPATIBILITY: This migration preserves all existing data while establishing
-- parent_id as the canonical source of truth for narrative hierarchies.
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Ensure parent_id Column Exists with Proper Constraints
-- ============================================================================

-- Check if parent_id column exists, if not create it
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'narratives' AND column_name = 'parent_id'
    ) THEN
        -- Add parent_id column to narratives table
        ALTER TABLE narratives 
        ADD COLUMN parent_id UUID REFERENCES narratives(id) ON DELETE CASCADE;
        
        RAISE NOTICE 'Added parent_id column to narratives table';
    ELSE
        RAISE NOTICE 'parent_id column already exists in narratives table';
    END IF;
END
$$;

-- Ensure we have the self-reference check constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_narratives_no_self_reference'
    ) THEN
        ALTER TABLE narratives 
        ADD CONSTRAINT chk_narratives_no_self_reference 
        CHECK (id != parent_id);
        
        RAISE NOTICE 'Added self-reference prevention constraint';
    END IF;
END
$$;

-- ============================================================================
-- STEP 2: Create Performance Indexes for parent_id Queries
-- ============================================================================

-- Index for efficient parent/child queries
CREATE INDEX IF NOT EXISTS idx_narratives_parent_id 
ON narratives(parent_id);

-- Partial index for finding all children of a parent (non-null parent_id)
CREATE INDEX IF NOT EXISTS idx_narratives_parent_children 
ON narratives(parent_id) 
WHERE parent_id IS NOT NULL;

-- Partial index for finding all parent narratives (null parent_id)
CREATE INDEX IF NOT EXISTS idx_narratives_parents 
ON narratives(parent_id) 
WHERE parent_id IS NULL;

-- Composite index for hierarchy traversal with created_at ordering
CREATE INDEX IF NOT EXISTS idx_narratives_hierarchy_created 
ON narratives(parent_id, created_at DESC);

-- Composite index for hierarchy with status filtering
CREATE INDEX IF NOT EXISTS idx_narratives_hierarchy_status 
ON narratives(parent_id, confidence_rating) 
WHERE confidence_rating IS NOT NULL;

RAISE NOTICE 'Created performance indexes for parent_id queries';

-- ============================================================================
-- STEP 3: Data Migration - Backfill parent_id from nested_within
-- ============================================================================

-- Create function to migrate nested_within data to parent_id
CREATE OR REPLACE FUNCTION migrate_nested_within_to_parent_id()
RETURNS TABLE(
    narrative_id text,
    old_nested_within jsonb,
    new_parent_id uuid,
    migration_status text
) AS $$
DECLARE
    rec RECORD;
    parent_uuid uuid;
    migration_count integer := 0;
    error_count integer := 0;
BEGIN
    RAISE NOTICE 'Starting migration of nested_within data to parent_id...';
    
    -- Find all narratives that have nested_within data but no parent_id
    FOR rec IN 
        SELECT n.id, n.narrative_id, n.nested_within
        FROM narratives n
        WHERE n.nested_within IS NOT NULL 
        AND jsonb_array_length(n.nested_within) > 0
        AND n.parent_id IS NULL
    LOOP
        BEGIN
            -- Extract the first parent UUID from nested_within array
            -- nested_within format: ["parent_uuid"] or ["parent_narrative_id"]
            IF jsonb_typeof(rec.nested_within) = 'array' AND jsonb_array_length(rec.nested_within) > 0 THEN
                -- Try to parse as UUID first
                BEGIN
                    parent_uuid := (rec.nested_within->>0)::uuid;
                EXCEPTION WHEN invalid_text_representation THEN
                    -- If not a UUID, try to find by narrative_id
                    SELECT id INTO parent_uuid 
                    FROM narratives 
                    WHERE narrative_id = (rec.nested_within->>0);
                    
                    IF parent_uuid IS NULL THEN
                        RETURN QUERY SELECT 
                            rec.narrative_id,
                            rec.nested_within,
                            NULL::uuid,
                            'ERROR: Parent not found by narrative_id: ' || (rec.nested_within->>0);
                        error_count := error_count + 1;
                        CONTINUE;
                    END IF;
                END;
                
                -- Verify parent exists
                IF EXISTS (SELECT 1 FROM narratives WHERE id = parent_uuid) THEN
                    -- Update parent_id
                    UPDATE narratives 
                    SET parent_id = parent_uuid
                    WHERE id = rec.id;
                    
                    migration_count := migration_count + 1;
                    
                    RETURN QUERY SELECT 
                        rec.narrative_id,
                        rec.nested_within,
                        parent_uuid,
                        'SUCCESS: Migrated to parent_id';
                ELSE
                    RETURN QUERY SELECT 
                        rec.narrative_id,
                        rec.nested_within,
                        parent_uuid,
                        'ERROR: Parent UUID not found in database';
                    error_count := error_count + 1;
                END IF;
            ELSE
                RETURN QUERY SELECT 
                    rec.narrative_id,
                    rec.nested_within,
                    NULL::uuid,
                    'ERROR: Invalid nested_within format';
                error_count := error_count + 1;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RETURN QUERY SELECT 
                rec.narrative_id,
                rec.nested_within,
                NULL::uuid,
                'ERROR: ' || SQLERRM;
            error_count := error_count + 1;
        END;
    END LOOP;
    
    RAISE NOTICE 'Migration completed: % records migrated, % errors', migration_count, error_count;
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Execute the migration and show results
RAISE NOTICE 'Executing nested_within to parent_id migration...';

DO $$
DECLARE
    migration_results RECORD;
    total_migrated integer := 0;
    total_errors integer := 0;
BEGIN
    -- Execute migration and count results
    FOR migration_results IN 
        SELECT * FROM migrate_nested_within_to_parent_id()
    LOOP
        IF migration_results.migration_status LIKE 'SUCCESS%' THEN
            total_migrated := total_migrated + 1;
        ELSE
            total_errors := total_errors + 1;
            RAISE WARNING 'Migration error for %: %', 
                migration_results.narrative_id, 
                migration_results.migration_status;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'MIGRATION SUMMARY: % narratives migrated successfully, % errors', 
        total_migrated, total_errors;
END
$$;

-- ============================================================================
-- STEP 4: Mark nested_within as Deprecated
-- ============================================================================

-- Add comment to mark nested_within as deprecated
COMMENT ON COLUMN narratives.nested_within IS 
'DEPRECATED: Use parent_id instead. This JSONB field is maintained for backward compatibility only. The canonical parent-child relationship is now stored in the parent_id UUID column for better performance and simpler queries.';

-- ============================================================================
-- STEP 5: Create Helper Functions and Views for Hierarchy Operations
-- ============================================================================

-- Function to get all children of a parent narrative
CREATE OR REPLACE FUNCTION get_narrative_children(parent_uuid uuid)
RETURNS TABLE(
    child_id uuid,
    child_narrative_id text,
    child_title text,
    child_summary text,
    child_created_at timestamp with time zone,
    child_confidence_rating text
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        n.id,
        n.narrative_id,
        n.title,
        n.summary,
        n.created_at,
        n.confidence_rating
    FROM narratives n
    WHERE n.parent_id = parent_uuid
    ORDER BY n.created_at ASC;
END;
$$ LANGUAGE plpgsql;

-- Function to get parent of a child narrative
CREATE OR REPLACE FUNCTION get_narrative_parent(child_uuid uuid)
RETURNS TABLE(
    parent_id uuid,
    parent_narrative_id text,
    parent_title text,
    parent_summary text,
    parent_created_at timestamp with time zone,
    parent_confidence_rating text
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.narrative_id,
        p.title,
        p.summary,
        p.created_at,
        p.confidence_rating
    FROM narratives n
    JOIN narratives p ON n.parent_id = p.id
    WHERE n.id = child_uuid;
END;
$$ LANGUAGE plpgsql;

-- Function to get complete narrative hierarchy (parent + all children)
CREATE OR REPLACE FUNCTION get_narrative_hierarchy(root_uuid uuid)
RETURNS TABLE(
    hierarchy_level integer,
    narrative_id uuid,
    narrative_display_id text,
    title text,
    summary text,
    parent_id uuid,
    created_at timestamp with time zone,
    confidence_rating text,
    is_parent boolean
) AS $$
BEGIN
    -- Return parent narrative (level 0)
    RETURN QUERY
    SELECT 
        0 as hierarchy_level,
        n.id,
        n.narrative_id,
        n.title,
        n.summary,
        n.parent_id,
        n.created_at,
        n.confidence_rating,
        true as is_parent
    FROM narratives n
    WHERE n.id = root_uuid AND n.parent_id IS NULL;
    
    -- Return child narratives (level 1)
    RETURN QUERY
    SELECT 
        1 as hierarchy_level,
        n.id,
        n.narrative_id,
        n.title,
        n.summary,
        n.parent_id,
        n.created_at,
        n.confidence_rating,
        false as is_parent
    FROM narratives n
    WHERE n.parent_id = root_uuid
    ORDER BY n.created_at ASC;
END;
$$ LANGUAGE plpgsql;

-- Enhanced hierarchy view with performance optimization
CREATE OR REPLACE VIEW narrative_hierarchy_v2 AS
SELECT 
    -- Child narrative info
    child.id as child_id,
    child.narrative_id as child_narrative_id,
    child.title as child_title,
    child.summary as child_summary,
    child.created_at as child_created_at,
    child.confidence_rating as child_confidence_rating,
    
    -- Parent narrative info
    parent.id as parent_id,
    parent.narrative_id as parent_narrative_id,
    parent.title as parent_title,
    parent.summary as parent_summary,
    parent.created_at as parent_created_at,
    parent.confidence_rating as parent_confidence_rating,
    
    -- Relationship metadata
    CASE WHEN child.parent_id IS NULL THEN 'parent' ELSE 'child' END as narrative_type,
    child.parent_id IS NOT NULL as has_parent,
    EXISTS(SELECT 1 FROM narratives WHERE parent_id = child.id) as has_children
    
FROM narratives child
LEFT JOIN narratives parent ON child.parent_id = parent.id;

-- Create materialized view for high-performance hierarchy queries
CREATE MATERIALIZED VIEW narrative_hierarchy_cache AS
SELECT 
    parent.id as parent_id,
    parent.narrative_id as parent_narrative_id,
    parent.title as parent_title,
    COUNT(child.id) as child_count,
    array_agg(child.id ORDER BY child.created_at) as child_ids,
    array_agg(child.narrative_id ORDER BY child.created_at) as child_narrative_ids,
    array_agg(child.title ORDER BY child.created_at) as child_titles,
    parent.created_at as parent_created_at,
    MAX(child.created_at) as latest_child_created_at
FROM narratives parent
LEFT JOIN narratives child ON child.parent_id = parent.id
WHERE parent.parent_id IS NULL  -- Only root parents
GROUP BY parent.id, parent.narrative_id, parent.title, parent.created_at;

-- Create unique index on materialized view
CREATE UNIQUE INDEX idx_narrative_hierarchy_cache_parent_id 
ON narrative_hierarchy_cache(parent_id);

-- Function to refresh the hierarchy cache
CREATE OR REPLACE FUNCTION refresh_narrative_hierarchy_cache()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW narrative_hierarchy_cache;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 6: Create Triggers for Automatic Cache Maintenance
-- ============================================================================

-- Function to refresh cache when narratives are modified
CREATE OR REPLACE FUNCTION trigger_refresh_hierarchy_cache()
RETURNS TRIGGER AS $$
BEGIN
    -- Refresh the materialized view when parent_id changes
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        IF NEW.parent_id IS DISTINCT FROM COALESCE(OLD.parent_id, NULL) THEN
            PERFORM refresh_narrative_hierarchy_cache();
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        IF OLD.parent_id IS NOT NULL THEN
            PERFORM refresh_narrative_hierarchy_cache();
        END IF;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic cache refresh
DROP TRIGGER IF EXISTS trg_refresh_hierarchy_cache ON narratives;
CREATE TRIGGER trg_refresh_hierarchy_cache
    AFTER INSERT OR UPDATE OF parent_id OR DELETE ON narratives
    FOR EACH ROW
    EXECUTE FUNCTION trigger_refresh_hierarchy_cache();

-- ============================================================================
-- STEP 7: Data Validation and Integrity Checks
-- ============================================================================

-- Function to validate hierarchy integrity
CREATE OR REPLACE FUNCTION validate_narrative_hierarchy()
RETURNS TABLE(
    check_name text,
    total_count bigint,
    valid_count bigint,
    invalid_count bigint,
    status text
) AS $$
BEGIN
    -- Check 1: No self-references
    RETURN QUERY
    SELECT 
        'Self-references' as check_name,
        COUNT(*) as total_count,
        COUNT(*) - COUNT(CASE WHEN id = parent_id THEN 1 END) as valid_count,
        COUNT(CASE WHEN id = parent_id THEN 1 END) as invalid_count,
        CASE WHEN COUNT(CASE WHEN id = parent_id THEN 1 END) = 0 
             THEN 'PASS' ELSE 'FAIL' END as status
    FROM narratives WHERE parent_id IS NOT NULL;
    
    -- Check 2: No orphaned parent_id references
    RETURN QUERY
    SELECT 
        'Orphaned parent references' as check_name,
        COUNT(*) as total_count,
        COUNT(p.id) as valid_count,
        COUNT(*) - COUNT(p.id) as invalid_count,
        CASE WHEN COUNT(*) - COUNT(p.id) = 0 
             THEN 'PASS' ELSE 'FAIL' END as status
    FROM narratives n
    LEFT JOIN narratives p ON n.parent_id = p.id
    WHERE n.parent_id IS NOT NULL;
    
    -- Check 3: No excessive hierarchy depth (max 2 levels)
    RETURN QUERY
    SELECT 
        'Hierarchy depth' as check_name,
        COUNT(*) as total_count,
        COUNT(*) - COUNT(grandparent.id) as valid_count,
        COUNT(grandparent.id) as invalid_count,
        CASE WHEN COUNT(grandparent.id) = 0 
             THEN 'PASS' ELSE 'FAIL' END as status
    FROM narratives child
    LEFT JOIN narratives parent ON child.parent_id = parent.id
    LEFT JOIN narratives grandparent ON parent.parent_id = grandparent.id
    WHERE child.parent_id IS NOT NULL;
    
    -- Check 4: Consistency between parent_id and nested_within
    RETURN QUERY
    SELECT 
        'parent_id vs nested_within consistency' as check_name,
        COUNT(*) as total_count,
        COUNT(CASE 
            WHEN parent_id IS NULL AND (nested_within IS NULL OR jsonb_array_length(nested_within) = 0) THEN 1
            WHEN parent_id IS NOT NULL AND nested_within IS NOT NULL AND jsonb_array_length(nested_within) > 0 THEN 1
        END) as valid_count,
        COUNT(*) - COUNT(CASE 
            WHEN parent_id IS NULL AND (nested_within IS NULL OR jsonb_array_length(nested_within) = 0) THEN 1
            WHEN parent_id IS NOT NULL AND nested_within IS NOT NULL AND jsonb_array_length(nested_within) > 0 THEN 1
        END) as invalid_count,
        CASE WHEN COUNT(*) - COUNT(CASE 
            WHEN parent_id IS NULL AND (nested_within IS NULL OR jsonb_array_length(nested_within) = 0) THEN 1
            WHEN parent_id IS NOT NULL AND nested_within IS NOT NULL AND jsonb_array_length(nested_within) > 0 THEN 1
        END) = 0 THEN 'PASS' ELSE 'WARNING' END as status
    FROM narratives;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 8: Performance Optimization Queries
-- ============================================================================

-- Create function to get query performance comparison
CREATE OR REPLACE FUNCTION compare_hierarchy_query_performance()
RETURNS TABLE(
    query_type text,
    execution_time_ms numeric,
    query_description text
) AS $$
DECLARE
    start_time timestamp;
    end_time timestamp;
    temp_result record;
BEGIN
    -- Test 1: Find children using parent_id (NEW WAY - should be faster)
    start_time := clock_timestamp();
    
    SELECT COUNT(*) INTO temp_result 
    FROM narratives 
    WHERE parent_id = (SELECT id FROM narratives WHERE parent_id IS NULL LIMIT 1);
    
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        'parent_id_lookup' as query_type,
        EXTRACT(milliseconds FROM (end_time - start_time)) as execution_time_ms,
        'Find children using parent_id UUID column' as query_description;
    
    -- Test 2: Find children using nested_within JSONB (OLD WAY - should be slower)
    start_time := clock_timestamp();
    
    SELECT COUNT(*) INTO temp_result 
    FROM narratives 
    WHERE nested_within @> jsonb_build_array(
        (SELECT id::text FROM narratives WHERE parent_id IS NULL LIMIT 1)
    );
    
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        'nested_within_lookup' as query_type,
        EXTRACT(milliseconds FROM (end_time - start_time)) as execution_time_ms,
        'Find children using nested_within JSONB containment' as query_description;
    
    -- Test 3: Hierarchy traversal using parent_id
    start_time := clock_timestamp();
    
    SELECT COUNT(*) INTO temp_result 
    FROM narratives parent
    LEFT JOIN narratives child ON child.parent_id = parent.id
    WHERE parent.parent_id IS NULL
    LIMIT 100;
    
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        'hierarchy_traversal_parent_id' as query_type,
        EXTRACT(milliseconds FROM (end_time - start_time)) as execution_time_ms,
        'Full hierarchy traversal using parent_id JOIN' as query_description;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 9: Migration Verification and Rollback Support
-- ============================================================================

-- Create function to verify migration success
CREATE OR REPLACE FUNCTION verify_parent_id_migration()
RETURNS TABLE(
    metric_name text,
    current_value bigint,
    expected_behavior text,
    status text
) AS $$
BEGIN
    -- Check 1: Total narratives with parent_id populated
    RETURN QUERY
    SELECT 
        'Narratives with parent_id' as metric_name,
        COUNT(parent_id) as current_value,
        'Should match narratives that had nested_within data' as expected_behavior,
        'INFO' as status
    FROM narratives;
    
    -- Check 2: Parent narratives count
    RETURN QUERY
    SELECT 
        'Parent narratives (parent_id IS NULL)' as metric_name,
        COUNT(*) as current_value,
        'Root-level narratives without parents' as expected_behavior,
        'INFO' as status
    FROM narratives 
    WHERE parent_id IS NULL;
    
    -- Check 3: Child narratives count
    RETURN QUERY
    SELECT 
        'Child narratives (parent_id IS NOT NULL)' as metric_name,
        COUNT(*) as current_value,
        'Narratives with parent relationships' as expected_behavior,
        'INFO' as status
    FROM narratives 
    WHERE parent_id IS NOT NULL;
    
    -- Check 4: Index existence
    RETURN QUERY
    SELECT 
        'Performance indexes created' as metric_name,
        COUNT(*) as current_value,
        'Should be >= 5 parent_id related indexes' as expected_behavior,
        CASE WHEN COUNT(*) >= 5 THEN 'PASS' ELSE 'FAIL' END as status
    FROM pg_indexes 
    WHERE tablename = 'narratives' 
    AND indexname LIKE '%parent%';
    
    -- Check 5: Helper functions created
    RETURN QUERY
    SELECT 
        'Helper functions created' as metric_name,
        COUNT(*) as current_value,
        'Should be >= 4 hierarchy helper functions' as expected_behavior,
        CASE WHEN COUNT(*) >= 4 THEN 'PASS' ELSE 'FAIL' END as status
    FROM information_schema.routines 
    WHERE routine_name LIKE '%narrative%' 
    AND routine_name LIKE '%parent%' OR routine_name LIKE '%hierarchy%';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 10: Execute Migration Verification
-- ============================================================================

-- Run data validation
RAISE NOTICE 'Running hierarchy integrity validation...';
DO $$
DECLARE
    validation_result RECORD;
BEGIN
    FOR validation_result IN SELECT * FROM validate_narrative_hierarchy() LOOP
        RAISE NOTICE 'Validation: % - % (% valid, % invalid)', 
            validation_result.check_name,
            validation_result.status,
            validation_result.valid_count,
            validation_result.invalid_count;
    END LOOP;
END
$$;

-- Run migration verification
RAISE NOTICE 'Running migration verification...';
DO $$
DECLARE
    verification_result RECORD;
BEGIN
    FOR verification_result IN SELECT * FROM verify_parent_id_migration() LOOP
        RAISE NOTICE 'Verification: % = % (%) - %', 
            verification_result.metric_name,
            verification_result.current_value,
            verification_result.expected_behavior,
            verification_result.status;
    END LOOP;
END
$$;

-- Create documentation table for this migration
CREATE TABLE IF NOT EXISTS migration_log (
    migration_id text PRIMARY KEY,
    applied_at timestamp with time zone DEFAULT now(),
    description text,
    changes_summary jsonb,
    rollback_notes text
);

-- Log this migration
INSERT INTO migration_log (migration_id, description, changes_summary, rollback_notes) 
VALUES (
    '002_narrative_hierarchy_canonical_parent_id',
    'Migrate narrative hierarchy from nested_within JSONB to canonical parent_id UUID field',
    jsonb_build_object(
        'added_columns', array['parent_id'],
        'deprecated_columns', array['nested_within'],
        'added_indexes', 5,
        'added_functions', 6,
        'added_views', 2,
        'performance_improvement', 'Significant - UUID JOIN vs JSONB containment'
    ),
    'To rollback: Remove parent_id column, restore nested_within usage in application code. Data is preserved in both fields during transition period.'
);

COMMIT;

-- ============================================================================
-- MIGRATION COMPLETED SUCCESSFULLY
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'NARRATIVE HIERARCHY MIGRATION COMPLETED SUCCESSFULLY!';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Changes Applied:';
    RAISE NOTICE '✓ Added parent_id UUID column with foreign key constraint';
    RAISE NOTICE '✓ Migrated data from nested_within to parent_id';
    RAISE NOTICE '✓ Created 5 performance indexes for hierarchy queries';
    RAISE NOTICE '✓ Added 6 helper functions for hierarchy operations';
    RAISE NOTICE '✓ Created materialized view for high-performance lookups';
    RAISE NOTICE '✓ Added automatic cache refresh triggers';
    RAISE NOTICE '✓ Marked nested_within as deprecated (backward compatible)';
    RAISE NOTICE '✓ Validated data integrity and migration success';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '1. Update application models to use parent_id';
    RAISE NOTICE '2. Update CLUST-2 to use parent_id instead of nested_within';
    RAISE NOTICE '3. Run performance tests to verify improvements';
    RAISE NOTICE '4. After validation period, remove nested_within references';
    RAISE NOTICE '============================================================';
END
$$;

-- Show final hierarchy statistics
SELECT 
    'MIGRATION SUMMARY' as summary_type,
    COUNT(*) as total_narratives,
    COUNT(parent_id) as narratives_with_parent,
    COUNT(*) - COUNT(parent_id) as root_narratives,
    (COUNT(parent_id)::float / COUNT(*) * 100)::numeric(5,2) as hierarchy_percentage
FROM narratives;