-- ============================================================================
-- FRINGE_AND_QUALITY_NOTES: Add structured metadata fields for narrative 
-- outliers and data quality tracking
-- Strategic Narrative Intelligence Platform
-- Migration ID: 004
-- Date: August 4, 2025
-- ============================================================================
--
-- OBJECTIVE: Add structured metadata fields (fringe_notes and data_quality_notes)
-- to capture narrative outliers and pipeline/data quality issues, enhancing 
-- analytical capabilities and transparency.
--
-- IMPLEMENTATION SCOPE:
-- 1. Add fringe_notes JSONB column (default empty array)
-- 2. Convert data_quality_notes from TEXT to JSONB (preserve existing data)
-- 3. Create GIN indexes for efficient JSONB queries
-- 4. Add validation constraints to ensure array type
-- 5. Create helper functions for querying notes
-- 6. Provide rollback capability
--
-- PERFORMANCE IMPACT: Enables efficient JSONB queries and structured analysis
-- DATA SAFETY: Preserves existing data_quality_notes as structured JSONB
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Verify Prerequisites and Current State
-- ============================================================================

-- Create function to check current database state
CREATE OR REPLACE FUNCTION check_fringe_quality_notes_prerequisites()
RETURNS TABLE(
    check_name text,
    status text,
    description text,
    action_required text
) AS $$
BEGIN
    -- Check 1: Verify narratives table exists
    RETURN QUERY
    SELECT 
        'narratives_table_exists'::text as check_name,
        CASE WHEN EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'narratives'
        ) THEN 'PASS' ELSE 'FAIL' END as status,
        'Narratives table must exist for migration'::text as description,
        CASE WHEN EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'narratives'
        ) THEN 'None' ELSE 'Create narratives table first' END::text as action_required;
    
    -- Check 2: Verify data_quality_notes column exists
    RETURN QUERY
    SELECT 
        'data_quality_notes_exists'::text as check_name,
        CASE WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'narratives' AND column_name = 'data_quality_notes'
        ) THEN 'PASS' ELSE 'FAIL' END as status,
        'data_quality_notes column must exist (current TEXT)'::text as description,
        CASE WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'narratives' AND column_name = 'data_quality_notes'
        ) THEN 'None' ELSE 'Add data_quality_notes TEXT column first' END::text as action_required;
    
    -- Check 3: Count existing data_quality_notes values
    RETURN QUERY
    SELECT 
        'existing_data_quality_notes_count'::text as check_name,
        'INFO'::text as status,
        ('Found ' || COALESCE((
            SELECT COUNT(*)::text 
            FROM narratives 
            WHERE data_quality_notes IS NOT NULL AND data_quality_notes != ''
        ), '0') || ' existing data_quality_notes entries')::text as description,
        'Will preserve during JSONB conversion'::text as action_required;
    
    -- Check 4: Check for fringe_notes column existence
    RETURN QUERY
    SELECT 
        'fringe_notes_column_status'::text as check_name,
        CASE WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'narratives' AND column_name = 'fringe_notes'
        ) THEN 'EXISTS' ELSE 'MISSING' END as status,
        'fringe_notes column should not exist yet'::text as description,
        CASE WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'narratives' AND column_name = 'fringe_notes'
        ) THEN 'Column already exists - migration may be partial' 
        ELSE 'Ready to add fringe_notes column' END::text as action_required;
END;
$$ LANGUAGE plpgsql;

-- Run prerequisite checks
SELECT * FROM check_fringe_quality_notes_prerequisites();

-- ============================================================================
-- STEP 2: Add fringe_notes JSONB Column
-- ============================================================================

-- Add fringe_notes column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'narratives' AND column_name = 'fringe_notes'
    ) THEN
        -- Add fringe_notes as JSONB with default empty array
        ALTER TABLE narratives 
        ADD COLUMN fringe_notes JSONB DEFAULT '[]'::jsonb NOT NULL;
        
        RAISE NOTICE 'Added fringe_notes JSONB column with default empty array';
    ELSE
        RAISE NOTICE 'fringe_notes column already exists, skipping...';
    END IF;
END $$;

-- ============================================================================
-- STEP 3: Convert data_quality_notes from TEXT to JSONB
-- ============================================================================

-- Create backup column for safety
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'narratives' AND column_name = 'data_quality_notes_text_backup'
    ) THEN
        ALTER TABLE narratives 
        ADD COLUMN data_quality_notes_text_backup TEXT;
        
        -- Copy existing data to backup
        UPDATE narratives 
        SET data_quality_notes_text_backup = data_quality_notes;
        
        RAISE NOTICE 'Created backup of existing data_quality_notes';
    END IF;
END $$;

-- Add new JSONB column for data_quality_notes
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'narratives' AND column_name = 'data_quality_notes_jsonb'
    ) THEN
        ALTER TABLE narratives 
        ADD COLUMN data_quality_notes_jsonb JSONB DEFAULT '[]'::jsonb NOT NULL;
        
        RAISE NOTICE 'Added data_quality_notes_jsonb column';
    END IF;
END $$;

-- Migrate existing TEXT data to structured JSONB format
UPDATE narratives 
SET data_quality_notes_jsonb = CASE 
    WHEN data_quality_notes IS NULL OR data_quality_notes = '' THEN 
        '[]'::jsonb
    ELSE 
        jsonb_build_array(
            jsonb_build_object(
                'note_type', 'quality',
                'summary', data_quality_notes,
                'source_count', null,
                'example_articles', '[]'::jsonb,
                'detected_at', COALESCE(updated_at, created_at, NOW())::timestamptz,
                'migrated_from_text', true
            )
        )
    END
WHERE data_quality_notes_jsonb = '[]'::jsonb;

-- ============================================================================
-- STEP 4: Replace original data_quality_notes column
-- ============================================================================

-- Drop old TEXT column and rename JSONB column
DO $$
DECLARE
    migration_count INTEGER;
BEGIN
    -- Count how many records were migrated
    SELECT COUNT(*) INTO migration_count
    FROM narratives 
    WHERE data_quality_notes_text_backup IS NOT NULL AND data_quality_notes_text_backup != '';
    
    -- Drop old column and rename new one
    ALTER TABLE narratives DROP COLUMN IF EXISTS data_quality_notes;
    ALTER TABLE narratives RENAME COLUMN data_quality_notes_jsonb TO data_quality_notes;
    
    RAISE NOTICE 'Migrated % existing data_quality_notes entries to JSONB format', migration_count;
END $$;

-- ============================================================================
-- STEP 5: Add Validation Constraints
-- ============================================================================

-- Ensure fringe_notes is always a JSONB array
ALTER TABLE narratives 
ADD CONSTRAINT chk_fringe_notes_is_array 
CHECK (jsonb_typeof(fringe_notes) = 'array');

-- Ensure data_quality_notes is always a JSONB array
ALTER TABLE narratives 
ADD CONSTRAINT chk_data_quality_notes_is_array 
CHECK (jsonb_typeof(data_quality_notes) = 'array');

-- Validate structure of fringe_notes entries
CREATE OR REPLACE FUNCTION validate_fringe_note_structure(note jsonb)
RETURNS boolean AS $$
BEGIN
    -- Check required fields exist and have correct types
    IF NOT (note ? 'note_type' AND note ? 'summary' AND note ? 'detected_at') THEN
        RETURN false;
    END IF;
    
    -- Check note_type is valid
    IF NOT (note->>'note_type' IN ('fringe', 'quality')) THEN
        RETURN false;
    END IF;
    
    -- Check arrays are actually arrays
    IF note ? 'example_articles' AND jsonb_typeof(note->'example_articles') != 'array' THEN
        RETURN false;
    END IF;
    
    RETURN true;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- STEP 6: Create Performance Indexes
-- ============================================================================

-- GIN indexes for efficient JSONB queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_narratives_fringe_notes_gin 
ON narratives USING gin (fringe_notes);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_narratives_data_quality_notes_gin 
ON narratives USING gin (data_quality_notes);

-- Specialized indexes for common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_narratives_fringe_notes_type 
ON narratives USING gin ((fringe_notes -> 'note_type'));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_narratives_quality_notes_type 
ON narratives USING gin ((data_quality_notes -> 'note_type'));

-- Index for notes with specific tones (fringe analysis)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_narratives_fringe_notes_tone 
ON narratives USING gin ((fringe_notes -> 'tone'));

-- Composite index for narrative analysis queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_narratives_notes_analysis 
ON narratives (id, created_at) 
WHERE jsonb_array_length(fringe_notes) > 0 OR jsonb_array_length(data_quality_notes) > 0;

-- ============================================================================
-- STEP 7: Create Helper Functions and Views
-- ============================================================================

-- Function to add fringe note to narrative
CREATE OR REPLACE FUNCTION add_fringe_note(
    narrative_uuid UUID,
    note_summary TEXT,
    source_count INTEGER DEFAULT NULL,
    tone TEXT DEFAULT NULL,
    example_articles TEXT[] DEFAULT ARRAY[]::TEXT[]
)
RETURNS boolean AS $$
DECLARE
    new_note jsonb;
BEGIN
    -- Build new fringe note object
    new_note := jsonb_build_object(
        'note_type', 'fringe',
        'summary', note_summary,
        'source_count', source_count,
        'tone', tone,
        'example_articles', to_jsonb(example_articles),
        'detected_at', NOW()
    );
    
    -- Add note to fringe_notes array
    UPDATE narratives 
    SET fringe_notes = fringe_notes || new_note,
        updated_at = NOW()
    WHERE id = narrative_uuid;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to add data quality note to narrative
CREATE OR REPLACE FUNCTION add_data_quality_note(
    narrative_uuid UUID,
    note_summary TEXT,
    source_count INTEGER DEFAULT NULL,
    example_articles TEXT[] DEFAULT ARRAY[]::TEXT[]
)
RETURNS boolean AS $$
DECLARE
    new_note jsonb;
BEGIN
    -- Build new quality note object
    new_note := jsonb_build_object(
        'note_type', 'quality',
        'summary', note_summary,
        'source_count', source_count,
        'example_articles', to_jsonb(example_articles),
        'detected_at', NOW()
    );
    
    -- Add note to data_quality_notes array
    UPDATE narratives 
    SET data_quality_notes = data_quality_notes || new_note,
        updated_at = NOW()
    WHERE id = narrative_uuid;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to get narratives with fringe content
CREATE OR REPLACE FUNCTION get_narratives_with_fringe_notes(
    limit_count INTEGER DEFAULT 100
)
RETURNS TABLE(
    narrative_id TEXT,
    title TEXT,
    fringe_count INTEGER,
    quality_count INTEGER,
    latest_fringe_note TEXT,
    latest_quality_note TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        n.narrative_id,
        n.title,
        jsonb_array_length(n.fringe_notes) as fringe_count,
        jsonb_array_length(n.data_quality_notes) as quality_count,
        CASE 
            WHEN jsonb_array_length(n.fringe_notes) > 0 THEN 
                (n.fringe_notes -> -1 ->> 'summary')
            ELSE NULL 
        END as latest_fringe_note,
        CASE 
            WHEN jsonb_array_length(n.data_quality_notes) > 0 THEN 
                (n.data_quality_notes -> -1 ->> 'summary')
            ELSE NULL 
        END as latest_quality_note
    FROM narratives n
    WHERE jsonb_array_length(n.fringe_notes) > 0 
       OR jsonb_array_length(n.data_quality_notes) > 0
    ORDER BY n.updated_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- View for fringe analysis
CREATE OR REPLACE VIEW narrative_fringe_analysis AS
SELECT 
    n.narrative_id,
    n.title,
    n.created_at,
    jsonb_array_length(n.fringe_notes) as fringe_note_count,
    jsonb_array_length(n.data_quality_notes) as quality_note_count,
    CASE 
        WHEN jsonb_array_length(n.fringe_notes) > 0 THEN
            (SELECT jsonb_agg(note->>'tone') 
             FROM jsonb_array_elements(n.fringe_notes) note 
             WHERE note->>'tone' IS NOT NULL)
        ELSE NULL
    END as fringe_tones,
    CASE 
        WHEN jsonb_array_length(n.fringe_notes) > 0 THEN
            (SELECT AVG((note->>'source_count')::integer) 
             FROM jsonb_array_elements(n.fringe_notes) note 
             WHERE note->>'source_count' IS NOT NULL)
        ELSE NULL
    END as avg_fringe_source_count
FROM narratives n
WHERE jsonb_array_length(n.fringe_notes) > 0 
   OR jsonb_array_length(n.data_quality_notes) > 0;

-- Function to query narratives by fringe tone
CREATE OR REPLACE FUNCTION get_narratives_by_fringe_tone(
    target_tone TEXT,
    limit_count INTEGER DEFAULT 50
)
RETURNS TABLE(
    narrative_id TEXT,
    title TEXT,
    matching_fringe_notes JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        n.narrative_id,
        n.title,
        (SELECT jsonb_agg(note) 
         FROM jsonb_array_elements(n.fringe_notes) note 
         WHERE note->>'tone' = target_tone) as matching_fringe_notes
    FROM narratives n
    WHERE n.fringe_notes @> jsonb_build_array(
        jsonb_build_object('tone', target_tone)
    )
    ORDER BY n.updated_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 8: Create Migration Verification and Rollback Functions
-- ============================================================================

-- Function to verify migration success
CREATE OR REPLACE FUNCTION verify_fringe_quality_notes_migration()
RETURNS TABLE(
    check_name text,
    status text,
    details text
) AS $$
BEGIN
    -- Check 1: Verify fringe_notes column exists and has correct type
    RETURN QUERY
    SELECT 
        'fringe_notes_column'::text as check_name,
        CASE WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'narratives' 
            AND column_name = 'fringe_notes' 
            AND data_type = 'jsonb'
        ) THEN 'PASS' ELSE 'FAIL' END as status,
        'fringe_notes JSONB column exists'::text as details;
    
    -- Check 2: Verify data_quality_notes is now JSONB
    RETURN QUERY
    SELECT 
        'data_quality_notes_jsonb'::text as check_name,
        CASE WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'narratives' 
            AND column_name = 'data_quality_notes' 
            AND data_type = 'jsonb'
        ) THEN 'PASS' ELSE 'FAIL' END as status,
        'data_quality_notes is now JSONB'::text as details;
    
    -- Check 3: Verify constraints exist
    RETURN QUERY
    SELECT 
        'validation_constraints'::text as check_name,
        CASE WHEN EXISTS (
            SELECT 1 FROM information_schema.check_constraints 
            WHERE constraint_name = 'chk_fringe_notes_is_array'
        ) AND EXISTS (
            SELECT 1 FROM information_schema.check_constraints 
            WHERE constraint_name = 'chk_data_quality_notes_is_array'
        ) THEN 'PASS' ELSE 'FAIL' END as status,
        'Array validation constraints exist'::text as details;
    
    -- Check 4: Verify indexes exist
    RETURN QUERY
    SELECT 
        'gin_indexes'::text as check_name,
        CASE WHEN EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE indexname = 'idx_narratives_fringe_notes_gin'
        ) AND EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE indexname = 'idx_narratives_data_quality_notes_gin'
        ) THEN 'PASS' ELSE 'FAIL' END as status,
        'GIN indexes for JSONB columns exist'::text as details;
    
    -- Check 5: Count migrated records
    RETURN QUERY
    SELECT 
        'migrated_records_count'::text as check_name,
        'INFO'::text as status,
        ('Migrated ' || (
            SELECT COUNT(*)::text 
            FROM narratives 
            WHERE data_quality_notes_text_backup IS NOT NULL 
            AND data_quality_notes_text_backup != ''
        ) || ' existing data_quality_notes to JSONB')::text as details;
    
    -- Check 6: Helper functions exist
    RETURN QUERY
    SELECT 
        'helper_functions'::text as check_name,
        CASE WHEN EXISTS (
            SELECT 1 FROM information_schema.routines 
            WHERE routine_name = 'add_fringe_note'
        ) AND EXISTS (
            SELECT 1 FROM information_schema.routines 
            WHERE routine_name = 'add_data_quality_note'
        ) THEN 'PASS' ELSE 'FAIL' END as status,
        'Helper functions for adding notes exist'::text as details;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 9: Rollback Function (if needed)
-- ============================================================================

CREATE OR REPLACE FUNCTION rollback_fringe_quality_notes_migration()
RETURNS text AS $$
DECLARE
    rollback_count INTEGER;
BEGIN
    -- Restore original data_quality_notes from backup if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'narratives' AND column_name = 'data_quality_notes_text_backup'
    ) THEN
        -- Add back TEXT column
        ALTER TABLE narratives ADD COLUMN data_quality_notes_text TEXT;
        
        -- Restore data from backup
        UPDATE narratives 
        SET data_quality_notes_text = data_quality_notes_text_backup;
        
        GET DIAGNOSTICS rollback_count = ROW_COUNT;
        
        -- Drop JSONB column and rename TEXT column back
        ALTER TABLE narratives DROP COLUMN data_quality_notes;
        ALTER TABLE narratives RENAME COLUMN data_quality_notes_text TO data_quality_notes;
        ALTER TABLE narratives DROP COLUMN data_quality_notes_text_backup;
        
        RETURN 'Rollback completed. Restored ' || rollback_count || ' data_quality_notes entries to TEXT format.';
    ELSE
        RETURN 'No backup found. Cannot rollback data_quality_notes migration.';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 10: Final Verification and Cleanup
-- ============================================================================

-- Run verification
SELECT * FROM verify_fringe_quality_notes_migration();

-- Update migration tracking (if you have a migrations table)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'schema_migrations') THEN
        INSERT INTO schema_migrations (version, applied_at) 
        VALUES ('004_add_fringe_and_quality_notes_jsonb', NOW())
        ON CONFLICT (version) DO UPDATE SET applied_at = NOW();
        
        RAISE NOTICE 'Updated schema_migrations table';
    END IF;
END $$;

-- Clean up temporary functions
DROP FUNCTION IF EXISTS check_fringe_quality_notes_prerequisites();

COMMIT;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Print success message
DO $$
BEGIN
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'FRINGE_AND_QUALITY_NOTES Migration Completed Successfully!';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'Added:';
    RAISE NOTICE '  - fringe_notes JSONB column with GIN index';
    RAISE NOTICE '  - Converted data_quality_notes from TEXT to JSONB';
    RAISE NOTICE '  - Validation constraints for array structure';
    RAISE NOTICE '  - Helper functions: add_fringe_note(), add_data_quality_note()';
    RAISE NOTICE '  - Query functions: get_narratives_with_fringe_notes()';
    RAISE NOTICE '  - Analysis view: narrative_fringe_analysis';
    RAISE NOTICE '';
    RAISE NOTICE 'Usage Examples:';
    RAISE NOTICE '  SELECT add_fringe_note(narrative_uuid, ''Low diversity detected'', 1, ''propagandistic'');';
    RAISE NOTICE '  SELECT * FROM get_narratives_with_fringe_notes(10);';
    RAISE NOTICE '  SELECT * FROM narrative_fringe_analysis;';
    RAISE NOTICE '============================================================================';
END $$;