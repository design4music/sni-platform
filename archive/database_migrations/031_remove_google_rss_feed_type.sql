-- Migration: Remove google_rss feed type and all related data
-- This migration removes all Google News integration from the database

BEGIN;

-- Remove all articles from Google RSS feeds
DELETE FROM articles 
WHERE feed_id IN (
    SELECT id FROM news_feeds WHERE feed_type = 'google_rss'
);

-- Remove all Google RSS feeds
DELETE FROM news_feeds 
WHERE feed_type = 'google_rss';

-- Create new enum without google_rss
CREATE TYPE feed_type_new AS ENUM ('RSS', 'xml_sitemap', 'api', 'scraper');

-- Update table to use new enum
ALTER TABLE news_feeds 
ALTER COLUMN feed_type TYPE feed_type_new 
USING feed_type::text::feed_type_new;

-- Drop old enum and rename new one
DROP TYPE feed_type;
ALTER TYPE feed_type_new RENAME TO feed_type;

-- Update comment
COMMENT ON TYPE feed_type IS 'Feed type enumeration: RSS, xml_sitemap, api, scraper';

COMMIT;
