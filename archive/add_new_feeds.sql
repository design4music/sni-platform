-- Add new RSS feeds to SNI system
-- Run date: 2025-08-30

-- Financial Times feeds
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
) VALUES
(gen_random_uuid(), 'Financial Times World', 'https://www.ft.com/world?format=rss', 'RSS', 'EN', 'GB', true, 1, 60, 0.9, NOW(), NOW()),
(gen_random_uuid(), 'Financial Times Technology', 'https://www.ft.com/technology?format=rss', 'RSS', 'EN', 'GB', true, 1, 60, 0.9, NOW(), NOW()),
(gen_random_uuid(), 'Financial Times Markets', 'https://www.ft.com/markets?format=rss', 'RSS', 'EN', 'GB', true, 1, 60, 0.9, NOW(), NOW()),
(gen_random_uuid(), 'Financial Times Climate', 'https://www.ft.com/climate-capital?format=rss', 'RSS', 'EN', 'GB', true, 1, 60, 0.9, NOW(), NOW()),

-- Fox News feeds
(gen_random_uuid(), 'Fox News Politics', 'https://moxie.foxnews.com/google-publisher/politics.xml', 'RSS', 'EN', 'US', true, 2, 60, 0.8, NOW(), NOW()),
(gen_random_uuid(), 'Fox News World', 'https://moxie.foxnews.com/google-publisher/world.xml', 'RSS', 'EN', 'US', true, 2, 60, 0.8, NOW(), NOW()),
(gen_random_uuid(), 'Fox News Technology', 'https://moxie.foxnews.com/google-publisher/tech.xml', 'RSS', 'EN', 'US', true, 2, 60, 0.8, NOW(), NOW()),

-- Other feeds
(gen_random_uuid(), 'ZeroHedge', 'https://cms.zerohedge.com/fullrss2.xml', 'RSS', 'EN', 'US', true, 2, 60, 0.7, NOW(), NOW()),
(gen_random_uuid(), 'Reason.com', 'https://reason.com/feed/', 'RSS', 'EN', 'US', true, 2, 60, 0.8, NOW(), NOW()),
(gen_random_uuid(), 'Der Spiegel International', 'https://www.spiegel.de/international/index.rss', 'RSS', 'EN', 'DE', true, 2, 60, 0.8, NOW(), NOW()),
(gen_random_uuid(), 'Daily Mail News', 'https://www.dailymail.co.uk/news/index.rss', 'RSS', 'EN', 'GB', true, 3, 60, 0.6, NOW(), NOW());

-- Verify the inserts
SELECT 
    name,
    url,
    country_code,
    priority,
    reliability_score
FROM news_feeds 
WHERE created_at > NOW() - INTERVAL '1 minute'
ORDER BY name;