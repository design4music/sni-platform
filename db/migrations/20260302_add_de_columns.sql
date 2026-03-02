-- DE Localization: add German translation columns
-- All nullable TEXT — dropping them restores schema exactly.

-- events_v3: German title (generated in Phase 4.5a alongside English)
ALTER TABLE events_v3 ADD COLUMN IF NOT EXISTS title_de TEXT;

-- events_v3: German summary (lazy, on-demand)
ALTER TABLE events_v3 ADD COLUMN IF NOT EXISTS summary_de TEXT;

-- ctm: German summary (lazy, on-demand)
ALTER TABLE ctm ADD COLUMN IF NOT EXISTS summary_text_de TEXT;

-- epics: German title + summary + timeline (generated at freeze time)
ALTER TABLE epics ADD COLUMN IF NOT EXISTS title_de TEXT;
ALTER TABLE epics ADD COLUMN IF NOT EXISTS summary_de TEXT;
ALTER TABLE epics ADD COLUMN IF NOT EXISTS timeline_de TEXT;
