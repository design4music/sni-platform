# WorldBrief SEO Strategy
**Last updated**: 2026-06-30
**Author**: compiled from docs/seo/* Phase 2 audit + session history

---

## 1. What We Have Built (SEO Infrastructure)

### 1.1 Technical foundation — completed

Everything below is live in production as of June 2026.

**Sitemap architecture (DB-backed)**
The old Next.js `sitemap.ts` approach caused 2 months of GSC "Couldn't fetch"
errors due to cold-start race conditions and missing `charset=utf-8`. Replaced
with pre-generated XML blobs stored in the `sitemap_cache` table and served via
fast PK lookups. A GitHub Actions cron regenerates the cache daily at 04:00 UTC.

| Sitemap file | Content | URL count | Cache key |
|---|---|---|---|
| `/sitemap-index.xml` | Index pointing to 6 sub-sitemaps | — | dynamic from DB |
| `/sitemap-geo.xml` | Regions, centroids, centroid/about | 312 EN+DE = 624 | `geo` |
| `/sitemap-sources.xml` | Outlet landings + outlet-month pages | ~880 EN+DE = 1,760 | `sources` |
| `/sitemap-static.xml` | Home, about, methodology, pricing, faq, terms, privacy, known-issues | 16 EN+DE = 32 | `static` |
| `/sitemaps/daily-YYYY-MM.xml` | Track-day daily-brief pages, split by month | ~8,500 total (×2 locales) | `daily-YYYY-MM` |
| `/sitemaps/events-YYYY-MM.xml` | Events with prose (`summary IS NOT NULL`) | ~4,600 total (×2 locales) | `events-YYYY-MM` |
| `/sitemap-news.xml` | Last 48h daily briefs in Google News format (`<news:news>`) | ~20–50 | dynamic |

Each `<url>` entry includes:
- `<lastmod>` where applicable (brief.generated_at / event.last_active)
- `<xhtml:link rel="alternate" hreflang="en" />` + `hreflang="de"` + `hreflang="x-default"`
- `<changefreq>` and `<priority>` tuned per content type

**Metadata library** (`apps/frontend/lib/seo.ts`)
- `buildPageMetadata()` — canonical + hreflang (en/de/x-default) + OG + Twitter
- `buildAlternates()` — locale-aware canonical/hreflang builder
- `truncateDescription()` — 160-char capping with word boundaries
- JSON-LD builders: `newsArticleJsonLd`, `breadcrumbList`, `articleJsonLd`, `websiteJsonLd`
- `formatCount()` / `joinList()` — locale-aware string helpers

**Structured data (JSON-LD)**
- `WebSite` + `SearchAction` on every page (root layout)
- `Person` (Maksim Micheliov, LinkedIn + /about sameAs) on every page (root layout) — primary E-E-A-T signal
- `NewsArticle` + `BreadcrumbList` on track-day pages (the highest-volume template)
- `NewsArticle` + `BreadcrumbList` on event-detail pages
- `author: Person` block inside all `NewsArticle` schemas
- `Organization` publisher block
- Visible byline "by WorldBrief & Maksim Micheliov | AI-generated summary" on track-day (when brief exists), event (when summary exists), and centroid about pages (when profile_json exists)

**Indexability controls**
- `noindex, nofollow` on auth/profile pages
- `noindex, follow` on search results
- `noindex, follow` on event pages where `summary IS NULL` (thin-content guard)
- CTM track overview (`/c/X/t/Y`) redirects 307 to most recent daily brief date,
  so crawlers land on the canonical dated page instead of the calendar shell

**Robots.txt**
```
Allow: /
Disallow: /api/
Sitemap: https://www.worldbrief.info/sitemap-index.xml
```

---

### 1.2 What was fixed vs. Phase 2 audit

The Phase 2 audit (docs/seo/ folder, dated 2026-05-12) catalogued 10 issues.
Status as of 2026-06-29:

| Issue | Description | Status |
|---|---|---|
| S-1 | sitemap.xml no charset | **FIXED** — replaced with DB-backed route handlers |
| S-2 | sitemap.xml uncached at origin | **FIXED** — `s-maxage=86400` on all sitemap routes |
| S-3 | Missing `hreflang="en"` self-ref in sitemap | **FIXED** — new cron generates proper triplet per URL |
| S-4 | 3 dead `/signals/*` URLs in sitemap | **NOT YET** — stale type slugs still in old sitemap.ts (now superseded; verify new sitemap doesn't include them) |
| S-5 | `/c/[centroid]/about` not in sitemap | **FIXED** — `generateGeo()` in cron includes `/c/${id}/about` for every centroid |
| M-1 | `/sources/[slug]` double `\| WorldBrief` in title | **FIXED** — 2026-06-30 |
| M-2 | Signals pages missing canonical + hreflang | **DEFERRED** — signals rework is parked |
| M-4 | `/c/[centroid]/about` not internally linked | **NOT YET** — centroid landing sidebar does not link to /about |
| M-5 | Templated descriptions on 207 outlet pages | **FIXED** — LLM-generated EN+DE descriptions in `feeds.description` / `feeds.description_de` |
| M-6 | No `og:image` site-wide | **NOT YET** — user task created |
| E-E-A-T | Person JSON-LD, author field, visible byline | **DONE** — 2026-06-30 |
| E-4 | Google News sitemap | **DONE** — `/sitemap-news.xml` live 2026-06-30 |

---

## 2. Content Asset Inventory

### 2.1 Indexable URL surface (June 2026)

| Template | Live URLs (EN canonical) | Sitemap | Traffic opportunity |
|---|---|---|---|
| Track-day (`/c/[c]/t/[t]/[date]`) | ~6,100+ | yes | **Highest** — unique per country×track×date |
| Event detail (`/events/[id]`) | ~4,600+ with prose | yes | High — cross-source aggregation angle |
| Outlet landing (`/sources/[slug]`) | 207 | yes | Medium — "media bias" queries |
| Outlet month (`/sources/[slug]/[month]`) | ~700+ | yes | Medium — monthly coverage queries |
| Centroid about (`/c/[c]/about`) | 75 | **yes (fixed)** | Medium — evergreen country profiles |
| Centroid landing (`/c/[c]`) | 75 | yes | Low-medium (compete with BBC/Reuters) |
| Centroid track (`/c/[c]/t/[t]`) | ~296 | yes | Medium — monthly topic digests |
| Region pages | 6 | yes | Low |
| Trending archive | ~100 | yes | Low-medium — "world news on [date]" |
| Static utility | 8 | yes | Brand only |
| **Total in-scope** | **~12,100+** | — | — |

Growth rate: pipeline adds ~300–400 new day-canonical pages per month (new daily
briefs across ~75 centroids × 4 tracks, not all active). Events accumulate faster
once prose generation is caught up. At current tempo: **~30,000 indexed URLs
by end of 2026** with no new templates built.

### 2.2 Templates not yet building SEO value

| Template | Status | Blocker |
|---|---|---|
| Friction nodes (`/friction-nodes/[slug]`) | `IS_SHADOW=true`, noindex | Awaiting editorial promotion decision |
| Strategic narratives (`/narratives/[id]`) | In sitemap but v2 redesign planned | Hold until v2 ships |
| Signal value pages (`/signals/[type]/[value]`) | Not in sitemap, no canonical | Needs signals-family rework spec |
| Per-outlet × entity sub-pages | Does not exist | Future work |

---

## 3. Keyword Strategy

### 3.1 Where WorldBrief can realistically win

**Channel A — "Country X on Date Y" (6,100+ pages)**
No major competitor has indexed per-country-per-date per-track landing pages.
Reuters/BBC/AP archive by article, not by structured day. Query patterns:
- "United States economy news June 15 2026"
- "Iran security news April 2026"
- "What happened in Germany on [date]"
- German: "Iran Nachrichten 15. Juni 2026"

This is our most defensible moat. The content is genuinely unique (curated daily
brief), structured data is in place (NewsArticle + BreadcrumbList), and 6,100+
URLs means we catch a vast long-tail even with modest per-page traffic.

**Channel B — "Country profile / geopolitical overview" (75 pages)**
`/c/[centroid]/about` pages are curated, multilingual, evergreen.
Query patterns:
- "Iran political profile 2026"
- "Saudi Arabia geopolitical position"
- "Why is Turkey strategically important"
- German: "Türkei geopolitische Lage"

These pages are now in the sitemap (fixed June 2026). They should rank within
weeks for low-competition informational queries. Not competing with Reuters; these
are "explainer" and "profile" intent, closer to Wikipedia than news.

**Channel C — "Outlet bias / coverage analysis" (207 + 700+ pages)**
AllSides and Ground News dominate generic "media bias" head queries with
human-rated left/center/right ratings. Our angle is different and un-replicated:
automated per-entity per-month stance ("How does Al Jazeera cover Iran in June
2026?"). Query patterns:
- "Reuters bias"
- "Al Jazeera coverage of Iran"
- "Is RT propaganda"
- "[Outlet] editorial stance [country]"

Currently under-performing because of the title bug (M-1) and templated
descriptions. Fix M-1 + add data-driven descriptions = immediate lift on these.

**Channel D — "World news on [date]" (~100 pages)**
`/trending?month=YYYY-MM&day=YYYY-MM-DD` trending archive day pages are unique
daily snapshots with rank-change signals and article-type OG metadata.
Query patterns:
- "Top world stories April 12 2026"
- "What happened globally on [date]"

Volume is modest but zero competition for exact-date queries.

**Channel E — "Person / leader in the news" (not yet indexed)**
`/signals/persons/[name]` pages exist but are broken (no canonical, not in
sitemap). "Putin news", "Trump foreign policy", "Xi Jinping coverage" are
high-volume but highly competitive. These pages become a meaningful channel only
after the signals family is reworked. Defer.

### 3.2 German-locale opportunity

We ship full EN+DE alternates via hreflang. DE-specific notes:
- German geopolitical search volume is substantial (e.g., "Iran Krieg", "Russland
  Ukraine Waffenruhe", "Geopolitik 2026")
- Our DE content quality varies: day-canonical pages have `summary_de` when
  lazily translated; some pages fall back to the translation banner
- Opportunity: push DE translation coverage upstream so more pages have filled
  `summary_de` fields — each filled DE page is an additional SERP appearance in
  German search
- DACH-priority centroid ordering on the DE home page (Germany, EU, Russia, USA,
  China, Iran) would help DE user satisfaction + engagement signals

### 3.3 2026 search trends mapping to our content

| Hot topic | Our page | Competitive position |
|---|---|---|
| Iran nuclear program | `/c/MIDEAST-IRAN/t/geo_security` + day pages | Good — deep coverage |
| Russia–Ukraine ceasefire/peace | `/c/EUROPE-UKRAINE`, `/c/EUROPE-RUSSIA` | OK — compete on long-tail dates |
| US–China trade / Trump foreign policy | `/c/AMERICAS-USA`, `/c/ASIA-CHINA` | Good on day-canonical |
| Gaza / Israel–Hamas | `/c/MIDEAST-ISRAEL`, `/c/MIDEAST-PALESTINE` | Good on day-canonical |
| EU–China trade frictions | `/c/EUROPE-EU` | Moderate |
| Energy / oil prices | `geo_economy` track | Mechanical; no dedicated commodity pages |
| Specific leaders (Putin, Trump, Xi) | `/signals/persons/[name]` | Broken — fix deferred |
| Media bias / outlet comparison | `/sources/[slug]` | Under-performing due to M-1 bug |

### 3.4 Information Gain — where we over-index

Google's 2026 algorithm weights *Information Gain*: does the page add something
a user can't get from existing top results?

- **Cross-source aggregation per event** — competitors show one source per article;
  we show N sources with a deduplicated synthesis. Unique.
- **Per-day per-country digests** — no competitor has this structure.
- **Outlet stance per entity per month** — AllSides/Ground News do outlet-level
  only; we do entity-level per month. Unique.

Where we're weaker on Information Gain:
- Centroid landings competing on "[country] news" — Reuters/BBC have more
  original reporting.
- Event detail pages — cross-source view is valuable, but the prose is synthesized,
  not original reporting.

---

## 4. Realistic Traffic Goals

### 4.1 Starting point assumptions (June 2026)

- Google is currently crawling and indexing the new sitemap structure
  (GSC showing 312/2,036+ URLs discovered, monthly sitemaps being queued)
- Organic traffic is near-zero due to 2-month GSC "Couldn't fetch" period
- No backlink profile to speak of (new domain)
- Bilingual content (EN/DE) with growing page count

### 4.2 Traffic scenarios

**Scenario 1 — Conservative (do nothing beyond current fixes)**
Timeline: 3–6 months
- Google fully crawls the 12,000+ page sitemap
- Day-canonical pages pick up long-tail "[country] [track] news [date]" queries
- Outlet pages remain below potential (M-1 unfixed)
- No new templates or E-E-A-T investment
**Expected**: 800–2,500 organic sessions/month by end of 2026

**Scenario 2 — Base case (fix outstanding bugs + execute bundles 1–5 from audit)**
Timeline: 6–9 months with consistent execution
- M-1 title bug fixed → outlet pages immediately more clickable
- Signals pages fixed → some person/entity traffic
- Outlet descriptions data-driven → differentiated CTR
- E-E-A-T basics (author schema, byline footer)
- Static OG image for better social unfurls
**Expected**: 5,000–15,000 organic sessions/month by March 2027

**Scenario 3 — Aggressive (base + Google News + new templates)**
Timeline: 9–18 months
- Google News Publisher Center submission and approval
  (requires: editorial standards page, predictable publication cadence,
  author bylines — all achievable)
- Google News inclusion alone can 10–20x a news site's organic traffic
- Person/entity signal pages indexed and in sitemap
- Per-outlet × entity sub-pages ("How does Reuters cover China?")
- Bilateral/topic cross-pages (coupling to friction node work)
**Expected**: 30,000–100,000 organic sessions/month by end of 2027

### 4.3 What determines which scenario materializes

| Factor | Impact | Controllable? |
|---|---|---|
| Speed of Google indexation | 2–4 months to fully index 12K pages | Partially — sitemap quality helps |
| Core Web Vitals (LCP, INP, CLS) | Ranking factor; force-dynamic routes need measurement | Yes — audit needed |
| E-E-A-T signals | Growing Google emphasis; single-operator sites can still rank | Yes — author schema, methodology |
| Google News inclusion | Potential 10–20x multiplier | Yes — but takes 6–12 months |
| DE content completeness | Doubles indexed URLs effectively if filled | Yes — translation backfill |
| Backlink acquisition | Core authority signal; hard to fake | Partially — PR, partnerships |
| New template velocity | More unique pages = more long-tail surface | Yes — depends on product roadmap |

The **most realistic target** with consistent but not heroic effort:
**10,000–20,000 organic sessions/month within 12 months** (by July 2027),
driven primarily by the day-canonical channel + repaired outlet pages.

Google News inclusion, if achieved, could push this to 50,000–200,000
sessions/month — but that is a separate multi-month project.

---

## 5. Prioritized Action Plan

### DONE (2026-06-29 – 2026-06-30)

- **A-1** (M-1): Outlet page double title fixed
- **B-1** (M-5): 207 outlet EN+DE descriptions generated via LLM, stored in `feeds.description` / `feeds.description_de`
- **C-1**: `Person` JSON-LD (Maksim Micheliov, LinkedIn sameAs) in root layout
- **C-2**: Visible byline on track-day, event, and centroid-about pages (conditional on prose existing)
- **E-4**: `/sitemap-news.xml` live with `<news:news>` tags for last 48h; added to sitemap index
- **Sitemap URLs**: Monthly sitemaps migrated to path-based `/sitemaps/daily-YYYY-MM.xml`; old query-param URLs 301-redirect
- **Contact email**: `/about` page corrected to `max.micheliov@gmail.com`

### NEXT (open)

**A-3: Add internal link to `/about` from centroid landing** (M-4)
File: `apps/frontend/app/[locale]/c/[centroid_key]/page.tsx`
The about pages are in the sitemap but not internally linked. Add a "Country Profile" or "Background Brief" link in the centroid sidebar.

**B-2: Data-driven region descriptions**
File: `apps/frontend/app/[locale]/region/[region]/page.tsx`
Inject top 3 centroids by current-month article count into the meta description.

**B-3: BreadcrumbList on centroid + track pages**
Track-day pages already have BreadcrumbList. Extend to centroid landing, track landing, outlet landing. Near-zero effort.

**C-3: Methodology page enrichment**
File: `apps/frontend/app/[locale]/methodology/page.tsx`
Add `Article` JSON-LD. Brief pipeline description improves E-E-A-T "trust" surface.

**D-1: Static OG image** (design dependency)
A single 1200×630 branded PNG. Unblocks `twitter:card = summary_large_image` site-wide.

**E-1: Signal value pages — index top-N**
`/signals/persons/[name]`, `/signals/orgs/[name]` etc. Add top entities by coverage threshold to sitemap once signals pages have canonical + hreflang.

**E-2: Per-outlet × entity sub-pages**
"How does Reuters cover Iran?" — new template, no competitor has this with indexed data.

**E-3: Bilateral / topic cross-pages**
`/topic/us-china-trade`, `/topic/iran-nuclear` — couples to friction node work.

**Google News Publisher Center submission** — manual step. Prerequisites complete (E-E-A-T basics done, news sitemap live). Submit now at publishercenter.google.com.

**SEO-aware prose prompts** — tune daily brief + event summary prompts to include the centroid name and date in the first sentence. Improves keyword density on long-tail queries without hurting readability.

---

## 6. Measurement & Monitoring

### 6.1 GSC metrics to track (weekly)

| Metric | Where | What to watch for |
|---|---|---|
| Total indexed pages | Coverage → Valid | Should grow from ~2,400 toward 12,000+ over 3–6 months |
| Monthly sitemap children | Sitemap detail | All 12 monthly sitemaps should turn green within 1–2 weeks |
| Impressions / clicks by page type | Performance → Pages | Day-canonical impressions should start appearing first |
| Top queries | Performance → Queries | Look for "[country] [track] news [date]" patterns |
| Soft-404 / crawl errors | Coverage → Excluded | Should drop once M-2 signals fix lands |

### 6.2 Baseline to capture now

Before any further changes, export the current GSC Performance report (last 3
months) as a baseline. Key dimensions: total impressions, total clicks, avg CTR,
avg position. All future work is measured against this baseline.

### 6.3 Core Web Vitals

The site currently uses `force-dynamic` on all content routes (per ISR cache
memory constraints on Render). This means every request hits the DB. LCP and
INP performance on Render's 512 MB container should be measured formally before
claiming the technical SEO foundation is complete. A Lighthouse run or PageSpeed
Insights check against 3–4 key templates is worth 30 minutes.

---

## 7. What NOT To Do

- **Do not blanket-set revalidate=N on dynamic-param routes.** Render is 512 MB;
  bot crawl fills cache to OOM in 30–50 min. Confirmed incident. Use force-dynamic
  + lib/cache.ts query memoization on dynamic routes.
- **Do not claim "data updates frequently."** WorldBrief ingests every 12h. That's
  the freshness ceiling for every downstream TTL or marketing claim.
- **Do not hardcode vocabulary lists.** Sitemap signal-type lists must stay in sync
  with the actual DB/code enums — the M-3 soft-404 issue was caused by exactly this.
- **Do not buy keyword volume data yet.** Defer Ahrefs/Semrush until the sitemap is
  fully indexed and we have a stable GSC query baseline. Without a baseline, paid
  keyword data has no calibration point.
- **Do not attempt Google News submission before E-E-A-T basics land.** Author
  schema + editorial byline + methodology page enrichment should come first.

---

## 8. Reference Files

| File | Content |
|---|---|
| `docs/seo/01_content_inventory.md` | Full template inventory + DB-backed page counts (2026-05-12) |
| `docs/seo/02_metadata_audit.md` | Per-template canonical/hreflang/OG/JSON-LD audit + HEAD verifications |
| `docs/seo/03_sitemap_indexability.md` | Sitemap delivery diagnosis, original GSC "Couldn't fetch" root causes |
| `docs/seo/04_keyword_research.md` | 2026 head topics, query intent clusters, three keyword bets |
| `docs/seo/05_action_plan.md` | Phase 2 action plan (bundles 1–7, original version) |
| `apps/frontend/lib/seo.ts` | Core SEO helpers (canonical, hreflang, OG, JSON-LD builders) |
| `apps/frontend/app/layout.tsx` | Root metadata + WebSite JSON-LD |
| `apps/frontend/app/robots.ts` | Robots.txt |
| `apps/frontend/app/api/cron/revalidate-sitemap/route.ts` | Sitemap cron generator |
| `apps/frontend/app/sitemap-index.xml/route.ts` | Sitemap index (dynamic from DB) |
| `.github/workflows/revalidate-sitemap.yml` | Daily 04:00 UTC cron trigger |
