-- Migration: Drop obsolete tables
-- Date: 2026-01-27
--
-- Tables being dropped (all replaced by v3 schema):
-- - centroids: replaced by centroids_v3
-- - data_entities: unused experiment
-- - event_families_backup: backup of removed table
-- - events: replaced by events_v3
-- - framed_narratives: unused experiment
-- - runs: old pipeline tracking
-- - taxonomy_categories: replaced by taxonomy_v3
-- - taxonomy_terms: replaced by taxonomy_v3
-- - titles: replaced by titles_v3
-- - titles_archive: archive of old titles table

BEGIN;

-- Drop tables in order to avoid FK constraint issues
DROP TABLE IF EXISTS event_families_backup CASCADE;
DROP TABLE IF EXISTS framed_narratives CASCADE;
DROP TABLE IF EXISTS events CASCADE;
DROP TABLE IF EXISTS runs CASCADE;
DROP TABLE IF EXISTS data_entities CASCADE;
DROP TABLE IF EXISTS taxonomy_categories CASCADE;
DROP TABLE IF EXISTS taxonomy_terms CASCADE;
DROP TABLE IF EXISTS titles_archive CASCADE;
DROP TABLE IF EXISTS titles CASCADE;
DROP TABLE IF EXISTS centroids CASCADE;

COMMIT;

-- Verify cleanup
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;
