-- Per-(narrative_id, locale) pre-computed view for /narratives/[id].
-- Replaces 4 live queries:
--   - getStrategicNarrativeById  (narrative metadata + event_count)
--   - getNarrativeWeeklyActivity (90d weekly aggregation)
--   - getNarrativeEvents         (top 50 events with title + summary)
--   - getCompetingNarratives     (top 10 narratives sharing events)
--
-- Stored shape (JSONB):
--   {
--     narrative:        StrategicNarrative,
--     weekly_activity:  SignalWeekly[],
--     events:           Array<EventDetail & { confidence: number }>,
--     competing:        Array<StrategicNarrative & { shared_events: number }>
--   }
--
-- ~520 rows total (260 narratives × 2 locales). Daemon refreshes every
-- 12h after narrative matching. When matching quality improves, the next
-- cycle picks up the new event_strategic_narratives rows automatically.

CREATE TABLE IF NOT EXISTS mv_narrative_detail (
    narrative_id  TEXT        NOT NULL,
    locale        TEXT        NOT NULL CHECK (locale IN ('en', 'de')),
    view          JSONB       NOT NULL,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (narrative_id, locale)
);
