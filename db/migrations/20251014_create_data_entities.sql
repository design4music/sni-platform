-- Create data_entities table to replace CSV-based entity matching
-- Replaces: data/actors.csv, data/go_people.csv
-- Populated from: Wikidata SPARQL queries

CREATE TABLE IF NOT EXISTS data_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id TEXT NOT NULL UNIQUE, -- Canonical ID (e.g., 'US', 'NATO', 'donald_trump')
    entity_type TEXT NOT NULL CHECK (entity_type IN ('COUNTRY', 'CAPITAL', 'PERSON', 'ORG')),

    -- Core identifiers
    iso_code TEXT, -- ISO 3166-1 alpha-2 for countries (e.g., 'US', 'CN')
    wikidata_qid TEXT, -- Wikidata entity ID (e.g., 'Q30' for USA)

    -- Primary name (English)
    name_en TEXT NOT NULL,

    -- Aliases for matching (JSONB array per language)
    -- Structure: {"en": ["USA", "United States", "U.S."], "ru": ["США", "Соединённые Штаты"], ...}
    aliases JSONB DEFAULT '{}',

    -- Optional metadata
    capital_entity_id TEXT, -- For countries: links to capital entity_id
    country_entity_id TEXT, -- For persons/orgs: home country entity_id
    domains_hint TEXT[], -- Domain patterns that suggest this entity (e.g., whitehouse.gov)

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast lookup
CREATE INDEX idx_data_entities_type ON data_entities(entity_type);
CREATE INDEX idx_data_entities_iso ON data_entities(iso_code) WHERE iso_code IS NOT NULL;
CREATE INDEX idx_data_entities_wikidata ON data_entities(wikidata_qid) WHERE wikidata_qid IS NOT NULL;
CREATE INDEX idx_data_entities_aliases ON data_entities USING GIN(aliases jsonb_path_ops);

-- Full-text search on names and aliases
CREATE INDEX idx_data_entities_name_search ON data_entities USING GIN(to_tsvector('simple', name_en));

-- Comments
COMMENT ON TABLE data_entities IS 'Canonical entity database for strategic filtering - replaces CSV files';
COMMENT ON COLUMN data_entities.entity_id IS 'Canonical identifier used in system (e.g., US, NATO, donald_trump)';
COMMENT ON COLUMN data_entities.entity_type IS 'Entity classification: COUNTRY, CAPITAL, PERSON, ORG';
COMMENT ON COLUMN data_entities.aliases IS 'Multilingual aliases as JSONB: {"en": ["USA", "U.S."], "ru": ["США"], ...}';
COMMENT ON COLUMN data_entities.capital_entity_id IS 'For countries: references the capital city entity';
COMMENT ON COLUMN data_entities.domains_hint IS 'Domain patterns that suggest this entity (whitehouse.gov)';
