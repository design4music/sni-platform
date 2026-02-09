-- Add topic_core column to events_v3
-- Stores the semantic essence of a consolidated topic (3-10 words)
-- Set by Phase 4.1 topic consolidation LLM
ALTER TABLE events_v3 ADD COLUMN IF NOT EXISTS topic_core TEXT;
