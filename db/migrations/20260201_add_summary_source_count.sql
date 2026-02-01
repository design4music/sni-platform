-- Add summary_source_count to events_v3
-- Tracks how many titles were present when the summary was last generated.
-- Phase 4.5a uses this to detect events that grew significantly since last summary.
ALTER TABLE events_v3 ADD COLUMN IF NOT EXISTS summary_source_count INTEGER;
