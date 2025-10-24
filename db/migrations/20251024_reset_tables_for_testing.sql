-- Migration: Reset tables for fresh pipeline testing
-- Date: 2025-10-24
-- Purpose: Archive current data, start fresh for testing

-- Step 1: Truncate event_families (remove all EF content)
TRUNCATE TABLE event_families CASCADE;

-- Step 2: Rename titles → titles_archive (preserves 19k records)
ALTER TABLE titles RENAME TO titles_archive;

-- Step 3: Create new empty titles table (same schema as titles_archive)
CREATE TABLE titles (LIKE titles_archive INCLUDING ALL);

-- Verify counts
DO $$
DECLARE
    archive_count INTEGER;
    titles_count INTEGER;
    ef_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO archive_count FROM titles_archive;
    SELECT COUNT(*) INTO titles_count FROM titles;
    SELECT COUNT(*) INTO ef_count FROM event_families;

    RAISE NOTICE 'Migration complete:';
    RAISE NOTICE '  titles_archive: % rows (backup)', archive_count;
    RAISE NOTICE '  titles: % rows (fresh)', titles_count;
    RAISE NOTICE '  event_families: % rows (reset)', ef_count;
END $$;

COMMENT ON TABLE titles_archive IS
  'Archived titles from production run (~19k records) - preserved for content analysis';
