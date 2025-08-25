-- Create minimal event_tokens_clean_30d materialized view
-- Simple filtering to reduce macro cluster noise

-- Drop existing view if it exists
DROP MATERIALIZED VIEW IF EXISTS event_tokens_clean_30d CASCADE;

-- Create the clean event tokens materialized view (minimal version)
CREATE MATERIALIZED VIEW event_tokens_clean_30d AS
SELECT 
    token
FROM event_tokens_30d et
WHERE 
    -- Basic format requirements
    LENGTH(token) >= 4
    AND token ~ '^[a-z]+$'  -- Only lowercase letters
    AND token !~ '^[0-9]+$'  -- Not purely numeric
    AND token !~ '^(19|20)[0-9]{2}$'  -- Not year patterns
    
    -- Additional noise filters
    AND token NOT IN ('said', 'says', 'added', 'told', 'asked', 'noted', 'stated', 'reported', 'announced', 'confirmed')  -- Communication verbs
    AND token NOT IN ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')  -- Days
    AND token NOT IN ('january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december')  -- Months
    AND token NOT IN ('morning', 'afternoon', 'evening', 'night', 'today', 'yesterday', 'tomorrow')  -- Time references
    AND token NOT IN ('people', 'person', 'man', 'woman', 'child', 'children', 'family', 'families')  -- Generic people terms
    AND token NOT IN ('number', 'numbers', 'amount', 'total', 'percent', 'percentage', 'million', 'billion', 'thousand')  -- Numeric terms
    AND token NOT IN ('business', 'company', 'companies', 'market', 'markets', 'economic', 'economy')  -- Generic business terms
    AND token NOT IN ('time', 'year', 'years', 'month', 'months', 'week', 'weeks', 'day', 'days')  -- Time terms
    AND token NOT IN ('government', 'officials', 'official', 'leader', 'leaders', 'president', 'minister')  -- Generic political terms
    AND token NOT IN ('public', 'private', 'local', 'national', 'international', 'global', 'world')  -- Generic scope terms
    
    -- Exclude very short or common terms that create noise
    AND token NOT IN ('news', 'report', 'reports', 'story', 'stories', 'article', 'media')  -- Media terms
    AND token NOT IN ('group', 'groups', 'team', 'teams', 'organization', 'organizations')  -- Generic group terms
ORDER BY token;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_event_tokens_clean_30d_token 
ON event_tokens_clean_30d(token);

-- Verify the view was created and show filtering impact
SELECT 
    'Original event_tokens_30d' AS source,
    COUNT(*) AS token_count
FROM event_tokens_30d
UNION ALL
SELECT 
    'Filtered event_tokens_clean_30d' AS source,
    COUNT(*) AS token_count
FROM event_tokens_clean_30d
ORDER BY source;