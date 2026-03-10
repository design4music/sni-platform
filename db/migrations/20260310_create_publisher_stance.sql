-- Publisher stance scoring: sentiment per (publisher, centroid, month).
-- Populated by pipeline/phase_4/score_publisher_stance.py

CREATE TABLE IF NOT EXISTS publisher_stance (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  feed_name       TEXT NOT NULL,
  centroid_id     TEXT NOT NULL REFERENCES centroids_v3(id),
  month           DATE NOT NULL,
  score           REAL NOT NULL,          -- -2 (hostile) to +2 (supportive)
  confidence      REAL NOT NULL DEFAULT 0, -- 0-1, based on sample agreement
  sample_size     INT NOT NULL DEFAULT 0,
  sample_titles   JSONB,                   -- sampled titles sent to LLM
  computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(feed_name, centroid_id, month)
);

CREATE INDEX IF NOT EXISTS idx_publisher_stance_feed ON publisher_stance(feed_name);
CREATE INDEX IF NOT EXISTS idx_publisher_stance_centroid ON publisher_stance(centroid_id, month);
