-- Keyword Canonicalization Schema V2 - Database-Driven
-- Strategic Narrative Intelligence Platform
-- Migration 028: Upgrade keyword_canon_map to flexible pattern matching

-- Step 1: Backup existing data
CREATE TABLE keyword_canon_map_backup AS 
SELECT * FROM keyword_canon_map;

-- Step 2: Create new schema (preserving existing table name)
DROP TABLE IF EXISTS keyword_canon_map_v2;

CREATE TABLE keyword_canon_map_v2 (
    id SERIAL PRIMARY KEY,
    pattern TEXT NOT NULL,
    pattern_type TEXT NOT NULL CHECK (pattern_type IN ('exact','lower','regex')),
    canon_token TEXT NOT NULL,
    canon_type TEXT NULL CHECK (canon_type IN ('country','org','person','event','place','keyword','hub')),
    priority INTEGER NOT NULL DEFAULT 100,
    lang TEXT NULL DEFAULT 'EN',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    notes TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Step 3: Create indexes for performance
CREATE INDEX idx_keyword_canon_v2_pattern_type ON keyword_canon_map_v2 (pattern_type, priority);
CREATE INDEX idx_keyword_canon_v2_canon_token ON keyword_canon_map_v2 (canon_token);
CREATE INDEX idx_keyword_canon_v2_canon_type ON keyword_canon_map_v2 (canon_type);
CREATE INDEX idx_keyword_canon_v2_active ON keyword_canon_map_v2 (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_keyword_canon_v2_priority ON keyword_canon_map_v2 (priority);

-- Step 4: Migrate existing data with intelligent conversion
-- Convert token_norm -> pattern mappings to new format
INSERT INTO keyword_canon_map_v2 (pattern, pattern_type, canon_token, canon_type, priority, notes)
SELECT 
    token_norm as pattern,
    'lower' as pattern_type,  -- Most existing mappings are lowercase variants
    canon_text as canon_token,
    CASE 
        -- Infer canon_type from canonical tokens
        WHEN canon_text IN ('united states', 'china', 'russia', 'ukraine', 'israel', 'palestine', 
                           'iran', 'iraq', 'syria', 'egypt', 'turkey', 'germany', 'france', 'italy', 
                           'spain', 'japan', 'korea', 'india', 'pakistan', 'afghanistan', 'lebanon',
                           'jordan', 'saudi arabia', 'kuwait', 'qatar', 'united arab emirates',
                           'united kingdom', 'european union') THEN 'country'
        WHEN canon_text LIKE '%trump%' OR canon_text LIKE '%biden%' OR canon_text LIKE '%putin%' 
             OR canon_text LIKE '%netanyahu%' OR canon_text LIKE '%xi jinping%' THEN 'person'
        WHEN canon_text IN ('nato', 'un', 'united nations', 'imf', 'who', 'fbi', 'cia') THEN 'org'
        ELSE 'keyword'
    END as canon_type,
    CASE
        -- Assign priority based on mapping confidence and frequency
        WHEN confidence >= 1.0 THEN 10  -- High confidence mappings first
        WHEN confidence >= 0.9 THEN 20  -- Medium confidence
        ELSE 50                         -- Lower confidence
    END as priority,
    CONCAT('Migrated from v1. Confidence: ', confidence) as notes
FROM keyword_canon_map
WHERE canon_text != token_norm  -- Only include actual mappings, not identity mappings
  AND canon_text != '';

-- Step 5: Add strategic hardcoded mappings from canonicalizer as DB rules
-- Acronym expansions (high priority)
INSERT INTO keyword_canon_map_v2 (pattern, pattern_type, canon_token, canon_type, priority, notes) VALUES
-- Country acronyms
('us', 'lower', 'united states', 'country', 5, 'acronym expansion'),
('usa', 'lower', 'united states', 'country', 5, 'acronym expansion'), 
('u.s.', 'lower', 'united states', 'country', 5, 'acronym expansion'),
('u.s.a.', 'lower', 'united states', 'country', 5, 'acronym expansion'),
('uk', 'lower', 'united kingdom', 'country', 5, 'acronym expansion'),
('u.k.', 'lower', 'united kingdom', 'country', 5, 'acronym expansion'),
('eu', 'lower', 'european union', 'org', 5, 'acronym expansion'),
('e.u.', 'lower', 'european union', 'org', 5, 'acronym expansion'),
('prc', 'lower', 'china', 'country', 5, 'acronym expansion'),
('uae', 'lower', 'united arab emirates', 'country', 5, 'acronym expansion'),
('u.a.e.', 'lower', 'united arab emirates', 'country', 5, 'acronym expansion'),

-- Organization acronyms  
('un', 'lower', 'united nations', 'org', 5, 'acronym expansion'),
('u.n.', 'lower', 'united nations', 'org', 5, 'acronym expansion'),
('nato', 'lower', 'nato', 'org', 5, 'self-mapping org'),
('imf', 'lower', 'international monetary fund', 'org', 5, 'acronym expansion'),
('who', 'lower', 'world health organization', 'org', 5, 'acronym expansion'),
('fbi', 'lower', 'federal bureau of investigation', 'org', 5, 'acronym expansion'),
('cia', 'lower', 'central intelligence agency', 'org', 5, 'acronym expansion'),

-- Demonym conversions (standalone only - handled in canonicalizer logic)
('american', 'lower', 'united states', 'country', 15, 'demonym (standalone only)'),
('british', 'lower', 'united kingdom', 'country', 15, 'demonym (standalone only)'),
('chinese', 'lower', 'china', 'country', 15, 'demonym (standalone only)'),
('russian', 'lower', 'russia', 'country', 15, 'demonym (standalone only)'),
('ukrainian', 'lower', 'ukraine', 'country', 15, 'demonym (standalone only)'),
('israeli', 'lower', 'israel', 'country', 15, 'demonym (standalone only)'),
('palestinian', 'lower', 'palestine', 'country', 15, 'demonym (standalone only)'),
('iranian', 'lower', 'iran', 'country', 15, 'demonym (standalone only)'),
('iraqi', 'lower', 'iraq', 'country', 15, 'demonym (standalone only)'),
('syrian', 'lower', 'syria', 'country', 15, 'demonym (standalone only)'),
('egyptian', 'lower', 'egypt', 'country', 15, 'demonym (standalone only)'),
('turkish', 'lower', 'turkey', 'country', 15, 'demonym (standalone only)'),
('german', 'lower', 'germany', 'country', 15, 'demonym (standalone only)'),
('french', 'lower', 'france', 'country', 15, 'demonym (standalone only)'),
('italian', 'lower', 'italy', 'country', 15, 'demonym (standalone only)'),
('spanish', 'lower', 'spain', 'country', 15, 'demonym (standalone only)'),
('japanese', 'lower', 'japan', 'country', 15, 'demonym (standalone only)'),
('korean', 'lower', 'korea', 'country', 15, 'demonym (standalone only)'),
('indian', 'lower', 'india', 'country', 15, 'demonym (standalone only)'),
('pakistani', 'lower', 'pakistan', 'country', 15, 'demonym (standalone only)'),
('afghan', 'lower', 'afghanistan', 'country', 15, 'demonym (standalone only)'),
('saudi', 'lower', 'saudi arabia', 'country', 15, 'demonym (standalone only)'),
('emirati', 'lower', 'united arab emirates', 'country', 15, 'demonym (standalone only)');

-- Title stripping patterns (regex - highest priority)
INSERT INTO keyword_canon_map_v2 (pattern, pattern_type, canon_token, canon_type, priority, notes) VALUES
('(?i)^(president|prime minister|pm|chancellor|minister|governor|mayor)\\s+trump$', 'regex', 'donald trump', 'person', 1, 'title stripping'),
('(?i)^(president|prime minister|pm|chancellor|minister)\\s+biden$', 'regex', 'joe biden', 'person', 1, 'title stripping'),
('(?i)^(president|prime minister|pm|chancellor|minister)\\s+putin$', 'regex', 'vladimir putin', 'person', 1, 'title stripping'),
('(?i)^(president|prime minister|pm|chancellor|minister)\\s+xi$', 'regex', 'xi jinping', 'person', 1, 'title stripping'),
('(?i)^(prime minister|pm|minister)\\s+netanyahu$', 'regex', 'benjamin netanyahu', 'person', 1, 'title stripping'),
('(?i)^(chancellor|minister)\\s+merkel$', 'regex', 'angela merkel', 'person', 1, 'title stripping'),
('(?i)^(mr|ms|mrs|miss|dr|prof|professor)\\.?\\s+([a-z]+)$', 'regex', '\\2', 'person', 2, 'honorific stripping (generic)');

-- Step 6: Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_keyword_canon_v2_updated_at 
    BEFORE UPDATE ON keyword_canon_map_v2 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Step 7: Replace old table with new one
DROP TABLE keyword_canon_map;
ALTER TABLE keyword_canon_map_v2 RENAME TO keyword_canon_map;

-- Update dependent views to use new schema
-- Note: This may require updating materialized view definitions

-- Step 8: Refresh function for canonical views
CREATE OR REPLACE FUNCTION refresh_canonical_views_v2() RETURNS INTEGER AS $$
DECLARE
    refresh_count INTEGER := 0;
BEGIN
    -- Refresh dependent materialized views
    REFRESH MATERIALIZED VIEW shared_keywords_300h;
    refresh_count := refresh_count + 1;
    
    RETURN refresh_count;
END;
$$ LANGUAGE plpgsql;

-- Comments
COMMENT ON TABLE keyword_canon_map IS 'Database-driven keyword canonicalization with pattern matching (V2)';
COMMENT ON COLUMN keyword_canon_map.pattern IS 'Pattern to match against normalized tokens';
COMMENT ON COLUMN keyword_canon_map.pattern_type IS 'Match type: exact, lower, or regex';
COMMENT ON COLUMN keyword_canon_map.canon_token IS 'Canonical form of the token';
COMMENT ON COLUMN keyword_canon_map.canon_type IS 'Semantic type: country, org, person, event, place, keyword, hub';
COMMENT ON COLUMN keyword_canon_map.priority IS 'Rule precedence (lower = higher priority)';
COMMENT ON COLUMN keyword_canon_map.is_active IS 'Whether this mapping is active';

-- Migration complete
SELECT 
    COUNT(*) as total_rules,
    COUNT(*) FILTER (WHERE pattern_type = 'exact') as exact_rules,
    COUNT(*) FILTER (WHERE pattern_type = 'lower') as lower_rules, 
    COUNT(*) FILTER (WHERE pattern_type = 'regex') as regex_rules,
    COUNT(*) FILTER (WHERE canon_type IS NOT NULL) as typed_rules
FROM keyword_canon_map;