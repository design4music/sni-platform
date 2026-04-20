# Next Steps Plan

**Date**: 2026-04-04
**Context**: March shipped, Jan/Feb labels extracted, friction nodes validated, daemon running for April.

---

## What We Have Now

### Working (Production)
- Pipeline daemon running on Render (main branch, old clustering for April)
- March data: frozen, layered clustering, 691 event families, LLM titles/summaries
- Frontend: family-grouped topics, filters (week/tags/countries/min sources/sort)
- Jan/Feb/Mar: full label extraction (sector, subject, signals)

### Validated (Local, Not Production)
- Layered clustering: Layer 1 mechanical + Layer 2 LLM (~$1 per CTM-month)
- Event families: LLM-assembled narrative topics from clusters
- Friction node detection: works across Jan-Mar, finds Venezuela, Greenland, Iran War
- Family synthesis concept: rich narrative pages from cluster descriptions

### Not Yet Built
- Friction node UI (pages, map overlay, timeline)
- Family synthesis (structured narrative pages)
- Daemon integration of new clustering
- 4-track system for Jan/Feb/April
- Epic system for non-friction stories (Epstein, ICE, AI)

---

## Two Types of "Big Stories"

### Friction Nodes (geopolitical, cross-centroid)
- Multiple countries involved as actors
- Detected from cross-centroid target correlation
- Persistent across months, have lifecycle (emerging → active → chronic → resolved)
- Examples: Iran War, Russia-Ukraine, US-China, Venezuela, Greenland
- **Replaces**: nothing currently — this is new capability
- **Display**: world map overlay + dedicated pages + timeline

### Epics (major stories, may be single-centroid)
- Significant stories that aren't bilateral/multilateral frictions
- Can be domestic (Epstein, ICE), thematic (AI/Pentagon), or events (Oslo bombing)
- Detected from high event-family source counts + LLM classification
- **Keeps**: existing epic concept but rebuilt on event families
- **Display**: dedicated pages, homepage section alongside friction nodes

### How They Differ

| | Friction Nodes | Epics |
|---|---|---|
| Scope | Cross-centroid (5+ countries) | Any (can be single centroid) |
| Nature | Geopolitical competition/conflict | Any major story |
| Duration | Months to years | Days to months |
| Detection | Cross-centroid target correlation | Source volume + LLM |
| Examples | Iran War, US-Russia | Epstein, ICE, AI arms race |

---

## Phase 1: Foundation ~~(This Week)~~ DONE

### 1.1 Switch to 4 Tracks (All Months) -- DONE (2026-04-08)
- ~~Remap Jan/Feb CTMs: geo_energy → geo_economy, geo_humanitarian → geo_society, geo_information → geo_politics~~
- ~~Fix April: wire SECTOR_TO_TRACK mechanical mapping into Phase 3.3 (replace LLM gating)~~
- ~~Delete old-track CTMs that have no events~~

### 1.2 Rebuild Jan/Feb with Layered Clustering -- NEEDS VERIFICATION
- ~~Run prototype_layered.py on all Jan/Feb CTMs~~
- ~~Build event families for Jan/Feb~~

### 1.3 Run Epic Detection for March
- Run existing epic detection pipeline on March data
- Or: identify epic candidates from event families with high source counts
- **Effort**: 30 min

---

## Phase 2: Friction Nodes (Next Week)

### 2.1 Create Friction Node Tables
```sql
friction_nodes: id, title, title_de, focal_signals[], participating_centroids[],
                status, first_detected, last_active, meta_narrative_id
friction_node_months: friction_node_id, month, centroid_event_counts, summary, summary_de
event_families.friction_node_id: links families to nodes
```

### 2.2 Detection Algorithm
- Run cross-centroid target correlation (already validated)
- Auto-create friction nodes for targets in 5+ centroids with 500+ titles
- Assign meta-narrative based on dominant strategic narrative matches
- Link event families to their friction node

### 2.3 Frontend: Friction Node Pages
- Node page: title, summary, map, participating centroids, timeline
- Monthly chapters: each month's key developments per centroid
- Cross-reference: "See this story from Iran's perspective"

### 2.4 Frontend: Map Overlay
- Gleaming dots on participating centroids
- Intensity proportional to source volume
- Click → friction node page

---

## Phase 3: Epic System Rebuild (Week After)

### 3.1 Epic Detection from Event Families
- Identify families with 100+ sources across 3+ centroids → friction node candidate
- Identify families with 50+ sources in single centroid → epic candidate
- LLM classifies: "Is this a geopolitical friction or a standalone major story?"

### 3.2 Epic Pages
- Similar to friction node pages but simpler (no map, no cross-centroid)
- Timeline, summary, source headlines
- Examples: Epstein files, ICE enforcement, AI Pentagon controversy

---

## Phase 4: Daemon Integration (Ongoing)

### 4.1 Replace Phase 3.3 with Mechanical Gating
- SECTOR_TO_TRACK mapping replaces LLM track assignment
- NON_STRATEGIC sector filter replaces LLM intel gating
- **Saves**: ~$1.34/day in LLM costs

### 4.2 Replace Phase 4 with Layered Clustering
- Wire prototype_layered.py into daemon Slot 3
- Incremental: new titles → Layer 1 clusters → assign to existing families
- Periodic: new families assembled when unassigned clusters accumulate

### 4.3 Friction Node Updates
- Run detection monthly (or weekly for fast-moving situations)
- New month → new chapter added to existing nodes
- New friction detected → auto-create node

---

## Phase 5: Family Synthesis (Parallel)

### 5.1 Rich Narrative Pages
- LLM synthesizes all cluster descriptions within a family into one structured article
- Sections: chronological phases, impact, key actors, outlook
- ~$7 for all 691 families

### 5.2 CTM Page Display
- Families shown with short summary (truncated)
- Click → family page with full narrative
- Individual clusters accessible from family page

---

## Priority Order

1. **4-track switch** — unblocks everything else, fixes live site
2. **Jan/Feb rebuild** — enables historical friction testing
3. **Friction node tables + detection** — the big new feature
4. **Friction node frontend** — makes it visible
5. **Epic rebuild** — complements friction nodes
6. **Daemon integration** — makes it sustainable
7. **Family synthesis** — enriches content quality

---

## Open Questions

1. Should April use new clustering from the start, or let daemon do old clustering and rebuild monthly?
2. Friction node lifecycle: how to detect "resolved" (e.g., Venezuela friction faded)?
3. Epic vs friction: where does "NATO expansion debate" fit? (cross-centroid but not a conflict)
4. How granular should friction node monthly chapters be? One summary or per-centroid?
5. German translations for friction node content?
