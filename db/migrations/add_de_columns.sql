-- Add German translation columns for localization (DE)
-- All columns nullable TEXT/JSONB. Dropping them restores the schema exactly.

-- centroids_v3: German description + profile brief
ALTER TABLE centroids_v3 ADD COLUMN IF NOT EXISTS description_de TEXT;
ALTER TABLE centroids_v3 ADD COLUMN IF NOT EXISTS profile_json_de JSONB;

-- events_v3: German title + summary
ALTER TABLE events_v3 ADD COLUMN IF NOT EXISTS title_de TEXT;
ALTER TABLE events_v3 ADD COLUMN IF NOT EXISTS summary_de TEXT;

-- ctm: German summary
ALTER TABLE ctm ADD COLUMN IF NOT EXISTS summary_text_de TEXT;

-- epics: German title + summary + timeline
ALTER TABLE epics ADD COLUMN IF NOT EXISTS title_de TEXT;
ALTER TABLE epics ADD COLUMN IF NOT EXISTS summary_de TEXT;
ALTER TABLE epics ADD COLUMN IF NOT EXISTS timeline_de TEXT;
