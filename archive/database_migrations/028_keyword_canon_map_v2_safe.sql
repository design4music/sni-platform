-- Safe Keyword Canonicalization Schema Migration
-- Strategic Narrative Intelligence Platform
-- Migration 028: Safely upgrade keyword_canon_map to flexible pattern matching

-- Step 1: Backup existing data
CREATE TABLE IF NOT EXISTS keyword_canon_map_backup AS 
SELECT * FROM keyword_canon_map;

-- Step 2: Add new columns to existing table (safe approach)
ALTER TABLE keyword_canon_map 
ADD COLUMN IF NOT EXISTS pattern TEXT,
ADD COLUMN IF NOT EXISTS pattern_type TEXT CHECK (pattern_type IN ('exact','lower','regex')),
ADD COLUMN IF NOT EXISTS canon_type TEXT CHECK (canon_type IN ('country','org','person','event','place','keyword','hub')),
ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 100,
ADD COLUMN IF NOT EXISTS lang TEXT DEFAULT 'EN',
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS notes TEXT;

-- Step 3: Migrate existing data to new columns
UPDATE keyword_canon_map SET
    pattern = token_norm,
    pattern_type = 'lower',  -- Most existing mappings are lowercase variants
    canon_type = CASE 
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
    END,
    priority = CASE
        -- Assign priority based on mapping confidence and frequency
        WHEN confidence >= 1.0 THEN 10  -- High confidence mappings first
        WHEN confidence >= 0.9 THEN 20  -- Medium confidence
        ELSE 50                         -- Lower confidence
    END,
    is_active = TRUE,
    notes = CONCAT('Migrated from v1. Confidence: ', confidence)
WHERE pattern IS NULL;  -- Only update rows that haven't been migrated yet

-- Step 4: Add strategic mappings that were previously hardcoded
-- Create a temporary table for new mappings to avoid conflicts
CREATE TEMP TABLE new_strategic_mappings (
    pattern TEXT,
    pattern_type TEXT,
    canon_token TEXT,
    canon_type TEXT,
    priority INTEGER,
    notes TEXT
);

-- Insert strategic mappings
INSERT INTO new_strategic_mappings VALUES
-- Country acronyms (highest priority)
('us', 'lower', 'united states', 'country', 5, 'acronym expansion'),
('usa', 'lower', 'united states', 'country', 5, 'acronym expansion'), 
('u s', 'lower', 'united states', 'country', 5, 'acronym expansion - normalized'),
('uk', 'lower', 'united kingdom', 'country', 5, 'acronym expansion'),
('u k', 'lower', 'united kingdom', 'country', 5, 'acronym expansion - normalized'),
('eu', 'lower', 'european union', 'org', 5, 'acronym expansion'),
('e u', 'lower', 'european union', 'org', 5, 'acronym expansion - normalized'),
('prc', 'lower', 'china', 'country', 5, 'acronym expansion'),
('uae', 'lower', 'united arab emirates', 'country', 5, 'acronym expansion'),
('u a e', 'lower', 'united arab emirates', 'country', 5, 'acronym expansion - normalized'),

-- Organization acronyms  
('un', 'lower', 'united nations', 'org', 5, 'acronym expansion'),
('u n', 'lower', 'united nations', 'org', 5, 'acronym expansion - normalized'),
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
('emirati', 'lower', 'united arab emirates', 'country', 15, 'demonym (standalone only)'),

-- Title stripping patterns (regex - highest priority)
('(?i)^(president|prime minister|pm|chancellor|minister|governor|mayor)\s+trump$', 'regex', 'donald trump', 'person', 1, 'title stripping'),
('(?i)^(president|prime minister|pm|chancellor|minister)\s+biden$', 'regex', 'joe biden', 'person', 1, 'title stripping'),
('(?i)^(president|prime minister|pm|chancellor|minister)\s+putin$', 'regex', 'vladimir putin', 'person', 1, 'title stripping'),
('(?i)^(president|prime minister|pm|chancellor|minister)\s+xi$', 'regex', 'xi jinping', 'person', 1, 'title stripping'),
('(?i)^(prime minister|pm|minister)\s+netanyahu$', 'regex', 'benjamin netanyahu', 'person', 1, 'title stripping'),
('(?i)^(chancellor|minister)\s+merkel$', 'regex', 'angela merkel', 'person', 1, 'title stripping');

-- Insert new mappings, avoiding duplicates
INSERT INTO keyword_canon_map (
    pattern, pattern_type, canon_text, canon_type, priority, 
    is_active, notes, token_norm, confidence
)
SELECT 
    nsm.pattern, nsm.pattern_type, nsm.canon_token, nsm.canon_type, nsm.priority,
    TRUE, nsm.notes, nsm.pattern, 1.0
FROM new_strategic_mappings nsm
WHERE NOT EXISTS (
    SELECT 1 FROM keyword_canon_map kcm 
    WHERE kcm.pattern = nsm.pattern OR kcm.token_norm = nsm.pattern
);

-- Step 5: Create indexes for performance on new columns
CREATE INDEX IF NOT EXISTS idx_keyword_canon_pattern_type ON keyword_canon_map (pattern_type, priority);
CREATE INDEX IF NOT EXISTS idx_keyword_canon_canon_type ON keyword_canon_map (canon_type);
CREATE INDEX IF NOT EXISTS idx_keyword_canon_active ON keyword_canon_map (is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_keyword_canon_priority ON keyword_canon_map (priority);
CREATE INDEX IF NOT EXISTS idx_keyword_canon_pattern ON keyword_canon_map (pattern);

-- Step 6: Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_keyword_canon_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_keyword_canon_map_updated_at ON keyword_canon_map;
CREATE TRIGGER update_keyword_canon_map_updated_at 
    BEFORE UPDATE ON keyword_canon_map 
    FOR EACH ROW EXECUTE FUNCTION update_keyword_canon_updated_at();

-- Step 7: Clean up any constraints that might conflict
-- Make pattern_type not null for new rows but allow existing nulls temporarily
ALTER TABLE keyword_canon_map ADD CONSTRAINT check_new_pattern_type 
    CHECK (pattern_type IS NOT NULL OR token_norm IS NOT NULL);

-- Comments
COMMENT ON COLUMN keyword_canon_map.pattern IS 'Pattern to match against normalized tokens (V2)';
COMMENT ON COLUMN keyword_canon_map.pattern_type IS 'Match type: exact, lower, or regex (V2)';
COMMENT ON COLUMN keyword_canon_map.canon_type IS 'Semantic type: country, org, person, event, place, keyword, hub (V2)';
COMMENT ON COLUMN keyword_canon_map.priority IS 'Rule precedence (lower = higher priority) (V2)';
COMMENT ON COLUMN keyword_canon_map.is_active IS 'Whether this mapping is active (V2)';

-- Migration summary
SELECT 
    COUNT(*) as total_rules,
    COUNT(*) FILTER (WHERE pattern_type = 'exact') as exact_rules,
    COUNT(*) FILTER (WHERE pattern_type = 'lower') as lower_rules, 
    COUNT(*) FILTER (WHERE pattern_type = 'regex') as regex_rules,
    COUNT(*) FILTER (WHERE canon_type IS NOT NULL) as typed_rules,
    COUNT(*) FILTER (WHERE is_active = TRUE) as active_rules
FROM keyword_canon_map;