-- Migration: Add parent_id to narratives table for parent/child hierarchy
-- Strategic Narrative Intelligence - CLUST-2 Support
-- 
-- This migration enables parent/child narrative relationships:
-- - parent_id IS NULL = parent narrative
-- - parent_id = UUID = child narrative referencing parent

BEGIN;

-- Add parent_id column to narratives table
ALTER TABLE narratives 
ADD COLUMN parent_id UUID REFERENCES narratives(id) ON DELETE CASCADE;

-- Add index for efficient parent/child queries
CREATE INDEX idx_narratives_parent_id ON narratives(parent_id);

-- Add index for finding all children of a parent
CREATE INDEX idx_narratives_parent_children ON narratives(parent_id) WHERE parent_id IS NOT NULL;

-- Add index for finding all parent narratives
CREATE INDEX idx_narratives_parents ON narratives(parent_id) WHERE parent_id IS NULL;

-- Add check constraint to prevent self-reference
ALTER TABLE narratives 
ADD CONSTRAINT chk_narratives_no_self_reference 
CHECK (id != parent_id);

-- Add fringe_notes field for tracking excluded narrative frames
ALTER TABLE narratives 
ADD COLUMN fringe_notes JSONB DEFAULT NULL;

-- Add index for fringe_notes queries
CREATE INDEX idx_narratives_fringe_notes_gin ON narratives USING gin(fringe_notes);

-- Update narrative_id generation to support parent/child structure
-- Parent narratives: EN-YYYYMMDD-XXX (existing format)
-- Child narratives: EN-YYYYMMDD-XXX-C01, EN-YYYYMMDD-XXX-C02, etc.

-- Add comment to document the hierarchy structure
COMMENT ON COLUMN narratives.parent_id IS 'NULL for parent narratives, UUID of parent for child narratives';
COMMENT ON COLUMN narratives.fringe_notes IS 'JSON field storing information about excluded/merged narrative frames during CLUST-2 processing';

-- Add constraint to ensure narrative hierarchy depth doesn't exceed 2 levels
-- (no grandchildren - only parent -> child relationships)
CREATE OR REPLACE FUNCTION check_narrative_hierarchy_depth()
RETURNS TRIGGER AS $$
BEGIN
    -- If this is a child narrative (has parent_id)
    IF NEW.parent_id IS NOT NULL THEN
        -- Check if the parent already has a parent (would create grandchild)
        IF EXISTS (
            SELECT 1 FROM narratives 
            WHERE id = NEW.parent_id 
            AND parent_id IS NOT NULL
        ) THEN
            RAISE EXCEPTION 'Narrative hierarchy cannot exceed 2 levels (parent -> child only)';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_narrative_hierarchy_depth
    BEFORE INSERT OR UPDATE ON narratives
    FOR EACH ROW
    EXECUTE FUNCTION check_narrative_hierarchy_depth();

-- Create view for easy parent/child navigation
CREATE VIEW narrative_hierarchy AS
SELECT 
    child.id as child_id,
    child.narrative_id as child_narrative_id,
    child.title as child_title,
    child.summary as child_summary,
    parent.id as parent_id,
    parent.narrative_id as parent_narrative_id,
    parent.title as parent_title,
    parent.summary as parent_summary,
    child.created_at as child_created_at,
    parent.created_at as parent_created_at
FROM narratives child
LEFT JOIN narratives parent ON child.parent_id = parent.id;

-- Grant appropriate permissions (adjust as needed for your user setup)
-- GRANT SELECT, INSERT, UPDATE ON narratives TO etl_user;
-- GRANT SELECT ON narrative_hierarchy TO etl_user;

COMMIT;

-- Migration completed successfully
-- Next: Run CLUST-2 segmentation to populate parent/child relationships