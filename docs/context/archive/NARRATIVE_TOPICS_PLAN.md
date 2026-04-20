# Narrative Topics: From Clusters to Stories

**Date**: 2026-04-01
**Context**: Clustering produces high-quality signal units but too many for human consumption. Need a narrative layer on top.

---

## Architecture: Four Layers

```
Layer 0: Titles          — raw headlines (120K+ per month)
Layer 1: Clusters        — signal units, mechanically grouped (1000-3000 per mega CTM)
Layer 2: Narrative Topics — user-facing stories, LLM-assembled from clusters (50-100 per CTM)
Layer 3: Sagas           — meta-narratives spanning topics (5-10 per centroid)
```

### Layer 1 (DONE): High-Resolution Clustering
- Faceted/layered clustering produces coherent signal units
- Small clusters (5-50 titles) are precise and clean
- Large clusters (100+) exist but are internally mixed
- These are NOT the user-facing output — they're building blocks

### Layer 2 (NEXT): Narrative Topics
- Assembled by LLM from Layer 1 clusters
- Each topic = one developing story or situation
- 50-100 topics per mega CTM, fewer for smaller centroids
- Each receives: title, structured summary (with subtopics as sections), timeline
- Examples for USA Security March 2026:
  - "US-Iran War: Air Campaign" (assembled from: airstrikes W1, Kharg Island, school strike, B-2 bombers)
  - "Strait of Hormuz Crisis" (assembled from: IRGC closure, mine-laying, coalition escorts, oil disruption)
  - "Trump's Iran War Policy" (assembled from: congressional approval, troop deployment debate, war goals)
  - "ICE Airport Deployments" (assembled from: TSA crisis, ICE tactical gear, government shutdown)

### Layer 3 (FUTURE): Sagas
- Meta-narratives that span multiple topics and centroids
- "Iran War" saga connects topics across USA, Iran, Israel, Gulf, UK centroids
- Detected by shared timeline + causal linkage + semantic overlap
- Already partially supported by existing saga/epic system

---

## Implementation Plan for Layer 2

### Step 1: LLM Topic Assembly
Input: All Layer 1 clusters for a CTM (with their top headlines)
Output: Grouped clusters with topic titles and structured summaries

Prompt concept:
```
You receive N news clusters, each with sample headlines and source count.
Organize them into major news stories (topics).
Each topic should be a coherent developing situation.
Small related clusters should merge into larger topics.
Return: {topics: [{title: "...", summary: "...", cluster_ids: [1,3,7], subtopics: ["Air campaign", "Civilian casualties"]}]}
```

For mega CTMs: split by sector (MILITARY, SECURITY, etc.) to keep context window manageable.

### Step 2: Structured Summaries
Each topic gets a multi-paragraph summary:
- Lead: what happened (the core event/situation)
- Body: key developments (drawn from subtopics/clusters)
- Context: reactions, implications, what's next
- ~200-500 words depending on topic size

### Step 3: Major Vector Detection
At CTM level, identify the 3-5 dominant narrative domains:
- e.g., "Iran War", "Domestic Policy", "Cuba Relations"
- These become section headers on the CTM page
- Topics are grouped under their domain

### Step 4: Saga Detection
Cross-centroid, cross-month narrative threads:
- "Iran War" appears in USA, Iran, Israel, Gulf, UK, France
- Each centroid contributes its perspective
- Saga page shows the full picture

---

## Sizing

### Per-CTM LLM Cost (Layer 2)
- Input: ~100 clusters × 3 headlines each × 30 tokens = ~9,000 tokens
- Output: ~50 topics × (title + summary) = ~15,000 tokens
- Per CTM: ~24,000 tokens = ~$0.01
- All March CTMs: ~280 × $0.01 = ~$2.80

### What Changes on Frontend
- CTM page shows **topics** (Layer 2), not clusters (Layer 1)
- Each topic: title, summary, source count, date range
- Expandable: shows member clusters as "related coverage"
- Filters: by domain, by week, by country
- Small CTMs (<30 clusters): topics = clusters (no assembly needed)

### What Stays the Same
- Layer 1 clustering pipeline (proven, working)
- Individual cluster/event pages (still accessible via links)
- Signal extraction (Phase 3.1)
- Title/source title display on event detail pages

---

## Open Questions

1. Where to store Layer 2 topics? New table `narrative_topics` or reuse `story_groups`?
2. How to handle incremental updates? New cluster arrives → assign to existing topic or create new?
3. Coherence filtering: should happen at Layer 1 (dissolve bad clusters) or Layer 2 (LLM rejects)?
4. How many clusters can we fit in one LLM call? Need to test with real data.
5. German translations for topic summaries?

---

## Relationship to Existing Concepts

| Existing | Maps to |
|----------|---------|
| events_v3 | Layer 1 clusters |
| story_groups (UI) | Proto-Layer 2 (signal-based, not narrative) |
| CTM summary | Layer 2 aggregate (already exists, needs better input) |
| Sagas/Epics | Layer 3 |
| Narrative matching | Cross-references between Layer 2 topics and strategic narratives |
