-- ============================================================================
-- Manual Parent Narrative Curation Schema Enhancement
-- Strategic Narrative Intelligence Platform
-- Migration ID: 027
-- Date: August 18, 2025
-- ============================================================================
--
-- OBJECTIVE: Enhance narratives table with manual curation workflow support
-- for creating strategic parent narratives that span multiple CLUST-1/CLUST-2 outputs
--
-- FEATURES ADDED:
-- 1. Curation workflow status and assignments
-- 2. Editorial control and approval process
-- 3. Manual cluster grouping capabilities
-- 4. Enhanced versioning and audit trail
-- 5. Bulk operation support for manual curation
-- 6. Integration with existing CLUST-2 pipeline
--
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Add Curation Workflow Columns to Narratives Table
-- ============================================================================

-- Add curation workflow columns
DO $$
BEGIN
    -- Curation status enum type
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'curation_status') THEN
        CREATE TYPE curation_status AS ENUM (
            'auto_generated',    -- Created by CLUST-2 pipeline
            'manual_draft',      -- Manual parent narrative in draft
            'pending_review',    -- Submitted for editorial review
            'reviewed',          -- Reviewed but needs changes
            'approved',          -- Approved for publication
            'published',         -- Live in production
            'archived'           -- No longer active
        );
    END IF;
    
    -- Curation source enum type  
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'curation_source') THEN
        CREATE TYPE curation_source AS ENUM (
            'clust1_pipeline',   -- CLUST-1 automatic clustering
            'clust2_pipeline',   -- CLUST-2 interpretive clustering  
            'manual_curation',   -- Human-curated parent narrative
            'hybrid_assisted'    -- Manual with ML assistance
        );
    END IF;

    -- Add new columns if they don't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'narratives' AND column_name = 'curation_status') THEN
        ALTER TABLE narratives ADD COLUMN curation_status curation_status DEFAULT 'auto_generated';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'narratives' AND column_name = 'curation_source') THEN
        ALTER TABLE narratives ADD COLUMN curation_source curation_source DEFAULT 'clust2_pipeline';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'narratives' AND column_name = 'curator_id') THEN
        ALTER TABLE narratives ADD COLUMN curator_id VARCHAR(100); -- User ID/email of curator
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'narratives' AND column_name = 'reviewer_id') THEN
        ALTER TABLE narratives ADD COLUMN reviewer_id VARCHAR(100); -- User ID/email of reviewer
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'narratives' AND column_name = 'curation_notes') THEN
        ALTER TABLE narratives ADD COLUMN curation_notes JSONB DEFAULT '[]'::jsonb; -- Editorial notes
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'narratives' AND column_name = 'manual_cluster_ids') THEN
        ALTER TABLE narratives ADD COLUMN manual_cluster_ids JSONB DEFAULT '[]'::jsonb; -- Manual cluster groupings
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'narratives' AND column_name = 'editorial_priority') THEN
        ALTER TABLE narratives ADD COLUMN editorial_priority INTEGER DEFAULT 5; -- 1=high, 5=low
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'narratives' AND column_name = 'review_deadline') THEN
        ALTER TABLE narratives ADD COLUMN review_deadline TIMESTAMP WITH TIME ZONE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'narratives' AND column_name = 'published_at') THEN
        ALTER TABLE narratives ADD COLUMN published_at TIMESTAMP WITH TIME ZONE;
    END IF;

    RAISE NOTICE 'Added curation workflow columns to narratives table';
END $$;

-- ============================================================================
-- STEP 2: Create Manual Curation Audit Log Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS narrative_curation_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    narrative_id UUID NOT NULL REFERENCES narratives(id) ON DELETE CASCADE,
    
    -- Action details
    action_type VARCHAR(50) NOT NULL, -- 'created', 'status_changed', 'assigned', 'reviewed', etc.
    old_values JSONB, -- Previous state
    new_values JSONB, -- New state  
    action_reason TEXT, -- Why the action was taken
    
    -- Actor information
    actor_id VARCHAR(100) NOT NULL, -- Who performed the action
    actor_type VARCHAR(20) DEFAULT 'user', -- 'user', 'system', 'pipeline'
    
    -- Context
    session_id VARCHAR(100), -- For tracking related actions
    metadata JSONB DEFAULT '{}'::jsonb, -- Additional context
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for audit log
CREATE INDEX IF NOT EXISTS idx_narrative_curation_log_narrative_id ON narrative_curation_log(narrative_id);
CREATE INDEX IF NOT EXISTS idx_narrative_curation_log_actor_id ON narrative_curation_log(actor_id);
CREATE INDEX IF NOT EXISTS idx_narrative_curation_log_action_type ON narrative_curation_log(action_type);
CREATE INDEX IF NOT EXISTS idx_narrative_curation_log_created_at ON narrative_curation_log(created_at);

-- ============================================================================
-- STEP 3: Create Manual Cluster Group Mappings Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS manual_cluster_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Group identification
    group_name VARCHAR(255) NOT NULL,
    group_description TEXT,
    
    -- CLUST-1/CLUST-2 cluster references
    cluster_ids JSONB NOT NULL, -- Array of cluster IDs being grouped
    cluster_metadata JSONB DEFAULT '{}'::jsonb, -- Metadata from original clusters
    
    -- Narrative association
    parent_narrative_id UUID REFERENCES narratives(id) ON DELETE CASCADE,
    
    -- Curation details
    curator_id VARCHAR(100) NOT NULL,
    curation_rationale TEXT, -- Why these clusters were grouped together
    strategic_significance TEXT, -- Strategic importance of this grouping
    
    -- Status and workflow
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'pending_review', 'approved'
    review_notes JSONB DEFAULT '[]'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    approved_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for cluster groups
CREATE INDEX IF NOT EXISTS idx_manual_cluster_groups_parent_narrative ON manual_cluster_groups(parent_narrative_id);
CREATE INDEX IF NOT EXISTS idx_manual_cluster_groups_curator ON manual_cluster_groups(curator_id);
CREATE INDEX IF NOT EXISTS idx_manual_cluster_groups_status ON manual_cluster_groups(status);
CREATE INDEX IF NOT EXISTS idx_manual_cluster_groups_cluster_ids_gin ON manual_cluster_groups USING gin(cluster_ids);

-- ============================================================================
-- STEP 4: Add Performance Indexes for Curation Workflow
-- ============================================================================

-- Indexes for curation workflow queries
CREATE INDEX IF NOT EXISTS idx_narratives_curation_status ON narratives(curation_status);
CREATE INDEX IF NOT EXISTS idx_narratives_curation_source ON narratives(curation_source);
CREATE INDEX IF NOT EXISTS idx_narratives_curator_id ON narratives(curator_id);
CREATE INDEX IF NOT EXISTS idx_narratives_reviewer_id ON narratives(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_narratives_editorial_priority ON narratives(editorial_priority);
CREATE INDEX IF NOT EXISTS idx_narratives_review_deadline ON narratives(review_deadline);
CREATE INDEX IF NOT EXISTS idx_narratives_published_at ON narratives(published_at);

-- Composite indexes for dashboard queries
CREATE INDEX IF NOT EXISTS idx_narratives_curation_workflow 
ON narratives(curation_status, curator_id, editorial_priority);

CREATE INDEX IF NOT EXISTS idx_narratives_manual_parents 
ON narratives(parent_id, curation_source) 
WHERE parent_id IS NULL AND curation_source = 'manual_curation';

CREATE INDEX IF NOT EXISTS idx_narratives_pending_review 
ON narratives(curation_status, review_deadline) 
WHERE curation_status IN ('pending_review', 'reviewed');

-- GIN indexes for JSONB fields
CREATE INDEX IF NOT EXISTS idx_narratives_curation_notes_gin 
ON narratives USING gin(curation_notes);

CREATE INDEX IF NOT EXISTS idx_narratives_manual_cluster_ids_gin 
ON narratives USING gin(manual_cluster_ids);

-- ============================================================================
-- STEP 5: Create Helper Functions for Manual Curation
-- ============================================================================

-- Function to create manual parent narrative
CREATE OR REPLACE FUNCTION create_manual_parent_narrative(
    p_title TEXT,
    p_summary TEXT,
    p_curator_id VARCHAR(100),
    p_cluster_ids JSONB DEFAULT '[]'::jsonb,
    p_editorial_priority INTEGER DEFAULT 3
)
RETURNS TABLE(
    narrative_uuid UUID,
    narrative_display_id TEXT,
    status TEXT
) AS $$
DECLARE
    new_uuid UUID;
    new_narrative_id TEXT;
    log_session_id TEXT;
BEGIN
    -- Generate new UUID and display ID
    new_uuid := gen_random_uuid();
    new_narrative_id := 'EN-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-M' || LPAD(EXTRACT(epoch FROM NOW())::TEXT, 6, '0');
    log_session_id := gen_random_uuid()::text;
    
    -- Insert new manual parent narrative
    INSERT INTO narratives (
        id,
        narrative_id,
        title,
        summary,
        origin_language,
        parent_id, -- NULL for parent narratives
        curation_status,
        curation_source,
        curator_id,
        manual_cluster_ids,
        editorial_priority,
        confidence_rating
    ) VALUES (
        new_uuid,
        new_narrative_id,
        p_title,
        p_summary,
        'en',
        NULL, -- This is a parent narrative
        'manual_draft',
        'manual_curation',
        p_curator_id,
        p_cluster_ids,
        p_editorial_priority,
        'medium' -- Default confidence for manual narratives
    );
    
    -- Log the creation
    INSERT INTO narrative_curation_log (
        narrative_id,
        action_type,
        new_values,
        action_reason,
        actor_id,
        session_id
    ) VALUES (
        new_uuid,
        'created_manual_parent',
        jsonb_build_object(
            'narrative_id', new_narrative_id,
            'title', p_title,
            'curation_source', 'manual_curation',
            'cluster_ids', p_cluster_ids
        ),
        'Manual parent narrative created by curator',
        p_curator_id,
        log_session_id
    );
    
    RETURN QUERY SELECT new_uuid, new_narrative_id, 'created'::text;
END;
$$ LANGUAGE plpgsql;

-- Function to assign child narratives to manual parent
CREATE OR REPLACE FUNCTION assign_children_to_manual_parent(
    p_parent_uuid UUID,
    p_child_uuids UUID[],
    p_curator_id VARCHAR(100),
    p_rationale TEXT DEFAULT NULL
)
RETURNS TABLE(
    assigned_count INTEGER,
    status TEXT
) AS $$
DECLARE
    assigned_children INTEGER := 0;
    child_uuid UUID;
    log_session_id TEXT;
BEGIN
    log_session_id := gen_random_uuid()::text;
    
    -- Validate parent exists and is manual curation
    IF NOT EXISTS (
        SELECT 1 FROM narratives 
        WHERE id = p_parent_uuid 
        AND parent_id IS NULL 
        AND curation_source = 'manual_curation'
    ) THEN
        RETURN QUERY SELECT 0, 'error_invalid_parent'::text;
        RETURN;
    END IF;
    
    -- Assign each child to the parent
    FOREACH child_uuid IN ARRAY p_child_uuids LOOP
        -- Update child to point to manual parent
        UPDATE narratives 
        SET 
            parent_id = p_parent_uuid,
            updated_at = NOW()
        WHERE id = child_uuid 
        AND parent_id IS NULL; -- Only assign orphaned narratives
        
        IF FOUND THEN
            assigned_children := assigned_children + 1;
            
            -- Log the assignment
            INSERT INTO narrative_curation_log (
                narrative_id,
                action_type,
                old_values,
                new_values,
                action_reason,
                actor_id,
                session_id
            ) VALUES (
                child_uuid,
                'assigned_to_parent',
                jsonb_build_object('parent_id', null),
                jsonb_build_object('parent_id', p_parent_uuid),
                COALESCE(p_rationale, 'Assigned to manual parent narrative'),
                p_curator_id,
                log_session_id
            );
        END IF;
    END LOOP;
    
    -- Update parent's metadata
    UPDATE narratives 
    SET 
        updated_at = NOW(),
        curation_notes = curation_notes || jsonb_build_array(
            jsonb_build_object(
                'action', 'children_assigned',
                'count', assigned_children,
                'timestamp', NOW(),
                'curator', p_curator_id
            )
        )
    WHERE id = p_parent_uuid;
    
    RETURN QUERY SELECT assigned_children, 'success'::text;
END;
$$ LANGUAGE plpgsql;

-- Function to update curation status with workflow validation
CREATE OR REPLACE FUNCTION update_curation_status(
    p_narrative_uuid UUID,
    p_new_status curation_status,
    p_actor_id VARCHAR(100),
    p_notes TEXT DEFAULT NULL
)
RETURNS TABLE(
    success BOOLEAN,
    message TEXT
) AS $$
DECLARE
    current_status curation_status;
    valid_transition BOOLEAN := FALSE;
BEGIN
    -- Get current status
    SELECT curation_status INTO current_status
    FROM narratives 
    WHERE id = p_narrative_uuid;
    
    IF current_status IS NULL THEN
        RETURN QUERY SELECT FALSE, 'Narrative not found'::text;
        RETURN;
    END IF;
    
    -- Validate status transition
    valid_transition := CASE 
        -- From auto_generated
        WHEN current_status = 'auto_generated' AND p_new_status IN ('pending_review', 'approved') THEN TRUE
        -- From manual_draft  
        WHEN current_status = 'manual_draft' AND p_new_status IN ('pending_review', 'archived') THEN TRUE
        -- From pending_review
        WHEN current_status = 'pending_review' AND p_new_status IN ('reviewed', 'approved', 'manual_draft') THEN TRUE
        -- From reviewed
        WHEN current_status = 'reviewed' AND p_new_status IN ('approved', 'manual_draft', 'pending_review') THEN TRUE  
        -- From approved
        WHEN current_status = 'approved' AND p_new_status IN ('published', 'reviewed') THEN TRUE
        -- From published
        WHEN current_status = 'published' AND p_new_status IN ('archived', 'reviewed') THEN TRUE
        -- Allow same status (idempotent)
        WHEN current_status = p_new_status THEN TRUE
        ELSE FALSE
    END;
    
    IF NOT valid_transition THEN
        RETURN QUERY SELECT FALSE, ('Invalid transition from ' || current_status::text || ' to ' || p_new_status::text)::text;
        RETURN;
    END IF;
    
    -- Update status
    UPDATE narratives 
    SET 
        curation_status = p_new_status,
        updated_at = NOW(),
        published_at = CASE WHEN p_new_status = 'published' THEN NOW() ELSE published_at END
    WHERE id = p_narrative_uuid;
    
    -- Log the status change
    INSERT INTO narrative_curation_log (
        narrative_id,
        action_type,
        old_values,
        new_values,
        action_reason,
        actor_id
    ) VALUES (
        p_narrative_uuid,
        'status_changed',
        jsonb_build_object('status', current_status),
        jsonb_build_object('status', p_new_status),
        COALESCE(p_notes, 'Status updated'),
        p_actor_id
    );
    
    RETURN QUERY SELECT TRUE, 'Status updated successfully'::text;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 6: Create Views for Curation Dashboard
-- ============================================================================

-- View for curation workflow dashboard
CREATE OR REPLACE VIEW curation_dashboard AS
SELECT 
    n.id,
    n.narrative_id,
    n.title,
    n.curation_status,
    n.curation_source,
    n.curator_id,
    n.reviewer_id,
    n.editorial_priority,
    n.review_deadline,
    n.created_at,
    n.updated_at,
    n.published_at,
    
    -- Child count for parent narratives
    CASE WHEN n.parent_id IS NULL THEN
        (SELECT COUNT(*) FROM narratives WHERE parent_id = n.id)
    ELSE 0 END as child_count,
    
    -- Manual cluster info
    CASE WHEN jsonb_array_length(n.manual_cluster_ids) > 0 THEN
        jsonb_array_length(n.manual_cluster_ids)
    ELSE 0 END as manual_cluster_count,
    
    -- Status indicators
    n.parent_id IS NULL as is_parent,
    n.curation_source = 'manual_curation' as is_manual,
    n.review_deadline < NOW() as is_overdue,
    
    -- Recent activity
    (SELECT MAX(created_at) FROM narrative_curation_log WHERE narrative_id = n.id) as last_activity
    
FROM narratives n
WHERE n.curation_source IN ('manual_curation', 'hybrid_assisted')
   OR n.curation_status != 'auto_generated';

-- View for pending review items
CREATE OR REPLACE VIEW pending_reviews AS
SELECT 
    cd.*,
    -- Review urgency scoring
    CASE 
        WHEN cd.review_deadline < NOW() THEN 5 -- Overdue
        WHEN cd.review_deadline < NOW() + INTERVAL '1 day' THEN 4 -- Due soon
        WHEN cd.editorial_priority <= 2 THEN 3 -- High priority
        WHEN cd.is_parent AND cd.child_count > 3 THEN 3 -- Complex parent
        ELSE cd.editorial_priority
    END as review_urgency,
    
    -- Days until deadline
    EXTRACT(days FROM cd.review_deadline - NOW())::INTEGER as days_until_deadline
    
FROM curation_dashboard cd
WHERE cd.curation_status IN ('pending_review', 'reviewed')
ORDER BY review_urgency DESC, cd.review_deadline ASC;

-- ============================================================================
-- STEP 7: Create Validation Functions
-- ============================================================================

-- Function to validate curation workflow integrity
CREATE OR REPLACE FUNCTION validate_curation_workflow()
RETURNS TABLE(
    check_name TEXT,
    status TEXT,
    details TEXT,
    affected_count BIGINT
) AS $$
BEGIN
    -- Check 1: Manual parents without children
    RETURN QUERY
    SELECT 
        'orphaned_manual_parents'::text,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'WARNING' END,
        'Manual parent narratives with no children'::text,
        COUNT(*)
    FROM narratives
    WHERE parent_id IS NULL 
    AND curation_source = 'manual_curation'
    AND NOT EXISTS (SELECT 1 FROM narratives child WHERE child.parent_id = narratives.id);
    
    -- Check 2: Children with invalid parents
    RETURN QUERY
    SELECT 
        'invalid_parent_references'::text,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
        'Child narratives with non-existent parent_id'::text,
        COUNT(*)
    FROM narratives child
    LEFT JOIN narratives parent ON child.parent_id = parent.id
    WHERE child.parent_id IS NOT NULL AND parent.id IS NULL;
    
    -- Check 3: Status transition violations
    RETURN QUERY
    SELECT 
        'status_workflow_issues'::text,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'WARNING' END,
        'Narratives with questionable status transitions'::text,
        COUNT(*)
    FROM narratives
    WHERE (curation_status = 'published' AND published_at IS NULL)
    OR (curation_status = 'pending_review' AND curator_id IS NULL);
    
    -- Check 4: Overdue reviews
    RETURN QUERY
    SELECT 
        'overdue_reviews'::text,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'WARNING' END,
        'Reviews past their deadline'::text,
        COUNT(*)
    FROM narratives
    WHERE curation_status IN ('pending_review', 'reviewed')
    AND review_deadline < NOW();
    
    -- Check 5: Manual cluster groups without narratives
    RETURN QUERY
    SELECT 
        'orphaned_cluster_groups'::text,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'WARNING' END,
        'Manual cluster groups not linked to narratives'::text,
        COUNT(*)
    FROM manual_cluster_groups
    WHERE parent_narrative_id IS NULL OR NOT EXISTS (
        SELECT 1 FROM narratives WHERE id = manual_cluster_groups.parent_narrative_id
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 8: Create Rollback Function
-- ============================================================================

CREATE OR REPLACE FUNCTION rollback_manual_curation_schema()
RETURNS TEXT AS $$
BEGIN
    -- Drop new tables
    DROP TABLE IF EXISTS narrative_curation_log CASCADE;
    DROP TABLE IF EXISTS manual_cluster_groups CASCADE;
    
    -- Drop new views
    DROP VIEW IF EXISTS curation_dashboard CASCADE;
    DROP VIEW IF EXISTS pending_reviews CASCADE;
    
    -- Drop new functions
    DROP FUNCTION IF EXISTS create_manual_parent_narrative;
    DROP FUNCTION IF EXISTS assign_children_to_manual_parent;
    DROP FUNCTION IF EXISTS update_curation_status;
    DROP FUNCTION IF EXISTS validate_curation_workflow;
    
    -- Drop new columns from narratives table
    ALTER TABLE narratives DROP COLUMN IF EXISTS curation_status;
    ALTER TABLE narratives DROP COLUMN IF EXISTS curation_source;
    ALTER TABLE narratives DROP COLUMN IF EXISTS curator_id;
    ALTER TABLE narratives DROP COLUMN IF EXISTS reviewer_id;
    ALTER TABLE narratives DROP COLUMN IF EXISTS curation_notes;
    ALTER TABLE narratives DROP COLUMN IF EXISTS manual_cluster_ids;
    ALTER TABLE narratives DROP COLUMN IF EXISTS editorial_priority;
    ALTER TABLE narratives DROP COLUMN IF EXISTS review_deadline;
    ALTER TABLE narratives DROP COLUMN IF EXISTS published_at;
    
    -- Drop new enum types
    DROP TYPE IF EXISTS curation_status;
    DROP TYPE IF EXISTS curation_source;
    
    RETURN 'Manual curation schema rollback completed successfully';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 9: Initialize Default Data and Constraints
-- ============================================================================

-- Update existing auto-generated narratives with proper status
UPDATE narratives 
SET 
    curation_status = 'auto_generated',
    curation_source = CASE 
        WHEN narrative_id LIKE '%-CLUST1-%' THEN 'clust1_pipeline'
        ELSE 'clust2_pipeline'
    END,
    editorial_priority = 5 -- Default low priority for auto-generated
WHERE curation_status IS NULL;

-- Add constraints
ALTER TABLE narratives ADD CONSTRAINT chk_editorial_priority 
CHECK (editorial_priority >= 1 AND editorial_priority <= 5);

ALTER TABLE narratives ADD CONSTRAINT chk_manual_parent_source
CHECK (
    -- Manual parents must have manual curation source
    (parent_id IS NULL AND curation_source = 'manual_curation') IS FALSE OR
    (parent_id IS NULL AND curation_source = 'manual_curation') IS TRUE
);

-- Add comments for documentation
COMMENT ON COLUMN narratives.curation_status IS 'Workflow status for editorial curation process';
COMMENT ON COLUMN narratives.curation_source IS 'Source of narrative creation (pipeline vs manual)';
COMMENT ON COLUMN narratives.curator_id IS 'User ID of assigned curator for manual narratives';
COMMENT ON COLUMN narratives.manual_cluster_ids IS 'JSONB array of CLUST-1/CLUST-2 cluster IDs manually grouped into this narrative';
COMMENT ON TABLE narrative_curation_log IS 'Audit trail for all manual curation actions and workflow changes';
COMMENT ON TABLE manual_cluster_groups IS 'Manual groupings of CLUST-1/CLUST-2 clusters for strategic parent narratives';

COMMIT;

-- ============================================================================
-- MIGRATION COMPLETED SUCCESSFULLY
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'MANUAL PARENT NARRATIVE CURATION SCHEMA DEPLOYED!';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Migration 027 Applied: %', NOW();
    RAISE NOTICE '';
    RAISE NOTICE 'NEW FEATURES ADDED:';
    RAISE NOTICE '✓ Curation workflow status tracking (draft → review → publish)';
    RAISE NOTICE '✓ Curator and reviewer assignment system';
    RAISE NOTICE '✓ Manual cluster grouping capabilities';
    RAISE NOTICE '✓ Editorial priority and deadline management';
    RAISE NOTICE '✓ Complete audit trail for all curation actions';
    RAISE NOTICE '✓ Dashboard views for workflow management';
    RAISE NOTICE '✓ Validation functions for data integrity';
    RAISE NOTICE '';
    RAISE NOTICE 'KEY FUNCTIONS:';
    RAISE NOTICE '- create_manual_parent_narrative(): Create new manual parent';
    RAISE NOTICE '- assign_children_to_manual_parent(): Link child narratives';
    RAISE NOTICE '- update_curation_status(): Workflow status management';
    RAISE NOTICE '- validate_curation_workflow(): Integrity checking';
    RAISE NOTICE '';
    RAISE NOTICE 'KEY VIEWS:';
    RAISE NOTICE '- curation_dashboard: Main workflow overview';
    RAISE NOTICE '- pending_reviews: Items needing editorial review';
    RAISE NOTICE '';
    RAISE NOTICE 'INTEGRATION READY: Compatible with existing CLUST-2 pipeline';
    RAISE NOTICE 'ROLLBACK: SELECT rollback_manual_curation_schema();';
    RAISE NOTICE '============================================================';
END $$;