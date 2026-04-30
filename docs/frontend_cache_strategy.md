# Frontend Cache Strategy

**Last updated:** 2026-04-30

The frontend serves traffic from a Render web service capped at 512 MB
RAM. Caching strategy is shaped by that constraint as much as by perf
goals. This doc is the canonical reference for which routes cache
where, why, and how to invalidate.

---

## The two cache layers

### 1. Page-level ISR cache (Next.js)

Each `page.tsx` declares one of:

- `export const revalidate = N` — Next caches the rendered HTML +
  RSC payload for N seconds; subsequent visitors get the cache. After
  N seconds the next visitor pays SSR cost and refills the cache.
- `export const dynamic = 'force-dynamic'` — no HTML cache; SSR every
  request.

The HTML cache is **per-process and per-dynamic-param-combination**.
A route like `/c/[id]/t/[track]/[date]` with N centroids × M tracks ×
D days × L locales potentially holds N×M×D×L cached entries
simultaneously. This is the OOM trap (see "What broke on 2026-04-29"
below).

**Hard cap:** `cacheMaxMemorySize: 80 * 1024 * 1024` in
`next.config.js`. Next LRU-evicts the in-process ISR cache when full.
This is belt-and-suspenders; the per-route choices below should keep
the cache well under 80 MB on their own.

### 2. Query-level memoisation (`apps/frontend/lib/cache.ts`)

`cached(key, ttlSeconds, fn)` is a per-process `Map` wrapping a
Postgres query. Bounded at 500 entries with lazy LRU-style eviction.
This layer is independent of the page-level cache — even
`force-dynamic` pages benefit, because their underlying queries get
memoised.

This is what makes `force-dynamic` viable for high-traffic dynamic
routes: the React tree re-renders per request, but the DB calls hit
warm memory.

---

## The sizing rule (the big lesson from 2026-04-29)

> **Page-level ISR is for flat routes only. Dynamic-param routes
> default to `force-dynamic` and rely on query-level memoisation.**

| Route shape | Default | Why |
|---|---|---|
| Flat (`/`, `/trending`, `/sources`) | `revalidate = 21600` | 1-2 cache entries × locales = trivial footprint. Big perf win. |
| Dynamic-param, small space (≤ ~750 entries × 6h TTL) | `revalidate = 1800` to `21600` | Footprint < 80 MB, OK with the cap. |
| Dynamic-param, large space (events, narratives detail, etc.) | `force-dynamic` | Bot crawlers can fill the cache to OOM in 30-50 min on a 512 MB instance. |
| Heavy one-shot generators (sitemaps) | `revalidate = false` + cron | Inline regeneration of multi-MB strings during a user request is an OOM trigger. |

---

## What's cached today

### Page-level ISR

| Route | TTL | Why |
|---|---|---|
| `/` (home) | 21600 (6h) | Flat. 2 entries (one per locale). |
| `/trending` | 21600 | Flat. 2 entries. |
| `/sources` (index) | 21600 | Flat. 2 entries. |
| `/search` | 21600 | Flat (query in searchParams, not in path). 2 entries. |
| `/narratives` | 21600 | Flat. 2 entries. |
| `/narratives/map` | 21600 | Flat. 2 entries. |
| `/epics` | 21600 | Flat. 2 entries. |
| `/about`, `/faq`, `/methodology`, `/pricing`, `/privacy`, `/terms`, `/known-issues` | 86400 (24h) | Static content. |
| `/c/[centroid_key]` | 1800 (30 min) | ~750 combos (75 × 5mo × 2). 30 min for freshness — this page renders live "active narratives" + theme chips + top events; 6h staleness would show during an active news day. |
| `/sources/[slug]` | 21600 | ~414 combos (207 × 2). Stance content updates monthly. 6h fine. |
| `/sources/[slug]/[month]` | 21600 | ~2,070 combos. Same content cadence as outlet landing. |

### `force-dynamic` (no HTML cache, query memoisation only)

| Route | Reason |
|---|---|
| `/events/[event_id]` | ~9,200 combos (4,606 events × 2 locales). Cache-fill OOM risk under bot crawl. |
| `/narratives/[id]` | ~520 combos. Reverted 2026-04-30 after OOMs. |
| `/narratives/meta/[id]` | ~18 combos. Small but reverted alongside its peers for consistency. |
| `/epics/[slug]` | ~40 combos. Same. |
| `/region/[region_key]` | ~14 combos. Same. |
| `/c/[id]/t/[track]` | ~3,000 combos. Cache-fill OOM risk. |
| `/c/[id]/t/[track]/[date]` | Tens of thousands of combos (75 × 4 × ~150 days × 2). Worst offender by 10×. |
| `/profile`, `/auth/...`, `/analysis/user/[id]`, `/analysis/comparative/...`, `/signals/...` | Per-user, query-driven, or per-input. |

### Cron-driven static (no inline regeneration)

| Route | TTL | Refresh |
|---|---|---|
| `/sitemap.xml` | `false` (cached forever) | Daily 04:00 UTC via `.github/workflows/revalidate-sitemap.yml` → `/api/cron/revalidate-sitemap` |
| `/sitemap-days.xml` | `false` | Same cron call (revalidates both paths) |
| `/sitemap-index.xml` | `false` | Static content, only changes when we add a new sitemap |

---

## Manual invalidation

### Outlet pages (after stance scoring, MV refresh, manual data fix)

```
POST /api/admin/revalidate-outlets
  Header: x-revalidate-token: $REVALIDATE_API_KEY
  Body:   optional { "slug": "cnn" }
```

Drops every outlet-scoped in-memory cache prefix AND calls
`revalidatePath('/[locale]/sources/[slug]', 'page')` plus the
`/[month]` variant.

```
curl -X POST https://www.worldbrief.info/api/admin/revalidate-outlets \
     -H "x-revalidate-token: $REVALIDATE_API_KEY"
```

### Sitemaps (forced fresh regeneration)

```
POST /api/cron/revalidate-sitemap
  Header: x-revalidate-token: $REVALIDATE_API_KEY
```

Calls `revalidatePath` on both `/sitemap.xml` and `/sitemap-days.xml`.
The next request to either URL gets a freshly-generated response.

The daily GitHub Actions cron does this automatically; manual invocation
is only useful if you've changed sitemap-relevant data and want to push
it out before the next 04:00 UTC.

### Required env var

`REVALIDATE_API_KEY` — strong random string. Set on Render (frontend
web service) and as a GitHub repo secret of the same name. Same key
gates both endpoints. Rotate by setting a new value in both places
simultaneously.

---

## What broke on 2026-04-29 (the source of the sizing rule)

Background: a single commit (`a34cf63`) extended `revalidate = 21600`
to 12 routes including dynamic-param ones (`/events/[id]`,
`/narratives/[id]`, etc.). Within hours, Render's 512 MB instance was
OOMing every 30-50 minutes overnight under bot-crawl traffic
(~12,500 requests over 10 hours, mostly Googlebot et al).

Two distinct OOM signatures appeared in logs:

| Signature | Cause | Fix |
|---|---|---|
| `String::SlowFlatten` → `EncodeUtf8String` | Single huge response — sitemap regenerating ~10K URL entries inline during a request | Move sitemap to `revalidate = false` + cron-driven `revalidatePath` (`df17af6`, `774fedd`) |
| Render "Ran out of memory (used over 512MB)", sawtooth memory pattern | Cumulative ISR cache fill from bot walking dynamic-param URLs | Revert dynamic-param routes to `force-dynamic` (`62a21fe`, `d8414c4`); add `cacheMaxMemorySize: 80MB` cap |

Both fixes shipped 2026-04-30. Memory should plateau around 250-350 MB
under steady state instead of climbing to 512.

If OOMs return after this, the conclusion is "512 MB is too small for
this app" — bump Render to Standard ($15-20/mo extra, 4× headroom)
rather than further cache surgery.

---

## When adding a new page

1. **Is it flat or dynamic-param?**
   - Flat → `revalidate = 21600` (or longer for static-static). Done.
   - Dynamic-param → continue.

2. **How big is the param space?** Multiply combinations × locales.
   - < ~750 → `revalidate = 1800` to `3600` is OK. Verify cache footprint
     is well under 80 MB (rough: combos × 100-300 KB).
   - > ~750 → default to `dynamic = 'force-dynamic'`. Trust query-level
     memoisation. Only revisit if profiling shows actual user-facing
     slowness on this specific route.

3. **Is regeneration cost itself heavy?** (Sitemaps, large RSS,
   bulk exports.)
   - Yes → `revalidate = false` + cron-driven `revalidatePath` from
     GitHub Actions. Don't let it regenerate during a user request.

4. **Does it depend on data the daemon updates?**
   - Yes → consider whether it warrants a cache prefix in
     `/api/admin/revalidate-outlets` or a similar endpoint, so the
     pipeline can push fresh data without waiting for TTL.

---

## See also

- `docs/context/30_DecisionLog.yml` — D-066 (SEO/sitemap), D-072
  (outlet stance system).
- `~/.claude/projects/.../memory/feedback_isr_cache_sizing.md` — the
  rule, distilled for future Claude sessions.
- `apps/frontend/next.config.js` — `cacheMaxMemorySize` setting.
- `.github/workflows/revalidate-sitemap.yml` — daily sitemap cron.
- Asana 1214347903349737 — outlet pages cache reference (mirrors
  this doc's outlet section).
