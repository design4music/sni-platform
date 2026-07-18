# SEO Phase 2 — Document 4: Keyword & Traffic Research

**Date**: 2026-05-12
**Scope**: identify search intents WorldBrief is structurally well-placed to
serve, with concrete keyword clusters per content template, and frame the
discoverability gaps that the action plan should close.
**Excluded**: friction-nodes, narratives (v1+v2), epics (per session scope).
**Sources for the external trend snapshot**: web search 2026-05-12 (links at end).

## Methodology

This is not a paid keyword-volume study. It's an opportunity map:

1. Identify the 2026 geopolitical search themes that have demonstrated traffic
   gravity (head queries that Reuters/BBC/AP currently win).
2. Identify the long-tail variants that map to WorldBrief content templates
   already producing unique content.
3. Identify what we have that competitors do not — those are the queries
   where we can actually win, not just compete.
4. List the keyword angles that would justify *new* page types
   (deferred — informational for the action plan, not a build-in-this-phase
   list).

Real keyword-volume validation (Ahrefs / Semrush / GSC query report) belongs in
a later phase once the structural fixes from Doc 3 land and indexation
stabilises.

## 2026 head topics — what the world is searching

From web research (Lazard 2026 outlook, EY Geostrategic Outlook, Deutsche Bank
This Month in Geopolitics May 2026, Diplomat outlook, German-language
clustering):

| Cluster | Queries (head-term examples, EN) | Queries (head-term examples, DE) | Our coverage |
|---|---|---|---|
| Iran nuclear / Iran tensions | "Iran nuclear deal", "Iran nuclear program", "Iran war", "Iran ceasefire", "Iran Israel war" | "Iran Atomprogramm", "Iran Krieg", "Iran Israel Krieg" | `MIDEAST-IRAN` centroid + 4 tracks + day-canonical pages + outlet stance toward Iran |
| Russia–Ukraine war | "Russia Ukraine war news", "Ukraine ceasefire", "Ukraine peace deal" | "Ukraine Krieg", "Russland Ukraine Waffenruhe" | `EUROPE-UKRAINE`, `EUROPE-RUSSIA` centroids + tracks |
| US–China trade & summit | "Trump Xi summit", "US China trade deal", "China tariffs" | "USA China Zollkrieg", "Trump Xi Gipfel" | `AMERICAS-USA` + `ASIA-CHINA` centroids; `geo_economy` track strong |
| Gaza / Israel–Hamas | "Israel Gaza news", "Hamas ceasefire", "Gaza humanitarian crisis" | "Israel Gaza Nachrichten" | `MIDEAST-ISRAEL`, `MIDEAST-PALESTINE` centroids |
| EU–China trade frictions | "EU China tariffs", "EU electric vehicles China", "European Commission China" | "EU China Handel", "EU Zölle China" | `EUROPE-EU` (if exists) + `ASIA-CHINA`; spotty bilateral coverage |
| Strait of Hormuz | "Strait of Hormuz news", "Hormuz tanker attack", "Iran navy Hormuz" | "Strasse von Hormuz", "Hormuz Iran" | Centroid-level coverage; friction node exists but WIP/excluded |
| Energy / oil prices | "oil prices", "global food prices", "energy crisis" | "Ölpreis", "Energiepreise" | `geo_economy` track gives mechanical aggregation but no dedicated commodity pages |
| Specific leaders | "Trump foreign policy", "Putin news", "Xi Jinping", "Netanyahu", "Pezeshkian" | "Trump Außenpolitik", "Putin Nachrichten" | `/signals/persons/[name]` exists but **not in sitemap, not indexed** |
| Media bias / source comparison | "Reuters bias", "Al Jazeera bias", "AllSides Reuters", "Ground News [outlet]" | "Reuters Bias", "Al Jazeera Voreingenommenheit" | `/sources/[slug]` with stance heatmap is uniquely positioned but currently buggy (M-1) and shallow on signal |
| World news live / today | "world news today", "international news live" | "Weltnachrichten heute", "internationale Nachrichten" | `/trending` (live) — well-positioned but single page |
| News archive by date | "news on April 12 2026", "what happened in March 2026" | "Nachrichten 12. April 2026" | Day-canonical track pages + trending archive day URLs. Uniquely strong — competitors mostly don't have indexable "Country X on Date Y" surfaces |

## What WorldBrief has that competitors don't

The strategic SEO leverage is in the templates that **only WorldBrief
produces**. These are the queries to optimize against:

### 1. "Country X on Date Y" — day-canonical track pages
**URL**: `/c/[centroid_key]/t/[track]/[date]`
**Count**: 6,092 indexable pages (≈70% of all days × all centroid+track combos
with a daily brief).
**Query patterns**:
- "United States economy news May 5 2026"
- "Iran security news April 23 2026"
- "Germany politics 9 March 2026"
- "What happened in [country] on [date]"
**Why we can win**: Reuters / BBC / FT don't have indexed per-country-per-date
landing pages. Their archive is by topic or by article, not by structured day.
We already have the title pattern (`{Country} {track}: {date} news`) and the
description is genuinely unique (a curated daily brief). The NewsArticle JSON-LD
+ BreadcrumbList signal is in place.
**Action**: ensure these are in `sitemap-days.xml` (they are) **and** that
internal linking surfaces them well (covered in Doc 5).

### 2. "Country X in Month Y" — per-track monthly briefings
**URL**: `/c/[centroid_key]/t/[track]` (defaults to latest month)
**Count**: 296 EN × 2 locales
**Query patterns**:
- "Iran security news April 2026"
- "Russia economy news March 2026"
- "Germany society news May 2026"
**Why we can win**: similar logic to day-canonical, one level coarser.
Currently the description is mechanically generated when no editorial state
exists; for the 4 canonical tracks (economy/politics/security/society) it
pulls from `centroid_summaries.{track}.state` (D-065). Description quality is
strong.

### 3. "Country X" head queries — centroid landing
**URL**: `/c/[centroid_key]`
**Count**: 75 EN × 2 locales
**Query patterns**:
- "Iran news"
- "Russia news"
- "Saudi Arabia news"
- "Germany news"
**Why we'll struggle**: these are dominated by Reuters/BBC/AP/Wikipedia.
Beating them on head queries requires authority signals (E-E-A-T) we don't yet
have (no author bios, no editorial branding, no "this is curated by X" surface).
But on the "Country X month YYYY-MM" long-tail we win.

### 4. "About / background on Country X" — strategic profile
**URL**: `/c/[centroid_key]/about`
**Count**: 75 EN × 2 locales
**Current status**: shipping with full metadata + curated background brief +
strategic narratives + mini-map. **Not in any sitemap** (Doc 3 issue S-5).
**Query patterns**:
- "Iran political profile"
- "Saudi Arabia strategic overview"
- "Turkey geopolitical position"
- "Why is [country] important geopolitically"
**Why we can win**: evergreen, curated, multilingual. Once advertised in the
sitemap and linked from each centroid landing, these are long-shelf-life pages.

### 5. "Outlet X coverage / bias" — outlet landing + stance heatmap
**URL**: `/sources/[slug]`
**Count**: 207 EN × 2 locales
**Query patterns**:
- "Reuters bias", "Al Jazeera bias", "RT propaganda"
- "Is [outlet] reliable"
- "[outlet] stance on Iran"
- "How does [outlet] cover [country]"
**Competitor benchmark**: AllSides and Ground News dominate "media bias"
queries with 5-point bias rating charts. Their angle is editorial (human-rated
left/center/right). **Our angle is automated, per-entity, per-month**: "How does
Al Jazeera cover Iran in April 2026?" — they can't answer that; we can.
**Why we'll under-perform today**:
  - Title has bug: `"X — Editorial Profile \| WorldBrief \| WorldBrief"` (Doc 2 M-1)
  - Description is templated and identical across all 207 outlets
  - We don't surface "stance toward X" as an indexed page — only as a heatmap on the outlet landing
  - No author bio / methodology authority signals
**Where the win is**:
  - Fix the bugs (M-1) so the title is presentable
  - Add a per-outlet meta description that includes the outlet's strongest
    coverage (e.g. "Coverage analysis of The Guardian: 2,847 stories on the UK,
    1,034 on Israel; predominantly critical of Russia, supportive of EU.")
  - Eventually: add per-outlet-per-entity pages (`/sources/[slug]/about/[entity]`)
    — but this is a future workstream, not in this audit

### 6. "Outlet X in month Y" — outlet monthly page
**URL**: `/sources/[slug]/[month]`
**Count**: 672 EN × 2 locales (varies by stance/stats coverage)
**Query patterns**:
- "Al Jazeera coverage April 2026"
- "Reuters editorial line March 2026"
**Why we can win**: niche but indexable, and again Reuters/BBC don't have this
self-referential surface for *other* outlets.

### 7. "Person X" — signal-value pages (currently broken)
**URL**: `/signals/persons/[name]`
**Count**: dynamic; no listing, no sitemap inclusion
**Query patterns**:
- "Putin in the news", "Trump news today", "Xi Jinping coverage"
**Current status**: pages render but **no canonical, no hreflang, not in
sitemap** (Doc 2 M-2, M-3). Person-page queries are likely a missed channel.
**Plan**: outside this audit's scope (signals-family rework is a separate
build); flag for the action plan as "future" not "fix now."

### 8. "World news on date Y" — trending archive day
**URL**: `/trending?month=YYYY-MM&day=YYYY-MM-DD`
**Count**: ~80–100
**Query patterns**:
- "World news on April 12 2026"
- "Top stories April 12 2026"
- "What happened globally on date X"
**Why we can win**: this is the only template I've seen that explicitly
canonicalises one URL per archive day with rank-change signals. Pages have
article OG + datelined description. ✓

## Templates × intent matrix (in-scope, summary)

| Template | Head-term opp | Long-tail opp | Differentiator | Discoverability today |
|---|---|---|---|---|
| Home | Low (brand) | – | – | OK |
| Region | Low | "Asia news", "Middle East news" | Curated multilingual | OK |
| Centroid landing | Brand vs head ("Iran news") — Reuters dominates | "Iran news May 2026" | Editorial overview + cross-track | OK |
| Centroid About | – | "Iran political profile", "country geopolitical profile" | Curated background brief | **Not in sitemap** |
| Centroid Track | – | "Iran security news" | Mechanical aggregation | OK |
| **Centroid Track Day** | – | "Iran security news 5 May 2026" + 6,000+ similar | **Unique** — no competitor has this | OK; rely on Doc 3 fixes |
| Event | Low | Specific event keywords | Cross-source aggregation per event | OK |
| Outlet landing | Brand ("Reuters bias") | "How does X cover Y" | Stance heatmap + tone | **Title bug + thin description** |
| Outlet month | – | "Reuters April 2026 coverage" | Per-month stance snapshot | OK once title bug fixed |
| Sources index | – | "international news sources" | 180+ multilingual list | OK |
| Signals index | – | – | – | OK |
| Signal value | – | "[Person] news", "[Org] coverage" | Cross-source aggregation | **Not in sitemap, missing canonical** |
| Trending live | Brand ("WorldBrief trending") | "top stories today" | Daily-fresh aggregation | OK |
| Trending past month | – | "global news April 2026 recap" | Monthly archive | OK |
| **Trending archive day** | – | "world news on [date]" | **Unique** — indexable day archive | OK |

## German-locale strategy

We already ship full DE alternates via hreflang. Per the German trend snapshot,
the DE locale is competitive (high-volume terms like "Iran Krieg", "Russland
China Iran", "Geopolitik 2026" all return high-quality German outlets). Our DE
content quality varies:

- Daily briefs and event prose: **lazy-translated on-demand** (per memory). Some
  pages have `_de` fields populated, some fall back to a translation banner.
- Centroid summaries: bilingual at the schema level (D-065 EN+DE columns).
- Outlet pages: descriptions are templated DE strings — same template every
  outlet, same issue as EN.

DE-specific opportunities:
- Push DE translation coverage upstream so more day-canonical pages have
  `summary_de` filled in (Tier-1 issue in `feedback_data_freshness_ceiling`).
- DE-specific Title/Description tuning where the EN version is verbose. (E.g.,
  EN "Iran nuclear program coverage" is 4 words; DE "Berichterstattung zum
  iranischen Atomprogramm" is 4 words. Length parity is mostly fine.)
- Consider DE-only landing variants of the home page that lead with regional
  DACH-relevant centroids (Germany, EU, Russia, USA, China, Iran).

## Information Gain — Google's 2026 emphasis

Per web research, Google's late-2025 / 2026 algorithm pushes toward
*Information Gain* as a primary signal: does your page bring something a user
can't get from the existing top results? Where WorldBrief over-indexes on
Information Gain:

- **Cross-source aggregation per event** — competitors usually show one source
  per article. We show N sources per event with a deduplicated synthesis.
- **Per-day per-country digests** — unique structural artifact.
- **Outlet stance per entity per month** — unique structural artifact;
  competitors (AllSides, Ground News) only do outlet-level not entity-level.

Where we're middling:
- Centroid landing competing on "Iran news" — Reuters/BBC have more
  Information Gain via reporting.
- Event detail — we add the cross-source view but the article body itself is
  not original reporting.

## E-E-A-T gap

Per web research, E-E-A-T (Experience, Expertise, Authoritativeness,
Trustworthiness) signals matter increasingly. We currently lack:

- **Author byline + Author Schema**. The "About" page mentions Maksim Micheliov
  as the operator, but no per-page byline.
- **Editorial methodology surface beyond `/methodology`**. Linking to it from
  every content page (footer or sidebar) helps. Already partial.
- **Verifiable contact info**. `/about` has it; could be more prominent.
- **Author Schema (`Person` JSON-LD)** with `sameAs` to LinkedIn / public
  profile. Lightweight to add.

For a single-operator site, the realistic E-E-A-T plays are:

1. Make the operator (Maksim) the editorial face. Author Schema. Link byline.
2. Surface the methodology clearly on every content page (footer link is
   probably enough).
3. Highlight source diversity ("aggregated from 207 international outlets")
   as a trust signal in description / OG.

## Concrete query → URL mapping examples

| Search query | Target URL today | Quality | Notes |
|---|---|---|---|
| "Iran nuclear news May 2026" | `/c/MIDEAST-IRAN/t/geo_security?month=2026-05` | ✓ indexable, good title/desc | OK |
| "What happened in Iran on April 23 2026" | `/c/MIDEAST-IRAN/t/geo_security/2026-04-23` (or other tracks) | ✓ indexable, NewsArticle JSON-LD | Strongest asset; in `sitemap-days.xml` |
| "Russia Ukraine ceasefire" | `/c/EUROPE-UKRAINE` or `/c/EUROPE-RUSSIA` | ✓ but competing with Reuters | Long-tail variant ("Russia Ukraine ceasefire May 2026") is winnable |
| "Iran political profile" | `/c/MIDEAST-IRAN/about` | ✓ content exists | **Not in sitemap → not indexed** |
| "Putin coverage" | `/signals/persons/Vladimir%20Putin` | ✓ page exists | **Not in sitemap, no canonical → unreliable** |
| "Reuters bias" | `/sources/reuters` | ◐ title bug, thin description | M-1 fix flips this |
| "Reuters Iran coverage" | `/sources/reuters` (stance heatmap visible) | ◐ data is on the page but not crawlable as a separate URL | No per-entity sub-page yet |
| "Top stories April 12 2026" | `/trending?month=2026-04&day=2026-04-12` | ✓ indexable, in sitemap | OK |
| "Al Jazeera April 2026 coverage" | `/sources/al-jazeera/2026-04` | ✓ indexable | OK |

## Three keyword-strategy bets

The action plan in Doc 5 turns these into concrete tickets.

### Bet A — "Country × Date" channel (largest existing surface)
6,092 day-canonical pages (× 2 locales = 12,184) are our strongest unique asset
and not yet driving the traffic the inventory implies. The bottleneck is *not*
content quality — it's that:
1. `sitemap-days.xml` (covered, indexed but maybe slow to crawl)
2. Internal linking depth is high — calendar pages list day-cells but the
   month-pickers and per-track navigation may not surface specific dates well
3. Hreflang chain has a minor bug in `sitemap.xml` (Doc 3 S-3)

Once Doc 3 fixes land, monitor `sitemap-days.xml` indexed-page count in GSC.

### Bet B — "Country profile" evergreen channel (lowest-hanging fix)
Add the 75 `/c/[centroid]/about` URLs to the sitemap. ×2 locales = 150 evergreen
pages with curated content. These should rank for "[country] geopolitical
profile" / "[country] political profile" / DE equivalents within weeks.

### Bet C — "Outlet bias / coverage" channel (vs AllSides / Ground News)
Fix the title bug (Doc 2 M-1) and lift the description quality (per-outlet
signal rather than templated string). 207 outlets × 2 locales is a meaningful
surface against a real search demand we structurally answer better than
incumbents.

## What's NOT in this phase

- Building new templates (e.g. person sub-pages, outlet-entity sub-pages,
  topic-comparison pages) — those are future work; flagged in the action plan
  as ideas, not commitments.
- Buying keyword-volume data (Ahrefs/Semrush). Defer until structural fixes
  land and we have a stable GSC baseline.
- Google News onboarding / Publisher Center setup. Worth a separate
  conversation — Google News inclusion has its own requirements (author bio,
  editorial standards page, frequent publication cadence).

## Sources (web research, 2026-05-12)

- [Top Geopolitical Trends in 2026 — Lazard](https://www.lazard.com/research-insights/top-geopolitical-trends-in-2026/)
- [This Month in Geopolitics: May 2026 — Deutsche Bank Research Institute](https://www.dbresearch.com/PROD/IE-PROD/PDFVIEWER.calias?pdfViewerPdfUrl=PROD0000000000626668&rwnode=REPORT)
- [Top 10 Geopolitical Developments in 2026 — EY](https://www.ey.com/en_gl/insights/geostrategy/geostrategic-outlook)
- [Outlook: Geopolitical Trends and Global Diplomacy in 2026 — The Diplomat](https://thediplomat.com/2025/12/outlook-geopolitical-trends-and-global-diplomacy-in-2026/)
- [SEO Best Practices in 2026 — AWR](https://www.advancedwebranking.com/seo/seo-best-practices)
- [SEO in 2026: Higher standards, AI influence — Search Engine Land](https://searchengineland.com/seo-2026-higher-standards-ai-influence-web-catching-up-473540)
- [Information Gain: Google's #1 Ranking Signal in 2026](https://www.digitalapplied.com/blog/information-gain-google-ranking-signal-april-2026)
- [Google News SEO: How to Rank in Google News in 2026 — DevriX](https://devrix.com/tutorial/google-top-stories-seo-how-to-rank-google-news/)
- [E-E-A-T Guide 2026 — SEO Kreativ](https://www.seo-kreativ.de/en/blog/e-e-a-t-guide-for-more-trust-and-top-rankings/)
- [International SEO & GEO: Best Practices & Strategy in 2026 — Elementor](https://elementor.com/blog/international-seo-geo-best-practices-strategy-in-year/)
- [Long-Tail Keywords: The Ultimate Guide for 2026 — Yotpo](https://www.yotpo.com/blog/long-tail-keywords-guide/)
- [Media Bias Chart — AllSides](https://www.allsides.com/media-bias/media-bias-chart)
- [Top 50 English-language news sites April 2026 — Press Gazette](https://pressgazette.co.uk/media-audience-and-business-data/media_metrics/most-popular-websites-news-world-monthly-2/)
