-- CLUST-2: Add bucket_members mapping table
-- Minimal join table to track which titles belong to which buckets

-- Create bucket_members mapping table
CREATE TABLE IF NOT EXISTS bucket_members (
    bucket_id UUID REFERENCES buckets(id) ON DELETE CASCADE,
    title_id  UUID REFERENCES titles(id)  ON DELETE CASCADE,
    added_at  TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (bucket_id, title_id)
);

-- Performance indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_bucket_members_bucket ON bucket_members(bucket_id);
CREATE INDEX IF NOT EXISTS idx_bucket_members_title ON bucket_members(title_id);
CREATE INDEX IF NOT EXISTS idx_bucket_members_added ON bucket_members(added_at);

-- Composite index for membership queries
CREATE INDEX IF NOT EXISTS idx_bucket_members_lookup ON bucket_members(bucket_id, title_id);

-- Comment for documentation
COMMENT ON TABLE bucket_members IS 'CLUST-2: Maps titles to buckets for actor-set grouping';
COMMENT ON COLUMN bucket_members.bucket_id IS 'Reference to bucket containing this title';
COMMENT ON COLUMN bucket_members.title_id IS 'Reference to title that belongs to the bucket';
COMMENT ON COLUMN bucket_members.added_at IS 'When this title was added to the bucket';