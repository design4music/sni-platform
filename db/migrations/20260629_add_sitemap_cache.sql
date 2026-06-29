-- Stores pre-generated sitemap XML blobs so sitemap routes do a single PK
-- lookup instead of running multi-join queries at request time.
-- Populated by /api/cron/revalidate-sitemap (GitHub Actions, daily 04:00 UTC).
CREATE TABLE IF NOT EXISTS sitemap_cache (
  name         TEXT PRIMARY KEY,
  content      TEXT NOT NULL,
  generated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
