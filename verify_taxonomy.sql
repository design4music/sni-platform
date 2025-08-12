-- Verify IPTC taxonomy loaded correctly
SELECT 
    source,
    COUNT(*) as topic_count
FROM taxonomy_topics 
GROUP BY source;

-- Check for sports-related topics
SELECT topic_id, name, source 
FROM taxonomy_topics 
WHERE LOWER(name) LIKE '%sport%' 
   OR LOWER(name) LIKE '%football%'
   OR LOWER(name) LIKE '%basketball%'
LIMIT 10;

-- Check language distribution in aliases
SELECT lang, COUNT(*) as alias_count
FROM taxonomy_aliases 
GROUP BY lang 
ORDER BY alias_count DESC;

-- Sample IPTC topics with hierarchy
SELECT 
    topic_id,
    name,
    parent_id,
    array_length(path, 1) as depth
FROM taxonomy_topics 
WHERE source = 'IPTC'
  AND topic_id LIKE 'iptc:15%'  -- Sports category
ORDER BY topic_id
LIMIT 15;