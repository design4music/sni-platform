# Friction Nodes: From News Noise to Geopolitical Reality

**Date**: 2026-04-01
**Status**: Vision / future milestone. Depends on Layer 2 narrative topics + narrative matching.

---

## The Insight

The lion's share of global news coverage orbits around a handful of active geopolitical friction points:
- US-Iran war (overlapping with Israel-Palestine, Lebanon)
- West vs Russia (Ukraine as focal point)
- US vs Cuba/Venezuela
- US-EU-NATO tensions (Greenland, burden-sharing)
- US-China competition (Taiwan, trade, tech)

These "friction nodes" generate thousands of events across dozens of centroids. The system should surface them automatically and show how all the political noise spins around very few meta-stories about power competition and sovereignty.

---

## Architecture

```
Meta-narratives (9, exist)           — world-ordering principles
  Friction nodes (NEW, auto-detected)  — active conflict/competition zones
    Centroid perspectives               — each centroid's view of the node
      Narrative topics (Layer 2)        — assembled stories per centroid
        Clusters (Layer 1)              — signal units
```

### Friction Node = Cross-Centroid Narrative Cluster

A friction node is detected when:
1. Multiple centroids (3+) have active strategic narratives from the same meta-narrative
2. These narratives share timeline overlap (same month/week)
3. They reference common actors (e.g., IR, US, IL all appear across centroids)

Example: "Iran War" friction node
- Meta: Security & Conflict Order + Great Power Competition
- Centroids: USA, Iran, Israel, Gulf, UK, France, Russia, India, China (15+)
- Actors: US, IL, IR, SA, KW, AE, GB, FR
- Timeline: Mar 1-31 (ongoing)
- ~2000 sources across centroids

### Detection Method

1. Run narrative matching on Layer 1 clusters (already exists, needs re-run)
2. Group matched strategic narratives by meta-narrative + month
3. Count centroid spread: how many centroids have matches for the same narrative?
4. High spread (5+ centroids) + high volume (100+ events) = friction node
5. Extract: participating centroids, dominant actors, timeline, source volume

### Display

Friction node page shows:
- Title and summary (LLM-generated)
- Map highlighting participating centroids
- Timeline of key developments
- Centroid perspectives: each centroid's narrative topics related to this node
- Source diversity metrics (how many countries, languages covering this)

---

## Dependencies

1. **Layer 2 narrative topics** (from NARRATIVE_TOPICS_PLAN.md) — must exist first
2. **Narrative matching re-run** — strategic narratives matched to current clusters
3. **Cross-centroid correlation** — query that finds co-occurring narratives

## Existing Infrastructure

- `meta_narratives` table (9 entries) — the world-ordering frames
- `strategic_narratives` table (~142 entries) — actor-specific claims
- `event_strategic_narratives` — links events to narratives (needs re-run)
- `narrative_weekly_activity` — activity tracking per narrative
- Epic system — already does cross-centroid story detection (related concept)

## Relationship to Epics

Epics detect cross-centroid stories via tag co-occurrence.
Friction nodes detect via narrative co-occurrence.
They may converge — a friction node IS a narrative epic.

---

## Timeline

- **April 2026**: Ship March with Layer 2 topics. Re-run narrative matching.
- **May 2026**: Build friction node detection. First "Iran War" node page.
- **Ongoing**: Friction nodes update incrementally as new events + narratives arrive.
