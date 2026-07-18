# Epic Narratives Improvement Plan

## Problem 1: TF-IDF Style Source Scoring

### Current State
`top_sources` is raw count of titles per publisher per frame. High-volume publishers (tass.com, Reuters) appear everywhere.

### Solution
Compute **over-index score** for each source in each frame:

```
source_share_in_frame = titles_by_source_in_frame / total_titles_in_frame
source_share_overall = titles_by_source_in_epic / total_titles_in_epic
over_index = source_share_in_frame / source_share_overall
```

- `over_index > 1.0` = source favors this frame more than average
- `over_index = 2.0` = source is 2x more likely to use this frame
- Filter: only show sources with `over_index >= 1.5` AND `count >= 3`

### Implementation
Modify `aggregate_results()` in `extract_epic_narratives.py`:
1. Compute total titles per source across all frames
2. For each frame, compute over-index instead of raw count
3. Store `top_sources` as sources with highest over-index (not raw count)
4. Optionally add `top_sources_scores` field for UI display

---

## Problem 2: Distinct Frames + Clear Separation

### Current State
- "Key Narratives" (from epic enrichment) = topical event summaries
- "Framed Narratives" (from Pass 1/2) = media framing lenses
- Overlap exists (e.g., "Humanitarian Crisis" vs "Humanitarian Pause")

### Solution

#### 2.1 Rename sections
- "Key Narratives" → "What Happened" (event-centric)
- "Framed Narratives" → "How It Was Framed" (perspective-centric)

#### 2.2 Reduce frame count via Pass 1 prompt refinement
Update Pass 1 prompt to:
- Request 4-6 frames (not 3-7)
- Require frames to be **mutually exclusive** in moral stance
- Explicitly forbid structural/analytical frames that all outlets share
- Focus on: who is victim, who is aggressor, who is right/wrong

#### 2.3 Deduplicate via semantic clustering
After Pass 1, before Pass 2:
- Compare frame descriptions pairwise
- Merge frames with >70% semantic overlap
- Keep the one with clearer moral directionality

Alternatively: stricter Pass 1 prompt that enforces distinctiveness upfront.

### Proposed New Pass 1 Prompt

```
Identify 4-6 distinct CONTESTED narrative frames used across these headlines.

Each frame MUST:
1. Represent a clear moral/ideological stance (not a neutral topic)
2. Assign roles: who is victim, aggressor, hero, or villain
3. Be mutually exclusive — a headline fitting Frame A should NOT fit Frame B
4. Cleanly separate outlets that disagree

BAD frames (reject these):
- "Geopolitical developments" — too neutral, everyone uses it
- "Humanitarian concerns" — too broad, doesn't assign blame
- "Diplomatic efforts" — describes topic, not stance

GOOD frames (aim for these):
- "Russian imperial aggression" — Russia = aggressor, Ukraine = victim
- "NATO provocation" — West = aggressor, Russia = defender
- "Trump's diplomatic triumph" — Trump = hero, peacemaker
- "Performative gestures" — skeptical, no one is hero

Return 4-6 frames. Each must be contestable — outlets should disagree.
```

---

## Problem 3: Elevate Strongly Distinct Frames

### Current State
All frames shown equally. A frame with 92 titles gets same visual weight as one with 438.

### Solution
Compute **distinctiveness score** per frame:
- How much do source distributions differ from the epic average?
- Frames where tass.com dominates vs Kyiv Post dominates = high distinctiveness
- Frames where all sources are equally present = low distinctiveness (drop or de-emphasize)

### Distinctiveness Metric
```
For each frame:
  source_distribution = {source: count/total for source in frame}
  epic_distribution = {source: count/total for source in epic}
  distinctiveness = KL_divergence(source_distribution, epic_distribution)
```

High KL divergence = frame has a unique source profile = worth highlighting.
Low KL divergence = frame looks like the average = consider dropping.

### Implementation
1. Compute distinctiveness score in `aggregate_results()`
2. Store in new column `distinctiveness_score FLOAT`
3. Filter: only keep frames with `distinctiveness_score >= threshold`
4. Or: sort by distinctiveness, show top 4

---

## Implementation Order

### Phase A: Fix Source Scoring (Problem 1)
1. Modify `aggregate_results()` to compute over-index scores
2. Update `top_sources` to use over-index ranking
3. Re-run on Ukraine epic
4. Verify: tass.com should only appear where it genuinely over-indexes

### Phase B: Improve Frame Quality (Problem 2)
1. Update Pass 1 prompt for stricter contested frames
2. Reduce target to 4-6 frames
3. Re-run on Ukraine epic
4. Review: frames should be mutually exclusive, assign clear roles

### Phase C: Add Distinctiveness Filtering (Problem 3)
1. Add distinctiveness score computation
2. Filter out low-distinctiveness frames
3. Re-run on Ukraine epic
4. Review: remaining frames should have clear source separation

### Phase D: Frontend Updates (after data is right)
- Rename sections
- Show fewer cards with expansion
- Emphasize source badges
- Add distinctiveness indicator

---

## Verification Criteria (per epic)

After each run, check:
1. **No source appears in >3 frames' top_sources** (unless genuinely dominant)
2. **Each frame has distinct top sources** — if Frame A and Frame B have same top 3 sources, one should be merged/dropped
3. **Frames are morally directional** — can answer "who is the good guy here?"
4. **4-5 frames max** — cognitive load limit

---

## Ready to Implement

Start with Phase A (TF-IDF source scoring) on Ukraine epic?
