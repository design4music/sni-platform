# Session Start

**Last refreshed**: 2026-04-22 (SEO + route merge + D-064 families removal + trending/v2 prototype)

If you are picking up work cold, this is the landing page. Read this
first, then branch out.

## Current state — where are we

WorldBrief is live at https://www.worldbrief.info with four months of
fully-processed 2026 data (Jan, Feb, Mar, Apr) on Render. Pipeline v4.0
is running continuously on the Render worker. Frontend ships the
day-centric calendar view, cross-track centroid hero, and (as of this
session) a reworked `/c/*/t/*` that folds the calendar view inline, a
full SEO layer, and a `/trending/v2` prototype ready for review.

For the complete snapshot: [`PIPELINE_STATUS.md`](PIPELINE_STATUS.md).

## Active strategic roadmap

Sorted by dependency + suggested phasing. None of these is the single
"right now" item — this is the menu.

### Phase 1 — foundation (highest compounding return)

1. **Centroid period summaries.** ✅ Done (D-065, 2026-04-20). New
   `centroid_summaries` table: tier-0 overall + per-track JSONB,
   bilingual, two period_kinds (rolling_30d via daemon Slot 4, monthly
   via freeze). Replaces legacy `centroid_monthly_summaries`. Frontend
   centroid page renders an "Overview" briefing above the hero and
   per-track state in TrackCards. Generator at
   `pipeline/phase_5/generate_centroid_summary.py`. Follow-up: migrate
   downstream consumers (narratives extraction, social posting, RAI)
   off `ctm.summary_text` so those legacy columns can be retired.
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

4. **Trending page rebuild.** 🟡 Prototype shipped at `/trending/v2`
   (D-068, 2026-04-22). Centroid-style layout at global scope:
   full-width cross-track hero, mechanical Overview prose, 2×2 track
   cards with top-5 events (cross-centroid Dice dedup), fastest-growing
   panel (last-7-day source increment, current month only), top-10
   Active Narratives sidebar, reused Trending Signals. Current
   `/trending` kept live with a "Preview v2 →" link in its header.
   Still open: editorial LLM overview (`global_summaries` table
   mirroring D-065), promotion (swap `/trending/v2` → `/trending`).
5. **SEO foundation.** ✅ Mostly shipped (D-066, 2026-04-22). Unique
   titles/descriptions on every centroid/track/event page (fed by
   D-065 editorial text where available, mechanical fallback);
   hreflang alternates (en/de/x-default); sitemap covers events /
   narratives / epics / sources / signals / centroids; JSON-LD
   (NewsArticle + BreadcrumbList + Article + SearchAction); OG +
   Twitter per-page. `/c/*/t/*/calendar` folded into `/c/*/t/*` with
   301 redirect. `noindex` on auth/profile/search/analysis.
   Remaining: Google Search Console submission (one-click),
   optional dynamic OG images, LLM overview for `/trending/v2`.

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

- **Narrative matching: investigate why Mar/Apr show 0 matches** — CLOSED.
  Render has 87k links (Mar 16k, Apr 9k) after reprocessing; local
  populated via manual run (78k links). Root-cause `DOMAIN_TO_TRACK`
  bug also fixed in `5457aed` (dead `geo_energy/_humanitarian/_information`
  consolidated to the four live tracks).
  ([1214106015283570](https://app.asana.com/1/1211666582649030/project/1211666445056038/task/1214106015283570))
- **Daemon: persist last_run across restarts**
  ([1214103726997112](https://app.asana.com/1/1211666582649030/project/1211666445056038/task/1214103726997112))
- **Phase 3.3: rewrite as bulk SQL** — CLOSED in `8c90ce8`
  ([1214111347970773](https://app.asana.com/1/1211666582649030/project/1211666445056038/task/1214111347970773))
- **CTM digests: restore + modernize period-level summaries** — centroid
  page surface CLOSED by D-065 (`centroid_summaries`); remaining scope is
  retiring `ctm.summary_text` columns via downstream-consumer migration
  (narratives / social / RAI)
  ([1214109791690038](https://app.asana.com/1/1211666582649030/project/1211666445056038/task/1214109791690038))

## Known dead code / cleanup candidates (not urgent)

- `pipeline/phase_4/generate_summaries_4_5.py` — still imported by
  `freeze_month.py` and `scripts/process_backlog.py`. Cannot unplug
  until downstream consumers (narratives extraction, social posting,
  RAI) migrate off `ctm.summary_text`.
- `out/beats_reextraction/*.py` frozen one-shots — reference dropped
  `family_id` column; will error if rerun. Documented, not touched.
- `core/archive_llm_client.py` — unimported, still has family refs.
  Deletable any time.
- `track_configs` table + its only consumer (`getConfiguredTracksForCentroid`
  in queries.ts) — unused at runtime. The table holds a 60-entry
  granular-track vocabulary (`armed_conflict`, `energy_conflict`, etc.)
  that never populates `ctm.track`.
- Four `energy_*` i18n entries (`energy_coercion/_competition/_governance/
  _infrastructure`) left in place — part of the track_configs vocab.
- Two untracked scripts (`scripts/push_month_to_render.py`,
  `scripts/reprocess_month_local.py`) have local docstring fixes from
  D-064. Track them when consolidating `scripts/` next.
- **GSC sitemap submission** — one-click, deferred.

## Recent key commits

```
3e6eb30  fix(trending/v2): full-width hero + cross-centroid dedup
8d98d16  feat(trending): /trending/v2 prototype — centroid-style layout global
5457aed  fix(narratives) + cleanup: consolidate dead tracks
c990e9a  fix(seo): unblock /sitemap.xml + /robots.txt; editorial descriptions
e6ef975  refactor(d-064): remove event_families — schema + code purged
dd20874  feat(seo): unique metadata, hreflang, sitemap, JSON-LD + merge /calendar
f580ba9  docs(context): log D-065 centroid_summaries + refresh SESSION_START
01b14a3  refactor(centroid): retire centroid_monthly_summaries
fcd2ed4  feat(centroid): period summaries + tier-0 briefing
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
