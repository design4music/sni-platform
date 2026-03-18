-- Narrative Mapping: meta_narratives, strategic_narratives, event_strategic_narratives
-- 2026-03-17

BEGIN;

-- Level 1: Meta-narratives (9 static world-ordering principles)
CREATE TABLE IF NOT EXISTS meta_narratives (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    name_de         TEXT,
    description     TEXT NOT NULL,
    description_de  TEXT,
    signals         JSONB,
    sort_order      INT DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Level 2: Strategic narratives (persistent actor-bound claims)
CREATE TABLE IF NOT EXISTS strategic_narratives (
    id                  TEXT PRIMARY KEY,
    meta_narrative_id   TEXT NOT NULL REFERENCES meta_narratives(id),
    category            TEXT,
    actor_centroid      TEXT REFERENCES centroids_v3(id),
    related_centroids   TEXT[],
    name                TEXT NOT NULL,
    name_de             TEXT,
    claim               TEXT,
    claim_de            TEXT,
    normative_conclusion TEXT,
    keywords            TEXT[],
    action_classes      TEXT[],
    actor_prefixes      TEXT[],
    actor_types         TEXT[],
    domains             TEXT[],
    is_active           BOOLEAN DEFAULT true,
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sn_meta ON strategic_narratives(meta_narrative_id);
CREATE INDEX IF NOT EXISTS idx_sn_actor_centroid ON strategic_narratives(actor_centroid);
CREATE INDEX IF NOT EXISTS idx_sn_category ON strategic_narratives(category);
CREATE INDEX IF NOT EXISTS idx_sn_active ON strategic_narratives(is_active) WHERE is_active = true;

-- Junction: event <-> strategic narrative links
CREATE TABLE IF NOT EXISTS event_strategic_narratives (
    event_id        UUID NOT NULL REFERENCES events_v3(id) ON DELETE CASCADE,
    narrative_id    TEXT NOT NULL REFERENCES strategic_narratives(id) ON DELETE CASCADE,
    confidence      REAL NOT NULL,
    matched_signals JSONB NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (event_id, narrative_id)
);

CREATE INDEX IF NOT EXISTS idx_esn_narrative ON event_strategic_narratives(narrative_id);
CREATE INDEX IF NOT EXISTS idx_esn_confidence ON event_strategic_narratives(confidence DESC);

COMMIT;
