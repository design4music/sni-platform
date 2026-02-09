-- Add feed_id FK to titles_v3 for publisher-country tracing
ALTER TABLE titles_v3 ADD COLUMN IF NOT EXISTS feed_id UUID REFERENCES feeds(id);

CREATE INDEX IF NOT EXISTS idx_titles_v3_feed_id ON titles_v3(feed_id);

-- Normalize feeds.country_code to uppercase
UPDATE feeds SET country_code = UPPER(country_code)
WHERE country_code IS NOT NULL AND country_code != UPPER(country_code);

-- Fix known anomalies
UPDATE feeds SET country_code = 'GB' WHERE UPPER(country_code) = 'BRI';
UPDATE feeds SET country_code = NULL WHERE country_code IN ('Wor', 'WOR');
