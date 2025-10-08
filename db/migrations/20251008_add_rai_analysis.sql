-- Migration: Add RAI Analysis support to Framed Narratives
-- Date: October 8, 2025
-- Purpose: Store Risk Assessment Intelligence analysis results from external RAI service

-- Add rai_analysis JSON field to store RAI service response
ALTER TABLE framed_narratives ADD COLUMN rai_analysis JSONB DEFAULT NULL;

-- Add index for querying FNs with/without RAI analysis
CREATE INDEX IF NOT EXISTS idx_framed_narratives_rai_analyzed
    ON framed_narratives(event_family_id)
    WHERE rai_analysis IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_framed_narratives_rai_pending
    ON framed_narratives(created_at DESC)
    WHERE rai_analysis IS NULL;

-- Comment for documentation
COMMENT ON COLUMN framed_narratives.rai_analysis IS 'Risk Assessment Intelligence analysis from external RAI service: adequacy_score, final_synthesis, key_conflicts, blind_spots, radical_shifts';
