-- D-071 Phase B: outlet × entity × month stance matrix.
--
-- One row per (outlet, entity, month) with LLM-generated stance summary.
-- Replaces retired publisher_stance + stance-clustered narratives.
--
-- entity_kind: 'country' (entity_code = ISO-2) | 'person' (entity_code =
-- canonical name from persons[] label). entity_country: for persons, their
-- country for rollup; null for countries.
--
-- stance: -2..+2 (nullable if the LLM could not read a consistent signal).

CREATE TABLE IF NOT EXISTS outlet_entity_stance (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    outlet_name        TEXT         NOT NULL,
    entity_kind        TEXT         NOT NULL CHECK (entity_kind IN ('country', 'person')),
    entity_code        TEXT         NOT NULL,
    entity_country     TEXT,
    month              DATE         NOT NULL,
    stance             SMALLINT     CHECK (stance IS NULL OR stance BETWEEN -2 AND 2),
    confidence         TEXT         CHECK (confidence IS NULL OR confidence IN ('low', 'medium', 'high')),
    tone               TEXT,
    patterns           JSONB,
    evidence_title_ids UUID[],
    caveats            TEXT,
    n_headlines        INT          NOT NULL,
    tokens_in          INT,
    tokens_out         INT,
    computed_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (outlet_name, entity_kind, entity_code, month)
);

CREATE INDEX IF NOT EXISTS idx_outlet_entity_stance_outlet
    ON outlet_entity_stance (outlet_name, month DESC);

CREATE INDEX IF NOT EXISTS idx_outlet_entity_stance_entity
    ON outlet_entity_stance (entity_kind, entity_code, month DESC);

COMMENT ON TABLE outlet_entity_stance IS
    'D-071: per outlet × entity × month LLM-generated editorial stance. '
    'One LLM call per row, from a bundle of ~25 random headlines the outlet '
    'published about the entity in the month.';
