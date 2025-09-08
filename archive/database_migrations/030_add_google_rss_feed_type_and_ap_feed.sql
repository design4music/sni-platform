-- Add google_rss to feed_type enum and insert Associated Press Google News feed
-- Migration 030: Add Google RSS feed type and Associated Press feed

-- Add google_rss to the feed_type enum if it doesn't exist
-- Note: This needs to be committed before being used
DO $$ 
BEGIN
    BEGIN
        ALTER TYPE feed_type ADD VALUE 'google_rss';
    EXCEPTION
        WHEN duplicate_object THEN
            -- Value already exists, ignore
            NULL;
    END;
END $$;
INSERT INTO news_feeds (
    id,
    name,
    url,
    feed_type,
    language,
    country_code,
    is_active,
    priority,
    fetch_interval_minutes,
    reliability_score,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'Associated Press (Google News)',
    'https://news.google.com/rss/search?q=site%3Aapnews.com&hl=en-US&gl=US&ceid=US%3Aen',
    'google_rss',
    'EN',
    'US',
    true,
    1,  -- High priority
    60, -- 60 minute fetch interval 
    0.9, -- High reliability
    NOW(),
    NOW()
);

-- Comment
COMMENT ON TYPE feed_type IS 'Feed type enumeration: rss, google_rss, xml_sitemap, api, scraper';