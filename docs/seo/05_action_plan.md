# SEO Phase 2 — Document 5: Action Plan

**Date**: 2026-05-12
**Inputs**: Documents 1–4 in this folder.
**Out of scope**: friction-nodes, narratives v1+v2, analysis, epics.

This is the prioritized backlog. Items are ordered: largest expected lift first
(after gating fixes). Each carries an ID that matches the audit docs so
upstream context is one click away.

Phase 2 of SEO work is **planning only** per the user's brief — execution of
each item below is a separate go/no-go decision.

## Layout

- **🔴 Critical / blocking** — likely cause of GSC "Couldn't fetch" / soft-404
  noise. Ship together as one PR.
- **🟠 High** — directly leaves traffic on the table. Quick effort, high lift.
- **🟡 Medium** — quality polish, structured-data signal, duplicate-content
  hygiene.
- **🟢 Future** — new templates / surfaces; needs separate scoping.

---

## Bundle 1 — Sitemap + indexability fixes (🔴 Critical)

Ship as one PR. Coupled because they're all in `app/sitemap.ts` + `app/robots`
adjacent. After deploy: cron-trigger `/api/cron/revalidate-sitemap`, then
re-submit `sitemap-index.xml` in GSC.

| Ref | Issue | Fix shape | Files |
|---|---|---|---|
| [S-1] | `sitemap.xml` ships `application/xml` with no charset | Migrate `app/sitemap.ts` → custom Route Handler `app/sitemap.xml/route.ts` returning `new Response(body, { headers: { 'Content-Type': 'application/xml; charset=utf-8', 'Cache-Control': 'public, max-age=3600, s-maxage=86400' }})`. Same body-construction logic, just wrapped. | `apps/frontend/app/sitemap.ts` → `apps/frontend/app/sitemap.xml/route.ts` (rename + wrap) |
| [S-2] | `sitemap.xml` `Cache-Control: max-age=0` — uncached at origin | Bundled with S-1 (set headers in Response). | same |
| [S-3] | Missing `hreflang="en"` self-reference on every `<url>` | Add `en: ${SITE_URL}${path}` to `alt()` helper's `languages` block. | same file, 1 line |
| [S-4] | Sitemap advertises 3 dead `/signals/[type]` URLs (soft-404) | Trim `signalTypes` array to `['persons','orgs','places','named_events']`. | same file, 1 line |
| [S-5] | `/c/[centroid]/about` pages not in sitemap | Add a `${SITE_URL}/c/${centroidId}/about` entry inside the existing centroid-iteration block. | same file, ~5 lines |

**Validation checklist post-deploy**:

- [ ] `curl -I https://www.worldbrief.info/sitemap.xml` shows `Content-Type: application/xml; charset=utf-8` and `Cache-Control: public, max-age=3600, s-maxage=86400`.
- [ ] First `<url>` entry has all three `xhtml:link` alternates (en, de, x-default).
- [ ] `/signals/commodities` is no longer in the file.
- [ ] `/c/MIDEAST-IRAN/about` and `/de/c/MIDEAST-IRAN/about` are listed.
- [ ] Re-submit `sitemap-index.xml` in GSC (delete + re-add).
- [ ] After 48–72 h, check GSC Coverage report: "Discovered – currently not indexed" count for `/c/.../about` should drop as Google picks them up.

---

## Bundle 2 — Title-bug + signals SEO basics (🟠 High)

Two small unrelated edits, low risk, immediate lift.

| Ref | Issue | Fix shape | Files |
|---|---|---|---|
| [M-1] | `/sources/[slug]` title is `"X — Editorial Profile \| WorldBrief \| WorldBrief"` (root `title.template` re-appends `\| WorldBrief`) | Strip ` \| WorldBrief` from the hardcoded title strings in `generateMetadata`. Root layout's template adds it back exactly once. | `apps/frontend/app/[locale]/sources/[slug]/page.tsx` |
| [M-2] | `/signals`, `/signals/[type]`, `/signals/[type]/[value]` ship no canonical, no hreflang | Replace inline `{ title, description }` returns with `buildPageMetadata({ title, description, path, locale })`. Persons page needs `path = /signals/${type}/${encodeURIComponent(value)}`. | 3 page files in `app/[locale]/signals/` |

**Validation**:

- [ ] `curl https://www.worldbrief.info/sources/the-guardian | grep -o '<title>[^<]*</title>'` returns single `| WorldBrief` suffix.
- [ ] `curl https://www.worldbrief.info/signals/persons | grep canonical` returns the canonical link tag.

---

## Bundle 3 — Surface the lowest-hanging keyword channels (🟠 High)

These leverage existing well-formed content that's currently invisible to
search.

| Ref | Item | Why | Files |
|---|---|---|---|
| [Bet B] | Internal-link `/c/[centroid]/about` from every centroid landing prominently | Even after sitemap inclusion (S-5), users + crawlers find pages via internal links. The "Background brief" should appear in the centroid sidebar, not just from the URL bar. | `apps/frontend/app/[locale]/c/[centroid_key]/page.tsx` (add a sidebar link block) |
| — | Add `BreadcrumbList` JSON-LD to centroid + track + sources pages (parity with track-day pages) | Improves SERP breadcrumb appearance; near-free. | `apps/frontend/app/[locale]/c/[centroid_key]/page.tsx`, `apps/frontend/app/[locale]/c/[centroid_key]/t/[track_key]/page.tsx`, `apps/frontend/app/[locale]/sources/[slug]/page.tsx` |
| [M-5] | Per-outlet meta description from real data, not template | The current "Cross-month editorial profile of {feed}: stance toward countries and persons…" is identical across 207 outlets. Pull in top 1–2 entity countries + dominant tone from `outlet_entity_stance`. | `apps/frontend/app/[locale]/sources/[slug]/page.tsx` (extend `generateMetadata`, add a small query helper) |

**Validation**:

- [ ] Spot-check 5 outlet pages — descriptions should be distinct.
- [ ] After 2–4 weeks, GSC Performance report: impressions for "[country] geopolitical profile" / "[outlet] coverage" queries should appear.

---

## Bundle 4 — Quality of SERP appearance (🟡 Medium)

These don't affect rankings much but improve click-through and social
unfurls.

| Ref | Item | Notes |
|---|---|---|
| [M-6] | Add a static `opengraph-image.png` (1200×630) at `apps/frontend/app/opengraph-image.png` + `twitter-image.png`. Site-wide fallback. Then optionally Twitter `summary_large_image` site-wide. | Cheap; one-time design. |
| [M-6 v2 — optional] | Per-template dynamic OG images via `app/.../opengraph-image.tsx` (Next.js built-in OG image generation). Centroid pages with flag + month, track-day with brief excerpt, etc. | Heavier build, bigger Render footprint per render. Defer. |
| [M-9] | Wrap static utility pages (`/about`, `/methodology`, `/faq`, `/pricing`, `/privacy`, `/terms`, `/known-issues`, `/sources`) in `buildPageMetadata` for full OG/Twitter parity. | Low-impact (these aren't ranking targets) but cheap consistency. |
| [Sources index] | `/sources` page is currently `revalidate=21600` (6h ISR) — that's fine, but the `buildPageMetadata` upgrade above sweeps in here too. | — |

---

## Bundle 5 — E-E-A-T / authority signal (🟡 Medium)

Per Doc 4: 2026 Google ranking emphasis is on Experience, Expertise,
Authoritativeness, Trustworthiness.

| Ref | Item | Notes |
|---|---|---|
| Author Schema in root layout | Emit a `Person` JSON-LD for the operator (Maksim Micheliov) with `sameAs` pointing to public LinkedIn / GitHub. Linked from the `WebSite.publisher` already in root. | One-time addition to `apps/frontend/lib/seo.ts` and `app/layout.tsx`. |
| Per-page byline footer link | "Curated by [name] · Methodology" footer link visible on every content page. | Already partially via `/about` mention. Make it a footer block. |
| Methodology page rich-up | `/methodology` is a static i18n page. Worth adding `Article` JSON-LD (currently has none) and one or two diagrams of the pipeline. | Light copy work. |

---

## Bundle 6 — Description quality at scale (🟡 Medium)

The mechanically-generated descriptions on centroid + track + track-day pages
are already strong. Two improvements that bake in more "Information Gain":

| Item | Notes |
|---|---|
| Centroid landing description: include top 1–2 *trending* signals when present (e.g. "Iran in May 2026: 4,627 sources; trending: Hormuz tensions, Pezeshkian elections."). Pulls from `centroid_summaries` + `trending_signals` if available. | Strengthens long-tail capture without manual writing. |
| Region pages: include top 3 centroids by current-month activity in description (e.g. "Asia in May 2026 news: top stories from China, Japan, and India."). | Cheap differentiation; today all 6 region descriptions are identical templates. |

---

## Bundle 7 — Future workstreams (🟢 separate scoping)

Out of this audit; documented here as the pipeline of follow-on opportunities.

| Item | Why future |
|---|---|
| **Person / leader sub-pages, indexable** | `/signals/persons/[name]` exists but the signals family needs canonical + hreflang treatment plus a sitemap surface for top-N persons. Worth a separate spec since "Putin coverage" / "Trump foreign policy" are real demand. |
| **Per-outlet × entity sub-pages** | `/sources/[slug]/about/[entity]` ("How does Al Jazeera cover Iran?") — uniquely positioned vs AllSides / Ground News. Needs a new template + data model decision. |
| **Topic / bilateral cross-pages** | `/topic/iran-israel`, `/topic/us-china-trade` — bilateral framing pages aggregating across both centroids. Cross-FN positioning naturally; couples to the friction-node work (currently excluded). |
| **Google News + Publisher Center submission** | Requires editorial-standards page, persistent author bios, predictable publication cadence. Worth a project once E-E-A-T basics land. |
| **Hreflang correctness audit at page level** | Doc 3 verified canonical + hreflang on rendered pages for major templates. A full sweep (every template both EN + DE) is worth scripting (a small Playwright crawl) once the dust settles. |
| **Image sitemap / per-page hero images** | We don't ship per-page hero images today. Adding them unlocks both `image_sitemap` and richer SERP appearance. Heavier image-pipeline work. |
| **Core Web Vitals audit** | Last formal CWV check pre-dates the recent ISR-cache rollback to `force-dynamic`. Worth re-measuring on Render and pulling INP / LCP per template family. |

---

## Suggested execution sequence

1. **Bundle 1** (🔴) — one PR, ~30–45 min of focused work, ships sitemap fixes.
2. **Bundle 2** (🟠) — second PR, ~30 min, fixes the title bug + signals
   canonical.
3. **GSC re-submit** the sitemap index.
4. **Wait 48–72 h** for GSC to reprocess. Verify Coverage report deltas.
5. **Bundle 3** (🟠) — internal linking + BreadcrumbList + outlet description.
   Ship as third PR.
6. Watch GSC Performance over 2–4 weeks. Capture baseline of top queries.
7. **Bundle 4 + 5 + 6** in flexible order based on what GSC tells us about
   click-through vs ranking issues.
8. Re-open the **future** column once a stable baseline exists.

Between bundles, leave time for GSC to react. Pushing all six in a week
prevents clean attribution; cadenced shipping lets us see which fix moved
which metric.

## Risks & open questions

- **Sitemap-days.xml indexation lag**. After fixing sitemap.xml, Google may
  still under-index `sitemap-days.xml` because of crawl-budget allocation. If
  6 weeks post-fix the day-canonical pages aren't picking up, consider
  splitting `sitemap-days.xml` by month (already designed in code comment).
- **Outlet description rewrites use `outlet_entity_stance`** — April 2026
  snapshot is partial through 2026-04-25 (per memory). May or per-page rebuild
  freshness is OK but coverage is uneven; description fallback to the current
  template if no stance data is fine.
- **Author Schema (`Person`)** requires a real public profile to link to. If
  user wants to remain anonymous, skip; the current `Organization` publisher
  schema is the next-best signal.
- **Render 512 MB ceiling** (per memory) is still active. Bundle 4 dynamic OG
  images would add render cost — keep that on the future list until ceilings
  loosen.

## Open questions for the user

| # | Question | Why it matters |
|---|---|---|
| Q1 | Public-facing author identity? (Personal byline + Author Schema, or stay "WorldBrief team"?) | Bundle 5 fork |
| Q2 | OK to add a static `opengraph-image.png` site-wide (one design)? | Bundle 4 unblock |
| Q3 | Priority on the future-bundle items (person pages? outlet-entity? Google News?) | Determines roadmap after bundles 1–6 |
| Q4 | Is the GSC re-submission step something you'll do, or do we have an automation hook? | Procedure clarity for Bundle 1 close-out |

---

## File set (this audit, all in `docs/seo/`)

- `01_content_inventory.md` — every in-scope template + DB-backed page count + sitemap inclusion
- `02_metadata_audit.md` — per-template canonical/hreflang/OG/Twitter/JSON-LD audit + production HEAD verifications
- `03_sitemap_indexability.md` — sitemap delivery diagnosis, GSC "Couldn't fetch" root-causes, defect catalog
- `04_keyword_research.md` — 2026 head topics, mapping to our templates, three keyword bets
- `05_action_plan.md` — this file
