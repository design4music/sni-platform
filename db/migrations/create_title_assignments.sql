-- Migration: Create title_assignments junction table for many-to-many title-centroid-track relationships
-- This allows one title to have different tracks for different centroids based on their track_configs

BEGIN;

-- Create title_assignments junction table
CREATE TABLE IF NOT EXISTS title_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title_id UUID NOT NULL REFERENCES titles_v3(id) ON DELETE CASCADE,
    centroid_id TEXT NOT NULL REFERENCES centroids_v3(id),
    track TEXT NOT NULL,
    ctm_id UUID NOT NULL REFERENCES ctm(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(title_id, centroid_id)
);

-- Create indexes for efficient querying
CREATE INDEX idx_title_assignments_title_id ON title_assignments(title_id);
CREATE INDEX idx_title_assignments_centroid_id ON title_assignments(centroid_id);
CREATE INDEX idx_title_assignments_ctm_id ON title_assignments(ctm_id);
CREATE INDEX idx_title_assignments_track ON title_assignments(track);

-- Drop track and ctm_ids columns from titles_v3 (data is now in title_assignments)
ALTER TABLE titles_v3
DROP COLUMN IF EXISTS track,
DROP COLUMN IF EXISTS ctm_ids;

COMMIT;
