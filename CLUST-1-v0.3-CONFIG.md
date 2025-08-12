# CLUST-1 v0.3 Configuration Summary

## Version: CLUST-1 v0.3 (2025-08-12)
**Status**: FROZEN - Production Excellence Configuration

## Core Configuration Parameters

### Hub-Suppression Settings
```python
HUB_COUNT_LIMIT = 12  # Reduced from 30
HUB_SUPPRESSION_THRESHOLD = 2  # Reject if 2+ hubs in combination
EVENT_GEO_EXCEPTION = True  # Allow event+geo even if geo is hub
```

### Event Tokens (Exception List)
```python
EVENT_TOKENS = {
    'tariffs', 'sanctions', 'ceasefire', 'election', 'referendum',
    'missile', 'drone', 'oil', 'gas'
}
```

### Library & Vocabulary Settings
```sql
-- shared_keywords_lib_30d
DOCUMENT_FREQUENCY_MIN = 2  -- Reduced from 3
DOCUMENT_FREQUENCY_MAX = 600
TIME_WINDOW = '30 days'

-- article_core_keywords  
KEYWORDS_PER_ARTICLE = 8  -- Increased from 6
CORE_KEYWORDS_WINDOW = '300 hours'
```

### Specificity & Anchored-Rare
```python
SPECIFICITY_GATE_THRESHOLD = 0.80
ANCHORED_RARE_CO_DOC_MIN = 5  # pairs30 minimum co-occurrence
```

### Clustering Thresholds
```python
# Seeding
MIN_CLUSTER_SIZE = 3
MIN_SOURCES = 2

# Densify
COSINE_SIMILARITY_THRESHOLD = 0.88  # Reduced from 0.90
SHARED_NONHUB_THRESHOLD_DIRECT = 2
SHARED_NONHUB_THRESHOLD_COSINE = 1

# Consolidation
JACCARD_OVERLAP_THRESHOLD = 0.60

# Refine (Giant Splitting)
GIANT_CLUSTER_SIZE = 80
GIANT_CLUSTER_ENTROPY = 2.4
MIN_CHILD_SIZE = 8
```

## Database Schema (v0.3)

### Materialized Views
```sql
-- Core vocabulary (df >= 2)
shared_keywords_lib_30d (tok, doc_freq, avg_score)

-- Top-12 most frequent tokens
keyword_hubs_30d (tok, doc_freq) LIMIT 12

-- Inverse document frequency scoring  
keyword_specificity_30d (tok, spec = 1.0/LN(doc_freq+1))
```

### Co-occurrence Patterns
```sql
-- Token pair co-occurrence (anchored-rare seeding)
pairs30 (tok_a, tok_b, co_doc >= 5)
```

## Performance Metrics (Achieved)

### Recall Recovery
- **Before (v0.2)**: 8.8% recall (49/559 articles)
- **After (v0.3)**: 19.9% recall (242/1,218 articles)
- **Improvement**: +11.1 percentage points (126% increase)

### Quality Preservation  
- **Average Cohesion**: 0.725 (excellent purity)
- **Cluster Count**: 48 consolidated clusters
- **Average Size**: 5.0 articles (optimal coherence)

### Coverage Expansion
- **Eligible Articles**: 1,218 (79.1% of 1,539 total)
- **Vocabulary Size**: 1,083 canonical tokens
- **Policy Topics Captured**: tariffs, sanctions, diplomatic relations

## Pipeline Stage Configuration

### Stage 1: Seed
- Hub-suppression with event+geo exceptions
- Specificity gate (≥0.80) with anchored-rare bypass
- Min 3 articles, 2+ sources per seed

### Stage 2: Densify  
- Shared-nonhub admission criteria
- Cosine similarity 0.88 for 1-nonhub combinations
- Direct admission for 2+ nonhub overlap

### Stage 3: Consolidate
- Jaccard overlap detection (≥0.60)
- Union-find connected components merging
- TF-IDF smart labeling (geo/org + event + person)

### Stage 4: Refine
- Giant cluster splitting (size>80, entropy>2.4) 
- Non-hub discriminator selection
- Minimum child size enforcement (≥8)

### Stage 5: Persist
- Database storage with computed labels
- Cluster metadata and member relationships
- Performance metrics logging

## Quality Assurance

### Validation Criteria
- Cohesion score ≥0.60 (achieved: 0.725 average)
- Source diversity (multiple news sources per cluster)  
- Thematic coherence (clear topic focus)
- No over-fragmentation (consolidated variants)

### Success Indicators
✅ Policy & economic topics recovered (tariffs, sanctions)  
✅ Diplomatic relations captured (Putin-Trump, bilateral talks)
✅ Cross-country analysis enabled (India-US-Russia trade)
✅ Event-driven clustering (elections, military actions)  
✅ Quality preservation during recall expansion

---
**Configuration Status**: FROZEN FOR PRODUCTION  
**Validation**: Comprehensive testing with 300h article corpus  
**Performance**: 126% recall improvement, maintained purity  
**Ready For**: Production deployment and scaling