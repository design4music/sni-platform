# SEO Phase 2 — Document 2: Metadata & Canonical Audit

**Date**: 2026-05-12
**Method**: code review of `generateMetadata` in every in-scope `page.tsx`, plus
production fetches via `curl -A "Mozilla/5.0 (compatible; Googlebot/2.1)"` to
verify what actually ships in the `<head>`.

## Helpers + global frame

Defined in `apps/frontend/lib/seo.ts`:

- `buildAlternates(path)` — emits `canonical` + `en` / `de` / `x-default` hreflang.
- `buildPageMetadata(args)` — `buildAlternates` + `openGraph` (type, title, desc,
  url, siteName, locale) + `twitter` (card, title, desc) + optional
  `article:publishedTime` / `og:image`.
- `newsArticleJsonLd`, `articleJsonLd`, `breadcrumbList`, `websiteJsonLd`.

`apps/frontend/app/layout.tsx`:

- `metadataBase = https://www.worldbrief.info`.
- `title.template = '%s | WorldBrief'`, default `'WorldBrief - Understand the world. Briefly.'`.
- Generic root `openGraph` (no `og:image`, no `og:url`) + `twitter.card = 'summary'`.
- Emits **`WebSite` JSON-LD with `SearchAction`** in every page. ✓

`apps/frontend/app/[locale]/auth/layout.tsx`:

- `robots: { index: false, follow: false }` → all `/auth/*` pages are noindex. ✓

## Per-template audit

Legend: ✓ = present, ✗ = missing/broken, ◐ = partial.

| Template | gen­Meta­data | `buildPage­Metadata` | Canonical | hreflang en/de/x-default | OG full | Twitter | JSON-LD beyond root WebSite | Issues |
|---|---|---|---|---|---|---|---|---|
| Home `/` | export const metadata | ✗ uses `buildAlternates` only | ✓ | ✓ | ◐ (title/desc inherited, no og:url, no og:image) | ◐ (summary, no image) | none | OG/Twitter not page-specific (acceptable; could add og:url) |
| Region `/region/[r]` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | none | OK |
| Centroid `/c/[c]` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | none on page (root only) | Could add `CollectionPage` + `BreadcrumbList` |
| Centroid About `/c/[c]/about` | ✓ | ✓ | ✓ | ✓ | ✓ (article) | ✓ | none | Could add `Article` + `BreadcrumbList`; **not in sitemap** |
| Track `/c/[c]/t/[t]` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | none | Could add `BreadcrumbList` |
| Track-day `/c/[c]/t/[t]/[d]` | ✓ | ✓ | ✓ | ✓ | ✓ (article + publishedTime) | ✓ | **NewsArticle + BreadcrumbList** ✓ | Best-treated template; only minor: `articleSection` could be I18N-translated |
| Event `/events/[id]` | ✓ | ✓ | ✓ | ✓ | ✓ (article + publishedTime) | ✓ | code imports `newsArticleJsonLd` — verify it ships (need body fetch) | Spot-check: code path renders body-level `<JsonLd>` in event page detail layout |
| Sources index `/sources` | ✓ | ✗ `buildAlternates` only | ✓ | ✓ | ✗ inherited | ✗ inherited | none | Add `buildPageMetadata` for consistent OG |
| Outlet landing `/sources/[slug]` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | none | **BUG: double "\| WorldBrief"** — title `"The Guardian — Editorial Profile \| WorldBrief \| WorldBrief"` because page hardcodes `\| WorldBrief` and root template appends `\| WorldBrief` again |
| Outlet month `/sources/[s]/[m]` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | none | OK (title ends with `\| Editorial Stance`, no duplication) |
| Trending live `/trending` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | none | Could add `CollectionPage` |
| Trending past month `?month=` | ✓ | ✓ | ✓ (self-ref incl. ?month) | ✓ | ✓ (article) | ✓ | none | OK |
| Trending archive day `?day=` | ✓ | ✓ | ✓ (incl. ?day) | ✓ | ✓ (article) | ✓ | none | OK |
| Signals index `/signals` | ✓ | ✗ plain object | **✗** | **✗** | ◐ inherited only | ◐ summary card | none | **Missing canonical + hreflang** |
| Signal category `/signals/[type]` | ✓ | ✗ plain object | **✗** | **✗** | ◐ inherited | ◐ | none | **Missing canonical + hreflang** |
| Signal value `/signals/[type]/[value]` | ✓ | ✗ plain object | **✗** | **✗** | ◐ inherited | ◐ | none | **Missing canonical + hreflang**; URL-encoded values can produce inconsistent paths |
| About `/about` | ✓ | ✗ `buildAlternates` only | ✓ | ✓ | ✗ inherited | ✗ inherited | none | Inherits root OG. OK for static. |
| Methodology / FAQ / Pricing / Privacy / Terms / Known issues | ✓ | ✗ `buildAlternates` only | ✓ | ✓ | ✗ inherited | ✗ inherited | none | Same as About. Acceptable. |
| Search `/search` | ✓ | n/a | n/a | n/a | n/a | n/a | none | `noindex, follow` ✓ |
| Profile `/profile` | ✓ | n/a | n/a | n/a | n/a | n/a | none | `noindex, nofollow` ✓ |
| Sign in / Sign up `/auth/*` | layout-level | n/a | n/a | n/a | n/a | n/a | none | `noindex, nofollow` via `auth/layout.tsx` ✓ |

## Production HEAD verifications (samples)

### `/c/AMERICAS-USA/t/geo_economy/2026-05-05` ✓ best case

```
<title>United States economy: 5 May 2026 news | WorldBrief</title>
<meta name="description" content="Workers at Google DeepMind in the UK have voted to unionize…"/>
<meta name="robots" content="index, follow"/>
<link rel="canonical" href="…/c/AMERICAS-USA/t/geo_economy/2026-05-05"/>
<link rel="alternate" hrefLang="en" href="…/c/AMERICAS-USA/t/geo_economy/2026-05-05"/>
<link rel="alternate" hrefLang="de" href="…/de/c/AMERICAS-USA/t/geo_economy/2026-05-05"/>
<link rel="alternate" hrefLang="x-default" href="…/c/AMERICAS-USA/t/geo_economy/2026-05-05"/>
<meta property="og:type" content="article"/>
<meta property="article:published_time" content="2026-05-05T00:00:00Z"/>
<meta name="twitter:card" content="summary"/>

<!-- body-rendered JSON-LD -->
<script type="application/ld+json">{ "@type":"WebSite", … }</script>   # from root layout
<script type="application/ld+json">{ "@type":"NewsArticle", "headline":"…", "datePublished":"…", "articleSection":"Economy" }</script>
<script type="application/ld+json">{ "@type":"BreadcrumbList", … }</script>
```

### `/sources/the-guardian` ✗ title bug

```
<title>The Guardian — Editorial Profile | WorldBrief | WorldBrief</title>
```

Root cause: `apps/frontend/app/[locale]/sources/[slug]/page.tsx:88-91` hardcodes
`| WorldBrief` in the title; root layout template appends `| WorldBrief` again.

Fix: strip `| WorldBrief` from the page title. Verify same isn't on
`/sources/[slug]/[month]` (it isn't — month title ends with `| Editorial Stance`).

### `/signals/persons` ✗ missing canonical + hreflang

```
<title>Top Persons - Signal Observatory | WorldBrief</title>
<meta name="description" content="Ranked top persons by event mentions over the last 30 days."/>
<meta name="robots" content="index, follow"/>
# No <link rel="canonical">
# No <link rel="alternate" hrefLang=…>
```

Affects `/signals`, `/signals/[type]`, and `/signals/[type]/[value]`. Without
canonical Google may pick a different URL as canonical for the same content
when crawlers find query-string variants.

## Signal-type vocabulary drift (not strictly metadata, but indexability)

- `app/sitemap.ts:189` lists **7** signal types
  (`persons, orgs, places, commodities, policies, systems, named_events`).
- `app/[locale]/signals/[type]/page.tsx:19-21` accepts only **4**
  (`persons, orgs, places, named_events`).
- Result: sitemap advertises 3 dead URLs (`/signals/commodities`, `/policies`,
  `/systems`) that return `notFound()` on the live site. → soft-404 in GSC.

## `og:image` — universally absent

No template sets an `og:image`. Twitter card is `summary` (small thumb) instead
of `summary_large_image`. Social-share unfurls (LinkedIn / Twitter / Discord)
fall back to favicon or nothing.

Two paths:

1. Static OG image (`opengraph-image.png` at the `app/` root, 1200×630)
   inherited site-wide. Cheap, immediate; same image everywhere.
2. Per-template dynamic OG via `app/.../opengraph-image.tsx` (Next.js dynamic OG
   via `@vercel/og` / Next built-in). Per-page composition (country flag,
   month, headline). Heavier — both code complexity and Render render budget.

## Canonical / hreflang shape consistency

Spot checks across `/c`, `/c/.../about`, `/c/.../t/...`, `/c/.../t/.../[date]`,
`/events`, `/sources`, `/sources/[slug]`, `/sources/[slug]/[month]`, `/trending`,
`/region`, `/about`: all emit `canonical` + `hreflang en`, `de`, `x-default` correctly.
`x-default` always points to the EN URL (correct under Google's reciprocal-cluster
rules — every page in the cluster lists every variant including itself).

For DE pages: confirmed via a spot check of `/de/c/AMERICAS-USA`, alternates
reciprocate identically. The `buildAlternates(path)` helper is locale-agnostic
and works both ways. ✓

## Description quality

Sampling 6 templates:

| Template | Description shape | Quality |
|---|---|---|
| Centroid `/c/USA` | "United States in May 2026: 4,627 sources covering politics, society and security. Top themes: diplomacy, society and military. Multilingual news briefing." | Mechanically generated when no editorial overview; falls back to `centroid_summaries.overall` when present. Good. |
| Track-day | Daily-brief prose, 160-char truncated. Genuinely unique per (centroid, track, date). | Excellent — the strongest SEO asset on the site. |
| Event | Event summary + dateline `(N sources, date)`. | Good when summary present; fallback could be stronger. |
| Outlet landing | Static template "Cross-month editorial profile of {feed}: stance toward countries and persons…" | Same wording for every outlet. **Repetitive across 207 pages** — Google may treat as low-quality duplicates. |
| Outlet month | Static template "Coverage analysis for {feed} in {month}: editorial stance, topics…" | Repetitive across 672 pages. Same risk. |
| Region | "Europe news intelligence: countries and sub-regions covered by WorldBrief with multilingual source analysis and narrative tracking." | Same for all 6 regions modulo the region name. Could fold in top centroids or top themes for the period. |
| Sources `/sources` | "Curated list of 180+ international media sources powering WorldBrief, spanning 6 continents and dozens of languages." | One-off page; fine. |

**Pattern**: per-period-specific descriptions (track-day, centroid, track) are
the strongest. Per-entity-with-no-period descriptions (outlet landing, outlet
month, region) are templated and could pull in lightweight signals (e.g. top
topic, last-30-day volume, stance dominant tone) to differentiate.

## JSON-LD coverage matrix

| Page | WebSite (root) | BreadcrumbList | NewsArticle / Article | CollectionPage | Organization |
|---|---|---|---|---|---|
| All pages | ✓ | – | – | – | – |
| Track-day (brief present) | ✓ | ✓ | ✓ (NewsArticle) | – | – |
| Event | ✓ | spot-check needed | needs verification | – | – |
| Centroid landing | ✓ | – | – | candidate | – |
| Centroid About | ✓ | – | – (could be Article) | – | – |
| Track landing | ✓ | – | – | candidate | – |
| Outlet | ✓ | – | – | – | candidate (NewsMediaOrganization) |
| Trending (live / past month / archive day) | ✓ | – | – | candidate | – |

The track-day template is the only one with full structured-data treatment. The
event-detail template imports `newsArticleJsonLd` and `breadcrumbList`; a body
fetch of an `/events/[id]` page will confirm shipping (deferred — same pattern
as track-day, very likely works).

## Summary of issues to address

| # | Issue | Affected pages | Severity |
|---|---|---|---|
| M-1 | Title double-suffix `\| WorldBrief \| WorldBrief` | `/sources/[slug]` × 207 (×2 locales) | High — bad SERP appearance |
| M-2 | Missing canonical + hreflang | `/signals`, `/signals/[type]`, `/signals/[type]/[value]` | High — risk of duplicate / wrong canonical |
| M-3 | Sitemap lists 3 dead `/signals/*` URLs (commodities, policies, systems) | 3 URLs ×2 locales | Medium — soft-404 noise in GSC |
| M-4 | `/c/[centroid]/about` not in any sitemap | 75 ×2 locales | Medium — high-quality curated content invisible to discovery |
| M-5 | Identical/templated descriptions on outlet & outlet-month pages | 207 + 672 ×2 locales | Medium — duplicate-meta signal |
| M-6 | No `og:image` site-wide; Twitter card is `summary` not `summary_large_image` | All pages | Medium — weak social unfurls; minor SEO signal |
| M-7 | Sitemap.xml served with `Content-Type: application/xml` (no `charset=utf-8`) and `Cache-Control: max-age=0, must-revalidate` (uncached); the other two sitemap files have proper headers | `/sitemap.xml` only | Medium — Googlebot tolerates but may delay/skip |
| M-8 | `og:image`-free Twitter cards collapse to favicon | all pages | Low (overlap with M-6) |
| M-9 | Static utility pages inherit generic root OG (no per-page `og:url`/`og:type=article`) | `/about`, `/methodology`, `/faq`, `/pricing`, `/privacy`, `/terms`, `/known-issues`, `/sources` | Low — these aren't ranking targets |
| M-10 | Centroid + track + sources page-level pages lack `BreadcrumbList` JSON-LD | most templates | Low — structured-data signal only |

Fix bundles for M-1…M-7 are short edits (1–2 lines each in most cases) and form
the bulk of the immediate quick-win backlog in `05_action_plan.md`.
