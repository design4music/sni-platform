-- Strategic Narrative Intelligence Platform - Data Validation and Constraints
-- This file contains comprehensive validation rules and business logic constraints

-- =============================================
-- JSON SCHEMA VALIDATION FUNCTIONS
-- =============================================

-- Function to validate NSF-1 frame_logic structure
CREATE OR REPLACE FUNCTION validate_frame_logic(frame_logic_json JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check required fields exist
    IF NOT (frame_logic_json ? 'primary_frame' AND
            frame_logic_json ? 'causal_chains' AND
            jsonb_typeof(frame_logic_json->'causal_chains') = 'array') THEN
        RETURN FALSE;
    END IF;
    
    -- Validate causal chains structure
    IF NOT (
        SELECT bool_and(
            item ? 'cause' AND item ? 'effect' AND 
            item ? 'confidence' AND
            (item->>'confidence')::decimal BETWEEN 0.0 AND 1.0
        )
        FROM jsonb_array_elements(frame_logic_json->'causal_chains') AS item
    ) THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to validate activity_timeline structure
CREATE OR REPLACE FUNCTION validate_activity_timeline(timeline_json JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    -- Must be an array
    IF jsonb_typeof(timeline_json) != 'array' THEN
        RETURN FALSE;
    END IF;
    
    -- Each timeline event must have required fields
    IF NOT (
        SELECT bool_and(
            item ? 'timestamp' AND
            item ? 'event' AND
            item ? 'impact_score' AND
            (item->>'impact_score')::decimal BETWEEN 0.0 AND 1.0
        )
        FROM jsonb_array_elements(timeline_json) AS item
    ) THEN
        RETURN FALSE;
    END IF;
    
    -- Validate timestamp format (basic check)
    IF NOT (
        SELECT bool_and(
            (item->>'timestamp')::timestamp IS NOT NULL
        )
        FROM jsonb_array_elements(timeline_json) AS item
    ) THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to validate turning_points structure
CREATE OR REPLACE FUNCTION validate_turning_points(turning_points_json JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    -- Can be null, but if present must be valid array
    IF turning_points_json IS NULL THEN
        RETURN TRUE;
    END IF;
    
    IF jsonb_typeof(turning_points_json) != 'array' THEN
        RETURN FALSE;
    END IF;
    
    -- Each turning point must have required fields
    IF NOT (
        SELECT bool_and(
            item ? 'date' AND
            item ? 'description' AND
            item ? 'significance' AND
            (item->>'significance')::decimal BETWEEN 0.0 AND 1.0
        )
        FROM jsonb_array_elements(turning_points_json) AS item
    ) THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to validate media_spike_history structure
CREATE OR REPLACE FUNCTION validate_media_spike_history(spike_history_json JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    IF spike_history_json IS NULL THEN
        RETURN TRUE;
    END IF;
    
    -- Must have daily_counts object
    IF NOT (spike_history_json ? 'daily_counts' AND
            jsonb_typeof(spike_history_json->'daily_counts') = 'object') THEN
        RETURN FALSE;
    END IF;
    
    -- All daily count values must be non-negative integers
    IF NOT (
        SELECT bool_and(
            jsonb_typeof(value) = 'number' AND
            (value::text)::integer >= 0
        )
        FROM jsonb_each(spike_history_json->'daily_counts') AS kv(key, value)
    ) THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================
-- CONSTRAINT ADDITIONS TO EXISTING TABLES
-- =============================================

-- Add JSON validation constraints to narratives table
ALTER TABLE narratives ADD CONSTRAINT valid_frame_logic_structure 
    CHECK (validate_frame_logic(frame_logic));

ALTER TABLE narratives ADD CONSTRAINT valid_activity_timeline_structure 
    CHECK (validate_activity_timeline(activity_timeline));

ALTER TABLE narratives ADD CONSTRAINT valid_turning_points_structure 
    CHECK (validate_turning_points(turning_points));

ALTER TABLE narratives ADD CONSTRAINT valid_media_spike_history_structure 
    CHECK (validate_media_spike_history(media_spike_history));

-- NSF-1 specific constraints (content-only fields)
-- Note: Temporal and scoring constraints moved to narrative_metrics table

-- Add constraints to raw_articles
ALTER TABLE raw_articles ADD CONSTRAINT positive_word_count
    CHECK (word_count IS NULL OR word_count >= 0);

ALTER TABLE raw_articles ADD CONSTRAINT reasonable_word_count
    CHECK (word_count IS NULL OR word_count <= 100000);

ALTER TABLE raw_articles ADD CONSTRAINT logical_article_dates
    CHECK (published_at <= scraped_at);

-- Add constraints to news_sources
ALTER TABLE news_sources ADD CONSTRAINT positive_update_frequency
    CHECK (update_frequency_minutes > 0 AND update_frequency_minutes <= 10080); -- Max 1 week

-- =============================================
-- NARRATIVE METRICS TABLE CONSTRAINTS
-- =============================================

-- Add constraints to narrative_metrics table (analytics/scoring data)
ALTER TABLE narrative_metrics ADD CONSTRAINT chk_narrative_metrics_trending_score
    CHECK (trending_score >= 0);

ALTER TABLE narrative_metrics ADD CONSTRAINT chk_narrative_metrics_credibility_score
    CHECK (credibility_score >= 0.0 AND credibility_score <= 10.0 OR credibility_score IS NULL);

ALTER TABLE narrative_metrics ADD CONSTRAINT chk_narrative_metrics_engagement_score
    CHECK (engagement_score >= 0.0 AND engagement_score <= 1.0 OR engagement_score IS NULL);

ALTER TABLE narrative_metrics ADD CONSTRAINT chk_narrative_metrics_sentiment_score
    CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0 OR sentiment_score IS NULL);

ALTER TABLE narrative_metrics ADD CONSTRAINT chk_narrative_metrics_priority
    CHECK (narrative_priority >= 1 AND narrative_priority <= 10);

ALTER TABLE narrative_metrics ADD CONSTRAINT chk_narrative_metrics_status
    CHECK (narrative_status IN ('active', 'emerging', 'declining', 'dormant', 'archived'));

ALTER TABLE narrative_metrics ADD CONSTRAINT chk_narrative_metrics_dates
    CHECK (
        narrative_start_date IS NULL OR narrative_end_date IS NULL OR 
        narrative_start_date <= narrative_end_date
    );

-- Ensure keywords array has reasonable size
ALTER TABLE narrative_metrics ADD CONSTRAINT reasonable_keywords_count
    CHECK (array_length(keywords, 1) IS NULL OR array_length(keywords, 1) <= 50);

-- =============================================
-- BUSINESS LOGIC VALIDATION FUNCTIONS
-- =============================================

-- Function to validate narrative completeness before activation
CREATE OR REPLACE FUNCTION validate_narrative_completeness(p_narrative_id UUID)
RETURNS TABLE (
    is_valid BOOLEAN,
    validation_errors TEXT[]
) AS $$
DECLARE
    errors TEXT[] := ARRAY[]::TEXT[];
    narrative_record RECORD;
    article_count INTEGER;
    actor_count INTEGER;
BEGIN
    -- Get narrative data
    SELECT * INTO narrative_record FROM narratives WHERE narrative_id = p_narrative_id;
    
    IF NOT FOUND THEN
        errors := array_append(errors, 'Narrative not found');
        RETURN QUERY SELECT FALSE, errors;
        RETURN;
    END IF;
    
    -- Check required fields
    IF narrative_record.title IS NULL OR length(trim(narrative_record.title)) = 0 THEN
        errors := array_append(errors, 'Title is required');
    END IF;
    
    IF narrative_record.summary IS NULL OR length(trim(narrative_record.summary)) < 50 THEN
        errors := array_append(errors, 'Summary must be at least 50 characters');
    END IF;
    
    IF narrative_record.frame_logic IS NULL THEN
        errors := array_append(errors, 'Frame logic is required');
    END IF;
    
    IF narrative_record.activity_timeline IS NULL OR jsonb_array_length(narrative_record.activity_timeline) = 0 THEN
        errors := array_append(errors, 'Activity timeline must have at least one event');
    END IF;
    
    -- Check minimum article count
    SELECT COUNT(*) INTO article_count FROM narrative_articles WHERE narrative_id = p_narrative_id;
    IF article_count < 3 THEN
        errors := array_append(errors, 'Narrative must have at least 3 related articles');
    END IF;
    
    -- Check if narrative has metrics record
    IF NOT EXISTS (SELECT 1 FROM narrative_metrics WHERE narrative_uuid = p_narrative_id) THEN
        errors := array_append(errors, 'Narrative must have metrics record');
    END IF;
    
    RETURN QUERY SELECT (array_length(errors, 1) IS NULL), errors;
END;
$$ LANGUAGE plpgsql;

-- Function to validate article-narrative relevance (updated for metrics separation)
CREATE OR REPLACE FUNCTION validate_article_relevance(
    p_article_id UUID,
    p_narrative_id UUID,
    p_relevance_score DECIMAL(3,2)
)
RETURNS BOOLEAN AS $$
DECLARE
    article_record RECORD;
    metrics_record RECORD;
    keyword_matches INTEGER := 0;
BEGIN
    -- Get article data
    SELECT title, content, published_at INTO article_record 
    FROM raw_articles WHERE article_id = p_article_id;
    
    -- Get metrics data (temporal and keyword information)
    SELECT keywords, narrative_start_date, narrative_end_date INTO metrics_record
    FROM narrative_metrics WHERE narrative_uuid = p_narrative_id;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Check if article is within narrative timeframe (with some tolerance)
    IF metrics_record.narrative_start_date IS NOT NULL AND
       article_record.published_at::date < metrics_record.narrative_start_date - interval '7 days' THEN
        RETURN FALSE;
    END IF;
    
    IF metrics_record.narrative_end_date IS NOT NULL AND
       article_record.published_at::date > metrics_record.narrative_end_date + interval '7 days' THEN
        RETURN FALSE;
    END IF;
    
    -- Check keyword overlap if keywords exist
    IF metrics_record.keywords IS NOT NULL THEN
        SELECT COUNT(*) INTO keyword_matches
        FROM unnest(metrics_record.keywords) AS keyword
        WHERE article_record.title ILIKE '%' || keyword || '%' 
           OR article_record.content ILIKE '%' || keyword || '%';
        
        -- Require at least one keyword match for high relevance scores
        IF p_relevance_score > 0.7 AND keyword_matches = 0 THEN
            RETURN FALSE;
        END IF;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- DATA QUALITY MONITORING
-- =============================================

-- Function to check data quality across the platform
CREATE OR REPLACE FUNCTION check_data_quality()
RETURNS TABLE (
    check_name TEXT,
    status TEXT,
    count_or_value BIGINT,
    threshold BIGINT,
    details TEXT
) AS $$
BEGIN
    -- Check for narratives without articles
    RETURN QUERY
    SELECT 
        'Narratives without articles'::TEXT,
        CASE WHEN COUNT(*) > 10 THEN 'CRITICAL' ELSE 'OK' END::TEXT,
        COUNT(*)::BIGINT,
        10::BIGINT,
        'Narratives that have no associated articles'::TEXT
    FROM narratives n
    JOIN narrative_metrics m ON n.id = m.narrative_uuid
    LEFT JOIN narrative_articles na ON n.id = na.narrative_id
    WHERE na.narrative_id IS NULL AND m.narrative_status = 'active';
    
    -- Check for articles without embeddings
    RETURN QUERY
    SELECT 
        'Articles without embeddings'::TEXT,
        CASE WHEN COUNT(*) > 100 THEN 'CRITICAL' 
             WHEN COUNT(*) > 50 THEN 'WARNING' 
             ELSE 'OK' END::TEXT,
        COUNT(*)::BIGINT,
        50::BIGINT,
        'Articles missing vector embeddings for semantic search'::TEXT
    FROM raw_articles
    WHERE title_embedding IS NULL OR content_embedding IS NULL;
    
    -- Check for stale narratives
    RETURN QUERY
    SELECT 
        'Stale narratives'::TEXT,
        CASE WHEN COUNT(*) > 20 THEN 'WARNING' ELSE 'OK' END::TEXT,
        COUNT(*)::BIGINT,
        20::BIGINT,
        'Active narratives not updated in over 7 days'::TEXT
    FROM narratives n
    JOIN narrative_metrics m ON n.id = m.narrative_uuid
    WHERE m.narrative_status = 'active' 
    AND n.updated_at < CURRENT_TIMESTAMP - interval '7 days';
    
    -- Check for narratives missing metrics
    RETURN QUERY
    SELECT 
        'Narratives missing metrics'::TEXT,
        CASE WHEN COUNT(*) > 0 THEN 'CRITICAL' ELSE 'OK' END::TEXT,
        COUNT(*)::BIGINT,
        0::BIGINT,
        'Narratives without corresponding metrics records'::TEXT
    FROM narratives n
    LEFT JOIN narrative_metrics m ON n.id = m.narrative_uuid
    WHERE m.narrative_uuid IS NULL;
    
    -- Check for duplicate articles
    RETURN QUERY
    SELECT 
        'Duplicate articles'::TEXT,
        CASE WHEN COUNT(*) > 5 THEN 'WARNING' ELSE 'OK' END::TEXT,
        COUNT(*)::BIGINT,
        5::BIGINT,
        'Articles with identical titles from same source'::TEXT
    FROM (
        SELECT source_id, title, COUNT(*) 
        FROM raw_articles
        GROUP BY source_id, title
        HAVING COUNT(*) > 1
    ) duplicates;
    
    -- Check embedding quality (articles with very low similarity to any narrative)
    RETURN QUERY
    SELECT 
        'Orphaned high-quality articles'::TEXT,
        CASE WHEN COUNT(*) > 50 THEN 'INFO' ELSE 'OK' END::TEXT,
        COUNT(*)::BIGINT,
        50::BIGINT,
        'High-quality articles not associated with any narrative'::TEXT
    FROM raw_articles ra
    LEFT JOIN narrative_articles na ON ra.article_id = na.article_id
    WHERE na.article_id IS NULL 
    AND ra.word_count > 200 
    AND ra.sentiment_score IS NOT NULL
    AND ra.published_at > CURRENT_DATE - interval '30 days';
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- AUTOMATED DATA CLEANUP PROCEDURES
-- =============================================

-- Function to clean up orphaned records
CREATE OR REPLACE FUNCTION cleanup_orphaned_data()
RETURNS TABLE (
    cleanup_action TEXT,
    records_affected INTEGER
) AS $$
DECLARE
    affected_count INTEGER;
BEGIN
    -- Remove narrative-article associations for deleted articles
    DELETE FROM narrative_articles 
    WHERE article_id NOT IN (SELECT article_id FROM raw_articles);
    
    GET DIAGNOSTICS affected_count = ROW_COUNT;
    RETURN QUERY SELECT 'Removed orphaned narrative-article links'::TEXT, affected_count;
    
    -- Remove narrative-actor associations for deleted actors
    DELETE FROM narrative_actors_relation 
    WHERE actor_id NOT IN (SELECT actor_id FROM narrative_actors);
    
    GET DIAGNOSTICS affected_count = ROW_COUNT;
    RETURN QUERY SELECT 'Removed orphaned narrative-actor links'::TEXT, affected_count;
    
    -- Remove timeline events for deleted narratives
    DELETE FROM narrative_timeline_events 
    WHERE narrative_id NOT IN (SELECT narrative_id FROM narratives);
    
    GET DIAGNOSTICS affected_count = ROW_COUNT;
    RETURN QUERY SELECT 'Removed orphaned timeline events'::TEXT, affected_count;
    
    -- Remove metrics for deleted narratives
    DELETE FROM narrative_metrics 
    WHERE narrative_uuid NOT IN (SELECT id FROM narratives);
    
    GET DIAGNOSTICS affected_count = ROW_COUNT;
    RETURN QUERY SELECT 'Removed orphaned narrative metrics'::TEXT, affected_count;
END;
$$ LANGUAGE plpgsql;

-- Function to archive completed narratives (updated for metrics separation)
CREATE OR REPLACE FUNCTION archive_completed_narratives()
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER := 0;
BEGIN
    -- Archive narratives that haven't had activity in 60 days
    UPDATE narrative_metrics 
    SET narrative_status = 'archived'
    WHERE narrative_status = 'active'
    AND narrative_uuid NOT IN (
        SELECT DISTINCT na.narrative_id 
        FROM narrative_articles na
        JOIN raw_articles ra ON na.article_id = ra.article_id
        WHERE ra.published_at > CURRENT_DATE - interval '60 days'
    )
    AND updated_at < CURRENT_TIMESTAMP - interval '60 days';
    
    GET DIAGNOSTICS archived_count = ROW_COUNT;
    
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- SAMPLE VALIDATION USAGE
-- =============================================

/*
-- Check data quality
SELECT * FROM check_data_quality();

-- Validate a specific narrative
SELECT * FROM validate_narrative_completeness('some-uuid-here');

-- Clean up orphaned data
SELECT * FROM cleanup_orphaned_data();

-- Archive old narratives
SELECT archive_completed_narratives() as archived_count;

-- Test JSON validation
SELECT validate_frame_logic('{"primary_frame": "conflict", "causal_chains": [{"cause": "economic", "effect": "unrest", "confidence": 0.8}]}'::jsonb);
*/