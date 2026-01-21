-- Add matched_aliases column to titles_v3
-- Stores flat list of normalized alias strings that matched during Phase 2
-- Example: ["greenland", "tariffs", "sanctions"]

ALTER TABLE titles_v3 ADD COLUMN IF NOT EXISTS matched_aliases JSONB;

-- GIN index for efficient querying by alias
CREATE INDEX IF NOT EXISTS idx_titles_v3_matched_aliases 
ON titles_v3 USING GIN(matched_aliases);

COMMENT ON COLUMN titles_v3.matched_aliases IS 
'Flat list of normalized alias strings that matched during centroid detection. Example: ["tariffs", "sanctions"]';
