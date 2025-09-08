-- Create eventlike_title_bigrams_30d materialized view
-- Mine clean action bigrams from article titles to augment event signals

DROP MATERIALIZED VIEW IF EXISTS eventlike_title_bigrams_30d CASCADE;

CREATE MATERIALIZED VIEW eventlike_title_bigrams_30d AS
WITH a AS (
    SELECT 
        id, 
        lower(regexp_replace(title, '[^a-z0-9 -]', ' ', 'g')) AS t, 
        published_at
    FROM articles
    WHERE language = 'EN' 
      AND published_at >= now() - interval '30 days' 
      AND title IS NOT NULL
      AND length(title) > 10  -- Skip very short titles
),
words AS (
    SELECT 
        id, 
        published_at,
        regexp_split_to_array(regexp_replace(t, '\s+', ' ', 'g'), '\s+') AS word_array
    FROM a
    WHERE t IS NOT NULL AND trim(t) != ''
),
bigrams AS (
    SELECT 
        id, 
        published_at,
        word_array[i] || ' ' || word_array[i+1] AS bg
    FROM words, generate_series(1, array_length(word_array, 1) - 1) AS i
    WHERE array_length(word_array, 1) >= 2
      AND word_array[i] IS NOT NULL 
      AND word_array[i+1] IS NOT NULL
      AND length(word_array[i]) >= 2
      AND length(word_array[i+1]) >= 2
),
clean AS (
    SELECT 
        id, 
        published_at,
        regexp_replace(bg, '\s+', ' ', 'g') AS bg
    FROM bigrams
    WHERE bg ~ '^[a-z][a-z0-9 -]*[a-z0-9]$'
      AND bg !~ '^\d'
      AND bg !~ '\b(sport|celebrity|gossip|entertainment|music|movie|film|game|games)\b'
      AND bg !~ '\b(said|says|told|asked|added|noted|stated|reported|announced)\b'
      AND bg !~ '\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b'
      AND bg !~ '\b(january|february|march|april|may|june|july|august|september|october|november|december)\b'
      AND length(bg) >= 6  -- Minimum meaningful length
      AND length(bg) <= 25 -- Maximum reasonable length
),
active_days AS (
    SELECT 
        bg, 
        COUNT(DISTINCT date_trunc('day', published_at)) AS days
    FROM clean 
    GROUP BY bg
),
geo_link AS (
    -- Require co-occurrence with at least one country token in article keywords
    SELECT 
        c.bg, 
        COUNT(DISTINCT c.id) AS total_docs,
        COUNT(DISTINCT CASE 
            WHEN EXISTS (
                SELECT 1 FROM article_core_keywords ack2
                JOIN ref_countries rc ON lower(rc.name) = ack2.token
                WHERE ack2.article_id = c.id
            ) THEN c.id 
        END) AS co_doc_with_country
    FROM clean c
    GROUP BY c.bg
),
bad AS (
    -- Drop entity-like bigrams (crude filter)
    SELECT bg FROM clean 
    WHERE bg ~ '\b(minister|president|prime minister|mr|ms|dr|chairman|ceo|director)\b'
      OR bg ~ '\b(company|corporation|limited|ltd|inc|group|holdings)\b'
      OR bg ~ '\b(university|college|school|hospital|church|hotel)\b'
)
SELECT g.bg AS bigram
FROM geo_link g
JOIN active_days d ON d.bg = g.bg
WHERE d.days >= 2
  AND g.co_doc_with_country >= 3
  AND g.total_docs >= 5  -- Minimum document frequency
  AND g.bg NOT IN (SELECT bg FROM bad)
ORDER BY g.co_doc_with_country DESC, d.days DESC;

-- Create unique index for performance
CREATE UNIQUE INDEX IF NOT EXISTS idx_eventlike_title_bigrams_30d 
ON eventlike_title_bigrams_30d(bigram);

-- Verify the view was created
SELECT 
    COUNT(*) AS total_bigrams,
    COUNT(DISTINCT left(bigram, 1)) AS first_letter_variety
FROM eventlike_title_bigrams_30d;