# Phase 4 Technical Summary

**Purpose**: Two-stage LLM enrichment process that transforms raw title feeds into strategic intelligence narratives

**Status**: NOT YET RUN - Schema incompatibility issue identified (see Critical Issues section)

---

## Architecture Overview

Phase 4 operates on **Centroid-Track-Month (CTM)** units created by Phase 3, enriching them through two sequential stages:

```
Phase 4.1: Events Digest Generation
  Input:  CTM with N titles (chronologically ordered)
  Output: JSON array of distinct events with dates and sources

Phase 4.2: Summary Generation
  Input:  Events digest from Phase 4.1
  Output: 150-250 word narrative summary
```

### Why Two Stages?

1. **Deduplication First**: Phase 4.1 collapses near-duplicate reports into distinct events
2. **Structured Intermediary**: Events digest provides auditable, structured data
3. **Reusability**: Events digest can be used for other outputs (alerts, charts, etc.)
4. **LLM Efficiency**: Summaries work from clean event timeline, not raw title noise

---

## Phase 4.1: Events Digest Generation

**File**: `v3/phase_4/generate_events_digest.py`

### Queue Selection Logic

```sql
SELECT c.id, c.centroid_id, c.track, c.month, c.title_count, cent.label
FROM ctm c
JOIN centroids_v3 cent ON c.centroid_id = cent.id
WHERE c.title_count > 0
  AND (c.events_digest = '[]'::jsonb OR c.events_digest IS NULL)
  AND c.is_frozen = false
ORDER BY c.title_count DESC, c.month DESC
```

**Selection Criteria**:
- CTM has titles (title_count > 0)
- No events digest yet (NULL or empty array)
- Not frozen (allows reprocessing)

**Processing Order**:
- Higher title counts first (more signal)
- More recent months first (DESC)

### Title Retrieval and Formatting

**Current Code** (lines 196-205):
```python
cur.execute("""
    SELECT id, title_display, pubdate_utc
    FROM titles_v3
    WHERE %s = ANY(ctm_ids)
    ORDER BY pubdate_utc ASC
""", (ctm_id,))
```

**CRITICAL ISSUE**: Uses removed `titles_v3.ctm_ids` column (see Critical Issues section)

**Title Formatting for LLM**:
```
[0] 2024-12-15: First title text here
[1] 2024-12-16: Second title text here
[2] 2024-12-17: Third title text here
```

- Numbered indices for LLM reference
- Date prefix for temporal context
- Chronological order (ASC by pubdate_utc)

### LLM Prompt Design

**System Prompt** (lines 64-84):
```
You are analyzing news titles for a specific centroid-track-month combination.
Extract distinct events from these chronologically ordered titles.

Your task:
1. Identify unique developments/events (merge near-duplicate reports)
2. Create 1-2 sentence summaries for each event
3. Link to source title indices
4. Use the most specific date available from source titles

Return ONLY a JSON array, no other text:
[{
  "date": "YYYY-MM-DD",
  "summary": "1-2 sentence event description",
  "source_title_indices": [0, 1, 2]
}]
```

**Key Design Decisions**:
- **Deduplication Focus**: "merge near-duplicate reports" - core value-add
- **Structured Output**: JSON-only response for reliable parsing
- **Date Extraction**: LLM extracts most specific date from title text
- **Source Tracking**: Indices maintain traceability to original titles

**User Prompt**:
```
Centroid: {centroid_label}
Track: {track}
Month: {month}

Titles:
{titles_text}
```

### LLM Parameters

```python
temperature=0.3      # Low for consistency
max_tokens=2000      # Enough for ~20-30 events
timeout=120s         # From config
```

### Response Processing

**Markdown Stripping** (lines 126-130):
- Handles LLM wrapping JSON in ```json code fences
- Strips to raw JSON for parsing

**Index-to-UUID Conversion** (lines 135-146):
```python
enriched_events = []
for event in events:
    title_ids = [str(titles[idx][0]) for idx in event["source_title_indices"]]
    enriched_events.append({
        "date": event["date"],
        "summary": event["summary"],
        "source_title_ids": title_ids,  # UUIDs, not indices
    })
```

**Database Update**:
```python
cur.execute("""
    UPDATE ctm
    SET events_digest = %s,
        processing_status = 'digest_complete',
        digest_generated_at = NOW()
    WHERE id = %s
""", (Json(enriched_events), ctm_id))
```

---

## Phase 4.2: Summary Generation

**File**: `v3/phase_4/generate_summaries.py`

### Queue Selection Logic

```sql
SELECT c.id, c.centroid_id, c.track, c.month,
       c.events_digest, c.title_count,
       cent.label, cent.class, cent.primary_theater
FROM ctm c
JOIN centroids_v3 cent ON c.centroid_id = cent.id
WHERE c.events_digest IS NOT NULL
  AND jsonb_array_length(c.events_digest) > 0
  AND c.summary_text IS NULL
  AND c.is_frozen = false
  AND c.title_count >= %s  -- v3_p4_min_titles threshold
ORDER BY c.title_count DESC, c.month DESC
```

**Selection Criteria**:
- Has non-empty events digest (Phase 4.1 complete)
- No summary yet (summary_text IS NULL)
- Meets minimum title threshold (default: 3)
- Not frozen

### Context Building

**Events Timeline Formatting**:
```
• 2024-12-15: First event summary here
• 2024-12-16: Second event summary here
• 2024-12-17: Third event summary here
```

**Centroid Context**:
```python
context_parts = [f"Centroid: {centroid_label} ({centroid_class})"]
if primary_theater:
    context_parts.append(f"Theater: {primary_theater}")
context_parts.append(f"Track: {track}")
context_parts.append(f"Month: {month}")
```

### LLM Prompt Design

**System Prompt** (lines 60-77):
```
You are a strategic intelligence analyst writing monthly summary reports.
Generate a cohesive 150-250 word narrative from the provided events timeline.

Requirements:
- Flow chronologically
- Highlight key developments
- Connect related events
- Provide context for significance
- Maintain journalistic tone
- Focus on strategic implications
- Use present/past tense appropriately
- Write as a single flowing paragraph or 2-3 short paragraphs

Do NOT:
- List events as bullet points
- Include dates in parentheses unless critical
- Use sensational language
- Add speculation beyond events
```

**Key Design Decisions**:
- **Narrative Flow**: Not a list, but connected prose
- **Strategic Focus**: "significance" and "strategic implications"
- **Word Count**: 150-250 words (controlled via max_tokens)
- **Journalistic Tone**: Professional, not sensational
- **Date Handling**: Chronological flow without date clutter

**User Prompt**:
```
{context}

Events timeline:
{events_text}

Generate summary:
```

### LLM Parameters

```python
temperature=config.v3_p4_temperature  # Default: 0.5 (more creative than 4.1)
max_tokens=config.v3_p4_max_tokens    # Default: 500
timeout=config.v3_p4_timeout_seconds  # Default: 120s
```

### Database Update

```python
cur.execute("""
    UPDATE ctm
    SET summary_text = %s,
        processing_status = 'complete',
        summary_generated_at = NOW()
    WHERE id = %s
""", (summary_text, ctm_id))
```

---

## Configuration Parameters

**File**: `core/config.py`

```python
v3_p4_min_titles: int = 3          # Skip CTMs with < 3 titles
v3_p4_temperature: float = 0.5     # Summary creativity (vs 0.3 for events)
v3_p4_max_tokens: int = 500        # ~200-250 words
v3_p4_timeout_seconds: int = 120   # LLM timeout
```

**Rationale**:
- `min_titles=3`: Low-volume CTMs likely noise, not worth enrichment cost
- `temperature=0.5`: Higher than Phase 4.1 (0.3) for more natural prose
- `max_tokens=500`: Controls summary length to 150-250 word target

---

## Critical Issues

### BLOCKER: Schema Incompatibility with Phase 3

**Location**: `generate_events_digest.py:200`

**Current Code**:
```python
cur.execute("""
    SELECT id, title_display, pubdate_utc
    FROM titles_v3
    WHERE %s = ANY(ctm_ids)
    ORDER BY pubdate_utc ASC
""", (ctm_id,))
```

**Problem**: Phase 3 refactoring removed `titles_v3.ctm_ids` column in favor of `title_assignments` junction table

**Impact**: Phase 4.1 will FAIL immediately when attempting to retrieve titles

**Required Fix**:
```python
cur.execute("""
    SELECT t.id, t.title_display, t.pubdate_utc
    FROM title_assignments ta
    JOIN titles_v3 t ON ta.title_id = t.id
    WHERE ta.ctm_id = %s
    ORDER BY t.pubdate_utc ASC
""", (ctm_id,))
```

**Status**: MUST FIX before running Phase 4

---

## Optimization Opportunities

### 1. Batch LLM Calls

**Current**: Sequential processing - one CTM at a time
**Opportunity**: Batch multiple CTMs into single LLM call with instruction to return multiple outputs
**Benefit**: 3-5x speedup, lower API costs
**Risk**: More complex parsing, harder error handling

### 2. Event Deduplication Validation

**Current**: Relies on LLM to merge duplicates
**Opportunity**: Post-process events digest to verify deduplication (e.g., cosine similarity check)
**Benefit**: Quality assurance, identify when LLM fails to merge
**Cost**: Additional embedding API calls

### 3. Minimum Title Threshold

**Current**: Fixed at `v3_p4_min_titles=3`
**Opportunity**: Dynamic threshold based on centroid importance or track priority
**Example**: Allow `min_titles=1` for high-priority tracks, `min_titles=5` for noisy ones
**Benefit**: Better resource allocation

### 4. Events Digest Caching

**Current**: Events digest regenerated if CTM reprocessed
**Opportunity**: Version control for events digests (keep history)
**Benefit**: A/B test prompt improvements, audit trail
**Cost**: Storage

### 5. Summary Templates by Track

**Current**: Same prompt template for all tracks
**Opportunity**: Track-specific prompt templates (e.g., military ops vs diplomatic)
**Benefit**: More appropriate tone/focus per domain
**Cost**: Prompt management complexity

### 6. Date Extraction Validation

**Current**: LLM extracts dates with no validation
**Opportunity**: Validate extracted dates are within CTM month
**Benefit**: Catch LLM hallucination
**Example**: Reject dates outside `month ± 5 days`

### 7. Title Filtering by Relevance

**Current**: All titles in CTM sent to Phase 4.1
**Opportunity**: Pre-filter titles by relevance score (if available)
**Benefit**: Reduce noise for LLM, lower token costs
**Risk**: May miss edge-case events

---

## Data Flow Summary

```
Phase 3 Output:
  ctm table with 299 rows (title_count > 0)

  ↓

Phase 4.1 Queue:
  299 CTMs with events_digest = NULL

  ↓ (for each CTM)

Retrieve Titles:
  Query title_assignments → titles_v3
  Order by pubdate_utc ASC

  ↓

LLM Events Extraction:
  Input: Numbered, dated title list
  Output: JSON array of events

  ↓

Store Events Digest:
  UPDATE ctm SET events_digest = [...], processing_status = 'digest_complete'

  ↓

Phase 4.2 Queue:
  CTMs with events_digest != NULL AND summary_text = NULL

  ↓ (for each CTM)

LLM Summary Generation:
  Input: Events timeline + centroid context
  Output: 150-250 word narrative

  ↓

Store Summary:
  UPDATE ctm SET summary_text = '...', processing_status = 'complete'
```

---

## Expected Output

Based on Phase 3 results:
- **299 CTMs** with titles ready for Phase 4.1
- **Est. ~200-250 CTMs** will have summaries after Phase 4.2 (filtering by min_titles)
- **~3,000-5,000 events** extracted across all CTMs (10-20 events per CTM avg)
- **Processing time**: ~1-2 hours total (depending on Deepseek API latency)

---

## Pre-Flight Checklist

- [ ] Fix schema incompatibility in `generate_events_digest.py:200`
- [ ] Verify Deepseek API credentials in config
- [ ] Confirm `v3_p4_min_titles` threshold (currently 3)
- [ ] Review LLM prompts for any domain-specific adjustments
- [ ] Test Phase 4.1 on 1-2 CTMs before full batch
- [ ] Monitor first few outputs for quality

---

## Next Steps

1. **FIX BLOCKER**: Update title retrieval query in Phase 4.1
2. **Verify config**: Check all Phase 4 settings in `core/config.py`
3. **Test run**: Process 5 CTMs through both stages
4. **Quality review**: Manually inspect events digests and summaries
5. **Full run**: Execute on all 299 CTMs
6. **Validation**: Run `db/pipeline_summary.py` to see Phase 4 stats
