-- Set up proper materialized view refresh order for clean event filtering
-- Dependencies: event_tokens_clean_30d -> event_anchored_triads_clean_30d

-- Function to refresh materialized views in correct dependency order
CREATE OR REPLACE FUNCTION refresh_clean_event_views() 
RETURNS void AS $$
BEGIN
    -- Step 1: Refresh base clean event tokens
    RAISE NOTICE 'Refreshing event_tokens_clean_30d...';
    REFRESH MATERIALIZED VIEW event_tokens_clean_30d;
    
    -- Step 2: Refresh clean triads that depend on clean events
    RAISE NOTICE 'Refreshing event_anchored_triads_clean_30d...';
    REFRESH MATERIALIZED VIEW event_anchored_triads_clean_30d;
    
    RAISE NOTICE 'Clean event materialized views refreshed successfully';
END;
$$ LANGUAGE plpgsql;

-- Create initial clean event materialized views
SELECT refresh_clean_event_views();

-- Show impact of clean filtering
WITH baseline AS (
    SELECT 
        COUNT(*) as original_events
    FROM event_tokens_30d
),
filtered AS (
    SELECT 
        COUNT(*) as clean_events
    FROM event_tokens_clean_30d
),
triads_baseline AS (
    SELECT 
        COUNT(*) as original_triads
    FROM event_anchored_triads_30d
),
triads_clean AS (
    SELECT 
        COUNT(*) as clean_triads
    FROM event_anchored_triads_clean_30d
)
SELECT 
    'Event Filtering Impact' AS metric,
    b.original_events,
    f.clean_events,
    ROUND(100.0 * f.clean_events / b.original_events, 1) AS event_retention_pct,
    tb.original_triads,
    tc.clean_triads,
    ROUND(100.0 * tc.clean_triads / tb.original_triads, 1) AS triad_retention_pct
FROM baseline b
CROSS JOIN filtered f
CROSS JOIN triads_baseline tb
CROSS JOIN triads_clean tc;