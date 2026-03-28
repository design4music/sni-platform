# Merge Plan for Faceted Clustering

**Date**: 2026-03-28
**Status**: Research complete, implementation pending
**Depends on**: Faceted clustering (prototype working, France + USA written to DB)

---

## Current State

Faceted clustering produces clean, coherent events but many small fragments:

| Centroid | Emerged | 2-3 sources | 4-5 | 6-10 | 11-20 | 21-50 | 50+ |
|----------|---------|-------------|-----|------|-------|-------|-----|
| USA security | 1,148 | 746 (65%) | 181 | 127 | 57 | 35 | 2 |

65% of events have only 2-3 sources. Many are fragments of the same story that landed in different anchor groups (e.g., NAVAL/HORMUZ and NAVAL/same-story-different-anchor).

---

## Problem: Naive Merge Produces 59K False Candidates

Merging on "shared signals + date overlap" produces 59,203 candidates for USA security alone. Reason: ubiquitous signals (TRUMP, IR, US) connect everything during the Iran war.

**Example false merge**: "Hormuz naval operations" + "Iranian school struck" share TRUMP + IR but are completely different stories.

---

## Merge Criteria (Refined)

### Mechanical Merge (cheap, fast)

Two events are merge candidates if ALL of:

1. **Same subject** (NAVAL+NAVAL, not NAVAL+AERIAL). Cross-subject merges are rare and dangerous.
2. **Shared specific signals** (not ubiquitous):
   - At least 1 shared PLC: (place) or EVT: (named event), OR
   - At least 1 shared PER: (person) that is NOT in the centroid's ubiquitous set
   - TGT: alone is not sufficient (too generic)
   - ORG: alone is not sufficient (PENTAGON, NATO too common)
3. **Tight temporal window**: events must overlap or be within 1 day of each other
4. **Ubiquitous exclusion**: same dynamic filtering as clustering (>10% of centroid = excluded from merge matching)

### LLM Merge (for stubborn cases)

After mechanical merge, remaining events >50 titles or candidate pairs that share subject + date but no specific signals could be sent to LLM:
- "Are these two events the same story? YES/NO"
- Pre-filtered candidates only (same subject + date overlap)
- One LLM call per candidate pair

### Title-Based Merge (alternative, requires Phase 4.5a first)

Generate LLM titles first, then merge events whose titles are paraphrases:
- Advantage: titles are a human-readable summary of the event, comparison is meaningful
- Disadvantage: requires generating titles for all events first (LLM cost)
- Could work as a secondary pass after mechanical + LLM merge

---

## Merge Order Options

**Option A: Merge first, then generate prose**
- Mechanical merge on signals + subject + date
- LLM merge on remaining candidates
- Then generate titles + summaries for merged events
- Pro: fewer events to generate prose for (cheaper)
- Con: merge quality unknown until we see results

**Option B: Generate titles first, then merge on titles**
- Generate short titles (Phase 4.5a, title-only tier)
- Merge events with similar titles (Dice/overlap)
- Then generate full summaries for merged events
- Pro: titles are a natural comparison surface
- Con: double LLM cost (titles before and possibly after merge)

**Option C: Hybrid**
- Mechanical merge first (cheap, safe)
- Generate titles for remaining events
- Title-based merge as cleanup pass
- Generate summaries last
- Best quality, moderate cost

---

## Implementation Plan

### Step 1: Mechanical merge in prototype_faceted.py

Add after faceted clustering, before DB write:
- Build event profiles (subject, signals, date range)
- Compute ubiquitous signals per centroid (same as clustering)
- Find candidates: same subject + shared specific signal + date overlap
- Merge smaller into larger (union of title indices)

### Step 2: Test and review

- Run on France + USA
- Review merge results on frontend
- Tune thresholds if needed

### Step 3: LLM merge (if needed)

- For remaining large events or close candidates
- Reuse existing `_llm_merge_clusters()` logic from rebuild_centroid.py

---

## UI Considerations (Separate from Merge)

With 1,000+ topics per CTM track, users need filtering. Ideas:
- Filter by signal (show only topics mentioning "Hormuz" or "IRGC")
- Filter by date range
- Group by subject (accordion: NAVAL, AERIAL, MISSILE, etc.)
- Search within CTM page

These are frontend features, independent of merge logic.

---

## Next Session Checklist

1. Implement mechanical merge in prototype (Step 1)
2. Run on France + USA, review
3. Decide on LLM merge approach
4. Once merge is stable, run all 75 centroids
5. Generate LLM prose (Phase 4.5a + 4.5b)
6. Push to Render
