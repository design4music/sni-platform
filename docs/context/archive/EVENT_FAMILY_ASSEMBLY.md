# Event Family Assembly — LLM Prompt Design

**Date**: 2026-04-08
**Status**: Prompt validated on three tiers (micro/medium/giant). Ready for production implementation.

---

## Concept: The Spine

An event family is defined by its SPINE — the one thing a reader would remember about the story. Everything in the family connects to that spine.

- A blockade of a vital waterway = spine
- Assassination of a leader = spine
- A deployment decision = spine
- A domestic scandal = spine

Different spines in the same theater = DIFFERENT families.
Same spine across different days/domains = SAME family.

---

## Three Levels

```
Level 1: THEATERS (friction nodes) — major geopolitical friction zones
  Created separately by cross-centroid detection algorithm.
  Families within a theater are distinct sub-stories.

Level 2: EVENT FAMILIES (this document) — developing story threads
  Each has a core spine (place, operation, incident, decision).
  Can span multiple domains (naval + diplomatic + economic).
  Created by LLM from Layer 1 clusters.

Level 3: TOPICS (clusters) — mechanically grouped headlines
  Input to family assembly. Many are fragments of the same family.
```

---

## Three Prompt Tiers

### Micro (< 100 clusters, e.g., Baltic, Oceania)
- Target: 5-10 families
- Prompt: standard, "organize into N families, group aggressively"
- Every story matters at this scale

### Medium (100-500 clusters, e.g., France, Germany, Russia)
- Target: 10-15 families
- Prompt: standard with "aggressive grouping" instruction
- Clear story threads with good separation

### Giant (500+ clusters, e.g., USA, Iran during active conflict)
- Target: 30-60 families
- Prompt: detailed "spine" concept (see below)
- Structured guidance on theaters, domestic vs international
- No data-specific examples — generic analytical framework

---

## Giant Prompt (Current Best)

```
You are an intelligence analyst organizing a large set of news clusters
into EVENT FAMILIES for a monthly strategic briefing.

THREE LEVELS OF GROUPING (you work at level 2):

Level 1 (above you): THEATERS -- major geopolitical friction zones.
You do NOT create these -- but your families will later be grouped
into theaters. Families about the same theater should be
distinguishable sub-stories, not duplicates of the theater itself.

Level 2 (YOUR JOB): EVENT FAMILIES -- the spine of a specific
developing story. What makes a family:
- It has a CORE IDENTITY: a specific place, operation, incident, or
  decision that is the spine. Everything connects to that spine.
- A blockade of a vital waterway is a family. Strikes on a specific
  target are a family. A political scandal is a family.
- The family can span multiple domains: naval, air, diplomatic,
  economic actions all related to the same spine belong together.
- Same spine, different days = same family.
- Different spines in the same theater = DIFFERENT families.

Level 3 (below you): TOPICS -- mechanically clustered headlines.
These are your input. Many are fragments of the same family.
Your job is to recognize which topics share a spine.

HOW TO IDENTIFY THE SPINE:
Ask: what is the ONE thing a reader would remember about this story?
- A specific geographic chokepoint being blocked
- A specific leader being killed or making a decision
- A specific military asset being destroyed or deployed
- A specific policy debate in government
- A specific domestic incident (attack, scandal, protest)

DOMESTIC vs INTERNATIONAL:
Domestic stories are separate from international theaters.
Each domestic story with its own spine is its own family.

RULES:
- Every cluster belongs to exactly one family. No orphans.
- Small clusters (1-3 sources) absorbed into nearest matching family.
- Do NOT create a catch-all 'miscellaneous' family.
- Do NOT merge different spines into mega-families.
```

---

## Validated Results

| Tier | CTM | Clusters | Families | Orphans | Quality |
|------|-----|----------|----------|---------|---------|
| Micro | Baltic security | 67 | 4 | 0 | Clean — distinct themes |
| Medium | France security | 134 | 14 | 7 | Excellent — nuclear, carrier, Iraq, bomb plot |
| Giant | USA security | 200 (of 1413) | 24 | 44 | Good — distinct spines, needs second pass for orphans |

### Giant families identified (USA security March 2026):
- Hormuz chokepoint operations (523 src)
- Khamenei assassination (337 src)
- Iranian retaliation strikes (322 src)
- Tehran airstrikes (264 src)
- Kharg Island bombing (235 src)
- Diplomatic facility attacks worldwide (224 src)
- Aircraft crashes and losses (208 src)
- FBI domestic terror investigations (253 src)
- ICE airport deployment (129 src)
- Ground troops debate (120 src)
- Submarine sinks Iranian warship (120 src)
- School bombing controversy (55 src)
- ... and 12 more specific incidents

---

## Implementation Notes

- Giant prompt costs more tokens (~500 system prompt) but runs only 6-10 times/month
- Orphans from first pass need second pass (assign to nearest family by word overlap)
- Remaining clusters (201-1413) not sent to LLM need mechanical assignment
- Family summaries generated inline during assembly (no separate step)
- Script: `scripts/test_giant_prompt.py` contains the current prompt

---

## Open Questions

1. Should "Trump's public statements" (967 src) be one family or split by week/topic?
2. How to handle clusters 201-1413 (not sent to LLM)? Mechanical assignment or second LLM pass?
3. Should the prompt mention the centroid name for context, or stay fully generic?
4. DE translations for family titles and summaries — when to generate?
