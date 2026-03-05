CREATE TABLE IF NOT EXISTS social_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform TEXT NOT NULL CHECK (platform IN ('telegram', 'x')),
    post_type TEXT NOT NULL CHECK (post_type IN ('trending', 'ctm_spotlight', 'narrative_of_day')),
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    narrative_id UUID,
    external_id TEXT,
    post_text TEXT NOT NULL,
    posted_at TIMESTAMPTZ DEFAULT NOW(),
    error TEXT,
    UNIQUE(platform, post_type, entity_id)
);
CREATE INDEX IF NOT EXISTS idx_social_posts_date ON social_posts(posted_at DESC);
