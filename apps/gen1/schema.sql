-- GEN-1: Event Families and Framed Narratives Schema
-- Database tables for Event Family Assembly system

-- Event Families table - coherent real-world news happenings
CREATE TABLE IF NOT EXISTS event_families (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Core event information
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    key_actors TEXT[] DEFAULT '{}',
    event_type TEXT NOT NULL,
    geography TEXT NULL,
    
    -- Time boundaries
    event_start TIMESTAMP WITH TIME ZONE NOT NULL,
    event_end TIMESTAMP WITH TIME ZONE NULL,
    
    -- Source metadata (references to CLUST-2)
    source_bucket_ids TEXT[] DEFAULT '{}',
    source_title_ids TEXT[] DEFAULT '{}',
    
    -- Quality indicators
    confidence_score DECIMAL(3,2) NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    coherence_reason TEXT NOT NULL,
    
    -- Processing metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processing_notes TEXT NULL
);

-- Framed Narratives table - stanceful renderings of Event Families
CREATE TABLE IF NOT EXISTS framed_narratives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_family_id UUID NOT NULL REFERENCES event_families(id) ON DELETE CASCADE,
    
    -- Core narrative content
    frame_type TEXT NOT NULL,
    frame_description TEXT NOT NULL,
    stance_summary TEXT NOT NULL,
    
    -- Evidence and support
    supporting_headlines TEXT[] DEFAULT '{}',
    supporting_title_ids TEXT[] DEFAULT '{}',
    key_language TEXT[] DEFAULT '{}',
    
    -- Narrative strength
    prevalence_score DECIMAL(3,2) NOT NULL CHECK (prevalence_score >= 0.0 AND prevalence_score <= 1.0),
    evidence_quality DECIMAL(3,2) NOT NULL CHECK (evidence_quality >= 0.0 AND evidence_quality <= 1.0),
    
    -- Processing metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes for Event Families
CREATE INDEX IF NOT EXISTS idx_event_families_created_at ON event_families(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_event_families_event_start ON event_families(event_start DESC);
CREATE INDEX IF NOT EXISTS idx_event_families_event_type ON event_families(event_type);
CREATE INDEX IF NOT EXISTS idx_event_families_key_actors ON event_families USING GIN(key_actors);
CREATE INDEX IF NOT EXISTS idx_event_families_source_buckets ON event_families USING GIN(source_bucket_ids);
CREATE INDEX IF NOT EXISTS idx_event_families_confidence ON event_families(confidence_score DESC);

-- Performance indexes for Framed Narratives  
CREATE INDEX IF NOT EXISTS idx_framed_narratives_event_family ON framed_narratives(event_family_id);
CREATE INDEX IF NOT EXISTS idx_framed_narratives_created_at ON framed_narratives(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_framed_narratives_frame_type ON framed_narratives(frame_type);
CREATE INDEX IF NOT EXISTS idx_framed_narratives_prevalence ON framed_narratives(prevalence_score DESC);
CREATE INDEX IF NOT EXISTS idx_framed_narratives_evidence_quality ON framed_narratives(evidence_quality DESC);
CREATE INDEX IF NOT EXISTS idx_framed_narratives_supporting_titles ON framed_narratives USING GIN(supporting_title_ids);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_event_families_time_confidence ON event_families(created_at DESC, confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_framed_narratives_event_prevalence ON framed_narratives(event_family_id, prevalence_score DESC);

-- Full-text search indexes for content search
CREATE INDEX IF NOT EXISTS idx_event_families_fulltext ON event_families USING GIN(to_tsvector('english', title || ' ' || summary));
CREATE INDEX IF NOT EXISTS idx_framed_narratives_fulltext ON framed_narratives USING GIN(to_tsvector('english', frame_description || ' ' || stance_summary));

-- Updated timestamp triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_event_families_updated_at 
    BEFORE UPDATE ON event_families 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_framed_narratives_updated_at 
    BEFORE UPDATE ON framed_narratives 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE event_families IS 'GEN-1: Coherent real-world news happenings assembled from CLUST-2 buckets';
COMMENT ON TABLE framed_narratives IS 'GEN-1: Stanceful renderings showing how outlets frame Event Families';

COMMENT ON COLUMN event_families.title IS 'Clear, descriptive title for the event family';
COMMENT ON COLUMN event_families.summary IS 'Factual summary of what happened';
COMMENT ON COLUMN event_families.key_actors IS 'Primary actors/entities involved in the event';
COMMENT ON COLUMN event_families.event_type IS 'Type of event (diplomatic meeting, economic policy, etc.)';
COMMENT ON COLUMN event_families.geography IS 'Geographic location if relevant to the event';
COMMENT ON COLUMN event_families.source_bucket_ids IS 'CLUST-2 bucket IDs that contributed to this Event Family';
COMMENT ON COLUMN event_families.source_title_ids IS 'Title IDs that are part of this event family';
COMMENT ON COLUMN event_families.confidence_score IS 'LLM confidence in event coherence (0.0-1.0)';
COMMENT ON COLUMN event_families.coherence_reason IS 'Explanation of why these titles form a coherent event';

COMMENT ON COLUMN framed_narratives.frame_type IS 'Type of framing (supportive, critical, neutral, etc.)';
COMMENT ON COLUMN framed_narratives.frame_description IS 'How this narrative frames the event';
COMMENT ON COLUMN framed_narratives.stance_summary IS 'Clear statement of evaluative/causal framing';
COMMENT ON COLUMN framed_narratives.supporting_headlines IS 'Headlines that exemplify this framing';
COMMENT ON COLUMN framed_narratives.supporting_title_ids IS 'Title IDs that support this narrative';
COMMENT ON COLUMN framed_narratives.key_language IS 'Key words/phrases that signal this framing';
COMMENT ON COLUMN framed_narratives.prevalence_score IS 'How dominant this framing is (0.0-1.0)';
COMMENT ON COLUMN framed_narratives.evidence_quality IS 'Quality of supporting evidence (0.0-1.0)';

-- Validation constraints
ALTER TABLE event_families ADD CONSTRAINT check_event_family_has_content 
    CHECK (length(trim(title)) > 0 AND length(trim(summary)) > 0);

ALTER TABLE event_families ADD CONSTRAINT check_event_family_time_logic 
    CHECK (event_end IS NULL OR event_end >= event_start);

ALTER TABLE framed_narratives ADD CONSTRAINT check_framed_narrative_has_content 
    CHECK (length(trim(frame_description)) > 0 AND length(trim(stance_summary)) > 0);

ALTER TABLE framed_narratives ADD CONSTRAINT check_framed_narrative_has_support 
    CHECK (array_length(supporting_headlines, 1) > 0 OR array_length(supporting_title_ids, 1) > 0);