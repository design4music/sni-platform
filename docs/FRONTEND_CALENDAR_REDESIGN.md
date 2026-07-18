# Frontend Calendar-Day Redesign

**Status**: Design locked 2026-04-14. Implementation pending.
**Companion to**: D-056 / D-057 clustering redesign (backend), CLUSTERING_REDESIGN.md.
**Supersedes**: Current event-centric frontend, CTM summary page, family rendering.

---

## Why

The current frontend is event-centric and presents families as primary containers. Several problems surfaced during validation:

1. **Families don't work as a primary UI primitive.** They nest smaller clusters inside larger ones, which breaks natural ordering (by size or by date) because smaller clusters become invisible inside families. Users see "families" as "something grouped" but can't easily scan the actual events.

2. **Overloaded event list.** Even with substrate filtering, a big CTM like USA/geo_security has hundreds of clusters per month, which is too many to scan in any flat list.

3. **No time dimension in the primary view.** Readers naturally ask "what happened on March 14?" but the current UI requires clicking into families or filtering.

4. **LLM prose cost.** Current Phase 4.5a generates per-event summaries (~2000 calls for USA alone). Phase 4.5b generates CTM-wide digests that duplicate content. Two-order-of-magnitude reduction is available if we shift to per-day summaries.

## The model

**Calendar day is the primary unit.** This is structurally aligned with D-056's day-atomic clustering: every events_v3 row already has a single `date`. The frontend simply groups by date.

### Layout (mobile-first, responsive)

```
+--------------------------------+
| AMERICAS-USA / geo_security    |  sticky header
| March 2026       [< Feb | Apr >]|
+--------------------------------+
| _||||_|||||__|||||_||||_||||__ |  activity stripe
| 1     8      15     22    30   |  (all days, log-scaled)
+--------------------------------+
|                                |
| v Tuesday, March 14   1,204 src|  day card (expanded)
|                                |
| +-- Daily Brief ------------+  |  LLM prose,
| | The US struck Iran's Kharg |  |  rich days only
| | oil terminal while Iraqi   |  |
| | protests continued ...     |  |
| +---------------------------+  |
|                                |
| +--------------------------+   |
| | 80  Kharg Island strike  |   |  cluster card
| |     "US strikes Iran..." |   |  tap -> event page
| +--------------------------+   |
| +--------------------------+   |
| | 60  Iraq KC-135 crash    |   |
| +--------------------------+   |
| +--------------------------+   |
| | 17  Baghdad embassy      |   |
| +--------------------------+   |
| ... 5 more v                   |  fold
|                                |
| > Wednesday, March 15    892   |  day card (collapsed)
| > Thursday,  March 16    744   |
+--------------------------------+
```

**Key mechanics**:

- Single vertical stream of day cards, one card per day
- **Single day expanded at a time** (default: today, or the biggest day in a frozen month)
- Tap a collapsed card to expand; others collapse
- Activity stripe always visible; tap a bar to jump to that day
- Cluster cards inside a day ordered by `source_count DESC`
- First 3-5 clusters visible, rest behind "show more" fold
- Substrate clusters hidden by default; per-day toggle (only shown when day volume justifies it)
- Sticky day header: currently-visible day's name stays at top of viewport as you scroll its clusters

**Desktop**: same layout, wider column. On very wide screens optionally 2-day comparison. No new structure.

## Locked parameters

| | value | meaning |
|---|---|---|
| K | 5 | min `source_count` for a cluster to have a full event page |
| M | 50 | min day `sum(source_count)` to generate daily brief |
| J | 5 | min `count(distinct clusters)` on a day to generate daily brief |
| N | 500 | min CTM `title_count` per month to generate briefs at all |
| substrate | src=1 AND places=NULL AND target='NONE' | hidden by default, per-day toggle |
| day expansion | single | one day open at a time, sticky header |
| cluster ordering | source_count DESC | stable per-day |
| month switcher | prev / next arrows | we only have 3.5 months of data |
| quiet CTMs | same layout, empty days show empty | defer special treatment |

## Workstreams

### A. Backend data contract (small, ~1-2 hours)

1. **Migration**: add `events_v3.is_substrate boolean NOT NULL DEFAULT false`
2. **Compute at write time** in `incremental_clustering.write_clusters_to_db`:
   ```python
   is_substrate = (
       c["source_count"] == 1
       and not c.get("dominant_entity")
       and (c.get("beat") or (None, None, None))[2] in (None, "NONE")
   )
   ```
3. **Read endpoint** returning a month of CTM data in one shot, shaped for the calendar view:
   ```json
   {
     "ctm": { "id": "...", "centroid_id": "...", "track": "...", "month": "..." },
     "days": [
       {
         "date": "2026-03-14",
         "total_sources": 1204,
         "cluster_count": 12,
         "daily_brief": "LLM prose or null",
         "clusters": [
           {
             "id": "...",
             "title": "...",
             "source_count": 80,
             "date_range": ["2026-03-14","2026-03-14"],
             "bucket_key": "MIDEAST-IRAN",
             "has_event_page": true,
             "is_substrate": false
           }
         ]
       }
     ],
     "activity_stripe": [{"date": "2026-03-01", "total_sources": 42}, ...]
   }
   ```
4. Endpoint path: `/api/ctm/:centroid/:track/:month` (existing or new).

### B. Phase 4.5-day (daily brief generator, medium)

1. **New module**: `pipeline/phase_4/generate_daily_brief_4_5d.py`
2. **Input**: (ctm_id, date) + all clusters of that day, with sample titles per cluster.
3. **Prompt**: 200-word max, "summarize the day's strategic news in this CTM/track". English + DE.
4. **Gates before the LLM call**:
   ```
   ctm.title_count >= N (500)
   day_sum_source_count >= M (50)
   day_cluster_count >= J (5)
   ```
5. **Storage**: new table or column
   - Option A: `daily_briefs(ctm_id uuid, date date, brief text, brief_de text, generated_at timestamptz, PRIMARY KEY (ctm_id, date))`
   - Option B: add columns to an existing day-aggregate table if one exists
6. **Daemon wiring**: Slot 4 enrichment calls this for unprocessed (ctm, date) pairs. Fixed cost per rich CTM-month = 31 calls (worst case), usually far fewer after gating.
7. **Replaces**: Phase 4.5a (event summaries) and Phase 4.5b (CTM digests) — both already unplugged in D-058.

### C. Frontend calendar view (largest, React)

1. **Route**: `/c/:centroid/:track/:month` or similar, URL-hashable for deep links to expanded days.
2. **Component tree**:
   - `StickyHeader` (centroid + track + month switcher)
   - `ActivityStripe` (tiny horizontal bar chart, tap to jump)
   - `DayStream` (list of DayCards)
     - `DayCard` (collapsible, sticky header when expanded)
       - `DailyBrief` (prose, shown when present)
       - `ClusterList` (ordered cards)
         - `ClusterCard` (compact: source count, title, tap action)
       - `SubstrateToggle` (volume-gated)
   - `EventDrawer` (inline modal for clusters below K=5 — shows headlines + publishers, no LLM prose)
   - `EventPage` (existing route, used for clusters with K >= 5)
3. **Data source**: single fetch of the endpoint from Workstream A.
4. **Mobile-first CSS**:
   - Single column stream, full width
   - Sticky header with safe-area padding for notches
   - Touch targets >= 44px
   - No hover states; tap-only
5. **State**:
   - URL hash encodes `?day=YYYY-MM-DD` for deep linking
   - Substrate toggle is per-day, not persisted
   - Month switcher navigates to a new route, full page load is fine

## Event page policy

Full event page (title + LLM-prose summary + all headlines + publisher list + DE/EN toggle) exists **only for clusters with source_count >= K (5)**. Below threshold, tapping the cluster card opens an inline drawer showing the list of headlines with publisher + link, plus the mechanical title. No LLM prose for small clusters.

**This clarifies**: we are **not** phasing out event pages entirely. We are gating them by size so the rich presentation is reserved for events that justify the effort. LLM per-event prose (currently Phase 4.5a output) can still be regenerated on-demand for promoted events if desired, but is not produced in bulk.

## Cross-day arcs (v2, not blocking)

When a cluster's dominant entity matches yesterday's biggest cluster, the frontend can render a visual ribbon connecting them (same-anchor highlight on hover or tap). Purely read-time, no backend support needed beyond querying adjacent days. **Defer to v2**; don't block the initial launch.

## Implementation order

Suggested:

1. **Workstream A first** — backend contract is small (~1-2 hours) and can be built while the April reprocess is still running. Delivers a testable endpoint against the existing v3.0.1 data.
2. **Workstream C with stub daily briefs** — frontend can be built and shipped showing cluster cards only, no daily prose. Ship as soon as it reads from A.
3. **Workstream B last** — daily prose generation added after the frontend is live and usable. It becomes an enhancement, not a blocker.

Alternative: B first (if reprocess is still running and LLM time is "free" parallel work), then A+C together. Less time-to-first-screen, more total throughput.

## What this replaces

| kill | replace with |
|---|---|
| Family-centric event list | Day stream with per-day clusters |
| CTM summary text | Stripe + expanded day + daily brief |
| Phase 4.5a event summaries (bulk) | Daily brief + on-demand event prose |
| Phase 4.5b CTM digests | Daily brief (accumulates to same effect) |
| Hover tooltips | Tap interactions only |
| Desktop-only layout | Mobile-first responsive |

Families table remains in DB (schema stability) but is no longer rendered. It can be dropped in a later cleanup pass.

---

## Tracking

- Asana tickets: TBD
- Branch: TBD (new branch off main once reprocess + sync-back are done)
- Target: frontend live after April reprocess completes
