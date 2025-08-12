-- Migration 007: Extend language codes for IPTC taxonomy support
-- IPTC uses language codes like "en-GB", "pt-BR", "zh-Hans" which are longer than 2 chars

-- Extend lang column in taxonomy_aliases from CHAR(2) to VARCHAR(10)
ALTER TABLE taxonomy_aliases 
    ALTER COLUMN lang TYPE VARCHAR(10);

-- Add index for better performance on language queries
CREATE INDEX IF NOT EXISTS idx_taxonomy_aliases_lang 
    ON taxonomy_aliases(lang);

-- Update any existing 'en' entries to 'en-GB' for consistency
UPDATE taxonomy_aliases 
SET lang = 'en-GB' 
WHERE lang = 'en';