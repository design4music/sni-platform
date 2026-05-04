-- Per-outlet pre-computed view for /sources/[slug].
-- Replaces 8 live queries in one PK lookup. None of the underlying
-- queries are locale-aware (locale is a UI prop only), so a single
-- row per outlet covers both en/de.
--
-- Stored shape (JSONB):
--   {
--     profile:          OutletProfile,
--     lifetime_stats:   PublisherStats | null,
--     stance_months:    string[],
--     stance_timeline:  OutletStanceTimelineRow[],
--     track_timeline:   OutletTrackTimelineRow[],
--     entity_daily:     OutletEntityDailyRow[],
--     minor_entities:   OutletMinorEntity[],
--     siblings:         SiblingOutlet[]
--   }
--
-- ~207 rows total. Daemon refresh 12h, no frozen-skip (rolling content).

CREATE TABLE IF NOT EXISTS mv_outlet_landing (
    feed_name   TEXT        NOT NULL,
    view        JSONB       NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (feed_name)
);
