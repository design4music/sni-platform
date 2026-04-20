# Faceted Clustering Analysis

**Date**: 2026-03-28
**Branch**: `feat/sector-clustering`
**Context**: Replacing Louvain graph clustering with mechanical faceted approach after quality issues at scale.

---

## Problem Statement

Louvain community detection produces clean clusters at small scale (France 1,104 titles) but degrades at volume (USA 27K titles):

- **False connections**: PER:MACRON connects unrelated stories (Iraq soldier + Congo UNICEF) because Macron commented on both
- **Generic signal pollution**: ACT:FR_LAW_ENFORCEMENT merges Strava leak + schoolchildren assault + prison escape into one cluster
- **Tweaking trap**: each fix (actor labels, coherence gate, temporal window, pass-2 rescue) solves one case but creates new problems elsewhere

Catchall rates with Louvain across iterations:
- Original (signals only): 83-93%
- Added actor+action labels: 46-57%
- Fixed coherence gate: 28-46%
- But quality of emerged clusters degraded — false merges

---

## Solution: Faceted Mechanical Clustering

Replace bottom-up graph clustering with top-down mechanical splitting. No Louvain, no Jaccard, no graph.

### Algorithm

```
L1: sector + subject (LLM-extracted, normalized across languages)
    - Hard partition by domain. MILITARY/DRONE separate from SECURITY/TERRORISM.

L2: anchor signal (LLM signals primary, title text fallback)
    - LLM signals: PER:, ORG:, PLC:, EVT:, TGT: (already normalized)
    - Title text: content words as fallback for zero-signal titles
    - Both filtered by ubiquitous threshold (>10% for signals, >5% for text words)
    - Each title assigned to its strongest anchor (highest frequency in group)
    - Hard partition: titles with different anchors never cluster together

L3: temporal window (1-day gap detection)
    - Within each anchor group, split at 1+ day gaps
    - Same anchor on different weeks = different events
```

### Key Properties

- **Deterministic**: same input always produces same output
- **Debuggable**: trace exactly why any title landed in any cluster
- **No false connections**: "Iraq" and "Congo" can never merge regardless of shared persons
- **Multilingual**: LLM signals normalize across languages (primary anchors)
- **Title text fallback**: catches titles with zero LLM signals using content words

### Dynamic Ubiquitous Filtering

No hardcoded stop word lists. Both LLM signals and title text words are filtered by the same principle: if a signal/word appears in >N% of titles for this centroid, it's too common to be a useful anchor.

- LLM signals: >10% of centroid titles = ubiquitous (e.g., PER:TRUMP for USA, PER:MACRON for France)
- Title text words: >5% of centroid titles = ubiquitous (stricter because text is noisier)
- Computed dynamically per centroid+month, not hardcoded

---

## Test Results

### France (1,514 strategic titles)

| Metric | Louvain (best) | Faceted |
|--------|---------------|---------|
| Emerged events | 113 | 225 |
| Catchall rate | 25% | 42% |
| Iraq/Congo mixed | Yes | **No** |
| Epstein/schoolchildren mixed | Yes | **No** |

Ubiquitous signals: PER:MACRON, PLC:PARIS, TGT:FR
Ubiquitous words: (none at 5% threshold for France)

### USA (25,258 strategic titles)

| Metric | Louvain (original) | Faceted |
|--------|-------------------|---------|
| Emerged events | 1,554 | 3,303 |
| Catchall rate | 90% -> 46% (tuned) | 26% |
| Iraq/Congo mixed | Yes | **No** |

Ubiquitous signals: PER:TRUMP, TGT:IR, TGT:US
Ubiquitous words: trump, iran, israel, says, with

---

## Known Limitations

### 1. Mega-clusters from continuous coverage
Stories with daily coverage (Iran war, Israel conflict) produce clusters spanning the full month because there are no 1-day temporal gaps. TGT:IL has 340 titles spanning 03/01-03/26.

**Potential fix**: Max cluster size cap or fixed rolling windows (3-5 days).

### 2. Higher event count
Faceted produces more events (225 vs 113 for France) because it doesn't merge across anchors. Two clusters about related but distinct sub-stories (e.g., Hormuz strait security + Hormuz oil disruption) stay separate.

**Potential fix**: Mechanical merge pass (existing step 4) or LLM merge pass (existing step 5) to combine related events post-clustering.

### 3. Single-anchor assignment
Each title goes to its strongest anchor only. A title mentioning both "Hormuz" and "Anthropic" goes to whichever is more frequent in the group. No multi-anchor overlap.

**Acceptable**: titles are plankton, events are the content unit. As long as the event is coherent, individual title placement is secondary.

### 4. Catchall for zero-signal, zero-keyword titles
Titles with no LLM signals AND no distinctive content words remain in catchall. These are typically generic opinion pieces or analytical commentary without specific entity mentions.

**Acceptable**: these titles don't contribute to event coherence anyway.

---

## Pipeline Integration Plan

The faceted approach replaces only the clustering step (L3 Louvain in `cluster_topdown()`). The rest of the pipeline stays:

```
Current:                          Proposed:
1. cluster_topdown()              1. cluster_faceted()
   L1 sector+subject                 L1 sector+subject (same)
   L1.5 target split                 L2 anchor signal split (replaces L1.5+L2+L3)
   L2 anchor keyword split           L3 temporal window
   L3 Louvain                        (no Louvain)
2. temporal_split                 2. (integrated into L3 above)
3. coherence gate                 3. coherence gate (may simplify or remove)
4. mechanical merge               4. mechanical merge (same, needed for cross-anchor)
5. LLM merge                     5. LLM merge (same, for cross-subject)
6. society threshold              6. society threshold (same)
7. pass-2 rescue                  7. (may not be needed with lower catchall)
```

### Next Steps

1. Review France + USA clusters on frontend (current session)
2. Decide on mega-cluster handling (max size vs rolling window)
3. Implement as replacement for `cluster_topdown()` in `rebuild_centroid.py`
4. Test mechanical merge + LLM merge on top of faceted output
5. Run all 75 centroids and compare catchall rates

---

## Files

| File | Role |
|------|------|
| `scripts/prototype_faceted.py` | Standalone prototype for testing |
| `pipeline/phase_4/rebuild_centroid.py` | Production clustering (to be modified) |
| `docs/context/FACETED_CLUSTERING_ANALYSIS.md` | This document |
