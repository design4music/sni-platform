-- Event triple materialization: actor -> action_class -> target with polarity
CREATE TABLE IF NOT EXISTS mv_event_triples (
    event_id UUID NOT NULL,
    centroid_id TEXT NOT NULL,
    month DATE NOT NULL,
    actor TEXT NOT NULL,
    action_class TEXT NOT NULL,
    domain TEXT NOT NULL,
    target TEXT NOT NULL DEFAULT 'NONE',
    polarity TEXT NOT NULL,
    title_count INT NOT NULL,
    importance_avg FLOAT,
    first_seen DATE,
    PRIMARY KEY (centroid_id, event_id, actor, action_class, target)
);

CREATE INDEX IF NOT EXISTS idx_mv_triples_centroid_month ON mv_event_triples(centroid_id, month);
CREATE INDEX IF NOT EXISTS idx_mv_triples_polarity ON mv_event_triples(polarity, centroid_id);
