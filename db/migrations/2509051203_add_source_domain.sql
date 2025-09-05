-- up
ALTER TABLE feeds ADD COLUMN IF NOT EXISTS source_domain text;

-- down
ALTER TABLE feeds DROP COLUMN IF EXISTS source_domain;