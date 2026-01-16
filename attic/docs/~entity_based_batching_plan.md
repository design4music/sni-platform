# Entity-Based Semantic Batching - Mini Development Plan

## Current State
- ✅ GEN-1 exists and processes titles → Event Families
- ✅ `titles.entities` column exists (JSONB)  
- ✅ Strategic Gate produces strategic titles (`gate_keep = true`)
- ❌ Need to populate `titles.entities` with extracted entities
- ❌ Need entity-based batching logic for LLM processing

## Goal: Entity-Based Semantic Batching
Group strategic titles by shared entities for optimal LLM processing, handling entity overlaps intelligently.

---

## **Phase 1: Entity Population** 🔧

### 1.1 Populate titles.entities (PRIORITY)
**File**: `apps/clust1/entity_enrichment.py` (new)

```python
def enrich_title_entities(title_dict):
    """Extract and store entities in titles.entities column"""
    # Use existing taxonomy_extractor from CLUST-1
    entities = {
        "actors": extract_actors(title_text),      # Countries, orgs
        "people": extract_people(title_text),      # Politicians 
        "themes": extract_themes(title_text),      # From stop/go lists
        "locations": extract_locations(title_text) # Geographic
    }
    return entities

def backfill_strategic_titles():
    """Backfill existing strategic titles with entities"""
    # Process titles WHERE gate_keep = true AND entities IS NULL
```

### 1.2 Integration Point
Modify `apps/clust1/run_gate.py` to populate entities during gate processing:
```python
# After gate processing, before database update:
if gate_result.keep:
    title_entities = enrich_title_entities(title)
    update_data['entities'] = title_entities
```

---

## **Phase 2: Entity-Based Batching** 🎯 **CORE LOGIC**

### 2.1 Entity Similarity Calculator
**File**: `apps/gen1/entity_grouper.py` (new)

```python
def calculate_entity_similarity(entities_a, entities_b):
    """Calculate similarity between two entity sets"""
    # Weighted similarity across entity types
    weights = {"actors": 0.4, "people": 0.3, "themes": 0.2, "locations": 0.1}
    
    total_score = 0
    for entity_type, weight in weights.items():
        jaccard = jaccard_similarity(entities_a[entity_type], entities_b[entity_type])
        total_score += jaccard * weight
    
    return total_score

def group_titles_by_entities(titles, similarity_threshold=0.3):
    """Group titles with similar entity profiles"""
    # Clustering algorithm based on entity similarity
    # Returns: List[List[title_dict]] - groups of similar titles
```

### 2.2 Handle Overlapping Entities **KEY CHALLENGE**
```python
def merge_related_entities(entity_groups):
    """Handle overlapping entities intelligently"""
    
    # Example: ["donald_trump", "US"] should be merged
    entity_hierarchy = {
        "donald_trump": ["US", "republican_party"],  # Trump implies US context
        "putin": ["Russia", "kremlin"],
        "xi_jinping": ["China", "CCP"]
    }
    
    # Strategy 1: Hierarchical Merging
    def expand_entity_context(entities):
        expanded = set(entities)
        for entity in entities:
            if entity in entity_hierarchy:
                expanded.update(entity_hierarchy[entity])
        return list(expanded)
    
    # Strategy 2: Co-occurrence Analysis  
    def find_frequent_pairs(titles):
        # Identify entities that frequently appear together
        # Use this to inform batching decisions
        pass
    
    # Strategy 3: Semantic Proximity
    def semantic_merge_threshold():
        # If Trump + US appear together > 80% of time, treat as related
        return 0.8
```

---

## **Phase 3: Batch Assembly** 📦

### 3.1 Smart Batch Construction
**File**: `apps/gen1/batch_assembler.py` (new)

```python
def create_semantic_batches(strategic_titles, target_batch_size=50):
    """Create entity-coherent batches for LLM processing"""
    
    # Step 1: Group by primary entities
    entity_groups = group_titles_by_entities(strategic_titles)
    
    # Step 2: Handle overlaps
    merged_groups = merge_related_entities(entity_groups)
    
    # Step 3: Size optimization
    optimized_batches = []
    for group in merged_groups:
        if len(group) > target_batch_size:
            # Split large groups by secondary criteria (time, themes)
            sub_batches = split_large_group(group, target_batch_size)
            optimized_batches.extend(sub_batches)
        elif len(group) < 10:
            # Merge small groups with compatible entities
            compatible_batch = find_compatible_batch(group, optimized_batches)
            if compatible_batch:
                compatible_batch.extend(group)
            else:
                optimized_batches.append(group)
        else:
            optimized_batches.append(group)
    
    return optimized_batches

def split_large_group(large_group, target_size):
    """Split large entity group by secondary criteria"""
    # Secondary clustering by timeframe or themes
    # Keep entity coherence while managing batch size
```

### 3.2 Batch Quality Validation
```python
def validate_batch_coherence(batch):
    """Ensure batch has coherent entity profile"""
    
    # Check 1: Dominant entity overlap
    entity_overlap = calculate_dominant_entities(batch)
    if entity_overlap < 0.6:
        return False, "Low entity coherence"
    
    # Check 2: Geographic coherence  
    locations = extract_batch_locations(batch)
    if len(locations) > 3:  # Too geographically scattered
        return False, "Geographic scatter"
    
    # Check 3: Temporal coherence
    time_span = calculate_time_span(batch) 
    if time_span > 72:  # Hours
        return False, "Temporal scatter"
        
    return True, "Coherent batch"
```

---

## **Phase 4: Integration with GEN-1** 🔄

### 4.1 Modify Existing run_gen1.py
```python
# Replace current title fetching logic:

# OLD:
strategic_titles = fetch_strategic_titles(limit=100)

# NEW:  
strategic_titles = fetch_strategic_titles(limit=500)  # Larger pool
semantic_batches = create_semantic_batches(strategic_titles)

for batch in semantic_batches:
    logger.info(f"Processing entity-coherent batch: {len(batch)} titles")
    batch_context = extract_batch_entity_context(batch)
    
    # Enhanced LLM prompt with entity context
    ef_results = process_batch_with_entity_context(batch, batch_context)
```

### 4.2 Enhanced LLM Prompts
```python
def create_entity_aware_prompt(batch, entity_context):
    """Create LLM prompt with entity context"""
    
    prompt = f"""
    You are analyzing {len(batch)} news titles that share common entities:
    
    DOMINANT ENTITIES:
    - Actors: {entity_context['primary_actors']}
    - People: {entity_context['key_people']}  
    - Themes: {entity_context['main_themes']}
    - Geography: {entity_context['regions']}
    
    Based on these shared entities, identify Event Families that represent 
    coherent geopolitical narratives...
    """
```

---

## **Implementation Steps** 📋

### Week 1: Entity Infrastructure
1. **Create `apps/clust1/entity_enrichment.py`**
   - Implement `enrich_title_entities()`
   - Reuse existing `taxonomy_extractor` logic
   - Add entity hierarchy definitions

2. **Modify `apps/clust1/run_gate.py`**
   - Add entity enrichment to gate processing
   - Update database schema calls

3. **Backfill Script**
   - Create `backfill_strategic_entities.py`
   - Process existing strategic titles

### Week 2: Batching Logic
1. **Create `apps/gen1/entity_grouper.py`**
   - Implement entity similarity calculation
   - Build grouping algorithms

2. **Create `apps/gen1/batch_assembler.py`**
   - Smart batch construction
   - Handle entity overlaps
   - Size optimization

### Week 3: Integration & Testing
1. **Modify `apps/gen1/run_gen1.py`**
   - Replace current batching with entity-based
   - Enhanced LLM prompts

2. **Testing & Validation**
   - A/B test: current vs entity-based batching
   - Measure Event Family quality improvements
   - Performance benchmarking

---

## **Open Questions & Solutions**

### Q1: How to handle overlapping entities (Trump + US)?
**Solution**: Multi-strategy approach
- **Hierarchy-based**: Trump → US context automatically
- **Co-occurrence**: Learn from data which entities frequently pair
- **Semantic proximity**: Use similarity thresholds

### Q2: What if entity extraction misses key entities?
**Solution**: Progressive fallback
- Primary: CSV vocabulary matching
- Secondary: LLM-based entity recognition
- Tertiary: Semantic similarity clustering

### Q3: How to validate batch quality?
**Solution**: Multi-dimensional validation
- Entity coherence score
- Geographic coherence  
- Temporal coherence
- LLM confidence scores

### Q4: Performance impact on current pipeline?
**Solution**: Incremental deployment
- Phase 1: Populate entities (low impact)
- Phase 2: A/B test batching approaches
- Phase 3: Full rollout based on results

---

## **Success Metrics**

- **Entity Coverage**: >90% of strategic titles have populated entities
- **Batch Coherence**: >80% of batches pass coherence validation
- **EF Quality**: Improved coherence scores vs current approach
- **Processing Efficiency**: Maintain or improve current processing times
- **Cross-entity Discovery**: Identify previously missed event connections

This plan focuses specifically on the entity-based batching challenge while building on existing SNI infrastructure.