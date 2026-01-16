-- Add description field for centroid card subtitles
-- Run with: psql -U postgres -d sni_v2 -f 20260113_add_centroid_description.sql

ALTER TABLE centroids_v3 ADD COLUMN IF NOT EXISTS description TEXT;

COMMENT ON COLUMN centroids_v3.description IS 'Short description for centroid cards (country lists for regions, domain descriptions for systemic)';

-- Verify
SELECT id, label, description FROM centroids_v3 LIMIT 5;
