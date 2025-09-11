-- Phase 2 Cleanup: Remove unused columns from titles table
-- These columns are completely empty and no longer needed

-- First drop views that depend on these columns
DROP VIEW IF EXISTS strategic_titles;
DROP VIEW IF EXISTS legacy_strategic_titles;

-- Remove unused columns from titles table
ALTER TABLE titles DROP COLUMN IF EXISTS publisher_country_code;
ALTER TABLE titles DROP COLUMN IF EXISTS lang;
ALTER TABLE titles DROP COLUMN IF EXISTS is_strategic;
ALTER TABLE titles DROP COLUMN IF EXISTS strategic_confidence;
ALTER TABLE titles DROP COLUMN IF EXISTS strategic_signals;
ALTER TABLE titles DROP COLUMN IF EXISTS entity_count;
ALTER TABLE titles DROP COLUMN IF EXISTS title_embedding;
ALTER TABLE titles DROP COLUMN IF EXISTS title_embedding_json;
ALTER TABLE titles DROP COLUMN IF EXISTS processed_at;
ALTER TABLE titles DROP COLUMN IF EXISTS gate_anchor_labels;

-- Recreate strategic_titles view without dropped columns
CREATE VIEW strategic_titles AS
SELECT 
    t.*,
    f.name as feed_name,
    f.language_code as feed_language,
    f.country_code as feed_country
FROM titles t
JOIN feeds f ON t.feed_id = f.id
WHERE t.gate_keep = true;  -- Use gate_keep instead of is_strategic

-- Create updated legacy view without dropped columns
CREATE VIEW legacy_strategic_titles AS
SELECT 
    t.*,
    f.name as feed_name,
    f.language_code as feed_language,
    f.country_code as feed_country
FROM titles t
JOIN feeds f ON t.feed_id = f.id
WHERE t.gate_keep = true;  -- Use gate_keep instead of is_strategic

-- Add comment for migration tracking
INSERT INTO runs (phase, prompt_version, input_ref, output_ref) 
VALUES (
    'cleanup', 
    'phase2_unused_columns', 
    'remove_unused_columns', 
    '{"columns_dropped": ["publisher_country_code", "lang", "is_strategic", "strategic_confidence", "strategic_signals", "entity_count", "title_embedding", "title_embedding_json", "processed_at", "gate_anchor_labels"]}'
);

COMMENT ON TABLE titles IS 'Headlines with strategic gate filtering and entity enrichment - cleaned of unused columns';