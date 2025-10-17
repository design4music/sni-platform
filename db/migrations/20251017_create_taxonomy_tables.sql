-- Create taxonomy management tables
-- Replaces: data/actors.csv, data/go_people.csv, data/stop_culture.csv
-- Enables dynamic taxonomy management with multilingual support

-- 1. Taxonomy categories (flat structure)
CREATE TABLE IF NOT EXISTS taxonomy_categories (
    category_id TEXT PRIMARY KEY, -- e.g., 'culture_cinema', 'politics_elections', 'actors_countries'
    name_en TEXT NOT NULL, -- Human-readable name in English
    description TEXT, -- Optional description of what this category covers
    is_positive BOOLEAN DEFAULT FALSE, -- TRUE for go_list categories, FALSE for stop_list
    is_active BOOLEAN DEFAULT TRUE, -- Allow soft-deletion of categories
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. Taxonomy terms (multilingual JSONB)
CREATE TABLE IF NOT EXISTS taxonomy_terms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id TEXT NOT NULL REFERENCES taxonomy_categories(category_id) ON DELETE CASCADE,

    -- Multilingual terms as JSONB
    -- Structure: {"en": ["term1", "term2"], "es": ["término1"], "ar": ["مصطلح١"], ...}
    -- This matches the proven multilingual approach from data_entities.aliases
    terms JSONB NOT NULL DEFAULT '{}',

    -- Optional metadata
    priority INTEGER DEFAULT 0, -- Higher priority terms checked first (for performance)
    notes TEXT, -- Internal notes about this term group

    -- Status flags
    is_active BOOLEAN DEFAULT TRUE, -- Allow soft-deletion of terms

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT terms_not_empty CHECK (jsonb_typeof(terms) = 'object' AND terms != '{}')
);

-- Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_taxonomy_categories_positive ON taxonomy_categories(is_positive) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_taxonomy_categories_active ON taxonomy_categories(is_active);

CREATE INDEX IF NOT EXISTS idx_taxonomy_terms_category ON taxonomy_terms(category_id) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_taxonomy_terms_active ON taxonomy_terms(is_active);
CREATE INDEX IF NOT EXISTS idx_taxonomy_terms_priority ON taxonomy_terms(priority DESC) WHERE is_active = TRUE;

-- GIN index for fast JSONB term matching
CREATE INDEX IF NOT EXISTS idx_taxonomy_terms_jsonb ON taxonomy_terms USING GIN(terms jsonb_path_ops);

-- Comments for documentation
COMMENT ON TABLE taxonomy_categories IS 'Taxonomy category definitions - replaces CSV-based vocabulary management';
COMMENT ON COLUMN taxonomy_categories.category_id IS 'Unique identifier for category (e.g., culture_cinema, politics_elections)';
COMMENT ON COLUMN taxonomy_categories.is_positive IS 'TRUE for go_list (strategic content), FALSE for stop_list (filter out)';

COMMENT ON TABLE taxonomy_terms IS 'Multilingual taxonomy terms organized by category';
COMMENT ON COLUMN taxonomy_terms.terms IS 'Multilingual terms as JSONB: {"en": ["term1"], "es": ["término1"], ...}';
COMMENT ON COLUMN taxonomy_terms.priority IS 'Higher priority terms checked first for performance optimization';

-- Insert initial category structure (migrated from CSV files)
INSERT INTO taxonomy_categories (category_id, name_en, description, is_positive) VALUES
    -- Positive categories (go_list / strategic actors)
    ('actors_countries', 'Countries', 'Strategic countries and states', TRUE),
    ('actors_capitals', 'Capital Cities', 'Capital cities of strategic importance', TRUE),
    ('actors_people', 'Strategic People', 'Politicians, military leaders, diplomats', TRUE),
    ('actors_organizations', 'Strategic Organizations', 'NATO, UN, EU, military alliances', TRUE),

    -- Negative categories (stop_list / non-strategic topics)
    ('stop_culture_entertainment', 'Entertainment & Pop Culture', 'Movies, music, celebrities, awards', FALSE),
    ('stop_culture_sports', 'Sports', 'Sports events, athletes, competitions', FALSE),
    ('stop_culture_lifestyle', 'Lifestyle', 'Fashion, cooking, travel, wellness', FALSE),
    ('stop_culture_tech_consumer', 'Consumer Technology', 'Product reviews, gadget news, apps', FALSE),
    ('stop_culture_business_markets', 'Business & Markets', 'Stock prices, earnings, IPOs (non-strategic)', FALSE),
    ('stop_culture_crime_local', 'Local Crime', 'Robberies, murders, local incidents', FALSE),
    ('stop_culture_weather', 'Weather & Natural Disasters', 'Storms, earthquakes (unless strategic impact)', FALSE),
    ('stop_culture_science_general', 'General Science', 'Research discoveries (unless strategic impact)', FALSE)
ON CONFLICT (category_id) DO NOTHING;
