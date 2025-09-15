# Centroids Database Schema Design

## Core Tables

### `centroids` Table
```sql
CREATE TABLE centroids (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL UNIQUE,
    category VARCHAR(20) NOT NULL CHECK (category IN ('ACTOR', 'THEME', 'THEATER', 'SYSTEM')),
    description TEXT NOT NULL,
    keywords JSONB NOT NULL, -- Array of keyword strings/phrases
    context JSONB, -- Additional metadata, aliases, sub-entities
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_centroids_category ON centroids(category);
CREATE INDEX idx_centroids_keywords ON centroids USING GIN(keywords);
CREATE INDEX idx_centroids_active ON centroids(is_active) WHERE is_active = true;
```

### `centroid_relationships` Table
```sql
CREATE TABLE centroid_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    centroid_a_id UUID REFERENCES centroids(id) ON DELETE CASCADE,
    centroid_b_id UUID REFERENCES centroids(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) DEFAULT 'related', -- 'related', 'contains', 'conflicts', 'enhances'
    strength FLOAT CHECK (strength >= 0.0 AND strength <= 1.0) DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(centroid_a_id, centroid_b_id)
);

CREATE INDEX idx_centroid_rel_a ON centroid_relationships(centroid_a_id);
CREATE INDEX idx_centroid_rel_b ON centroid_relationships(centroid_b_id);
```

## Integration Tables

### `title_centroid_matches` Table
```sql
CREATE TABLE title_centroid_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title_id UUID REFERENCES titles(id) ON DELETE CASCADE,
    centroid_id UUID REFERENCES centroids(id) ON DELETE CASCADE,
    match_score FLOAT CHECK (match_score >= 0.0 AND match_score <= 1.0) NOT NULL,
    match_method VARCHAR(50) NOT NULL, -- 'keyword', 'semantic', 'manual', 'llm'
    match_evidence JSONB, -- Which keywords matched, confidence scores, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(title_id, centroid_id)
);

CREATE INDEX idx_title_centroid_title ON title_centroid_matches(title_id);
CREATE INDEX idx_title_centroid_centroid ON title_centroid_matches(centroid_id);
CREATE INDEX idx_title_centroid_score ON title_centroid_matches(match_score DESC);
```

### `event_family_centroids` Table
```sql
CREATE TABLE event_family_centroids (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_family_id UUID REFERENCES event_families(id) ON DELETE CASCADE,
    centroid_id UUID REFERENCES centroids(id) ON DELETE CASCADE,
    relevance_score FLOAT CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0) NOT NULL,
    assignment_method VARCHAR(50) NOT NULL, -- 'aggregated', 'llm', 'manual'
    assignment_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(event_family_id, centroid_id)
);

CREATE INDEX idx_ef_centroids_ef ON event_family_centroids(event_family_id);
CREATE INDEX idx_ef_centroids_centroid ON event_family_centroids(centroid_id);
CREATE INDEX idx_ef_centroids_relevance ON event_family_centroids(relevance_score DESC);
```

## Usage Patterns

### 1. Title Processing (First Pass)
```sql
-- During title ingestion, match against centroids
INSERT INTO title_centroid_matches (title_id, centroid_id, match_score, match_method, match_evidence)
SELECT 
    :title_id,
    c.id,
    calculate_keyword_match_score(:title_text, c.keywords),
    'keyword',
    json_build_object('matched_keywords', find_matching_keywords(:title_text, c.keywords))
FROM centroids c
WHERE c.is_active = true
  AND calculate_keyword_match_score(:title_text, c.keywords) > 0.3;
```

### 2. Event Family Enhancement (Second Pass)
```sql
-- Aggregate centroid relevance for Event Families
INSERT INTO event_family_centroids (event_family_id, centroid_id, relevance_score, assignment_method)
SELECT 
    ef.id,
    tcm.centroid_id,
    AVG(tcm.match_score) as relevance_score,
    'aggregated'
FROM event_families ef
JOIN titles t ON t.event_family_id = ef.id
JOIN title_centroid_matches tcm ON tcm.title_id = t.id
GROUP BY ef.id, tcm.centroid_id
HAVING AVG(tcm.match_score) > 0.4;
```

### 3. Cross-EF Discovery (Third Pass)
```sql
-- Find Event Families sharing significant centroids
WITH shared_centroids AS (
    SELECT 
        efc1.event_family_id as ef1_id,
        efc2.event_family_id as ef2_id,
        efc1.centroid_id,
        (efc1.relevance_score + efc2.relevance_score) / 2 as shared_strength
    FROM event_family_centroids efc1
    JOIN event_family_centroids efc2 ON efc1.centroid_id = efc2.centroid_id
    WHERE efc1.event_family_id != efc2.event_family_id
      AND efc1.relevance_score > 0.6
      AND efc2.relevance_score > 0.6
)
SELECT ef1_id, ef2_id, COUNT(*) as shared_count, AVG(shared_strength) as avg_strength
FROM shared_centroids
GROUP BY ef1_id, ef2_id
HAVING COUNT(*) >= 2 AND AVG(shared_strength) > 0.7
ORDER BY shared_count DESC, avg_strength DESC;
```

## Migration Strategy

### Phase 1: Foundation
1. Create centroids tables
2. Populate with LLM-generated centroids (manual curation)
3. Build keyword matching functions

### Phase 2: Title Integration  
1. Add centroid matching to title processing pipeline
2. Backfill existing titles with centroid matches
3. Monitor match quality and tune thresholds

### Phase 3: EF Enhancement
1. Aggregate title centroids to Event Family level
2. Use centroids for improved EF clustering
3. Enable cross-EF discovery via shared centroids

### Phase 4: Advanced Features
1. Semantic matching (beyond keywords)
2. LLM-driven centroid assignment
3. Dynamic centroid evolution
4. Centroid-based narrative analysis

## Performance Considerations

- **Keyword matching**: Use PostgreSQL's full-text search capabilities
- **JSONB indexes**: Enable efficient centroid keyword queries  
- **Batch processing**: Process centroid matches in title processing batches
- **Caching**: Cache frequently accessed centroid data
- **Monitoring**: Track match quality and processing performance

This design supports your multi-pass approach while maintaining performance at scale.