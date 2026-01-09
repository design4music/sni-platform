-- Migration: Add Phase 4.2 summary focus line columns to track_configs
-- This enables dynamic prompt customization per centroid type and track

BEGIN;

-- Add new columns for Phase 4.2 summary generation
ALTER TABLE track_configs
ADD COLUMN llm_summary_centroid_focus TEXT,
ADD COLUMN llm_summary_track_focus JSONB;

-- Rename llm_prompt to llm_track_assignment for clarity
ALTER TABLE track_configs
RENAME COLUMN llm_prompt TO llm_track_assignment;

-- Add comments for documentation
COMMENT ON COLUMN track_configs.llm_track_assignment IS 'LLM prompt for Phase 3 track assignment';
COMMENT ON COLUMN track_configs.llm_summary_centroid_focus IS 'Centroid-type focus line for Phase 4.2 summary generation';
COMMENT ON COLUMN track_configs.llm_summary_track_focus IS 'Track-specific focus lines (JSONB map) for Phase 4.2 summary generation';

COMMIT;
