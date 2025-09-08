-- Migration 004: Add fringe_notes and data_quality_notes JSONB fields
-- Strategic Narrative Intelligence Platform

BEGIN;

-- Add the JSONB columns
ALTER TABLE narratives 
ADD COLUMN fringe_notes JSONB DEFAULT '[]'::jsonb,
ADD COLUMN data_quality_notes JSONB DEFAULT '[]'::jsonb;

-- Add validation constraints
ALTER TABLE narratives
ADD CONSTRAINT valid_fringe_notes CHECK (jsonb_typeof(fringe_notes) = 'array'),
ADD CONSTRAINT valid_data_quality_notes CHECK (jsonb_typeof(data_quality_notes) = 'array');

-- Add GIN indexes for efficient JSONB queries
CREATE INDEX idx_narratives_fringe_notes_gin ON narratives USING GIN (fringe_notes);
CREATE INDEX idx_narratives_data_quality_notes_gin ON narratives USING GIN (data_quality_notes);

COMMIT;