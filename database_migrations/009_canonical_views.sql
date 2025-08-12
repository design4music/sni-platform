-- Canonical Keywords Materialized Views
-- Strategic Narrative Intelligence Platform
-- Migration 009: Enhanced canonical vocabulary views

-- Shared keywords over 300h window with document frequency filtering
CREATE MATERIALIZED VIEW shared_keywords_300h AS
SELECT 
    kcm.canon_text as canonical_token,
    kcm.concept_cluster,
    COUNT(DISTINCT a.id) as doc_frequency,
    AVG(ak.strategic_score) as avg_strategic_score,
    MAX(ak.strategic_score) as max_strategic_score,
    COUNT(ak.id) as total_mentions,
    MIN(a.published_at) as first_seen,
    MAX(a.published_at) as last_seen
FROM keyword_canon_map kcm
JOIN keywords k ON kcm.token_norm = LOWER(TRIM(k.keyword))
JOIN article_keywords ak ON k.id = ak.keyword_id  
JOIN articles a ON ak.article_id = a.id
WHERE a.published_at >= NOW() - INTERVAL '300 hours'
  AND (a.language = 'EN' OR a.language IS NULL)
  AND kcm.canon_text != ''
GROUP BY kcm.canon_text, kcm.concept_cluster
HAVING COUNT(DISTINCT a.id) BETWEEN 3 AND 250
ORDER BY doc_frequency DESC, avg_strategic_score DESC;

-- Index for performance
CREATE INDEX idx_shared_keywords_300h_token ON shared_keywords_300h (canonical_token);
CREATE INDEX idx_shared_keywords_300h_cluster ON shared_keywords_300h (concept_cluster);
CREATE INDEX idx_shared_keywords_300h_doc_freq ON shared_keywords_300h (doc_frequency DESC);

-- Enhanced article_core_keywords view (top 6 canonical per article)
-- Note: This will be populated by the nightly job, not as a view to allow flexibility

-- Function to refresh all canonical views
CREATE OR REPLACE FUNCTION refresh_canonical_views() RETURNS INTEGER AS $$
DECLARE
    refresh_count INTEGER := 0;
BEGIN
    -- Refresh shared keywords view
    REFRESH MATERIALIZED VIEW shared_keywords_300h;
    refresh_count := refresh_count + 1;
    
    RETURN refresh_count;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON MATERIALIZED VIEW shared_keywords_300h IS 'Canonical tokens from 300h window with doc frequency [3..250]';
COMMENT ON FUNCTION refresh_canonical_views() IS 'Refresh all canonical vocabulary materialized views';