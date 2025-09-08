-- Create event_tokens_clean_30d materialized view
-- Strategic event filtering to reduce macro cluster noise from 71% to target <20%

-- Drop existing view if it exists
DROP MATERIALIZED VIEW IF EXISTS event_tokens_clean_30d CASCADE;

-- Create the clean event tokens materialized view
CREATE MATERIALIZED VIEW event_tokens_clean_30d AS
WITH countries AS (
    -- Load country tokens
    SELECT LOWER(name) AS country_tok FROM ref_countries
),
hubs AS (
    -- Load hub tokens to exclude
    SELECT tok FROM keyword_hubs_30d
),
person_entities AS (
    -- Exclude person names from spaCy NER
    SELECT DISTINCT LOWER(entity_text) AS entity_tok
    FROM article_entities ae
    JOIN articles a ON a.id = ae.article_id
    WHERE ae.entity_label = 'PERSON'
      AND a.published_at >= NOW() - INTERVAL '30 days'
      AND a.language = 'EN'
),
gpe_org_entities AS (
    -- Exclude GPE/ORG entities from spaCy NER
    SELECT DISTINCT LOWER(entity_text) AS entity_tok
    FROM article_entities ae
    JOIN articles a ON a.id = ae.article_id
    WHERE ae.entity_label IN ('GPE', 'ORG')
      AND a.published_at >= NOW() - INTERVAL '30 days'
      AND a.language = 'EN'
),
shared_lib AS (
    -- Load shared keywords library (df >= 2)
    SELECT token AS tok FROM shared_keywords_lib_norm_30d
),
event_candidates AS (
    -- Start with base event tokens from auto-discovery
    SELECT 
        et.token,
        et.country_cooccur,
        et.days_active
    FROM event_tokens_30d et
    WHERE et.token IS NOT NULL
),
country_cooccurrence AS (
    -- Calculate country co-occurrence metrics for each event candidate
    SELECT 
        ack.token,
        COUNT(DISTINCT a.id) as total_docs,
        COUNT(DISTINCT CASE 
            WHEN EXISTS (
                SELECT 1 FROM article_core_keywords ack2
                WHERE ack2.article_id = ack.article_id
                  AND ack2.token IN (SELECT country_tok FROM countries)
            ) THEN a.id 
        END) as docs_with_countries,
        COUNT(DISTINCT CASE 
            WHEN EXISTS (
                SELECT 1 FROM article_core_keywords ack2
                WHERE ack2.article_id = ack.article_id
                  AND ack2.token IN (SELECT country_tok FROM countries)
            ) THEN ack2.token
        END) as distinct_countries
    FROM article_core_keywords ack
    JOIN articles a ON a.id = ack.article_id
    WHERE a.published_at >= NOW() - INTERVAL '30 days'
      AND a.language = 'EN'
      AND ack.token IN (SELECT token FROM event_candidates)
    GROUP BY ack.token
),
filtered_events AS (
    -- Apply comprehensive filtering rules
    SELECT 
        ec.token,
        ec.country_cooccur,
        ec.days_active,
        cc.total_docs,
        cc.docs_with_countries,
        cc.distinct_countries
    FROM event_candidates ec
    JOIN country_cooccurrence cc ON cc.token = ec.token
    WHERE 
        -- Basic format requirements
        LENGTH(ec.token) >= 4
        AND ec.token ~ '^[a-z]+$'  -- Only lowercase letters
        AND ec.token !~ '^[0-9]+$'  -- Not purely numeric
        AND ec.token !~ '^(19|20)[0-9]{2}$'  -- Not year patterns
        
        -- Activity requirements
        AND ec.days_active >= 2  -- Active across multiple days
        
        -- Country co-occurrence requirements
        AND (cc.docs_with_countries >= 3 OR cc.distinct_countries >= 2)
        
        -- Exclusion filters
        AND ec.token NOT IN (SELECT country_tok FROM countries)  -- Not countries
        AND ec.token NOT IN (SELECT tok FROM hubs)  -- Not hubs
        AND ec.token NOT IN (SELECT entity_tok FROM person_entities)  -- Not persons
        AND ec.token NOT IN (SELECT entity_tok FROM gpe_org_entities)  -- Not GPE/ORG
        
        -- Must be in shared keywords library
        AND ec.token IN (SELECT tok FROM shared_lib)
        
        -- Additional noise filters
        AND ec.token NOT IN ('said', 'says', 'added', 'told', 'asked', 'noted', 'stated', 'reported', 'announced', 'confirmed')  -- Communication verbs
        AND ec.token NOT IN ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')  -- Days
        AND ec.token NOT IN ('january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december')  -- Months
        AND ec.token NOT IN ('morning', 'afternoon', 'evening', 'night', 'today', 'yesterday', 'tomorrow')  -- Time references
        AND ec.token NOT IN ('people', 'person', 'man', 'woman', 'child', 'children', 'family', 'families')  -- Generic people terms
        AND ec.token NOT IN ('number', 'numbers', 'amount', 'total', 'percent', 'percentage', 'million', 'billion', 'thousand')  -- Numeric terms
)
SELECT 
    token,
    country_cooccur,
    days_active,
    total_docs,
    docs_with_countries,
    distinct_countries,
    -- Calculate quality score for ranking
    (country_cooccur::float * 0.4 + days_active::float * 0.3 + distinct_countries::float * 0.3) AS quality_score
FROM filtered_events
ORDER BY quality_score DESC;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_event_tokens_clean_30d_token 
ON event_tokens_clean_30d(token);

CREATE INDEX IF NOT EXISTS idx_event_tokens_clean_30d_quality 
ON event_tokens_clean_30d(quality_score DESC);

-- Verify the view was created and show filtering impact
SELECT 
    'Original event_tokens_30d' AS source,
    COUNT(*) AS token_count,
    NULL AS avg_quality_score
FROM event_tokens_30d
UNION ALL
SELECT 
    'Filtered event_tokens_clean_30d' AS source,
    COUNT(*) AS token_count,
    ROUND(AVG(quality_score), 2) AS avg_quality_score
FROM event_tokens_clean_30d
ORDER BY source;