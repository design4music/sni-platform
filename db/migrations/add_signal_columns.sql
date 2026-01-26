-- Migration: Add typed signal columns to title_labels and lifecycle columns to events_v3
-- Date: 2026-01-26

-- title_labels: new signal columns for typed entity extraction
ALTER TABLE title_labels ADD COLUMN IF NOT EXISTS persons TEXT[];
ALTER TABLE title_labels ADD COLUMN IF NOT EXISTS orgs TEXT[];
ALTER TABLE title_labels ADD COLUMN IF NOT EXISTS places TEXT[];
ALTER TABLE title_labels ADD COLUMN IF NOT EXISTS commodities TEXT[];
ALTER TABLE title_labels ADD COLUMN IF NOT EXISTS policies TEXT[];
ALTER TABLE title_labels ADD COLUMN IF NOT EXISTS systems TEXT[];
ALTER TABLE title_labels ADD COLUMN IF NOT EXISTS named_events TEXT[];

-- events_v3 (Topics): add lifecycle and saga columns
ALTER TABLE events_v3 ADD COLUMN IF NOT EXISTS last_active DATE;
ALTER TABLE events_v3 ADD COLUMN IF NOT EXISTS saga TEXT;

-- Add comments for documentation
COMMENT ON COLUMN title_labels.persons IS 'Named persons mentioned (e.g., Trump, Zelensky)';
COMMENT ON COLUMN title_labels.orgs IS 'Organizations mentioned (e.g., NATO, Federal Reserve, Gazprom)';
COMMENT ON COLUMN title_labels.places IS 'Sub-national places (e.g., Crimea, Gaza, Greenland)';
COMMENT ON COLUMN title_labels.commodities IS 'Commodities mentioned (e.g., oil, gold, wheat, LNG)';
COMMENT ON COLUMN title_labels.policies IS 'Policies/agreements (e.g., sanctions, tariffs, JCPOA)';
COMMENT ON COLUMN title_labels.systems IS 'Systems/platforms (e.g., SWIFT, S-400, Nord Stream)';
COMMENT ON COLUMN title_labels.named_events IS 'Named events (e.g., G20 Summit, COP28)';
COMMENT ON COLUMN events_v3.last_active IS 'Date of most recent title in this topic';
COMMENT ON COLUMN events_v3.saga IS 'LLM-generated saga name for topic persistence';
