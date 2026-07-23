-- P3: materialized-view tables for the position pages (SPEC v2 §5.5).
-- Pre-computed JSONB blobs, PK lookups. 12h staleness gate in the materializer.

BEGIN;

CREATE TABLE IF NOT EXISTS mv_positions_landing (
  locale      text PRIMARY KEY,
  view        jsonb NOT NULL,
  updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mv_position_detail (
  position_id text NOT NULL,
  locale      text NOT NULL,
  view        jsonb NOT NULL,
  updated_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (position_id, locale)
);

COMMIT;
