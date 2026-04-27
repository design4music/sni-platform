# Outlet Landing Page — Open Items (last touched 2026-04-27)

Temporary scratchpad. Delete once items are either implemented or
moved into Asana tickets.

## Current state

- New cross-month dashboard live at `/sources/[slug]` (replaced redirect
  handler). File: `apps/frontend/app/[locale]/sources/[slug]/page.tsx`.
- New component: `apps/frontend/components/OutletStanceHeatmap.tsx`
  (server component, top-N entities × months, click-through to monthly
  detail).
- New query: `getOutletStanceTimeline(feedName)` in
  `apps/frontend/lib/queries.ts`.
- New i18n keys (en + de): `landingIntro`, `browseMonths`,
  `lifetimeOverview`, `heatmapTitle`/`Description`/`Empty`/etc.,
  `totalArticles`, `monthsTracked`.
- Tested in dev against: tass-en (36 cells), jerusalem-post (35),
  lenta-ru (29), rt (29), cgtn (24), bloomberg (18), handelsblatt (15),
  new-york-times (12).
- **Not committed yet** — still a prototype pending architecture
  decision (see Q1 below).

### 2026-04-27 additions

- New SVG charts (server components, no chart lib):
  - `OutletEntityVolume.tsx` — top-12 entity sparklines, peak month
    marked, click-through to peak.
  - `OutletTrackTimeline.tsx` — stacked-area for security/politics/
    economy/society shares per month, with month-link strip below.
- New query: `getOutletTrackTimeline(feedName)` reads
  `mv_publisher_stats_monthly`.
- Per-month gating implemented:
  - Landing's "Browse by month" strip + heatmap + sparklines + track
    timeline use `getOutletStanceMonths` (stance months only).
  - Monthly page month-switcher uses `getOutletStanceMonths` — only
    stance months are linked.
  - Monthly page sets `robots: noindex, follow` when the visited
    month has no stance data. URL still works (deep-link-friendly).
  - When outlet has zero stance months, monthly page redirects bare
    "no data at all" hits to landing; landing hides all monthly-
    split content (Browse, heatmap, both charts), shows lifetime
    overview only.
- New i18n keys: `volumeTitle`/`volumeDescription`/`volumePeakLink`/
  `volumePeakLabel`, `trackTimelineTitle`/`trackTimelineDescription`/
  `trackTimelineMonthLink` in en + de.
- Smoke-tested: 8 stance outlets render all three viz blocks; 5
  zero-stance outlets render landing-only (just "Lifetime overview"
  h2); stats-only month pages return `noindex, follow`.

## Open question 1: keep or revert dual-page architecture?

Two pages per outlet (landing dashboard + monthly detail) vs. revert
to single per-month page with a redirect at `/sources/[slug]`.

Pros of dual-page: cross-month story (heatmap, future charts), one
canonical entry, SEO-friendly bare URL.

Cons: more surface to maintain; landing page may feel thin if heatmap
is the only differentiator.

**Decision pending Max's evaluation of the prototype.**

## Open question 2: monthly sub-page gating — RESOLVED 2026-04-27

User chose: page exists for any URL, but stats-only months are
**noindex** + **never linked** from our site. Implemented as
described above.

## Footer + header restructure 2026-04-27 (round 8)

- Removed "Browse by month" strip + the `MonthsStrip` + `formatMonthShort`
  helpers (no longer needed; the heatmap header itself is the
  navigator).
- New `components/SiblingOutletsDropdown.tsx` — client component,
  click-outside / Escape dismissal, mobile-friendly. Renders inside
  the header next to the outlet domain link as
  `"<count> more from <country> ▾"`.
- Sibling outlets removed from the bottom row entirely.
- Bottom row now always 3-col on md+: **Top actors | Domain focus |
  Publication pattern**. Same vertical-bar list visual for all three.
- Publication pattern was an inline DoW horizontal-bar chart; rebuilt
  as a vertical bar list (Mon→Sun, label + bar + %) matching Top
  actors / Domain focus styling so the footer reads as one cohesive
  block. Peak hour moved to a small caption beneath the list.
- New i18n keys: `dayMon..daySun` (full weekday names) +
  `moreFromCountryShort` ("X more from {country}") in en + de.

## Track-distribution unification 2026-04-27 (round 7)

The lifetime "Track distribution" horizontal bar duplicated content
already shown by the "Topic mix over time" stacked-area chart. User
wanted them combined and exact percentages surfaced.

- Removed the standalone `trackDistributionBlock` (lifetime TrackBar)
  from the page. The local `TrackBar` helper component + supporting
  `LIVE_TRACK_COLORS` table + `tTracks` translation getter all
  deleted.
- `OutletTrackTimeline` now computes lifetime shares internally
  (weighted by per-month title_count) and surfaces them in the
  legend with exact `%` values per track ("Security 34.5%").
- Added a per-month chip strip below the legend: each chip is a
  Link to the monthly detail page and carries an `<InfoTip>` with a
  rich tooltip — month label, total title count, and per-track %
  breakdown. Mobile-friendly (tap-to-show via the shared InfoTip
  pattern).
- Component now also handles the 1-month fallback: when only one
  month of data exists, renders a simple horizontal lifetime bar
  instead of the (degenerate) stacked-area chart.
- Wired into both variants: stance outlets see Track timeline inside
  the stance section (after Volume chart); low-coverage outlets see
  it after Lifetime overview.
- New i18n keys: `lifetimeLabel` ("Lifetime"), `byMonthLabel`
  ("By month") in en + de.

## Page reorganization 2026-04-27 (round 6)

After reviewing CNN (stance variant) vs Albanian Daily News (low-
coverage variant), reorganized the landing page so the most relevant
content surfaces first.

**Stance variant (e.g., CNN, Fox News, TASS):**

```
Header + intro
Browse by month strip
Editorial stance over time (heatmap)
Coverage volume by entity (chart)
Topic mix over time (track timeline)
Lifetime overview (5 stats inc. Months tracked)
Track distribution (lifetime)
Publication pattern (lifetime)
3-col footer: Top actors | Domain focus | Sibling outlets
```

**Low-coverage variant (e.g., Albanian Daily News, 66 articles):**

```
Header + REWRITTEN intro
  ("Coverage profile for X. We have N articles ingested so far —
   not enough sustained focus … The lifetime summary below is what
   we can show.")
Lifetime overview (4 stats — drops "Months tracked")
Track distribution (lifetime)
Publication pattern (lifetime)
2-col footer: Top actors | Domain focus
  (siblings hidden when there are none — grid collapses to 2-col)
```

- New i18n key `landingIntroLowCoverage` (en + de) takes `name` and
  `n` (article count) parameters.
- Stats grid switches from `md:grid-cols-5` to `md:grid-cols-4` when
  no stance months exist.
- Bottom 3-col grid swaps to 2-col when sibling-outlet count is 0;
  fetched once on the page (cached) and used to choose grid class.

## Mobile InfoTip viewport-centering 2026-04-27 (round 5)

- InfoTip: on phones (<sm) the tooltip is now `position: fixed` and
  centered on the viewport (`top-1/2 left-1/2 -translate-x-1/2
  -translate-y-1/2`) with `w-[calc(100vw-1.5rem)] max-w-sm`. This
  guarantees the tooltip is always fully visible and never causes
  page horizontal overflow regardless of where the trigger sits.
- On sm+ behaviour unchanged — tooltip floats above its trigger.
- Root cause: previously the tooltip was `position: absolute` with
  `left-1/2 -translate-x-1/2` everywhere; legend rows near the right
  edge of the viewport produced tooltips that extended past the
  viewport, which made the page itself scroll horizontally on
  phones.

## Layout + tooltip polish 2026-04-27 (round 4)

- Heatmap is now flexible: `table-fixed w-full` so cells share remaining
  width on iPad+ (768px+), `min-width` only enforces phone-scroll
  fallback below `md:`. Removed `sticky left-0` from entity column —
  scrolled month columns now disappear off-screen instead of sliding
  behind the entity column.
- Promoted InfoTip to `components/InfoTip.tsx`. Mobile-friendly: the
  trigger has `tabIndex={0}` and the tooltip uses
  `group-focus-within:visible` so tap-and-release keeps it open until
  the user taps elsewhere. Optional rich `children` for multi-line
  content; legacy `text` prop still works.
- Volume chart legend rebuilt: `grid-cols-1` on phones,
  `sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4` upward. "Date · count"
  meta drops to `text-[10px]` on phones. Each row gains a wide
  `<InfoTip>` showing peak/total/active-weeks + per-month breakdown
  in a JSX layout (label, two-column month table). Same look as the
  existing "i" tooltips on the page.

## Visual unification + mobile + placeholders 2026-04-27 (round 3)

- New shared `components/PersonIcon.tsx` (extracted from
  OutletStanceSection). Used in heatmap, volume chart legend, stance
  pills.
- Removed local `/flags/{iso2}.png` flags from SourceCountryAccordion
  and emoji flags from heatmap + volume chart. All flag rendering now
  goes through `components/FlagImg.tsx` (flagcdn) — single style
  across `/sources`, heatmap, chart, monthly stance section.
- Heatmap entity column shrunk to 140px with truncate; cells bumped
  to 80×36px for mobile readability.
- Heatmap now extends through Dec of the latest data year. Months
  beyond the last scored month render as diagonal-striped placeholder
  cells, headers unlinked + dimmed, with title="Awaiting coverage".
  Legend gets a placeholder swatch.
- Volume chart wrapped in a mobile-only horizontal-scroll container
  (`overflow-x-auto -mx-4 px-4`) with inner `min-w-[820px]`. md+
  breakpoints fall back to fluid full-width. Each week now gets ~50px
  of horizontal real estate on phones.

## Idea 1: per-entity volume — WEEKLY + LOG REWRITE 2026-04-27 (round 2)

Final form (round 2, after Max review):
- Bucketed daily counts into Monday-anchored weeks → simple angular
  polylines, ~17 weeks for current 4-month corpus.
- Removed all raw scatter dots and overshoot markers. One entity →
  one line; line breaks on zero-volume weeks. Peak marker (one per
  entity, larger) sits ON the line, not floating above.
- Y axis is now log10(v+1) with ticks at 1/2/5/10/25/50/100/250/...
  → fine resolution for small entities (Greenland, Khamenei) while
  still showing high-volume Trump/US peaks.
- Peak marker tooltip: entity name, peak week + count, lifetime
  total + active weeks count, monthly breakdown.
- Legend tooltip carries the same summary.

## Idea 1 (round 1 — superseded): per-entity volume — DAY-LEVEL REWRITE 2026-04-27

Discovery: monthly resolution misrepresents reality (a single dot per
month can't show whether Greenland was a 3-day spike or a 4-week
trend). Switched to day-level using `title_labels.entity_countries`
(JSONB) + `title_labels.persons` (text[]) — labelling coverage is
95-100% for all backfilled months, so day-level GROUP BY gives clean
series.

Final form:
- New query `getOutletEntityDailyVolume(feedName)` joins titles_v3 +
  title_labels, scoped to entities present in `outlet_entity_stance`
  for that outlet. Span = full title lifetime (NOT just stance months).
- Chart: raw daily counts as small low-opacity dots + a 7-day centered
  rolling-mean line per entity. Line breaks where the smoothed value
  drops below 0.1 (long zero stretches → visible gap, not crawling
  baseline).
- Peak marker = max raw daily count, dark-stroked circle with `<title>`
  tooltip showing date + value.
- Legend below: clickable to peak month detail page.
- Y axis shared across entities for spike-height comparability. X
  axis lifetime, month tick labels.
- Entity selection + ordering: matches heatmap (months covered desc,
  then total desc); top-12.

**Pending Max review** — visual density at 120+ days × 12 lines may
need further tuning (line opacity, dot radius, window size).


Show the "Iran/Greenland/Venezuela spike-and-vanish" pattern.

- One mini line/area chart per top-12 entity, laid out 3-4 columns wide.
- Same entity ordering and selection as the heatmap (months covered
  desc, total volume desc).
- Y axis = `n_headlines` per month. Shared X axis (all months in
  lifetime, even ones the entity wasn't covered in — shows the gaps).
- Plain inline SVG (we already do this in `DowChart`).
- Click-through: link the spike's peak month to its monthly detail.

Tradeoff: redundant with heatmap (volume already encoded as opacity)
but spike timing reads better as a line. Try it; if it feels like
duplication we drop one.

## Idea 2: track distribution stacked area — DONE 2026-04-27

Implemented. Pending review.



Stacked area showing security/politics/economy/society shares per
month. Wide chart, single SVG.

Source data: needs per-outlet per-month track distribution. Already
in `mv_publisher_stats_monthly.stats.track_distribution`. Just need
to fan it out across `getOutletAvailableMonths` and stack.

Defer until Idea 1 ships and we see if more charts are useful or
just noise. User instinct: "I am still not sure how useful it is."
Don't pile on visualizations without a clear question they answer.

## Idea 3: lower stance threshold from 15 to 5

User's reasoning: maps look thin because most outlets only score
their own country + USA + their next target. If we lower the bar we
might pick up "directional but uncertain" stance for the long tail
of countries an outlet briefly mentions.

**Pilot first — do not run full backfill.**

Pilot plan:

1. Pick 2 outlets with known sparse coverage:
   - **Lenta-RU** (Russian regional, lots of bundles probably below 15)
   - **One small English regional** (TBD — Jerusalem Post is too big;
     maybe Anadolu or a Reuters-Africa-equivalent. Pick something with
     ~50-150 titles/month total).
2. Run `pipeline/phase_5/score_outlet_stance.py` for one month
   (suggest 2026-03) with `min_titles=5` instead of 15, **into a
   throwaway table** (`outlet_entity_stance_pilot`) to keep prod
   data clean.
3. Sample-read ~10 entity bundles per outlet, side by side with the
   current 15-titles output where it overlaps.

Quality gate questions:

- Do 5-title bundles produce a stance the LLM can actually defend?
- Or do we get vibes-based hallucination (random −1 / +1 / 0 with
  hand-wavy "patterns" text)?
- Is the LLM honest about its uncertainty (caveats field) when the
  bundle is thin?

Decision branches:

- **If quality holds** at 5 titles → lower threshold to 5 globally,
  add a `coverage_thin = true` flag on the row when `n_headlines < 15`,
  surface as a UI caveat "Based on N titles — directional only".
  Re-run backfill Jan-Apr.
- **If quality degrades** → keep threshold at 15, accept thin maps
  as the truth (these outlets really don't have a strong stance on
  the long tail).

Do not write the pilot script tonight — user said "examine data and
run some tests" tomorrow.

## Misc / cleanup

- Title on monthly page currently reads "TASS English · April 2026".
  No change needed unless threshold work surfaces ambiguity.
- `.next/` accumulating; if dev server starts misbehaving tomorrow,
  `Remove-Item -Recurse -Force apps/frontend/.next` before debugging
  anything fancier.
