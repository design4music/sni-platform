-- ============================================================================
-- SNI v3 Database Migration - Simplified Schema
-- Creates new tables for centroid-based architecture
-- Date: 2025-11-03
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. centroids_v3: Clean centroid metadata
-- ============================================================================

CREATE TABLE IF NOT EXISTS centroids_v3 (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,

    -- Centroid classification
    class TEXT NOT NULL CHECK (class IN ('geo', 'systemic')),
    primary_theater TEXT,  -- Required for 'geo', NULL for 'systemic'
    is_superpower BOOLEAN DEFAULT false,  -- US/EU/CN/RU catch-all flag

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraint: geo centroids must have primary_theater
    CHECK (
        (class = 'geo' AND primary_theater IS NOT NULL) OR
        (class = 'systemic' AND primary_theater IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_centroids_v3_class ON centroids_v3(class);
CREATE INDEX IF NOT EXISTS idx_centroids_v3_active ON centroids_v3(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_centroids_v3_superpower ON centroids_v3(is_superpower) WHERE is_superpower = true;
CREATE INDEX IF NOT EXISTS idx_centroids_v3_theater ON centroids_v3(primary_theater) WHERE primary_theater IS NOT NULL;

COMMENT ON TABLE centroids_v3 IS 'Stable narrative anchors. Geo centroids have theaters, systemic are global.';
COMMENT ON COLUMN centroids_v3.class IS 'geo = geographic/theater-based, systemic = global topics';
COMMENT ON COLUMN centroids_v3.is_superpower IS 'Flag for US/EU/CN/RU catch-all centroids used in Pass 3';

-- ============================================================================
-- 2. taxonomy_v3: Unified lookup table with flexible item types
-- ============================================================================

CREATE TABLE IF NOT EXISTS taxonomy_v3 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core term data
    item_raw TEXT NOT NULL,  -- Canonical string as seen in titles
    item_type TEXT NOT NULL CHECK (item_type IN (
        'geo',      -- Countries, cities, regions
        'org',      -- States, ministries, armies, blocs, companies, NGOs
        'person',   -- Individuals
        'model',    -- Concrete systems/models (HIMARS, ATACMS, F-16, TSMC N3)
        'anchor',   -- Institutional/programmatic tokens (UNFCCC, COP30, WTO, etc.)
        'domain',   -- Generic terms (missile, refugee, heat wave, microchips)
        'stop'      -- Disqualify from any centroid even if strategic signals present
    )),

    -- Centroid linkage (supports shared terms, can be NULL)
    centroid_ids TEXT[],

    -- Matching configuration
    aliases JSONB DEFAULT '[]'::jsonb,  -- Spellings, transliterations, grammar forms, synonyms

    -- Entity metadata (optional)
    iso_code TEXT,
    wikidata_qid TEXT,

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_taxonomy_v3_item_raw ON taxonomy_v3(item_raw);
CREATE INDEX IF NOT EXISTS idx_taxonomy_v3_item_raw_lower ON taxonomy_v3(LOWER(item_raw));
CREATE INDEX IF NOT EXISTS idx_taxonomy_v3_item_type ON taxonomy_v3(item_type);
CREATE INDEX IF NOT EXISTS idx_taxonomy_v3_centroid_ids ON taxonomy_v3 USING GIN(centroid_ids);
CREATE INDEX IF NOT EXISTS idx_taxonomy_v3_aliases ON taxonomy_v3 USING GIN(aliases);
CREATE INDEX IF NOT EXISTS idx_taxonomy_v3_iso ON taxonomy_v3(iso_code) WHERE iso_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_taxonomy_v3_active ON taxonomy_v3(is_active) WHERE is_active = true;

COMMENT ON TABLE taxonomy_v3 IS 'Unified lookup for all terms used in centroid matching. Single table with flexible types.';
COMMENT ON COLUMN taxonomy_v3.item_type IS 'Type of term: geo, org, person, model, anchor, domain, stop';
COMMENT ON COLUMN taxonomy_v3.centroid_ids IS 'Array of centroid IDs this term maps to. Can be shared across centroids or NULL.';
COMMENT ON COLUMN taxonomy_v3.aliases IS 'JSON array of alternative spellings, transliterations, grammar forms, synonyms';

-- ============================================================================
-- 3. ctm: Centroid-Track-Month aggregation with events digest
-- ============================================================================

CREATE TABLE IF NOT EXISTS ctm (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- CTM identity (unique combination)
    centroid_id TEXT NOT NULL REFERENCES centroids_v3(id) ON DELETE CASCADE,
    track TEXT NOT NULL CHECK (track IN (
        'military',
        'diplomacy',
        'economic',
        'tech_cyber',
        'humanitarian',
        'information_media',
        'legal_regulatory'
    )),
    month DATE NOT NULL,  -- First day of calendar month (e.g., 2025-11-01)

    -- Aggregation metrics
    title_count INT DEFAULT 0,

    -- Phase 4: Events digest - timeline of distinct updates
    events_digest JSONB DEFAULT '[]'::jsonb,

    -- Month summary (generated at freeze time)
    summary_text TEXT,

    -- Status
    is_frozen BOOLEAN DEFAULT false,  -- False during month, true when closed

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Ensure uniqueness
    UNIQUE(centroid_id, track, month)
);

CREATE INDEX IF NOT EXISTS idx_ctm_centroid ON ctm(centroid_id);
CREATE INDEX IF NOT EXISTS idx_ctm_track ON ctm(track);
CREATE INDEX IF NOT EXISTS idx_ctm_month ON ctm(month DESC);
CREATE INDEX IF NOT EXISTS idx_ctm_count ON ctm(title_count DESC);
CREATE INDEX IF NOT EXISTS idx_ctm_frozen ON ctm(is_frozen);
CREATE INDEX IF NOT EXISTS idx_ctm_composite ON ctm(centroid_id, track, month);
CREATE INDEX IF NOT EXISTS idx_ctm_events_digest ON ctm USING GIN(events_digest);

COMMENT ON TABLE ctm IS 'Centroid-Track-Month aggregation units. Each CTM is unique (centroid, track, month).';
COMMENT ON COLUMN ctm.month IS 'First day of month (YYYY-MM-01). CTMs aggregate all titles from that calendar month.';
COMMENT ON COLUMN ctm.events_digest IS 'Phase 4 array of distinct events: [{date, summary, event_id, source_title_ids}]';
COMMENT ON COLUMN ctm.summary_text IS 'Optional 150-250 word month summary generated at freeze time';
COMMENT ON COLUMN ctm.is_frozen IS 'False during active month, true when month is closed and finalized';

-- ============================================================================
-- 4. titles_v3: Simplified title table
-- ============================================================================

CREATE TABLE IF NOT EXISTS titles_v3 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core title data
    title_display TEXT NOT NULL,
    url_gnews TEXT,
    publisher_name TEXT,
    pubdate_utc TIMESTAMP NOT NULL,
    detected_language TEXT,

    -- v3: Centroid and track assignment
    centroid_id TEXT REFERENCES centroids_v3(id) ON DELETE SET NULL,
    track TEXT CHECK (track IN (
        'military',
        'diplomacy',
        'economic',
        'tech_cyber',
        'humanitarian',
        'information_media',
        'legal_regulatory'
    )),

    -- v3: CTM linkage
    ctm_id UUID REFERENCES ctm(id) ON DELETE SET NULL,

    -- Processing status
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN (
        'pending',
        'assigned',
        'out_of_scope'
    )),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_titles_v3_centroid ON titles_v3(centroid_id);
CREATE INDEX IF NOT EXISTS idx_titles_v3_track ON titles_v3(track);
CREATE INDEX IF NOT EXISTS idx_titles_v3_ctm ON titles_v3(ctm_id);
CREATE INDEX IF NOT EXISTS idx_titles_v3_pubdate ON titles_v3(pubdate_utc DESC);
CREATE INDEX IF NOT EXISTS idx_titles_v3_status ON titles_v3(processing_status);
CREATE INDEX IF NOT EXISTS idx_titles_v3_url ON titles_v3(url_gnews);
CREATE INDEX IF NOT EXISTS idx_titles_v3_month_centroid_track ON titles_v3(
    date_trunc('month', pubdate_utc),
    centroid_id,
    track
) WHERE centroid_id IS NOT NULL AND track IS NOT NULL;

COMMENT ON TABLE titles_v3 IS 'Simplified title table for SNI v3. Month is computed from pubdate_utc or CTM link.';
COMMENT ON COLUMN titles_v3.processing_status IS 'pending = not processed, assigned = linked to CTM, out_of_scope = rejected';

-- ============================================================================
-- 5. Helper functions
-- ============================================================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach triggers to all v3 tables
CREATE TRIGGER update_centroids_v3_updated_at
    BEFORE UPDATE ON centroids_v3
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_taxonomy_v3_updated_at
    BEFORE UPDATE ON taxonomy_v3
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ctm_updated_at
    BEFORE UPDATE ON ctm
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_titles_v3_updated_at
    BEFORE UPDATE ON titles_v3
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 6. Validation queries (commented out - for manual testing)
-- ============================================================================

-- Check table creation
-- SELECT table_name, table_type
-- FROM information_schema.tables
-- WHERE table_name IN ('centroids_v3', 'taxonomy_v3', 'ctm', 'titles_v3')
-- ORDER BY table_name;

-- Check indexes
-- SELECT tablename, indexname
-- FROM pg_indexes
-- WHERE tablename IN ('centroids_v3', 'taxonomy_v3', 'ctm', 'titles_v3')
-- ORDER BY tablename, indexname;

-- Check constraints
-- SELECT conname, contype, conrelid::regclass
-- FROM pg_constraint
-- WHERE conrelid IN ('centroids_v3'::regclass, 'taxonomy_v3'::regclass, 'ctm'::regclass, 'titles_v3'::regclass)
-- ORDER BY conrelid, conname;

COMMIT;

-- ============================================================================
-- Migration complete
-- ============================================================================
