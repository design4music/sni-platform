-- P2: derived event <-> position links (NARRATIVE_CONSOLIDATION_SPEC v2 §5.4, D-100)
-- Every row is reproducible from title_narratives; nothing else writes here.
-- Rebuilt by scripts/build_event_positions.py (idempotent full rebuild).

BEGIN;

CREATE TABLE IF NOT EXISTS event_positions (
  event_id     uuid NOT NULL,
  position_id  text NOT NULL REFERENCES positions(id),
  title_count  integer NOT NULL,        -- event's titles carrying this position
  PRIMARY KEY (event_id, position_id)
);

CREATE INDEX IF NOT EXISTS idx_event_positions_position ON event_positions (position_id);

COMMIT;
