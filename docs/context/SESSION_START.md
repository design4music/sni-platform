# Session Start

**Last refreshed**: 2026-07-07 (fn-map branch: strategic asset registry
(340 assets, 10 categories, source-anchored YAML + generator), asset_flows
supply-web layer, FN id naming convention + full LatAm/Mexico/Panama/Haiti
theater rebuild, `affected_asset_ids` mechanism framework, and a DB
migration safety incident + fix. See D-086..D-091 below and
[`fn-map current state`](#fn-map-strategic-asset-registry--conflict-map-new)
further down. **fn-map is a separate branch, not merged to main. Render
has NOT received any fn-map content.** Additionally: a pre-existing
deployment-drift gap was found independent of fn-map — several
friction-node migrations dated 2026-05/06 were committed but never
actually applied to live Render (see below); this affects the base
Middle East FN state described in the next paragraph, which may describe
the repo's intent more than Render's actual current rows.)

**Pre-2026-07-07 history below is preserved as-written; verify against
current DB state before relying on specific counts — see the
deployment-drift note above.**

**Pre-2026-05-13 history**: Friction Nodes rearchitected 2026-05-12
(theater pattern + 1-to-1 narrative<->FN collapse + 5-step stance
palette + taxonomy_v3 fn_anchor unification). Iran cluster = 1 theater
+ 4 atomic FNs + 12 narratives on Render. See D-075..D-079.

Earlier 2026-05-07: initial FN architecture shipped (3 Iran-cluster
FNs with publisher-stance bucketing). Earlier 2026-05-06: daemon
resilience hardened (D-073: TCP keepalives + pool-reset-on-error +
per-slot `daemon_state` health metrics, after the 2026-05-04
half-open-connection outage); frontend cache-bust admin endpoint
shipped (D-074). See PIPELINE_STATUS.md.

If you are picking up work cold, this is the landing page. Read this
first, then branch out.

## Current state — where are we

WorldBrief is live at https://www.worldbrief.info with four months of
fully-processed 2026 data (Jan, Feb, Mar, Apr) on Render. Pipeline v4.0
is running continuously on the Render worker. Frontend ships the
day-centric calendar view, cross-track centroid hero, and a reworked
`/c/*/t/*` that folds the calendar view inline, full SEO layer, and a
`/trending/v2` prototype.

**As of 2026-05-07**: the Friction Nodes shadow architecture is live
with 3 FNs in the Iran cluster. New analytical layer above events and
narratives. See [Friction Nodes section below](#friction-nodes-new) for
links to the concept doc + runbook.

For the complete snapshot: [`PIPELINE_STATUS.md`](PIPELINE_STATUS.md).

## fn-map: strategic asset registry + conflict map (new)

Separate branch (`fn-map`), not merged to main, not deployed to Render.
Started as a map-visualization redesign (D-086: asset-first architecture
replacing circle-based conflict markers) and grew into a full economic-
exposure layer sitting above the existing friction-node/narrative system.

**What exists (local DB, verified 2026-07-07):**
- **340 active `strategic_assets`** across 10 categories (chokepoints,
  ports, oil, gas, power, minerals, agriculture, tech, pipelines,
  corridors), each with `subcategory`, `ranking_source`, `rank_note`.
  Source of truth is `db/registry/*.yaml`; the DB is generated via
  `scripts/generate_asset_registry.py` (upsert, preserves existing
  geometry). See `db/registry/README.md` and D-087.
- **`asset_flows`** — 23 sourced oil-supply relationships, rendered on
  asset selection (D-088). Gas is the natural next commodity, not yet built.
- **FN id naming convention** (`docs/context/FN_ID_NAMING.md`, D-089):
  45 legacy generic ids (`regime_survival`, `nuclear_arms_control`...)
  renamed to `<geo>_<phenomenon>`. `latam_theater` retired and replaced
  with 6 theaters at peer granularity (`venezuela_theater`,
  `mexico_theater`, `panama_canal_theater`, `cuba_theater`,
  `latam_hemispheric_theater`, `haiti_theater`), reflecting real 2026
  events (US intervention in Venezuela, US-Mexico cartel-war military
  standoff, Panama Canal ports dispute with China).
- **`affected_asset_ids` mechanism framework** (D-090): home territory /
  demonstrated reach / named economic lever, replacing "co-occurs in
  centroid_ids" as the inclusion test. Applied fully to `iran_theater`;
  systematic backfill across the other ~27 theaters is the next planned
  pass (only the 6 new LatAm theaters have `primary_target` populated,
  the mechanical anchor for mechanism 1).
- **`scripts/safe_db_migrate.py`** (D-091): mandatory wrapper for any
  `.sql` migration against a database with real data, after a replayed
  migration silently cascade-deleted 15,945 `event_friction_nodes` rows
  during this work. Full incident: `docs/context/DB_SAFETY_INCIDENT_20260707.md`.

**Not yet done:**
- Systematic `affected_asset_ids` backfill (D-090 follow-up).
- Merge to main + Render deploy. Blocking items: the pre-existing
  deployment-drift gap (below) must be resolved as part of the same
  deploy plan, since fn-map migrations assume FN rows that may not exist
  on live Render yet.
- Regulatory data layer (BGBl/EUR-Lex feeds) — architecture designed
  in `docs/regulatory_layer_concept.md`, deliberately sequenced *after*
  fn-map ships to main.
- Intelligence-dashboard product surfaces (Chokepoint Monitor, Exposure
  Watchlist, Commodity Lens...) — concept in
  `docs/intelligence_dashboards_concept.md`, not started.

**Deployment-drift discovery (independent of fn-map, found while
refreshing local from Render):** several friction-node migrations
committed to the repo well before this session — e.g.
`20260621_add_primary_target_to_friction_nodes.sql` and some of the
2026-05/06 theater seed migrations — had never actually been applied to
live Render. This means Render's current `friction_nodes` row count and
schema may lag what's described elsewhere in this file and in
`FRICTION_NODES_RUNBOOK.md`. Verify against live Render (or a fresh dump)
before assuming any specific FN/theater is present on production.

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

### Phase 2.5 — Narrative Mapping (NV strategy)

The strategic differentiator. WorldBrief evolves from news aggregator
to **narrative intelligence platform** — mapping the structure of
global political narratives as a navigable graph (3-level hierarchy:
meta → strategic → event). Substrate is current title_labels; matching
is mechanical for operational narratives + LLM-as-judge for ideological
ones. Spec: [`docs/Narrative_map_spec.md`](../Narrative_map_spec.md).
Taxonomy draft v2 at [`docs/narrative_taxonomy.yaml`](../narrative_taxonomy.yaml)
(9 meta + 59 strategic narratives).

#### Middle East FN expansion (2026-05-13, local only)

Theater coverage now spans Iran + Israel + Syria + Turkey + Yemen/Red Sea
+ Sudan (standalone atomic). Numbers below are local DB; Render still
on the 2026-05-12 state (Iran + Israel only).

| Theater | Atomic FNs | Narratives | Atomic events (local) |
|---|---|---:|---:|
| iran_theater (live on Render) | 4 | 12 | ~3.6k (Render) |
| israel_theater (live on Render) | 4 | 12 | ~3.3k (Render) |
| **syria_theater** (local) | 4 | 10 | ~605 |
| **sudan_civil_war** (standalone, local) | — | 3 | 385 |
| **turkey_theater** (local) | 4 | 11 | ~402 |
| **yemen_red_sea_theater** (local) | 3 | 9 | ~658 |

Open work:
- Render sync of the 4 new theaters
- Narrative tuning per ongoing review (russia_iran_loss_lament dropped
  2026-05-13; other narratives may need cohort/anchor refinement)
- Pre-curate missing Turkey FNs: Turkey-Russia frenemy, Turkey-Greece
  East Med, Turkey-Caucasus (candidates for sleeping-FN treatment)

Specs:
- [`SYRIA_THEATER_SPEC.md`](SYRIA_THEATER_SPEC.md)
- [`TURKEY_THEATER_SPEC.md`](TURKEY_THEATER_SPEC.md)
- [`YEMEN_RED_SEA_THEATER_SPEC.md`](YEMEN_RED_SEA_THEATER_SPEC.md)
- [`SUDAN_FN_SPEC.md`](SUDAN_FN_SPEC.md)
- [`NARRATIVE_DISCOVERY_PLAN.md`](NARRATIVE_DISCOVERY_PLAN.md) — for review

#### Friction Nodes (shipped 2026-05-07, rearchitected 2026-05-12)

The structural-layer view above narratives. A friction node is a
contested phenomenon where multiple narratives apply with incompatible
prescriptions. Iran cluster is live as a shadow route at
`/friction-nodes/[slug]` (footer link only, noindex).

**Read for context**:
- [`FRICTION_NODES_RUNBOOK.md`](FRICTION_NODES_RUNBOOK.md) —
  current architecture + how to add a new theater/FN/narrative
  end-to-end. **Reflects the 2026-05-12 rearchitecture.**
- The legacy concept doc
  `out/concept_friction_nodes_and_narratives_v2.md` describes the
  initial publisher-stance bucketing rollout (FN2-FN4) but is
  outdated on schema specifics (join table, narrative_type,
  topic_keywords, etc. — all retired).

**Live structure on Render** (2026-05-12):

Theater + 4 atomic FNs in the Iran cluster:

| FN | Type | Events | Narratives |
|---|---|---|---|
| `iran_theater` | theater | (catch-all) | 4: regime-change (-2), sovereign-existence (+2), EU diplomatic (0), multipolar (+1) |
| `iran_nuclear_program` | atomic | 1,036 | 2 |
| `iran_proxy_network` | atomic | 1,349 | 2 |
| `gulf_attacks_on_arab_states` | atomic | 521 | 2 |
| `strait_of_hormuz_sovereignty` | atomic | 2,581 | 2 |

Total: ~5,500 event_friction_nodes + ~27,000 title_narratives on Render.

**Architectural shifts since 2026-05-07**:
- **Theater pattern**: `friction_nodes.fn_type` discriminator with
  `atomic` (specific phenomenon) and `theater` (catch-all umbrella
  bundling member atomic FNs). Atomic FNs claim titles first; theater
  catches the rest via NOT EXISTS subquery.
- **1-to-1 narrative<->FN**: `friction_node_narratives` join dropped;
  `narratives_v2.fn_id` is the direct link. Strategic-narrative library
  retired. Each narrative carries FN-specific prose.
- **5-step stance**: `narratives_v2.stance` is smallint -2..+2 (mirrors
  `outlet_entity_stance.stance`). Frontend palette uses the same colour
  function as OutletStanceBricks.
- **taxonomy_v3 unification (Phase 1+2)**: `taxonomy_function`
  discriminator + `linked_id` polymorphic FK. FN topic gate is now an
  `fn_anchor` row in taxonomy_v3 (multi-lingual aliases jsonb).
  `centroid_id` column scheduled to drop after worker redeploy
  picks up the `linked_id` query in `match_centroids.py`.
- **Bootstrap simplified**: 1-to-1 means publisher cohort + fn_anchor
  alias + centroid overlap is enough; framing-keyword filter retired
  from attribution (still ranks sample titles + populates the UI
  vocabulary chip).
- **Retired columns**: `narratives_v2.narrative_type`, `.tier`,
  `.topic_keywords`, `.editorial_organ_publishers`, `.notes_*`,
  `.scope_centroid_ids`; `friction_nodes.event_actor_markers`,
  `.event_topic_markers`, `.event_title_anchors`, `.topic_keywords`.

**Open / next**:
- Map out remaining theaters (in planning):
  - Israel-Gaza / Lebanon theater
  - Russia-Ukraine theater
  - China theater (Taiwan, South China Sea, trade)
  - US-Venezuela / Cuba
  - US-EU / NATO (Greenland, burden-sharing)
- Drop `taxonomy_v3.centroid_id` after worker redeploy verifies
  linked_id query is clean (2-3 daemon cycles).
- Promote out of shadow once theater/FN coverage spans the active
  geopolitical surface.

### Phase 3 — lighthouse

5b. **Outlet stance matrix (D-072 — shipped, with three follow-ups
   open).** Per-title stance retired in D-071; the aggregated
   replacement (one LLM call per outlet × entity × month bundle of
   ~25 headlines) is now live. Schema, scorer, backfill and the
   outlet-facing UI all shipped between 2026-04-24 and 2026-04-29.
   - **Schema**: `outlet_entity_stance` (migration
     `20260424_outlet_entity_stance.sql`) + companion materialized
     view `mv_publisher_stats_monthly`.
   - **Scorer**: `pipeline/phase_5/score_outlet_stance.py` (async,
     concurrent, idempotent UPSERT, dry-run + report modes).
   - **Backfill state (Render, verified 2026-05-01)**: Jan 2026
     (407 rows / 94 outlets), Feb (524 / 131), Mar (742 / 185),
     Apr (389 / 130 — partial-month snapshot computed 2026-04-25;
     final refresh deferred at the 2026-05-01 freeze).
   - **Frontend live**: outlet landing `/sources/[slug]` rebuilt
     (`74591a3`) with `OutletStanceHeatmap`, volume chart, topic
     mix; per-month `/sources/[slug]/[month]` (`2960b15`) with
     stance-coloured world map (`bcd38e9`); sitemap entries from
     the new table. New queries: `getOutletStance`,
     `getOutletStanceMonths`, `getOutletStanceTimeline`.
   - **Centroid Media Lens shipped** (`788fb38`, 2026-04-29):
     `getCentroidMediaLens` query joins `outlet_entity_stance` to
     `centroids_v3.iso_codes`, picks top 5 outlets by `n_headlines`
     for the active month. Sidebar `MediaLensSection` renders flag
     + stance dot + tone, each row linking to the outlet's monthly
     page. Hides cleanly for systemic centroids (no iso_codes) and
     months without stance data.
   - **Still open**:
     1. **Comparative + user analysis rewire** —
        `/analysis/comparative/...` and `/analysis/user/...` still
        read legacy `narratives WHERE
        extraction_method='stance_clustered'` via
        `getStanceNarratives` + `getEntityAnalysis`. Asana
        1214268284594725 tracks; no commits yet.
     2. **Monthly automation** — `pipeline/freeze/freeze_month.py`
        Step 4 is just a comment block. New months will not get
        stance rows until either freeze is wired to call
        `score_outlet_stance.py` or a separate cron is added.

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
- **Daemon: persist last_run across restarts** — CLOSED (was already
  shipped much earlier; doc was stale). 2026-05-06: daemon further
  hardened with TCP keepalives, pool reset on exception, and per-slot
  health columns in `daemon_state` (D-073).
  ([1214103726997112](https://app.asana.com/1/1211666582649030/project/1211666445056038/task/1214103726997112))
- **Phase 3.3: rewrite as bulk SQL** — CLOSED in `8c90ce8`
  ([1214111347970773](https://app.asana.com/1/1211666582649030/project/1211666445056038/task/1214111347970773))
- **CTM digests: restore + modernize period-level summaries** — centroid
  page surface CLOSED by D-065 (`centroid_summaries`); remaining scope is
  retiring `ctm.summary_text` columns via downstream-consumer migration
  (narratives / social / RAI)
  ([1214109791690038](https://app.asana.com/1/1211666582649030/project/1211666445056038/task/1214109791690038))

## Known dead code / cleanup candidates (not urgent)

- **D-071/D-072 stance archives** — moved to explicit `archive/`
  folders (2026-04-29): `pipeline/archive/score_publisher_stance.py`,
  `pipeline/archive/extract_stance_narratives.py`, and
  `apps/frontend/components/archive/StanceClusterCard.tsx`. Each
  archive folder has a README with provenance. Deletable outright
  once comparative analysis is rewired off the legacy `narratives`
  rows.
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
410059b  feat(frontend): admin endpoint to bust in-memory query cache (D-074)
fa21b1b  fix(daemon): reset connection pool on error + record per-slot health (D-073)
35c210f  chore(db): centralize psycopg2 connect kwargs + enable TCP keepalives (D-073)
a34cf63  perf(frontend): extend 6h ISR cache to remaining dynamic pages
be1ced5  perf(centroid): drop Cartesian-product COUNT in track summary
da5d5ee  perf(sources): 6h ISR cache + manual revalidation endpoint
9e028d7  feat(sources): "also covered" tail under volume chart
74591a3  feat(sources): outlet landing dashboard with stance heatmap, volume chart, topic mix
bcd38e9  feat(map): stance-coloured outlet map + prompt fix for spokesperson bundles
2960b15  feat(sources): per-month outlet pages — slug URLs + monthly stats (D-071 follow-up)
209cc87  feat(stance): outlet page editorial-stance section + nav tidy (D-071 Phase B)
4bfd88b  feat(stance): Phase B — outlet_entity_stance schema + scoring script (D-071)
f8b0f4e  refactor(stance): retire per-title LLM stance + stance-clustered narratives (D-071)
3e6eb30  fix(trending/v2): full-width hero + cross-centroid dedup
8d98d16  feat(trending): /trending/v2 prototype — centroid-style layout global
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
