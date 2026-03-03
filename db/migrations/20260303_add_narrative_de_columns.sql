-- Add German translation columns to narratives table
ALTER TABLE narratives ADD COLUMN IF NOT EXISTS label_de TEXT;
ALTER TABLE narratives ADD COLUMN IF NOT EXISTS description_de TEXT;
ALTER TABLE narratives ADD COLUMN IF NOT EXISTS moral_frame_de TEXT;
ALTER TABLE narratives ADD COLUMN IF NOT EXISTS rai_full_analysis_de TEXT;
ALTER TABLE narratives ADD COLUMN IF NOT EXISTS rai_synthesis_de TEXT;
ALTER TABLE narratives ADD COLUMN IF NOT EXISTS rai_conflicts_de text[];
ALTER TABLE narratives ADD COLUMN IF NOT EXISTS rai_blind_spots_de text[];

-- Epic centroid summaries
ALTER TABLE epics ADD COLUMN IF NOT EXISTS centroid_summaries_de JSONB;
