# SEO Phase 2 — Document 1: Content Inventory

**Date**: 2026-05-12
**Source**: routes enumerated from `apps/frontend/app/[locale]/**/page.tsx`;
counts from local PostgreSQL (mirrors Render, both have Jan–Apr 2026 frozen + May 2026 in-flight).
**Excluded from audit scope** (work-in-progress): friction-nodes, narratives v1 + v2,
analysis (comparative + user), epics.

## Top-line numbers (live URLs from production sitemap, 2026-05-12)

- `sitemap.xml`: **8,124** URLs, 3.65 MB, TTFB 119 ms
- `sitemap-days.xml`: **8,508** URLs, 5.12 MB, TTFB 137 ms
- `sitemap-index.xml` (canonical entry in robots.txt): points to both
- **Total advertised**: 16,632 URLs (well under Google's 50K-URL / 50MB cap per sitemap)
- Google reportedly has ~9,000 pages indexed → close to `sitemap.xml` count;
  `sitemap-days.xml` appears under-indexed.

## Template inventory

Counts are unique URL combinations. EN+DE locale variants are inline `xhtml:link
rel="alternate"` within each `<url>` entry (not separate sitemap rows).

| # | Template | Route pattern | DB / source | Live page count | In sitemap | Notes |
|---|---|---|---|---|---|---|
| **In scope — indexable** |
| 1 | Home | `/` | static | 1 | ✓ static block | Hero + map + region cards |
| 2 | Region | `/region/[region_key]` | `REGIONS` const (7 keys) | 6 indexable (EUROPE, ASIA, AFRICA, AMERICAS, OCEANIA, MIDEAST) — INT-ORGS excluded by sitemap loop | ✓ | Hardcoded keys; lowercased path |
| 3 | Centroid landing | `/c/[centroid_key]` | `centroids_v3` (active) | **75** | ✓ | Calendar hero + 2×2 track cards + active narratives sidebar |
| 4 | Centroid About | `/c/[centroid_key]/about` | `centroids_v3.profile_json` | **75** | **✗ NOT IN SITEMAP** | Background brief; curated content; high evergreen SEO value |
| 5 | Centroid + Track | `/c/[centroid_key]/t/[track_key]` | `ctm` (centroid×track) | **296** | ✓ | Calendar view, month nav |
| 6 | Centroid + Track + Day | `/c/[centroid_key]/t/[track_key]/[date]` | `daily_briefs` (date×ctm_id) | **6,092** | ✓ via `sitemap-days.xml` | Indexable only if `daily_brief` non-null (else noindex). Per-track breakdown: politics 2,097 / economy 1,722 / security 1,349 / society 924. |
| 7 | Event detail | `/events/[event_id]` | `events_v3` (promoted, ≥5 sources, not catchall) | **4,606** | ✓ (capped at remaining sitemap budget) | NewsArticle JSON-LD + saga linking |
| 8 | Outlet landing | `/sources/[slug]` | `feeds` (active) | **207** | ✓ | Stance heatmap, volume chart |
| 9 | Outlet month | `/sources/[slug]/[month]` | `outlet_entity_stance ∪ mv_publisher_stats_monthly` | **672** | ✓ | Auto-noindex for months without stance data (sitemap still lists them). |
| 10 | Sources index | `/sources` | aggregate | 1 | ✓ static block | Grouped by region+country |
| 11 | Trending live | `/trending` | `mv_global_month_view` (current) | 1 | ✓ static block | Self-canonicalises live month to `/trending` |
| 12 | Trending past month | `/trending?month=YYYY-MM` | past months from `mv_global_month_view` | ~3 past months | ✓ | Article tone, self-referential canonical |
| 13 | Trending archive day | `/trending?month=YYYY-MM&day=YYYY-MM-DD` | per-day activity in past months | ~80–100 day URLs | ✓ | One per active day in archive months |
| 14 | Signals index | `/signals` | aggregate | 1 | ✓ static block | Co-occurrence graph |
| 15 | Signal category | `/signals/[type]` | hardcoded 4 types (sitemap lists 7) | 4 valid (persons/orgs/places/named_events) — **3 stale slugs in sitemap** (commodities/policies/systems no longer in `VALID_TYPES`) | ✓ static block | |
| 16 | Signal value | `/signals/[type]/[value]` | per-value (no listing) | dynamic, unindexed | ✗ not in sitemap | Could add top-N per category |
| **In scope — static/utility** |
| 17 | About | `/about` | i18n | 1 | ✓ | |
| 18 | Methodology | `/methodology` | i18n | 1 | ✓ | |
| 19 | FAQ | `/faq` | i18n | 1 | ✓ | |
| 20 | Pricing | `/pricing` | i18n | 1 | ✓ | |
| 21 | Privacy | `/privacy` | i18n | 1 | ✓ | |
| 22 | Terms | `/terms` | i18n | 1 | ✓ | |
| 23 | Known issues | `/known-issues` | i18n | 1 | ✓ | |
| **Auth / private (noindex)** |
| 24 | Sign in | `/auth/signin` | client | 1 | ✗ | `noindex,nofollow` via `[locale]/auth/layout.tsx` ✓ |
| 25 | Sign up | `/auth/signup` | client | 1 | ✗ | `noindex,nofollow` ✓ |
| 26 | Profile | `/profile` | session | 1 | ✗ | `noindex,nofollow` ✓ |
| 27 | Search results | `/search?q=…` | dynamic | ∞ | ✗ | `noindex,follow` ✓ |
| **Excluded from this phase (WIP)** |
| – | Friction node | `/friction-nodes/[slug]` | `friction_nodes` | 7 (5 atomic + 1 theater + cluster pages) | ✗ — `IS_SHADOW=true` keeps it noindex | Footer link only, awaiting promotion |
| – | Strategic narrative | `/narratives/[id]` | `strategic_narratives` | 260 | ✓ in sitemap | **Will be redesigned (v2)** — exclude from this audit |
| – | Meta narrative | `/narratives/meta/[id]` | `meta_narratives` | 9 | ✓ in sitemap | Same |
| – | Narratives index | `/narratives` | aggregate | 1 | ✓ | Same |
| – | Narrative map | `/narratives/map` | aggregate | 1 | ✓ | Same |
| – | Epic detail | `/epics/[slug]` | `epics` | 20 | ✓ in sitemap | **Excluded** per user direction |
| – | Epics index | `/epics` | aggregate | 1 | ✓ | Excluded |
| – | Analysis comparative | `/analysis/comparative/[entity_type]/[entity_id]` | session-gated | dynamic | ✗ | Depends on legacy narratives; excluded |
| – | Analysis user | `/analysis/user/[id]` | user-generated | dynamic | ✗ | Excluded |

## Indexable surface totals (in-scope only, excluding WIP)

| Template family | Live URLs | EN+DE total (×2) | Notes |
|---|---|---|---|
| Country pages (centroid + about + track) | 75 + 75 + 296 = **446** | 892 | About pages currently not in sitemap |
| Day-canonical pages (track-day) | **6,092** | 12,184 | Largest single template; only ~70% have a daily brief that qualifies for indexing |
| Event detail | **4,606** | 9,212 | Capped by ≥5 source threshold |
| Outlet + outlet-month | 207 + 672 = **879** | 1,758 | |
| Static (home + region + sources + signals + trending live + 7 utility) | 14 + 6 + 1 + 1 + 1 + 7 = **30** | 60 | |
| Trending past archive | ~100 | 200 | Past month + per-day URLs |
| **Total in-scope** | **~12,150** | **~24,300** | |

If we add the WIP scope back: + ~270 narrative-family pages and ~20 epics. Total
including WIP: ~12,400 unique URLs / ~24,800 with locale alternates. Production
sitemap counts (8,124 + 8,508 = 16,632) sit below that because the day sitemap
caps per locale-set behavior is slightly different from this back-of-envelope
sum; reconciliation in `03_sitemap_indexability.md`.

## What's *not* in any sitemap (in-scope gaps)

| URL | Why it should be there |
|---|---|
| `/c/[centroid_key]/about` × 75 | Curated background; high-quality evergreen content; canonical+hreflang+OG already wired; only the sitemap loop omits them. |
| Signal value pages worth indexing (top-N per category) | High informational value (e.g. "Putin", "Macron", "OPEC"); currently dynamic with no listing. |

## Auth/session/dynamic pages — correctly excluded

- `/auth/signin`, `/auth/signup`, `/profile`, `/search?q=…`, `/analysis/*` — all
  carry `noindex` and are not in any sitemap. ✓

## DB query reference

Counts above come from these queries (run 2026-05-12 against local DB which
mirrors Render Jan–Apr frozen state):

```sql
-- centroids
SELECT count(*) FROM centroids_v3 WHERE is_active = true;             -- 75
-- centroid + track combinations
SELECT count(*) FROM (SELECT DISTINCT centroid_id, track FROM ctm)x;  -- 296
-- track-day pages (indexable count = same as daily_briefs rows)
SELECT count(*) FROM daily_briefs;                                    -- 6092
-- events with dedicated page
SELECT count(*) FROM events_v3
 WHERE is_promoted=true AND merged_into IS NULL
   AND is_catchall=false AND source_batch_count >= 5;                 -- 4606
-- outlets
SELECT count(*) FROM feeds WHERE is_active=true AND slug IS NOT NULL; -- 207
-- outlet-month combos
SELECT count(*) FROM (
  SELECT f.slug, d.month FROM feeds f JOIN (
    SELECT outlet_name AS feed_name, month FROM outlet_entity_stance
    UNION SELECT feed_name, month FROM mv_publisher_stats_monthly
  ) d ON d.feed_name = f.name
  WHERE f.is_active=true AND f.slug IS NOT NULL
) x;                                                                  -- 672
```

## Files reviewed for this inventory

- `apps/frontend/app/[locale]/**/page.tsx` (all 32 page files)
- `apps/frontend/app/sitemap.ts` (structural sitemap)
- `apps/frontend/app/sitemap-days.xml/route.ts` (day-canonical sitemap)
- `apps/frontend/app/sitemap-index.xml/route.ts` (sitemap index)
- `apps/frontend/app/robots.ts`
- `apps/frontend/middleware.ts`
- `apps/frontend/lib/seo.ts` (metadata + JSON-LD helpers)
