-- P1: the position layer (NARRATIVE_CONSOLIDATION_SPEC.md v2, D-095..D-101)
-- The POSITION is the narrative entity; narratives_v2 rows become CARDS under it.
-- Additive + idempotent: CREATE TABLE IF NOT EXISTS, ADD COLUMN IF NOT EXISTS.
-- Meta/owner live on the position; coalition is derived at read time (never stored).

BEGIN;

CREATE TABLE IF NOT EXISTS positions (
  id                  text PRIMARY KEY,               -- slug, snake_case, globally unique
  name_en             text NOT NULL,
  name_de             text NOT NULL,
  claim_en            text NOT NULL,                  -- the universal claim
  claim_de            text NOT NULL,
  stance_sign         smallint NOT NULL,              -- -1 / 0 / +1 (orientation only)
  meta_narrative_id   text REFERENCES meta_narratives(id),   -- primary
  meta_secondary_ids  text[] NOT NULL DEFAULT '{}',
  owner_centroids     text[] NOT NULL DEFAULT '{}',   -- assigned, corpus-verified
  is_active           boolean NOT NULL DEFAULT true,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);

-- narratives_v2 keeps every column; it gains a parent (the card -> position link).
ALTER TABLE narratives_v2
  ADD COLUMN IF NOT EXISTS position_id text REFERENCES positions(id);

CREATE INDEX IF NOT EXISTS idx_narratives_v2_position_id ON narratives_v2 (position_id);
CREATE INDEX IF NOT EXISTS idx_positions_meta ON positions (meta_narrative_id);

COMMIT;
