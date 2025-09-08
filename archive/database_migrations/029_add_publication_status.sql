-- Add Publication Status Field to Narratives
-- Strategic Narrative Intelligence Platform
-- Migration 029: Add missing publication_status column for publisher functionality

-- Step 1: Add publication_status column with proper constraints
ALTER TABLE narratives 
ADD COLUMN IF NOT EXISTS publication_status TEXT 
CHECK (publication_status IN ('draft', 'published', 'archived', 'rejected')) 
DEFAULT 'draft';

-- Step 2: Create index for performance on publication queries
CREATE INDEX IF NOT EXISTS idx_narratives_publication_status 
ON narratives (publication_status) 
WHERE publication_status IS NOT NULL;

-- Step 3: Migrate existing data based on consolidation_stage
-- Map existing consolidation_stage values to publication_status
UPDATE narratives SET publication_status = 
    CASE consolidation_stage
        WHEN 'raw' THEN 'draft'           -- New narratives ready for review
        WHEN 'consolidated' THEN 'draft'  -- Consolidated narratives ready for publishing
        WHEN 'archived' THEN 'archived'   -- Keep archived status
        ELSE 'draft'                      -- Default for any other values
    END
WHERE publication_status IS NULL OR publication_status = 'draft';

-- Step 4: Add publication tracking fields
ALTER TABLE narratives 
ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ NULL,
ADD COLUMN IF NOT EXISTS published_by TEXT NULL,
ADD COLUMN IF NOT EXISTS publication_metadata JSONB DEFAULT '{}';

-- Step 5: Create indexes for publication queries
CREATE INDEX IF NOT EXISTS idx_narratives_published_at 
ON narratives (published_at DESC) 
WHERE published_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_narratives_publication_metadata 
ON narratives USING GIN (publication_metadata) 
WHERE publication_metadata != '{}';

-- Step 6: Create publication status transition trigger
CREATE OR REPLACE FUNCTION update_publication_timestamps()
RETURNS TRIGGER AS $$
BEGIN
    -- When status changes to 'published', set published_at
    IF OLD.publication_status != 'published' AND NEW.publication_status = 'published' THEN
        NEW.published_at = NOW();
        
        -- Add publication event to activity_timeline
        NEW.activity_timeline = COALESCE(NEW.activity_timeline, '[]'::jsonb) || 
            jsonb_build_object(
                'ts', NOW(),
                'stage', 'publisher',
                'action', 'narrative_published',
                'previous_status', OLD.publication_status,
                'published_at', NOW()
            );
    END IF;
    
    -- When status changes from 'published', clear published_at if moving to draft
    IF OLD.publication_status = 'published' AND NEW.publication_status = 'draft' THEN
        NEW.published_at = NULL;
        NEW.published_by = NULL;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger
DROP TRIGGER IF EXISTS update_publication_timestamps_trigger ON narratives;
CREATE TRIGGER update_publication_timestamps_trigger
    BEFORE UPDATE ON narratives
    FOR EACH ROW
    WHEN (OLD.publication_status IS DISTINCT FROM NEW.publication_status)
    EXECUTE FUNCTION update_publication_timestamps();

-- Step 7: Create views for common publication queries
CREATE OR REPLACE VIEW published_narratives AS
SELECT 
    narrative_id,
    title,
    summary,
    publication_status,
    published_at,
    published_by,
    consolidation_stage,
    activity_timeline,
    publication_metadata,
    created_at,
    updated_at
FROM narratives 
WHERE publication_status = 'published'
ORDER BY published_at DESC;

CREATE OR REPLACE VIEW draft_narratives AS
SELECT 
    narrative_id,
    title,
    summary,
    publication_status,
    consolidation_stage,
    activity_timeline,
    created_at,
    updated_at
FROM narratives 
WHERE publication_status = 'draft'
  AND consolidation_stage IN ('raw', 'consolidated')
ORDER BY updated_at DESC;

-- Step 8: Update materialized view dependencies if they exist
-- Refresh any views that might depend on narratives table structure
DO $$
BEGIN
    -- Try to refresh narrative-related views (ignore errors if they don't exist)
    BEGIN
        REFRESH MATERIALIZED VIEW narrative_hierarchy_cache;
        RAISE NOTICE 'Refreshed narrative_hierarchy_cache';
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'narrative_hierarchy_cache not found or refresh failed: %', SQLERRM;
    END;
END
$$;

-- Step 9: Add comments for documentation
COMMENT ON COLUMN narratives.publication_status IS 'Publication workflow status: draft, published, archived, rejected';
COMMENT ON COLUMN narratives.published_at IS 'Timestamp when narrative was published (NULL for unpublished)';
COMMENT ON COLUMN narratives.published_by IS 'User or system that published the narrative';
COMMENT ON COLUMN narratives.publication_metadata IS 'Additional publication metadata (channels, versions, etc.)';

COMMENT ON VIEW published_narratives IS 'All published narratives ordered by publication date';
COMMENT ON VIEW draft_narratives IS 'All draft narratives ready for publication review';

COMMENT ON TRIGGER update_publication_timestamps_trigger ON narratives IS 'Automatically updates publication timestamps and activity timeline';

-- Migration summary and verification
SELECT 
    COUNT(*) as total_narratives,
    COUNT(*) FILTER (WHERE publication_status = 'draft') as draft_count,
    COUNT(*) FILTER (WHERE publication_status = 'published') as published_count,
    COUNT(*) FILTER (WHERE publication_status = 'archived') as archived_count,
    COUNT(*) FILTER (WHERE published_at IS NOT NULL) as has_published_timestamp
FROM narratives;