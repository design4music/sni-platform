# Signal Observatory -- Implementation Plan

**Goal:** Three-tier signal analytics: cross-signal graph, category views, individual signal deep-dives. Plus enrichment of existing UI.

**Data source:** All queries against existing tables (title_labels, events_v3, event_v3_titles, centroids_v3, ctm, monthly_signal_rankings). No new pipeline phases.

---

## Build Order (5 phases, each shippable)

### Phase 1: Data Layer -- API routes + queries
**Why first:** Every page depends on these queries. Build once, reuse everywhere.

**API routes to create:**

| Route | Returns | Used by |
|-------|---------|---------|
| `GET /api/signals/top` | Top N signals per type (with counts) | Observatory, Category |
| `GET /api/signals/[type]/[value]` | Single signal profile (temporal, geo, theme, co-occurrence, top events) | Detail page |
| `GET /api/signals/co-occurrence` | Pairwise co-occurrence matrix for top signals | Observatory graph |
| `GET /api/signals/[type]` | Top signals for one type with sparkline data | Category page |

**Core queries:**

```sql
-- 1. Co-occurrence: signals sharing events
WITH signal_events AS (
  SELECT 'persons' as sig_type, unnest(tl.persons) as sig_value, evt.event_id
  FROM event_v3_titles evt
  JOIN title_labels tl ON tl.title_id = evt.title_id
  -- UNION ALL for orgs, places, commodities, policies, systems, named_events
)
SELECT a.sig_value as source, b.sig_value as target,
       a.sig_type as source_type, b.sig_type as target_type,
       COUNT(DISTINCT a.event_id) as weight
FROM signal_events a
JOIN signal_events b ON a.event_id = b.event_id
  AND (a.sig_value < b.sig_value OR a.sig_type < b.sig_type)  -- dedupe pairs
WHERE a.sig_value IN (top_N) AND b.sig_value IN (top_N)
GROUP BY source, target, source_type, target_type
HAVING COUNT(DISTINCT a.event_id) >= 2
ORDER BY weight DESC;

-- 2. Temporal: weekly mention counts
SELECT date_trunc('week', e.date) as week, COUNT(DISTINCT e.id) as count
FROM events_v3 e
JOIN event_v3_titles evt ON evt.event_id = e.id
JOIN title_labels tl ON tl.title_id = evt.title_id
WHERE $signal_value = ANY(tl.$signal_type)
GROUP BY week ORDER BY week;

-- 3. Geographic: country distribution
SELECT unnest(e.iso_codes) as country, COUNT(DISTINCT e.id) as count
FROM events_v3 e
JOIN event_v3_titles evt ON evt.event_id = e.id
JOIN title_labels tl ON tl.title_id = evt.title_id
WHERE $signal_value = ANY(tl.$signal_type)
GROUP BY country ORDER BY count DESC;

-- 4. Theme: track + domain breakdown
SELECT e.track, COUNT(DISTINCT e.id) as count
FROM events_v3 e
JOIN event_v3_titles evt ON evt.event_id = e.id
JOIN title_labels tl ON tl.title_id = evt.title_id
WHERE $signal_value = ANY(tl.$signal_type)
GROUP BY e.track ORDER BY count DESC;

-- 5. Top events for a signal
SELECT e.id, e.title, e.date, e.source_batch_count, e.centroid_label, e.track
FROM events_v3 e
JOIN event_v3_titles evt ON evt.event_id = e.id
JOIN title_labels tl ON tl.title_id = evt.title_id
WHERE $signal_value = ANY(tl.$signal_type)
GROUP BY e.id ORDER BY e.source_batch_count DESC LIMIT 20;
```

**Performance note:** Co-occurrence matrix for top ~50 signals could be slow. Options:
- Materialize nightly during freeze (best)
- Cache in API with 1h TTL (good enough to start)
- Start with top 30 signals, expand if fast enough

**Deliverable:** 4 API routes returning JSON. Testable with curl.

---

### Phase 2: Individual Signal Page (`/signals/[type]/[value]`)
**Why second:** Simplest page, validates all queries work end-to-end.

**Depends on:** Phase 1 (API routes)

**URL examples:** `/signals/persons/trump`, `/signals/orgs/nato`, `/signals/places/gaza`

**Layout (top to bottom):**

```
+----------------------------------------------------------+
| TRUMP                            395 mentions | 47 events |
| Person | United States                                    |
| "Dominates trade, immigration, and foreign policy..."    |
| (context from monthly_signal_rankings)                   |
+----------------------------------------------------------+
| [=== Mention Timeline (area chart, weekly) ===========]  |
+---------------------------+------------------------------+
| Relationships (top 10)   | Geographic Distribution      |
| - Zelensky (42 shared)   | [horizontal bar chart]       |
| - EU (38)                | US ======== 120              |
| - Tariffs (35)           | UA ====== 89                 |
| - NATO (28)              | RU ==== 67                   |
| - Musk (22)              | DE === 45                    |
| (clickable -> their page)|                              |
+---------------------------+------------------------------+
| Theme Breakdown           | Top Events                   |
| Military   ====== 30%    | 1. Trump Announces New...    |
| Diplomacy  ===== 25%     | 2. Trade War Escalates...    |
| Economic   ==== 20%      | 3. NATO Summit Tensions...   |
| Domestic   === 15%       | (clickable -> event page)    |
| Society    == 10%        |                              |
+---------------------------+------------------------------+
```

**Components:**
- `SignalHeader` -- name, type badge, country flag, mention count, context
- `MentionTimeline` -- area chart (recharts or lightweight canvas)
- `RelationshipList` -- top co-occurring signals with counts, links
- `GeoDistribution` -- horizontal bar chart of countries
- `ThemeBreakdown` -- horizontal bar chart of tracks
- `TopEvents` -- list linking to event pages

**Chart library:** recharts (already a Next.js standard, SSR-friendly, lightweight)

**Deliverable:** Fully functional signal detail page.

---

### Phase 3: Category Pages (`/signals/[type]`)
**Why third:** Reuses Phase 2 queries + components. Natural stepping stone.

**Depends on:** Phase 1 + Phase 2 (reuses components)

**URL examples:** `/signals/persons`, `/signals/orgs`, `/signals/commodities`

**Layout:**

```
+----------------------------------------------------------+
| Top Persons                                    Feb 2026  |
+----------------------------------------------------------+
| 1. TRUMP        395 | [sparkline~~~~] | Trade, NATO...   |
| 2. ZELENSKY     187 | [sparkline~~~~] | Defense aid...   |
| 3. EPSTEIN       97 | [sparkline~~~~] | Legal fallout... |
| 4. XI JINPING    84 | [sparkline~~~~] | Trade, Taiwan... |
| 5. MUSK          76 | [sparkline~~~~] | DOGE, SpaceX...  |
+----------------------------------------------------------+
| Each row clickable -> /signals/persons/[name]            |
```

**Per row:** name, mention count, 30-day sparkline, LLM context (from monthly_signal_rankings), top 3 co-occurring signals as pills.

**Also:** Signal type index at `/signals` linking to all categories (temporary until Phase 4 replaces it with the observatory).

**Deliverable:** 7 category pages (one per signal type) + index.

---

### Phase 4: Cross-Signal Observatory (`/signals`)
**Why fourth:** Most complex UI. Needs all data + queries proven stable.

**Depends on:** Phase 1 (co-occurrence API), Phase 2+3 (detail pages for click-through)

**The "spaceship dashboard" layout:**

```
+----------------------------------------------------------+
|  SIGNAL OBSERVATORY                         Feb 2026     |
+----------------------------------------------------------+
|                                         |  TOP MOVERS    |
|        [Force-Directed Graph]           |  ^ Trump +12%  |
|                                         |  ^ Tariffs +45%|
|     (persons)O----O(orgs)               |  v Zelensky -8%|
|              \   /                      |  ^ Gaza +22%   |
|         O----O--O                       |  v NATO -15%   |
|              |                          |                |
|         O----O(places)                  +----------------+
|                                         |  CATEGORIES    |
|   [click node = highlight + panel]      |  Persons (12)  |
|   [hover = tooltip with context]        |  Orgs (8)      |
|   [scroll = zoom]                       |  Places (9)    |
|   [drag = reposition]                   |  Commodities(5)|
+-----------------------------------------+----------------+
|  [Temporal Heatmap -- week x signal grid, color=intensity]|
+----------------------------------------------------------+
```

**Graph implementation:**
- Library: `react-force-graph-2d` (uses canvas, handles 200+ nodes at 60fps)
- Nodes: top 40-60 signals across all types
- Node size: log(mention_count) -- prevents Trump from dwarfing everything
- Node color: signal type (consistent palette)
- Edges: co-occurrence weight >= 3 shared events (threshold to avoid hairball)
- Interactions: hover (tooltip), click (select + highlight neighbors), drag (reposition)

**Side panels:**
- **Top movers:** signals with biggest week-over-week velocity change
- **Category links:** quick nav to Phase 3 category pages
- **Selected signal panel:** appears on node click, shows mini-profile + "View full" link to Phase 2 detail page

**Temporal heatmap (bottom):**
- Rows = top 20 signals, columns = weeks (last 8 weeks)
- Cell color intensity = mention count that week
- Like GitHub contribution graph but for geopolitical signals

**Deliverable:** Interactive observatory page. The flagship feature.

---

### Phase 5: Existing UI Enrichment
**Why last:** Polish and integration. Each item is independent and small.

**Depends on:** Phase 2 (detail pages exist for linking)

**Items:**
1. **Signal pills -> clickable links** -- existing pills on TrendingCard link to `/signals/[type]/[value]`
2. **GeoBrief "Top signals" widget** -- on country profile pages, show top 5 signals for that centroid this month
3. **Trending sidebar sparklines** -- add tiny sparklines next to signal names in trending sidebar
4. **Epic signal constellation** -- on epic detail page, show which signals participate

**Deliverable:** Richer existing pages with signal cross-links.

---

## Dependency Graph

```
Phase 1 (Data Layer)
  |
  +---> Phase 2 (Individual Signal Page)
  |       |
  |       +---> Phase 3 (Category Pages)
  |               |
  +---------------+---> Phase 4 (Observatory Graph)
  |
  +---> Phase 5 (UI Enrichment) [can start after Phase 2]
```

Phases 4 and 5 can run in parallel once Phase 3 is done.

---

## Tech Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Chart library | recharts | Already Next.js standard, SSR-friendly, area/bar/sparkline |
| Graph library | react-force-graph-2d | Canvas-based, performant, good React integration |
| Data caching | API-level (300s revalidate) | Same pattern as existing trending queries |
| Co-occurrence | Compute on request, cache 1h | Start simple, materialize if slow |
| Sparklines | recharts `<Line>` (tiny, no axes) | Reuse same library |
| World map | Not in v1 | Horizontal bar charts for geo. Add map later if wanted |

## Open Questions

- **Q-003:** Co-occurrence threshold -- minimum shared events to draw an edge? Start with 3, tune visually.
- **Q-004:** Signal deduplication -- "Donald Trump" vs "Trump" vs "TRUMP". Currently handled by Phase 3.1 normalization. Verify consistency.
- **Q-005:** Time window -- observatory shows current month? Last 30 days rolling? Last 90 days? Suggest: 30-day rolling default with month selector.
