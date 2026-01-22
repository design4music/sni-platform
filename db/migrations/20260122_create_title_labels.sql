-- Migration: Create title_labels table for structured event labeling
-- Date: 2026-01-22
-- Purpose: Phase 3.5 - Event Label Extraction using ELO v2.0 ontology
-- Label format: PRIMARY_ACTOR -> ACTION_CLASS -> DOMAIN (-> OPTIONAL_TARGET)

CREATE TABLE IF NOT EXISTS title_labels (
    title_id UUID NOT NULL REFERENCES titles_v3(id) ON DELETE CASCADE,

    -- Full event label string
    event_label TEXT NOT NULL,      -- "ACTOR -> ACTION -> DOMAIN -> TARGET?"

    -- Parsed components
    actor TEXT NOT NULL,            -- e.g., "US_EXECUTIVE", "RU_ARMED_FORCES"
    action_class TEXT NOT NULL,     -- from ACTION_CLASSES ontology
    domain TEXT NOT NULL,           -- from DOMAINS ontology
    target TEXT,                    -- optional target actor/entity

    -- Metadata
    label_version TEXT NOT NULL DEFAULT 'ELO_v2.0',
    confidence FLOAT DEFAULT 1.0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Primary key: one label per title
    PRIMARY KEY (title_id),

    -- Validate action_class against ontology
    CONSTRAINT title_labels_action_class_check CHECK (action_class IN (
        -- T1: FORMAL DECISION
        'LEGAL_RULING', 'LEGISLATIVE_DECISION', 'POLICY_CHANGE', 'REGULATORY_ACTION',
        -- T2: COERCIVE ENFORCEMENT
        'MILITARY_OPERATION', 'LAW_ENFORCEMENT_OPERATION', 'SANCTION_ENFORCEMENT',
        -- T3: RESOURCE & CAPABILITY
        'RESOURCE_ALLOCATION', 'INFRASTRUCTURE_DEVELOPMENT', 'CAPABILITY_TRANSFER',
        -- T4: COORDINATION
        'ALLIANCE_COORDINATION', 'STRATEGIC_REALIGNMENT', 'MULTILATERAL_ACTION',
        -- T5: PRESSURE & INFLUENCE
        'POLITICAL_PRESSURE', 'ECONOMIC_PRESSURE', 'DIPLOMATIC_PRESSURE', 'INFORMATION_INFLUENCE',
        -- T6: CONTESTATION
        'LEGAL_CONTESTATION', 'INSTITUTIONAL_RESISTANCE', 'COLLECTIVE_PROTEST',
        -- T7: INCIDENTS
        'SECURITY_INCIDENT', 'SOCIAL_INCIDENT', 'ECONOMIC_DISRUPTION'
    )),

    -- Validate domain against ontology
    CONSTRAINT title_labels_domain_check CHECK (domain IN (
        'GOVERNANCE', 'ECONOMY', 'SECURITY', 'FOREIGN_POLICY', 'SOCIETY', 'TECHNOLOGY', 'MEDIA'
    ))
);

-- Index for querying by actor (spike detection: "who is doing what")
CREATE INDEX IF NOT EXISTS idx_title_labels_actor ON title_labels(actor);

-- Index for querying by action_class (spike detection: "what type of action")
CREATE INDEX IF NOT EXISTS idx_title_labels_action_class ON title_labels(action_class);

-- Index for querying by domain (filtering by thematic area)
CREATE INDEX IF NOT EXISTS idx_title_labels_domain ON title_labels(domain);

-- Index for full event_label (grouping identical labels)
CREATE INDEX IF NOT EXISTS idx_title_labels_event_label ON title_labels(event_label);

-- Composite index for common spike detection query: actor + action
CREATE INDEX IF NOT EXISTS idx_title_labels_actor_action ON title_labels(actor, action_class);


-- Trigger to update updated_at on modification
CREATE OR REPLACE FUNCTION update_title_labels_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS title_labels_updated_at_trigger ON title_labels;
CREATE TRIGGER title_labels_updated_at_trigger
    BEFORE UPDATE ON title_labels
    FOR EACH ROW
    EXECUTE FUNCTION update_title_labels_updated_at();


-- Comments
COMMENT ON TABLE title_labels IS 'Structured event labels for titles using ELO v2.0 ontology. Phase 3.5 output.';
COMMENT ON COLUMN title_labels.event_label IS 'Full label: ACTOR -> ACTION_CLASS -> DOMAIN (-> TARGET)';
COMMENT ON COLUMN title_labels.actor IS 'Primary actor with country prefix (e.g., US_EXECUTIVE, RU_ARMED_FORCES)';
COMMENT ON COLUMN title_labels.action_class IS 'Action from 7-tier ontology (T1-T7)';
COMMENT ON COLUMN title_labels.domain IS 'Thematic domain (GOVERNANCE, ECONOMY, SECURITY, etc.)';
COMMENT ON COLUMN title_labels.target IS 'Optional target actor/entity';


-- Sample validation queries (commented out)
--
-- Label distribution by action_class:
-- SELECT action_class, COUNT(*) FROM title_labels GROUP BY action_class ORDER BY COUNT(*) DESC;
--
-- Actor distribution:
-- SELECT actor, COUNT(*) FROM title_labels GROUP BY actor ORDER BY COUNT(*) DESC LIMIT 20;
--
-- Domain distribution:
-- SELECT domain, COUNT(*) FROM title_labels GROUP BY domain ORDER BY COUNT(*) DESC;
--
-- Sample labels with titles:
-- SELECT t.title_display, tl.event_label, tl.confidence
-- FROM title_labels tl
-- JOIN titles_v3 t ON tl.title_id = t.id
-- ORDER BY tl.created_at DESC LIMIT 50;
