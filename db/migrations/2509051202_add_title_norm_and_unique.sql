-- up
ALTER TABLE titles ADD COLUMN IF NOT EXISTS title_norm text;
ALTER TABLE titles ADD CONSTRAINT uq_titles_hash_feed UNIQUE (content_hash, feed_id);
-- down
ALTER TABLE titles DROP CONSTRAINT IF EXISTS uq_titles_hash_feed;
ALTER TABLE titles DROP COLUMN IF EXISTS title_norm;