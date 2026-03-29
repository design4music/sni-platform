# Story Groups Design

**Date**: 2026-03-29
**Status**: Design phase, building on validated faceted clustering + UI prototype

---

## Concept

Story groups are "topics of topics" -- umbrella containers that organize related clusters/events under a shared signal. Example: "HORMUZ" group contains Hormuz naval operations, Hormuz oil disruption, Hormuz ultimatum, etc.

The CTM page adapts to volume:
- **Low volume** (<50 events): flat list with individual descriptions (current design)
- **High volume** (50+ events): grouped view with group-level descriptions

---

## Data Model

### Story Group (new concept)
- **Anchor signal**: PER:KHAMENEI, PLC:HORMUZ, ORG:ICE, TGT:CN, etc.
- **Group description**: LLM-generated 2-3 sentence digest covering all member events
- **Member events**: ordered by source count
- **Metadata**: topic count, total sources, date range

### Event (existing, modified display)
- **On CTM page (grouped mode)**: one-line format: country badge | LLM title | date | source count
- **On Topic detail page**: full description, source titles, narratives, RAI analysis

---

## CTM Page Evolution (Incremental Growth)

### Days 1-3 (0-20 events): Flat Mode
- Individual event cards with titles and descriptions
- Same as current design
- Descriptions generated immediately

### Days 4-7 (20-50 events): Transition
- Still flat but getting crowded
- Groups forming but not yet displayed
- Individual descriptions still visible

### Day 7+ (50+ events): Grouped Mode
- Switch to StoryGroupList UI
- Group-level descriptions generated
- Individual events collapse to one-liners inside accordions
- Individual event descriptions still exist (on Topic pages) but hidden from CTM

### Key principle: content is additive
- New events join existing groups or form new ones
- Group descriptions regenerate when group grows significantly
- Individual event descriptions created early are NEVER deleted (they live on Topic pages)
- The CTM page just changes what it SHOWS, not what exists

---

## LLM Prose Changes

### Current (Phase 4.5a/4.5b)
1. **Event title** (5-12 words) -- for all events
2. **Event description** (2-3 sentences) -- for events with 5+ sources
3. **CTM summary** (150-250 words) -- monthly digest for the whole track

### Proposed
1. **Event title** (5-12 words) -- for events with N+ sources (threshold TBD)
2. **Event description** (2-3 sentences) -- for events with N+ sources, displayed on Topic page
3. **Group description** (2-3 sentences) -- NEW: covers the story group, displayed on CTM page
4. **CTM summary** (150-250 words) -- fed from group descriptions instead of event descriptions

### Prose Generation Thresholds (needs analysis)

Current thresholds:
- Title-only (1-4 sources): generate title, no summary
- Mini (5-15 sources): title + 2-3 sentence summary
- Medium (16-40 sources): title + 1-2 paragraph summary
- Maxi (40+ sources): title + 2-3 paragraph summary

Question: should we raise thresholds for high-volume centroids?
- USA with 25K titles: generating prose for 3,600 events is expensive and most won't be seen
- Maybe: only generate prose for events with 5+ sources (857 events) or 10+ sources (310 events)
- Small centroids keep current thresholds (every event matters)

---

## LLM Merge Within Groups

Each story group is a natural boundary for LLM merge review:
- Events within a group share the anchor signal
- LLM can compare pairs within the group: "same specific story? YES/NO"
- Much smaller candidate space than global merge (each group has 3-50 events, not 3,000)
- Could run after group formation, before prose generation

---

## Pipeline Order (Proposed)

```
1. Faceted clustering (L1 -> L2 -> L3 -> recursive)
2. Mechanical merge (2+ shared specific signals)
3. Form story groups (by topic_core anchor)
4. LLM merge within groups (compare group members)
5. Generate event titles (for events above threshold)
6. Generate group descriptions (for groups with 3+ events)
7. Generate CTM summary (from group descriptions)
```

Steps 1-3 are mechanical (free). Steps 4-7 use LLM (cost).

---

## UI Components

### StoryGroupList (exists, needs refinement)
- Collapsible accordion per group
- Group header: label + signal badges + topic/source counts
- Default: show top 5 events, "show more" expands
- One-line event format inside accordion

### EventOneLiner (new component)
- Single line: [country badge] [LLM title or first headline] [date range] [source count]
- Links to Topic detail page
- No description, no source titles on CTM page

### GroupDescription (new, inside accordion header)
- 2-3 sentence LLM-generated digest
- Shows below group label when accordion is expanded
- Regenerated when group grows by 50%+

---

## Storage

`story_groups` table:
```sql
CREATE TABLE story_groups (
    id UUID PRIMARY KEY,
    ctm_id UUID REFERENCES ctm(id),
    anchor TEXT NOT NULL,        -- "PER:KHAMENEI", "PLC:HORMUZ"
    label TEXT,                  -- human-readable: "Khamenei", "Hormuz"
    title TEXT,                  -- LLM-generated group title
    title_de TEXT,
    description TEXT,            -- LLM-generated 2-3 sentence digest
    description_de TEXT,
    event_count INT,
    source_count INT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE (ctm_id, anchor)
);
```

Events link to groups via `topic_core` field (already stored in events_v3).
No junction table needed -- simple lookup: `WHERE topic_core LIKE anchor || '%'`.

events_v3 remains the primary data entity. Story groups are a presentation layer
with their own LLM prose, not a replacement for events.

## Grouping Threshold

Per centroid analysis (March 2026):
- 36 centroids have 50+ emerged events (would trigger grouping)
- 35 centroids have <50 events (flat list fine)
- 3 centroids empty

50 topics across 3-4 tracks = ~15 per track -- flat list is still usable.
Consider boosting threshold to 100+ topics total before switching to grouped view.
This is a visual decision -- try both and decide.

## Dynamic Prose Thresholds (by centroid volume)

| Tier | Strategic titles | Min sources for prose | Example centroids |
|------|------------------|-----------------------|-------------------|
| Mega | 10K+ | >= 10 | USA, Iran |
| Large | 3-10K | >= 5 | Israel, Gulf, China, Russia |
| Medium | 1-3K | >= 3 | France, UK, Germany, Japan |
| Small | <1K | >= 2 | Nordic, Brazil, Canada |

This gives ~600 events total for prose ($6) vs 6,500 at threshold 3 ($65).

## Time Pressure

Remote pipeline stopped since 2026-03-27. Content debt growing.
Priority: get March rebuilt, generate prose, push to Render, restart daemon.

## Implementation Plan

### Phase 1: Complete March Rebuild (immediate)
1. Rebuild all 75 centroids with faceted clustering (RUNNING)
2. Clean stale CTMs from old track system
3. Generate event titles (Phase 4.5a with dynamic thresholds)
4. Generate CTM summaries (Phase 4.5b)
5. Push to Render, restart daemon

### Phase 2: Story Groups MVP
1. Create story_groups table
2. Compute groups from topic_core anchors (mechanical)
3. Generate group titles + descriptions (LLM)
4. StoryGroupList component refinements:
   - EventOneLiner for individual topics inside groups
   - Group description display
   - Configurable threshold for grouped vs flat mode
5. LLM merge within groups (optional, refines quality)

### Phase 3: Daemon Integration
1. Wire faceted clustering into daemon Slot 3
2. Replace Phase 3.3 with mechanical sector filter
3. Story group computation as part of clustering slot
4. Group description regeneration trigger (when group grows significantly)

## Open Questions

1. Grouping threshold: 50? 100? Visual decision needed
2. Group stability across incremental updates (new events joining groups)
3. How to handle group splits when new data arrives
4. LLM merge within groups: before or after prose generation?
