-- EF Context Enhancement Migration
-- Adds strategic context fields and removes unused fields
-- Created: 2025-09-22

BEGIN;

-- Remove unused fields from event_families table
ALTER TABLE event_families
    DROP COLUMN IF EXISTS promotion_score,
    DROP COLUMN IF EXISTS event_start,
    DROP COLUMN IF EXISTS event_end;

-- Add new context field (primary_theater already exists)
ALTER TABLE event_families
    ADD COLUMN ef_context JSONB DEFAULT '{}';

-- Create index for ef_context JSONB queries
CREATE INDEX IF NOT EXISTS idx_event_families_ef_context ON event_families USING GIN (ef_context);
CREATE INDEX IF NOT EXISTS idx_event_families_primary_theater ON event_families (primary_theater);

-- Create centroids table for macro-link management
CREATE TABLE IF NOT EXISTS centroids (
    id VARCHAR(50) PRIMARY KEY,  -- e.g., "ARC-UKR", "ARC-CLIMATE"
    label TEXT NOT NULL,         -- e.g., "War in Ukraine / NATO–Russia confrontation"
    keywords TEXT[] DEFAULT '{}',-- Keywords for mechanical matching
    actors TEXT[] DEFAULT '{}',  -- Primary actors for matching
    theaters TEXT[] DEFAULT '{}',-- Geographic theaters for matching
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index for centroids keyword/actor/theater matching
CREATE INDEX IF NOT EXISTS idx_centroids_keywords ON centroids USING GIN (keywords);
CREATE INDEX IF NOT EXISTS idx_centroids_actors ON centroids USING GIN (actors);
CREATE INDEX IF NOT EXISTS idx_centroids_theaters ON centroids USING GIN (theaters);

-- Create updated_at trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language plpgsql;

-- Create updated_at trigger for centroids
CREATE TRIGGER update_centroids_updated_at
    BEFORE UPDATE ON centroids
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert centroids data from centroids.json
INSERT INTO centroids (id, label, keywords, actors, theaters) VALUES
    ('ARC-UKR', 'War in Ukraine / NATO–Russia confrontation',
     ARRAY['ukraine','russia','donbas','crimea','nato','poland','belarus'],
     ARRAY['Russia','Ukraine','NATO','Poland','Belarus','United States'],
     ARRAY['Ukraine','Eastern Europe','Black Sea']),

    ('ARC-MIDEAST-ISR', 'Israel–Palestine conflict',
     ARRAY['israel','gaza','hamas','west bank','idf','ceasefire'],
     ARRAY['Israel','Palestine','Hamas','Fatah'],
     ARRAY['Gaza','West Bank','Israel']),

    ('ARC-MIDEAST-IRN', 'Israel–Iran regional rivalry',
     ARRAY['iran','hezbollah','qatar','syria','iran nuclear','iaea'],
     ARRAY['Israel','Iran','Hezbollah','Qatar','Syria'],
     ARRAY['Middle East','Levant','Persian Gulf']),

    ('ARC-REDSEA', 'Red Sea and Yemen conflict',
     ARRAY['houthi','yemen','aden','red sea','shipping','suez','gulf of aden'],
     ARRAY['Houthis','Saudi Arabia','UAE','Egypt','US Navy'],
     ARRAY['Red Sea','Gulf of Aden','Yemen']),

    ('ARC-CHN-TWN', 'China–Taiwan–US tensions',
     ARRAY['taiwan','pla drills','adiz','reunification','tsmc','arms sale'],
     ARRAY['China','Taiwan','United States'],
     ARRAY['Taiwan Strait','East China Sea']),

    ('ARC-SCS', 'South China Sea disputes',
     ARRAY['south china sea','spratly','paracel','scarborough','freedom of navigation'],
     ARRAY['China','Philippines','Vietnam','Malaysia','US Navy'],
     ARRAY['South China Sea']),

    ('ARC-KOREA', 'Korean Peninsula tensions',
     ARRAY['north korea','south korea','missile','dmz','denuclearization'],
     ARRAY['North Korea','South Korea','United States','China'],
     ARRAY['Korean Peninsula']),

    ('ARC-INDPAK', 'India–Pakistan rivalry',
     ARRAY['kashmir','line of control','pulwama','surgical strike'],
     ARRAY['India','Pakistan'],
     ARRAY['Kashmir','South Asia']),

    ('ARC-MYANMAR', 'Myanmar civil conflict',
     ARRAY['myanmar','junta','rohingya','ethnic armed groups'],
     ARRAY['Myanmar military','Opposition groups','ASEAN'],
     ARRAY['Myanmar','Southeast Asia']),

    ('ARC-AFRICA-SAHEL', 'Sahel coups & jihadist insurgencies',
     ARRAY['mali','niger','burkina','coup','jihadists','french withdrawal'],
     ARRAY['Mali','Niger','Burkina Faso','France','ECOWAS'],
     ARRAY['Sahel','West Africa']),

    ('ARC-HORN', 'Horn of Africa conflicts',
     ARRAY['ethiopia','eritrea','somalia','sudan','tigray'],
     ARRAY['Ethiopia','Eritrea','Somalia','Sudan'],
     ARRAY['Horn of Africa','Red Sea']),

    ('ARC-LATAM-VEN', 'Venezuela crisis',
     ARRAY['venezuela','maduro','guyana','oil','sanctions'],
     ARRAY['Venezuela','Guyana','United States'],
     ARRAY['Venezuela','Latin America']),

    ('ARC-BALKANS', 'Balkans tensions',
     ARRAY['serbia','kosovo','bosnia','dayton','nato'],
     ARRAY['Serbia','Kosovo','Bosnia','EU','NATO'],
     ARRAY['Balkans']),

    ('ARC-US-ELECT', 'US electoral cycle & polarization',
     ARRAY['us election','campaign','primary','assassination attempt','trump','biden','ballot'],
     ARRAY['United States','Donald Trump','Joe Biden'],
     ARRAY['United States']),

    ('ARC-EU-COHESION', 'EU cohesion and internal strains',
     ARRAY['brexit','hungary','poland','eu budget','eu elections'],
     ARRAY['European Union','Hungary','Poland'],
     ARRAY['Europe','EU institutions']),

    ('ARC-BRICS', 'Global South / BRICS+ assertion',
     ARRAY['brics','summit','africa','south-south','non-aligned'],
     ARRAY['Brazil','Russia','India','China','South Africa'],
     ARRAY['Global South']),

    ('ARC-ENERGY', 'Global energy geopolitics',
     ARRAY['opec','oil','gas','lng','pipeline','nuclear','renewables'],
     ARRAY['OPEC','Saudi Arabia','Russia','EU','United States'],
     ARRAY['Middle East','Europe','Global']),

    ('ARC-CLIMATE', 'Climate change impacts',
     ARRAY['climate','flood','heatwave','cop','adaptation','mitigation'],
     ARRAY['UNFCCC','IPCC','UN'],
     ARRAY['Global']),

    ('ARC-TECH', 'AI, tech & cyber competition',
     ARRAY['semiconductor','chip','ai','cyber','quantum','tsmc','openai'],
     ARRAY['United States','China','Taiwan','EU','Big Tech firms'],
     ARRAY['Global']),

    ('ARC-TRADE', 'Global trade & finance',
     ARRAY['wto','tariffs','sanctions','supply chain','debt crisis','dollar'],
     ARRAY['United States','EU','China','IMF','World Bank'],
     ARRAY['Global']),

    ('ARC-MIGRATION', 'Migration and demographics',
     ARRAY['refugee','migrant','border','aging','population','demographic'],
     ARRAY['UNHCR','EU','US','Latin America'],
     ARRAY['Global']),

    ('ARC-HEALTH', 'Global health & pandemics',
     ARRAY['pandemic','covid','vaccine','who','epidemic'],
     ARRAY['WHO','United States','China'],
     ARRAY['Global']),

    ('ARC-INFOOPS', 'Information & media systems',
     ARRAY['disinformation','propaganda','social media','platform','digital sovereignty'],
     ARRAY['Russia','China','US','EU','Big Tech'],
     ARRAY['Global']),

    ('ARC-ALLIANCES', 'Alliance systems under stress',
     ARRAY['nato','quad','aukus','us-japan-korea'],
     ARRAY['United States','Japan','Australia','India','NATO'],
     ARRAY['Global']),

    ('ARC-AUTHDEM', 'Authoritarian vs democratic governance',
     ARRAY['human rights','democracy','autocracy','freedom','rule of law'],
     ARRAY['US','EU','China','Russia'],
     ARRAY['Global']),

    ('ARC-RELIGION', 'Religious & identity politics',
     ARRAY['sunni','shia','hindu nationalism','evangelical'],
     ARRAY['Iran','Saudi Arabia','India','US'],
     ARRAY['Global']);

-- Add comments for documentation
COMMENT ON COLUMN event_families.ef_context IS 'Strategic context: macro_link, comparables, abnormality';
COMMENT ON TABLE centroids IS 'Narrative centroids/storylines for macro-link classification';

-- Migration complete
INSERT INTO runs (phase, prompt_version, input_ref, output_ref)
VALUES ('migration', '005_ef_context', 'event_families_schema',
        '{"fields_removed": ["promotion_score", "confidence_score", "event_start", "event_end"], "fields_added": ["ef_context"], "tables_created": ["centroids"]}');

COMMIT;