-- up
CREATE TABLE IF NOT EXISTS feeds (
  feed_url           text PRIMARY KEY,
  etag               text,
  last_modified      text,
  last_pubdate_utc   timestamptz,
  last_run_at        timestamptz
);
-- down
DROP TABLE IF EXISTS feeds;