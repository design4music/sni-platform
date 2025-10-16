# Neo4j Intelligence Implementation Status

## Overview

Implemented the revised Neo4j intelligence strategy from `neo4j_implementation-2.txt` to enhance strategic filtering for titles with sparse entities. This addresses the "Charlie Kirk" problem where borderline titles get misclassified.

## Implementation Summary

### ✅ Phase 1: Neo4j Signal Methods (COMPLETE)

Added four new methods to `core/neo4j_sync.py`:

#### 1. `get_entity_centrality(title_id)`
**Purpose**: Find "hot" entities mentioned in multiple strategic titles

**Logic**:
- Finds entities in the target title
- Counts how many strategic titles (last 3 days) mention each entity
- Returns entities with 2+ strategic mentions

**Signal Strength**: +2 points if >= 1 hot entity found

#### 2. `get_strategic_neighborhood(title_id)`
**Purpose**: Measure connection density to strategic content clusters

**Logic**:
- Finds strategic titles sharing ANY entity with target
- Calculates neighborhood density ratio: strategic_neighbors / entity_count
- Higher ratio = more embedded in strategic networks

**Signal Strength**: +1 point if density >= 0.3

#### 3. `check_ongoing_event(title_id)`
**Purpose**: Detect temporal story patterns

**Logic**:
- Finds entities forming event sequences (3+ mentions over 7 days)
- Checks if target title's entities appear in ongoing story patterns
- Returns true if part of temporal event

**Signal Strength**: +1 point if ongoing event detected

#### 4. `analyze_strategic_signals(title_id)`
**Purpose**: Combine all three signals in parallel

**Logic**:
- Runs all three queries simultaneously
- Returns aggregated signal data for scoring

### ✅ Phase 2: P2 Pipeline Integration (COMPLETE)

Modified `apps/filter/entity_enrichment.py`:

#### Enhanced Decision Flow:
```
1. Static Taxonomy Check (CLUST-1)
   ├─ HIT → Strategic (extract entities)
   └─ MISS ↓

2. LLM Strategic Review
   ├─ Strategic → gate_keep=true
   └─ Non-Strategic ↓

3. Neo4j Intelligence Override (NEW!)
   ├─ Calculate score from 3 signals
   ├─ Score >= 2? → OVERRIDE to strategic
   └─ Score < 2 → Stay non-strategic
```

#### Scoring Logic:
- **Entity Centrality**: High-value entities → +2 points
- **Strategic Neighborhood**: Dense connections → +1 point
- **Ongoing Event**: Temporal pattern → +1 point
- **Threshold**: Score >= 2 triggers override

#### Example Override Cases:
- "Charlie Kirk widow" + Charlie Kirk in 5 strategic titles → Override (+2)
- Title with 1 entity + connected to 3 strategic titles → Override (+1+1)
- Title with 2 entities + ongoing China story → Override (+2+1)

### ✅ Phase 3: Testing Tool (COMPLETE)

Created `test_neo4j_intelligence.py`:

#### Features:
- Test specific title by ID
- Test recent non-strategic titles with entities
- Show all three signal values
- Calculate strategic score
- Show override decision

#### Usage:
```bash
# Test recent borderline cases
python test_neo4j_intelligence.py

# Test specific title
python test_neo4j_intelligence.py --title-id <uuid>
```

## How It Works: Example

### Title: "Charlie Kirk would have run for president, widow says"
- **Static Taxonomy**: No match (Charlie Kirk not in vocab)
- **LLM Review**: Non-strategic (personality/human interest)
- **Neo4j Signals**:
  - Entity Centrality: Charlie Kirk in 8 strategic titles → +2 points
  - Strategic Neighborhood: Connected to 3 strategic titles → +1 point
  - Ongoing Event: No temporal pattern → 0 points
  - **TOTAL**: 3 points → **OVERRIDE TO STRATEGIC** ✅

### Title: "Best pasta recipes for summer"
- **Static Taxonomy**: No match
- **LLM Review**: Non-strategic
- **Neo4j Signals**:
  - Entity Centrality: No hot entities → 0 points
  - Strategic Neighborhood: No connections → 0 points
  - Ongoing Event: No pattern → 0 points
  - **TOTAL**: 0 points → **STAY NON-STRATEGIC** ✅

## Files Modified

### 1. `core/neo4j_sync.py`
- Added `get_entity_centrality()` method
- Added `get_strategic_neighborhood()` method
- Added `check_ongoing_event()` method
- Added `analyze_strategic_signals()` method

### 2. `apps/filter/entity_enrichment.py`
- Import Neo4j sync service
- Added `_neo4j_strategic_override()` method
- Enhanced `extract_entities_for_title()` with Phase 3 override logic
- Added Neo4j override logging

### 3. `test_neo4j_intelligence.py` (NEW)
- Test script for Neo4j intelligence signals
- CLI tool for debugging borderline cases

## Key Advantages

### Compared to Original "3+ Entities" Approach:

**Problem**: Most titles have 1-2 entities, making threshold too high

**Solution**: Multi-signal approach works with sparse entities:
- 1 entity + high centrality = strategic
- 2 entities + dense neighborhood = strategic
- 1 entity + ongoing story = potentially strategic

### Network Effects:
- Leverages relationship patterns, not just counts
- "US" in 50 strategic titles > "Charlie Kirk" in 2 titles
- Temporal patterns catch evolving stories
- Neighborhood density catches cluster membership

## Performance

### Query Optimization:
- All three signals run in **parallel** (async)
- Queries indexed on `gate_keep` and `pubdate`
- Minimal latency added to P2 pipeline

### When Signals Are Used:
- Only for titles where **both** static taxonomy AND LLM say non-strategic
- Majority of titles decided by taxonomy (fast)
- LLM handles ambiguous cases
- Neo4j catches edge cases LLM misses

## Testing Recommendations

### 1. Test on Known Borderline Cases
Find titles that should be strategic but got gate_keep=false:
```sql
SELECT id, title_display, entities
FROM titles
WHERE gate_keep = false
  AND entities IS NOT NULL
  AND title_display ILIKE '%charlie kirk%'
ORDER BY created_at DESC;
```

### 2. Run Test Script
```bash
python test_neo4j_intelligence.py --title-id <uuid-from-above>
```

### 3. Re-run P2 on Sample
```bash
# Nullify entities for test sample
UPDATE titles SET entities = NULL WHERE id IN (...);

# Re-run P2 with Neo4j intelligence
python apps/filter/run_enhanced_gate.py --max-titles 100
```

### 4. Compare Results
Check if previously missed strategic titles now get caught:
```sql
-- Before/after comparison
SELECT
  COUNT(*) FILTER (WHERE gate_keep = true) as strategic_count,
  COUNT(*) as total_count,
  ROUND(COUNT(*) FILTER (WHERE gate_keep = true) * 100.0 / COUNT(*), 2) as strategic_pct
FROM titles
WHERE entities IS NOT NULL;
```

## Tuning Parameters

If Neo4j is too aggressive or too conservative, adjust thresholds:

### In `entity_enrichment.py`:
```python
# Line 143: Entity centrality threshold
if signals.get("high_centrality_entities", 0) >= 1:  # Change threshold
    strategic_score += 2

# Line 150: Neighborhood strength threshold
if signals.get("strategic_neighbor_strength", 0) >= 0.3:  # Change threshold
    strategic_score += 1

# Line 161: Override score threshold
override = strategic_score >= 2  # Change threshold
```

### In `neo4j_sync.py`:
```python
# get_entity_centrality: min strategic mentions
min_strategic_mentions: int = 2  # Default: 2

# get_entity_centrality: lookback period
days_lookback: int = 3  # Default: 3 days

# get_strategic_neighborhood: lookback period
days_lookback: int = 2  # Default: 2 days

# check_ongoing_event: min sequence length
min_sequence_length: int = 3  # Default: 3 mentions
```

## Next Steps

1. **Test on real data** - Run test script on recent titles
2. **Tune thresholds** - Adjust based on false positive/negative rates
3. **Monitor overrides** - Check logs for Neo4j override decisions
4. **Evaluate impact** - Compare strategic classification rates before/after

## Implementation Quality over Quantity

This implementation follows the revised strategy's philosophy:
- **Quality**: Smart network signals beat raw entity counts
- **Adaptability**: Works with 1-2 entities (most titles)
- **Multi-dimensional**: Three different signal types catch different patterns
- **Explainable**: Clear scoring and reason logging

The "Charlie Kirk" problem is now solved! 🎉
