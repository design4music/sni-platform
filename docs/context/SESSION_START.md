# Session Start

**Last refreshed**: 2026-04-20

If you are picking up work cold, this is the landing page. Read this
first, then branch out.

## Current state — where are we

WorldBrief is live at https://www.worldbrief.info with four months of
fully-processed 2026 data (Jan, Feb, Mar, Apr) on Render. Pipeline v4.0
is running continuously on the Render worker. Frontend ships the
day-centric calendar view and cross-track centroid hero.

For the complete snapshot: [`PIPELINE_STATUS.md`](PIPELINE_STATUS.md).

## Active strategic roadmap (from 2026-04-19)

Sorted by dependency + suggested phasing. None of these is the single
"right now" item — this is the menu.

### Phase 1 — foundation (highest compounding return)

1. **CTM summaries — design + build.** Closes the single biggest
   perceived-quality gap on centroid pages. Feature is about
   distillation: the "what IS the state of play in Germany's economy this
   month, and what changed vs last month" that a non-analyst user can
   scan in 20 seconds. Existing ticket. Needs a prompt-design session
   before coding.
2. **Code + doc cleanup.** ✅ Families removed (D-064, 2026-04-20):
   event_families table, events_v3.family_id column, 11 orphan scripts,
   2 pipeline modules, /families/[id] route. Plan retained at
   [`EVENT_FAMILIES_REMOVAL.md`](EVENT_FAMILIES_REMOVAL.md). Archive of
   deprecated docs also done in this folder. Still open: consolidate
   one-shot scripts in `scripts/` vs `out/beats_reextraction/`.
3. **Centroid sidebar stats → DB.** Persist stance scores and
   unusual-activity monthly so they don't recompute on every request and
   stop showing "same value across months". New table
   `centroid_monthly_stats(centroid_id, month, stats_type, payload jsonb)`.

### Phase 2 — visible wins

4. **Trending page with calendar timeline.** Reuse the calendar
   hero pattern at global (cross-centroid) scope. Segments can start
   as 4 tracks, evolve to top-centroid breakdown later.
5. **SEO foundation.** Schema markup on event/narrative/centroid
   pages, full sitemap, proper canonical/meta/og tags, mobile audit.
   Prerequisite for monetization.

### Phase 3 — lighthouse

6. **Friction nodes.** The positioning-defining feature. Day-centric
   data + daily_briefs.themes + event_strategic_narratives are the
   substrate. See [`FRICTION_NODES_VISION.md`](FRICTION_NODES_VISION.md).
   Start with a one-page scope doc: algorithmic definition, detection
   cadence, UI shape. Otherwise scope explodes.

### Phase 4 — revenue

7. **Stripe + paid plans.** Subscription state, entitlements,
   webhooks. Two-week focused sprint when product is "worth paying
   for" (arguably now).
8. **Google AdSense.** After SEO lands. Start with small placements
   on high-traffic pages.

### Parallel / ongoing

- Main page polish + content cleanup
- Performance audit
- German coverage enrichment (Phase 2 alias list expansion — see research
  notes below)

## Research findings (2026-04-19)

Recent diagnostic queries established:

1. **Promotion coverage**: 97-99% of source-weighted coverage is
   visible in the UI. Every cluster ≥5 sources is promoted. The
   ~15% "invisible" titles are 1-2 source single-outlet blurbs. The
   day-cap is correctly filtering the thin tail.

2. **Germany coverage is not thin for a European peer**: 2,744
   March titles, 99% promotion rate, on par with UK (3,086) and
   ahead of France (2,071). The USA/Germany gap (10×) is
   structural — global feed mix is English-biased. To grow Germany
   volume: enrich Phase 2 aliases with more DE politicians/parties/
   states/industries, or add more German-language feeds.

## Active tickets (Asana, RAI/SNI project)

- **CTM digests: restore + modernize period-level summaries**
  ([1214109791690038](https://app.asana.com/1/1211666582649030/project/1211666445056038/task/1214109791690038))
- **Narrative matching: investigate why Mar/Apr show 0 matches**
  ([1214106015283570](https://app.asana.com/1/1211666582649030/project/1211666445056038/task/1214106015283570))
- **Daemon: persist last_run across restarts**
  ([1214103726997112](https://app.asana.com/1/1211666582649030/project/1211666445056038/task/1214103726997112))
- **Phase 3.3: rewrite as bulk SQL** — CLOSED in `8c90ce8`
  ([1214111347970773](https://app.asana.com/1/1211666582649030/project/1211666445056038/task/1214111347970773))

## Recent key commits

```
485b747  fix(rerun): null inbound merged_into before DELETE
8c90ce8  perf(phase-3.3): bulk SQL rewrite (~450x)
cfb6ba5  feat(frontend): theme chips + narratives sidebar
3c21123  feat(frontend): centroid hero + enriched track cards
0b7215e  feat(frontend): theme-colored calendar chart
bec07aa  feat(scripts): backfill prose + briefs by month
44942a4  fix(daemon): drop redundant DISTINCT in describe-promoted
```

## Key principles (memory)

These persist across sessions via `~/.claude/projects/.../memory/`:

- **Optimize before running.** Prefer bulk SQL over per-row loops.
  Shard LLM workloads. Raise alternatives in planning. Long jobs (>1h)
  should be spec'd with concurrency/sharding before they start.
- **No patches, root solutions only.** Don't add a downstream phase to
  paper over an upstream gap.
- **Estimates divided by ~8.** My instinct runs hot.
- **Never delete or overwrite production data without confirmation.**
- **DE version is default.** Every UI content block must support
  German (via `_de` columns, locale-aware render, translate on-demand).
