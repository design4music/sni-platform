# Key Architectural Decisions - GEN-1 Event Family Generation

*September 11, 2025*

## Current State Assessment

### ✅ Achievements
- **Database Fix Completed**: UUID casting error resolved, title assignments working perfectly
- **Corpus-Wide Processing**: Successfully processes 7,501 unassigned strategic titles
- **Quality Output**: High-confidence Event Families (0.75-0.95) with sophisticated Framed Narratives
- **Simplified Architecture**: Removed artificial time windows, processes entire corpus intelligently

### 🚨 Critical Performance Issues Identified

**8-Minute Processing Analysis:**
- **Speed**: 44 titles processed in 8 minutes = 5.5 titles/minute
- **Projected Total Time**: ~22 hours for full corpus (not viable for production)
- **Micro-EF Problem**: Creating tiny, specific events instead of broad strategic themes
- **Example**: 3 headlines → 1 micro-EF instead of 200 related titles → 1-3 strategic EFs

## Architectural Problems Diagnosed

### Problem 1: Chronological Batching
**Current Approach (Flawed):**
```python
# Sequential batches of 50 titles regardless of content
batch_1 = titles[0:50]    # Random mix: Trump, Gaza, Russia, etc.
batch_2 = titles[50:100]  # Another random mix
```

**Result**: LLM cannot see thematic connections across batches, creates fragmented micro-events.

### Problem 2: Insufficient Context for Strategic Narratives
- **Current**: 50 titles → multiple tiny EFs
- **Needed**: 200+ related titles → comprehensive strategic EF
- **Core Issue**: Cannot create overarching strategic narratives from limited, unrelated headlines

### Problem 3: Processing Inefficiency  
- **2 minutes per batch** (50 titles) = too slow
- **LLM calls**: 2 per batch (EF + FN generation) × 151 batches = 302+ API calls
- **Cost implications**: Substantial with current approach

## Strategic Solutions Identified

### Solution 1: Entity-Based Semantic Batching 🎯 **PRIORITY**

**Concept**: Group titles by strategic actor entities before LLM processing

**Implementation:**
```python
# Group by strategic entities
trump_titles = get_titles_with_entity("donald_trump")  # ~200 titles
gaza_titles = get_titles_with_entity("palestine")      # ~150 titles  
russia_titles = get_titles_with_entity("russia")       # ~180 titles

# Create semantic batches
trump_batch = process_entity_batch(trump_titles)
gaza_batch = process_entity_batch(gaza_titles)

# Handle overlapping entities (Trump + US together)
combined_batch = merge_related_entities(["donald_trump", "US"])
```

**Benefits:**
- **Thematic Coherence**: LLM sees all related content together
- **Strategic Scale**: Creates comprehensive narratives from large title sets
- **Processing Efficiency**: Fewer, larger, more meaningful batches
- **Natural Grouping**: Israel+Palestine, Russia+Ukraine, Trump+US politics

### Solution 2: Two-Pass Architecture 🚀 **FUTURE ENHANCEMENT**

**Pass 1: Quick Assembly**
- Basic EF creation with minimal metadata
- Focus on grouping and initial categorization
- No Framed Narratives generation
- Fast processing for initial structure

**Pass 2: Strategic Enhancement**
- Merge related micro-EFs into macro-themes
- Generate comprehensive Framed Narratives with full context
- Build overarching strategic narratives
- Quality refinement and consolidation

**Benefits:**
- **Speed**: Fast initial processing
- **Quality**: Deep analysis with full context
- **Flexibility**: Can run passes independently
- **Scalability**: Optimizes both speed and depth

## Technical Implementation Plan

### Phase 1: Entity-Based Batching
1. **Database Query Enhancement**: 
   ```sql
   SELECT DISTINCT jsonb_array_elements_text(entities->'actors') as actor
   FROM titles WHERE gate_keep = true AND event_family_id IS NULL
   ORDER BY COUNT(*) DESC
   ```

2. **Semantic Batch Creation**:
   - Group titles by dominant entities
   - Handle overlapping entity relationships  
   - Create batches of 100-200 related titles

3. **LLM Prompt Optimization**:
   - Update prompts for larger, thematic context
   - Focus on strategic, overarching narratives
   - Reduce micro-event creation

### Phase 2: Two-Pass Processing (Future)
1. **Quick Assembly Pass**: Basic EF creation
2. **Enhancement Pass**: Consolidation and FN generation
3. **Optimization**: Cost and speed improvements

## Decision Rationale

### Why Entity-Based Batching?
- **Immediate Impact**: Addresses both speed and quality issues
- **Architectural Soundness**: Aligns with natural news thematic grouping
- **Cost Effective**: Fewer, more efficient LLM calls
- **Strategic Relevance**: Creates the broad narratives we need

### Why Two-Pass is Secondary?
- **Complexity**: More architectural changes required
- **Current Priority**: Need working solution first
- **Optimization**: Can be added after core batching works

## Success Metrics

### Target Performance
- **Processing Time**: <4 hours for full corpus (5x improvement)
- **Event Family Scale**: 10-50 titles per EF (not 3-5)
- **Strategic Scope**: Broad thematic narratives, not micro-events
- **API Efficiency**: <100 LLM calls for full corpus

### Quality Indicators
- **Thematic Coherence**: EFs should represent strategic themes
- **Title Coverage**: Higher percentage of titles assigned per batch
- **Narrative Depth**: FNs should reflect comprehensive analysis
- **Confidence Scores**: Maintain 0.85+ with better context

## Next Actions

1. **✅ Document Complete**: Current findings captured
2. **🔄 Commit Current State**: Preserve working corpus-wide processing
3. **🚀 Implement Entity-Based Batching**: Priority development focus
4. **📊 Benchmark Performance**: Test improvements against current metrics
5. **🎯 Optimize and Iterate**: Refine based on results

---

*This document captures the transition from micro-event generation to strategic narrative assembly through intelligent entity-based processing.*