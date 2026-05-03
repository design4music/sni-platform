-- Per-locale pre-computed view for the /narratives landing page.
-- Replaces 3 live queries (getAllMetaNarratives, getStrategicNarratives,
-- getNarrativeSparklines) with a single PK lookup. The page filters
-- in-process, so a single warm row covers all actor/meta/q combos.
--
-- Stored shape (JSONB):
--   {
--     meta_narratives: MetaNarrative[],
--     narratives:      StrategicNarrative[],
--     sparklines:      { [narrative_id]: SignalWeekly[] }
--   }
--
-- Daemon refreshes every 12h after the narrative-matching phase so the
-- event_count fields reflect the latest matches. Only 2 rows total (en/de).

CREATE TABLE IF NOT EXISTS mv_narratives_landing (
    locale      TEXT        NOT NULL CHECK (locale IN ('en', 'de')),
    view        JSONB       NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (locale)
);
