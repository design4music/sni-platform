-- Add bucket columns to events_v3 for geo pre-clustering
-- event_type: 'bilateral', 'multilateral', or 'domestic'
-- bucket_key: For bilateral, the counterparty centroid_id (e.g., 'ASIA-CHINA')

ALTER TABLE events_v3
ADD COLUMN IF NOT EXISTS event_type VARCHAR(20),
ADD COLUMN IF NOT EXISTS bucket_key VARCHAR(100);

-- Add index for filtering by bucket
CREATE INDEX IF NOT EXISTS idx_events_v3_bucket
ON events_v3 (ctm_id, event_type, bucket_key);

-- Comment for documentation
COMMENT ON COLUMN events_v3.event_type IS 'Bucket type: bilateral, multilateral, or domestic';
COMMENT ON COLUMN events_v3.bucket_key IS 'For bilateral: counterparty centroid_id';
