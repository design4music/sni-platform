-- Add iso_codes column to centroids_v3 for map visualization

ALTER TABLE centroids_v3
ADD COLUMN IF NOT EXISTS iso_codes TEXT[];

COMMENT ON COLUMN centroids_v3.iso_codes IS 'ISO 3166-1 alpha-2 country codes for map highlighting';
