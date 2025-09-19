-- Migration: Add EF Events Schema for Evolutionary Event Families
-- Date: September 18, 2025
-- Purpose: Implement events timeline and seed/active status system

-- Add events JSON field to store discrete event timeline
ALTER TABLE event_families ADD COLUMN events JSONB DEFAULT '[]';

-- Add research tracking fields for intelligent EF generation
ALTER TABLE event_families ADD COLUMN last_research_date TIMESTAMP NULL;
ALTER TABLE event_families ADD COLUMN promotion_score REAL DEFAULT 0.0;

-- Add monitoring start date for disclaimers
ALTER TABLE event_families ADD COLUMN monitoring_start_date TIMESTAMP DEFAULT NOW();

-- Update status field to support 'seed' as default (field already exists)
ALTER TABLE event_families ALTER COLUMN status SET DEFAULT 'seed';

-- Create index on status for efficient querying
CREATE INDEX IF NOT EXISTS idx_event_families_status ON event_families(status);

-- Create index on events JSON field for event search
CREATE INDEX IF NOT EXISTS idx_event_families_events ON event_families USING GIN(events);

-- Reset all existing EFs to 'seed' status (will be regenerated with new system)
UPDATE event_families SET status = 'seed';