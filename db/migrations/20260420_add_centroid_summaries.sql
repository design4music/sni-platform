-- 2026-04-20 — Add centroid_summaries table
--
-- Period-level "state of play" summaries per centroid (country or entity).
--
-- period_kind='rolling_30d': one active row per centroid, replaced on each refresh.
--   Written by daemon Slot 4 when stale.
-- period_kind='monthly': one row per centroid per month, generated at month freeze.
--   Immutable after creation.
--
-- Tier semantics:
--   tier=1  FULL        Tier 0 overall + 4 track paragraphs (Economy/Politics/Security/Society).
--   tier=2  LIGHT       Tier 0 overall only + top events rendered client-side. No track paragraphs.
--   tier=3  CANNED      Pure static bilingual message. No LLM call. overall_* holds the canned text.
--
-- Bilingual: overall_en + overall_de; per-track JSONB holds {state_en, state_de, supporting_events}.

BEGIN;

CREATE TABLE IF NOT EXISTS centroid_summaries (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  centroid_id        TEXT NOT NULL REFERENCES centroids_v3(id) ON DELETE CASCADE,
  period_kind        TEXT NOT NULL CHECK (period_kind IN ('rolling_30d','monthly')),
  period_end         DATE NOT NULL,
  tier               INT  NOT NULL CHECK (tier IN (1,2,3)),

  overall_en         TEXT,
  overall_de         TEXT,

  -- Per-track payload: {"state_en":"...","state_de":"...","supporting_events":["id1",...]}
  economy            JSONB,
  politics           JSONB,
  security           JSONB,
  society            JSONB,

  source_event_count INT  NOT NULL DEFAULT 0,
  generated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  UNIQUE (centroid_id, period_kind, period_end)
);

CREATE INDEX IF NOT EXISTS idx_centroid_summaries_lookup
  ON centroid_summaries (centroid_id, period_kind, period_end DESC);

COMMENT ON TABLE centroid_summaries IS
  'Period-level state-of-play summaries per centroid. rolling_30d row replaced each refresh; monthly rows immutable after month freeze.';

COMMIT;
