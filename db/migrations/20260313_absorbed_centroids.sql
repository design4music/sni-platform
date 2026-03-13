-- Phase 4.4: Cross-centroid sibling merge support
-- Stores which centroids were absorbed into an anchor event
ALTER TABLE events_v3 ADD COLUMN IF NOT EXISTS absorbed_centroids TEXT[];

-- Clean up stale sibling_group entity_analyses (will be replaced by event-level analysis)
DELETE FROM entity_analyses WHERE entity_type = 'sibling_group';
