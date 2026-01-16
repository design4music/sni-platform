# EF Generation v2 - Implementation Plan

**Date**: 2025-10-21
**Based on**: docs/tickets/ef_generation_v.2.txt

---

## Executive Summary

**Goal**: Make Event Family generation more deterministic, data-driven, and scalable by:
1. Using entity frequencies (from P2 enrichment) for theater assignment
2. Adding semantic anchor (`strategic_purpose`) for thematic coherence
3. Introducing micro-prompt validation (P3.5) for incremental title assignment

**Key Insight**: Separate mechanical clustering (fast, deterministic) from thematic validation (AI-powered, precise).

---

## Review & Commentary

### ✓ Strengths

1. **Leverages Recent P2 Work**
   - Entity enrichment (name_en format + country auto-add) provides rich data
   - 521 entities with countries → reliable theater inference
   - No longer dependent on LLM guessing from rigid theater list

2. **Reduces LLM Burden**
   - Current: LLM picks theater from 16-option list (error-prone)
   - Proposed: Mechanical frequency analysis (deterministic)
   - Micro-prompts (YES/NO) much cheaper than full analysis

3. **Semantic Anchor: `strategic_purpose`**
   - One-sentence core narrative provides clear matching criteria
   - Example: "Russia's military operations in Ukraine" vs "US sanctions on Russia"
   - Enables precise micro-prompt questions

4. **Scalability**
   - P3.5 micro-prompts can process incoming titles continuously
   - Pre-filtering by event_type reduces LLM calls
   - Deterministic theater assignment scales linearly

5. **Aligns with Neo4j Vision**
   - Entity frequency analysis = graph traversal
   - Can incorporate entity centrality scores
   - Can use temporal patterns for validation

### ⚠ Challenges & Considerations

1. **Multi-Theater Scenarios**
   - "Biden meets Xi Jinping" → US + China (which is primary?)
   - "NATO discusses Ukraine" → NATO + Ukraine (organization vs country?)
   - **Solution**: Need theater priority rules or multi-theater support

2. **Entity Quality**
   - Relies on P2 entity extraction quality
   - Ambiguous titles may have incomplete entities
   - **Solution**: Use Neo4j network context to fill gaps

3. **Strategic Purpose Generation**
   - LLM must generate clear, distinguishable purposes
   - Too broad: "Conflict in Middle East" (too many EFs match)
   - Too specific: "Biden sanctions Russia on Oct 15" (won't match future titles)
   - **Solution**: Need prompt engineering + examples

4. **P3.5 Queue Management**
   - Risk of titles never finding home (all NO answers)
   - Need retry logic or fallback to create new EF
   - **Solution**: After N rejections, trigger new P3 batch

5. **EF Splitting**
   - Document mentions "potentially splitting" but doesn't detail
   - What triggers split? How to migrate titles?
   - **Solution**: Phase 2 enhancement (not MVP)

---

## Implementation Plan

### Phase 1: Enhanced EF Seed Creation (P3 Modification)

**Goal**: Add dynamic theater assignment and strategic_purpose generation

#### 1.1 Database Changes

```sql
-- Add strategic_purpose column to event_families
ALTER TABLE event_families
ADD COLUMN strategic_purpose TEXT;

-- Add index for P3.5 queries
CREATE INDEX idx_ef_event_type_status
ON event_families(event_type, status)
WHERE status IN ('seed', 'active');
```

#### 1.2 Theater Assignment Module

**File**: `apps/generate/theater_inference.py`

```python
def infer_theater_from_entities(
    entities: List[str],
    entity_enricher: CountryEnricher
) -> Tuple[str, float]:
    """
    Determine primary theater from entity frequency analysis.

    Args:
        entities: List of all entities from titles in cluster
        entity_enricher: For country lookups

    Returns:
        (theater_name, confidence_score)

    Logic:
    1. Filter for country entities (via data_entities.entity_type)
    2. Count frequency of each country
    3. Apply priority rules:
       - Single dominant country (>60%) → that country
       - US + adversary (RU/CN/IR) → "US-[adversary] Relations"
       - Multiple regions → most frequent region
       - Tie → alphabetical (deterministic)
    4. Return theater + confidence score
    """
```

**Theater Priority Rules**:
- Single country dominant (>60% of entities) → that country
- US + Russia → "US-Russia Relations"
- US + China → "US-China Relations"
- Multiple EU countries → "Europe"
- Multiple Middle East → "Middle East"
- NATO + country → that country (NATO not a theater)
- Tie-breaker → alphabetical order (deterministic)

#### 1.3 Enhanced LLM Prompt

**File**: `apps/generate/incident_processor.py` (modify)

```python
ENHANCED_EF_GENERATION_PROMPT = """
Analyze this cluster of news headlines and generate Event Family metadata.

Headlines:
{headlines}

Entities detected: {entities}
Event type: Must choose from: {event_type_list}

Generate:
1. title: Concise 5-10 word title for this story
2. summary: 2-3 sentence summary capturing key facts
3. event_type: Choose ONE from the list above
4. strategic_purpose: ONE sentence core narrative (the "why this matters")

Strategic Purpose Guidelines:
- Focus on the underlying dynamic, not just the event
- Good: "Russia's military pressure on Ukraine's eastern front"
- Bad: "Russia attacks Ukraine" (too generic)
- Good: "US efforts to contain Chinese tech dominance"
- Bad: "US-China tensions" (too vague)

Output valid JSON only:
{
  "title": "...",
  "summary": "...",
  "event_type": "...",
  "strategic_purpose": "..."
}
"""
```

**Note**: Removed primary_theater from LLM prompt entirely.

#### 1.4 Modified P3 Flow

```python
# apps/generate/incident_processor.py

async def create_ef_from_cluster(cluster_titles: List[Title]) -> EventFamily:
    """
    Enhanced P3 flow with dynamic theater assignment.
    """
    # 1. Mechanical bucketing (existing)
    # ... cosine similarity clustering ...

    # 2. Collect all entities from cluster
    all_entities = []
    for title in cluster_titles:
        all_entities.extend(title.entities or [])

    # 3. LLM analysis (ENHANCED: adds strategic_purpose, removes theater)
    llm_result = await llm_client.generate_ef_metadata(
        titles=cluster_titles,
        entities=all_entities
    )

    # 4. DYNAMIC THEATER ASSIGNMENT (NEW)
    from apps.generate.theater_inference import infer_theater_from_entities
    primary_theater, theater_confidence = infer_theater_from_entities(
        entities=all_entities,
        entity_enricher=get_country_enricher()
    )

    # 5. Generate ef_key (using inferred theater)
    ef_key = generate_ef_key(
        actors=[],  # Still ignored
        primary_theater=primary_theater,
        event_type=llm_result["event_type"]
    )

    # 6. Create/merge EF (existing logic)
    ef = upsert_event_family(
        title=llm_result["title"],
        summary=llm_result["summary"],
        event_type=llm_result["event_type"],
        primary_theater=primary_theater,
        strategic_purpose=llm_result["strategic_purpose"],  # NEW
        ef_key=ef_key,
        source_title_ids=[t.id for t in cluster_titles]
    )

    return ef
```

---

### Phase 2: Thematic Validation (New P3.5 Process)

**Goal**: Continuous micro-prompt validation for incoming titles

#### 2.1 Micro-Prompt Design

**File**: `apps/generate/thematic_validator.py`

```python
THEMATIC_VALIDATION_PROMPT = """
Does this headline fit the following story's core narrative?

Story: {ef_title}
Core Narrative: {ef_strategic_purpose}
Event Type: {ef_event_type}

Headline: {title_display}
Detected Entities: {entities}

Answer YES or NO only.

Guidelines:
- YES if headline advances/relates to the same underlying dynamic
- NO if headline is about a different story, even if same entities
- Focus on strategic purpose alignment, not just entity overlap

Examples:
Story: "Russia's military pressure on Ukraine"
- "Russian forces advance near Bakhmut" → YES
- "Putin meets with Chinese leader" → NO (different story)

Your answer (YES or NO):
"""
```

#### 2.2 P3.5 Worker Implementation

**File**: `apps/generate/p3_5_continuous_processor.py`

```python
class ThematicValidationProcessor:
    """
    P3.5: Continuous thematic validation for incoming titles.
    Runs as background worker or cron job.
    """

    async def process_batch(self, batch_size: int = 50):
        """
        Process batch of unassigned strategic titles.

        Logic:
        1. Get titles (gate_keep=true, event_family_id IS NULL)
        2. For each title:
           a. Pre-filter: Get candidate EFs (same event_type)
           b. Micro-prompt: Ask if title fits each EF's strategic_purpose
           c. Route: Assign to first YES, or leave for P3 if all NO
        """

        # 1. Get unassigned strategic titles
        unassigned = get_unassigned_titles(limit=batch_size)

        for title in unassigned:
            # 2. Pre-filter by event_type
            candidates = get_candidate_efs(
                event_type=infer_event_type(title),  # Heuristic or micro-prompt
                max_age_days=30  # Only recent EFs
            )

            # 3. Micro-prompt validation
            matched_ef = None
            for ef in candidates:
                result = await llm_client.validate_thematic_fit(
                    title=title,
                    ef=ef
                )

                if result == "YES":
                    matched_ef = ef
                    break  # Stop at first match

            # 4. Route decision
            if matched_ef:
                assign_title_to_ef(title.id, matched_ef.id)
                logger.info(f"P3.5: Assigned '{title.title_display}' to EF '{matched_ef.title}'")
            else:
                # Leave for next P3 batch
                logger.debug(f"P3.5: No match for '{title.title_display}', will create new EF")
```

#### 2.3 Event Type Inference

**Challenge**: Need to pre-filter by event_type, but title doesn't have it yet.

**Options**:
1. **Heuristic**: Simple keyword matching to guess event_type
2. **Micro-Prompt**: Quick LLM call to classify event_type
3. **Skip Pre-Filter**: Check all active EFs (expensive)

**Recommended**: Heuristic first (fast), fallback to micro-prompt if needed.

```python
def infer_event_type_heuristic(title: Title) -> Optional[str]:
    """
    Quick heuristic to guess event_type from title text and entities.

    Keywords:
    - "sanctions", "embargo" → Economic
    - "meeting", "summit", "talks" → Diplomacy
    - "attack", "strike", "military" → Military
    - "election", "vote", "parliament" → Politics
    - etc.
    """
```

---

### Phase 3: Neo4j Integration (Future Enhancement)

**Goal**: Use graph intelligence to improve theater and validation decisions

#### 3.1 Entity Centrality for Theater

```python
# In theater_inference.py

def infer_theater_with_neo4j(
    entities: List[str],
    neo4j_sync: Neo4jSync
) -> Tuple[str, float]:
    """
    Enhanced theater inference using entity centrality.

    Logic:
    1. Get entity frequency (baseline)
    2. Query Neo4j for entity centrality scores
    3. Weight frequency by centrality (hot entities boost theater score)
    4. Apply priority rules with weighted scores
    """

    # Get baseline frequencies
    freq = Counter(entities)

    # Enhance with Neo4j centrality
    for entity in entities:
        centrality = neo4j_sync.get_entity_centrality(entity)
        freq[entity] *= (1 + centrality)  # Boost by centrality

    # Continue with priority rules...
```

#### 3.2 Network Context for Validation

```python
# In thematic_validator.py

async def validate_with_network_context(
    title: Title,
    ef: EventFamily,
    neo4j_sync: Neo4jSync
) -> str:
    """
    Enhanced validation using entity network patterns.

    Signals:
    - Title shares entities with EF members → likely fit
    - Title entities are 1-hop away from EF entities → possible fit
    - Title entities disconnected → likely different story
    """

    # Get network similarity
    network_score = neo4j_sync.compute_network_similarity(
        title_entities=title.entities,
        ef_entities=extract_ef_entities(ef)
    )

    # Use network score to bias micro-prompt or skip it
    if network_score > 0.8:
        return "YES"  # High confidence, skip LLM
    elif network_score < 0.2:
        return "NO"   # Low confidence, skip LLM
    else:
        # Medium confidence, ask LLM
        return await llm_client.validate_thematic_fit(title, ef)
```

---

## Data Flow Diagrams

### Current P3 Flow
```
Titles (gate_keep=true)
  → Cosine Clustering
  → LLM (title, summary, event_type, theater←RIGID LIST)
  → Generate ef_key(theater + type)
  → Create/Merge EF
```

### Proposed P3 Flow (Enhanced)
```
Titles (gate_keep=true)
  → Cosine Clustering
  → Collect Entities from Cluster
  → LLM (title, summary, event_type, strategic_purpose) ← NO THEATER
  → THEATER INFERENCE (frequency analysis + priority rules)
  → Generate ef_key(inferred_theater + type)
  → Create/Merge EF with strategic_purpose
```

### New P3.5 Flow (Continuous)
```
Unassigned Titles (gate_keep=true, ef_id IS NULL)
  → Infer event_type (heuristic)
  → Pre-filter: Get candidate EFs (same event_type, active, recent)
  → For each candidate:
      → Micro-Prompt: "Does headline fit strategic_purpose?"
      → If YES → Assign to EF, STOP
  → If all NO → Leave for next P3 batch
```

---

## Implementation Checklist

### Phase 1: Enhanced P3 (Core)
- [ ] Database migration: Add `strategic_purpose` column
- [ ] Create `theater_inference.py` module
  - [ ] `infer_theater_from_entities()` function
  - [ ] Theater priority rules (US+adversary, regions, etc.)
  - [ ] Unit tests with edge cases
- [ ] Update LLM prompt in `incident_processor.py`
  - [ ] Add `strategic_purpose` field
  - [ ] Remove `primary_theater` selection
  - [ ] Add strategic purpose guidelines
- [ ] Modify `create_ef_from_cluster()` flow
  - [ ] Call theater inference before ef_key generation
  - [ ] Store strategic_purpose in EF
- [ ] Test with historical data
  - [ ] Verify theater assignment quality
  - [ ] Validate strategic_purpose clarity

### Phase 2: P3.5 Continuous Validation
- [ ] Create `thematic_validator.py` module
  - [ ] Micro-prompt design
  - [ ] YES/NO parsing logic
- [ ] Create `p3_5_continuous_processor.py` worker
  - [ ] Queue management (get unassigned titles)
  - [ ] Event type inference heuristic
  - [ ] Pre-filtering by event_type
  - [ ] Micro-prompt validation loop
  - [ ] Title assignment logic
- [ ] Add cron job or background worker
  - [ ] Run every 5-10 minutes
  - [ ] Process batches of 50 titles
  - [ ] Track success/failure metrics
- [ ] Monitoring & metrics
  - [ ] P3.5 assignment rate
  - [ ] Micro-prompt accuracy
  - [ ] Titles left for P3

### Phase 3: Neo4j Enhancement (Future)
- [ ] Integrate entity centrality into theater inference
- [ ] Add network similarity scoring
- [ ] Use network context to skip/bias micro-prompts
- [ ] Track Neo4j signal effectiveness

---

## Success Metrics

### P3 Enhanced Seed Creation
- **Theater Assignment Accuracy**: >90% (manual review of 100 EFs)
- **Strategic Purpose Clarity**: Can distinguish between EFs (manual review)
- **EF Fragmentation**: Reduced merge rate (fewer duplicate EFs)

### P3.5 Thematic Validation
- **Assignment Rate**: >70% of titles assigned to existing EFs
- **Micro-Prompt Accuracy**: >85% (manual review)
- **Processing Speed**: <30 seconds per batch of 50 titles
- **EF Growth Rate**: Existing EFs grow over time (not just new EFs)

### System Health
- **LLM Cost Reduction**: Fewer full EF generation calls
- **Determinism**: Same titles → same theater (reproducible)
- **Scalability**: Linear processing time as EFs grow

---

## Risk Mitigation

### Risk: Theater inference fails for ambiguous clusters
**Mitigation**:
- Fallback to LLM theater selection if confidence < threshold
- Log ambiguous cases for manual review
- Improve priority rules iteratively

### Risk: Strategic purpose too broad/narrow
**Mitigation**:
- Provide examples in prompt
- A/B test different phrasings
- Manual review of first 50 EFs

### Risk: P3.5 creates orphaned titles (all NO)
**Mitigation**:
- After 3 rejections, trigger immediate P3 batch
- Track orphan rate as key metric
- Adjust pre-filtering criteria

### Risk: Micro-prompts too expensive at scale
**Mitigation**:
- Pre-filter aggressively (event_type + age)
- Use Neo4j to skip obvious YES/NO cases
- Batch micro-prompts to same EF

---

## Recommendations

### Start with Phase 1 (Enhanced P3)
- Immediate value: Better theater assignment
- Low risk: Still creates EFs deterministically
- Enables Phase 2 (needs strategic_purpose)

### Validate Before Phase 2 (P3.5)
- Test Phase 1 with 100-200 titles
- Verify theater quality and strategic_purpose clarity
- Ensure ef_key collisions are intentional (same story)

### Phase 3 (Neo4j) is Optional
- Only if Phase 2 shows bottlenecks
- Neo4j can optimize, but not required
- Focus on data-driven decisions first

### Quick Wins
1. **Theater inference from entities** - Use P2 enrichment work immediately
2. **Strategic purpose** - Simple prompt addition, high value
3. **Micro-prompts** - Cheaper than full analysis, scalable

---

## Open Questions for Discussion

1. **Theater Granularity**: Use countries (Russia, Ukraine) or regions (Eastern Europe)?
2. **Multi-Theater Support**: Should EFs have multiple theaters or always pick one?
3. **Event Type Pre-Filter**: Heuristic sufficient or need micro-prompt?
4. **P3.5 Frequency**: How often to run? Real-time or batched?
5. **EF Splitting**: Include in MVP or defer to Phase 2?
6. **Historical Migration**: Re-process existing EFs with new logic?

---

## Conclusion

This proposal is **well-designed and aligns perfectly** with our recent P2 improvements:
- Leverages entity enrichment (name_en + country auto-add)
- Reduces LLM guesswork (mechanical theater assignment)
- Introduces semantic anchor (strategic_purpose)
- Enables continuous validation (micro-prompts)

**Recommendation**: Proceed with Phase 1 (Enhanced P3) immediately. Phase 2 (P3.5) after validating Phase 1 quality.

**Estimated Effort**:
- Phase 1: 2-3 days (theater inference + prompt updates + testing)
- Phase 2: 3-4 days (P3.5 worker + micro-prompts + monitoring)
- Phase 3: 1-2 days (Neo4j integration)

**Total: 6-9 days** for complete v2 implementation.
