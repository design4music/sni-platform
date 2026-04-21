# SEO Page Inventory

**Date**: 2026-04-21
**Purpose**: Rough inventory of unique, search-relevant pages on worldbrief.info to inform SEO phase 2 planning.

---

## Current page counts (2026-04-21, Render)

Counts are of **canonical** content URLs. Each is published in two locales (EN + DE), so the effective indexable count doubles.

| Page type | Canonicals | × 2 locales | Route pattern |
|---|---:|---:|---|
| Event detail (≥5 sources) | 5,883 | **11,766** | `/events/[event_id]` |
| Track-month (CTM) pages | 1,132 | **2,264** | `/c/[centroid]/t/[track]/calendar` |
| Outlet / source profiles | 207 | **414** | `/sources/[feed_name]` |
| Strategic narratives | 260 | **520** | `/narratives/[id]` |
| Centroid overview | 75 | **150** | `/c/[centroid]` |
| Cross-country epics | 20 | **40** | `/epics/[id]` |
| Regions | ~6 | 12 | `/region/[id]` |
| Home / trending / signals / etc. | ~15 | ~30 | various |
| **Total indexable** | **~7,600** | **~15,000** | |

Event detail pages dominate at **~78%** of the total.

## Growth projection

Current ingestion rate produces roughly **~1,500 event pages per month** (promoted events with ≥5 sources):

| Date | Expected total (EN+DE) |
|---|---:|
| 2026-04-21 (today) | ~15,000 |
| End of May 2026 | ~18,000 |
| End of July 2026 | ~22,000 |
| End of 2026 | ~30,000+ |

Narratives, outlets, and centroids grow slowly (curated additions). Epics grow ~monthly. Growth is therefore driven almost entirely by events.

## Month-variant URLs (not counted above)

The canonical centroid and track-month URLs have no month in the path; month is a query parameter (`?month=YYYY-MM`). Per `apps/frontend/app/[locale]/c/[centroid_key]/page.tsx` (`export const revalidate = 1800`), the canonical is monthless and Google should see one URL per centroid regardless of month.

If in phase 2 we decide to expose month-variants as distinct indexable URLs (e.g. `/c/[centroid]/[YYYY-MM]`), this would multiply centroid + track-month pages by ~4 months already covered → adds ~7K pages immediately and grows by ~(centroid × 2 × 1) = ~150 per month thereafter.

## What's NOT yet in the count

- Narrative event-list subpages (`/narratives/[id]/events` if we expose)
- Signal detail pages (`/signals/[type]/[value]`) — currently exist; not inventoried here
- User analysis pages (`/analysis/user/[id]`) — gated, not public / not SEO-relevant
- Legacy `/families/[id]` — redirected to `/trending` (D-064), not counted

---

## Data source

Counts derived from live Render DB on 2026-04-21:

```sql
-- Events ≥5 sources (visible event-detail pages)
SELECT COUNT(*) FROM events_v3
 WHERE is_promoted = true AND merged_into IS NULL AND source_batch_count >= 5;
-- 5,883

-- Track-month pages (CTM with coverage)
SELECT COUNT(*) FROM ctm WHERE title_count > 0;
-- 1,132

-- Active outlets
SELECT COUNT(*) FROM feeds WHERE is_active = true;
-- 207

-- Strategic narratives (total catalog)
SELECT COUNT(*) FROM strategic_narratives;
-- 260

-- Active centroids
SELECT COUNT(*) FROM centroids_v3 WHERE is_active = true;
-- 75

-- Cross-country epics
SELECT COUNT(*) FROM epics;
-- 20
```

---

## Relationship to SEO phase 1

Phase 1 (dd20874) shipped: unique per-page metadata, hreflang, sitemap, JSON-LD on centroid/event/narrative/region pages, and merged `/calendar` into the track page. That work made the ~15K pages **indexable**. Phase 2 is about **rank-worthiness** — see the Asana ticket that references this doc.
