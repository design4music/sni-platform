-- Refactor taxonomy_terms table
-- 1. Add name_en column for canonical English term
-- 2. Populate name_en from terms->head_en
-- 3. Drop priority and notes columns

BEGIN;

-- Add name_en column
ALTER TABLE taxonomy_terms
ADD COLUMN IF NOT EXISTS name_en TEXT;

-- Populate name_en from terms->head_en for all existing records
UPDATE taxonomy_terms
SET name_en = terms->>'head_en'
WHERE terms ? 'head_en';

-- Make name_en NOT NULL after population
ALTER TABLE taxonomy_terms
ALTER COLUMN name_en SET NOT NULL;

-- Drop unused columns
ALTER TABLE taxonomy_terms
DROP COLUMN IF EXISTS priority,
DROP COLUMN IF EXISTS notes;

-- Add index on name_en for fast lookups
CREATE INDEX IF NOT EXISTS idx_taxonomy_terms_name_en ON taxonomy_terms(name_en);

-- Update table comment
COMMENT ON COLUMN taxonomy_terms.name_en IS 'Canonical English term name (extracted from terms.head_en)';

COMMIT;
