-- Support for cross-bucket event merging (Phase 4.3)
-- merged_into points to the absorbing event; merged events are soft-deleted
ALTER TABLE events_v3 ADD COLUMN IF NOT EXISTS merged_into UUID REFERENCES events_v3(id);
CREATE INDEX IF NOT EXISTS idx_events_v3_merged_into ON events_v3(merged_into) WHERE merged_into IS NOT NULL;
