-- Create event_signals_30d materialized view
-- Union of clean event tokens and eventlike title bigrams

DROP MATERIALIZED VIEW IF EXISTS event_signals_30d CASCADE;

CREATE MATERIALIZED VIEW event_signals_30d AS
SELECT token AS signal, 'token' AS kind 
FROM event_tokens_clean_30d
UNION
SELECT bigram AS signal, 'bigram' AS kind 
FROM eventlike_title_bigrams_30d
ORDER BY signal;

-- Create unique index for fast lookups
CREATE UNIQUE INDEX IF NOT EXISTS idx_event_signals_30d 
ON event_signals_30d(signal);

-- Create index by kind for filtering
CREATE INDEX IF NOT EXISTS idx_event_signals_30d_kind 
ON event_signals_30d(kind);

-- Verify the view was created and show composition
SELECT 
    kind,
    COUNT(*) AS signal_count
FROM event_signals_30d
GROUP BY kind
UNION ALL
SELECT 
    'TOTAL' AS kind,
    COUNT(*) AS signal_count
FROM event_signals_30d
ORDER BY kind;