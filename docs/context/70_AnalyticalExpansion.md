# Analytical Expansion Roadmap (L2)

**Last refreshed**: 2026-04-22

Next-generation analytical capabilities beyond the base pipeline
(ingest → classify → cluster → summarize → narrate). The current
system answers "What is the world talking about?" — the expansion
answers:

| Question | Mechanism | Tier | Status |
|---|---|---|---|
| What's big right now, globally? | Cross-centroid aggregation + calendar hero | — | 🟡 Prototype (`/trending/v2`, D-068) |
| Where are the active power struggles? | Cross-centroid narrative correlation | — | 📋 Vision (D-052, scope doc pending) |
| What changed this week? | Baseline deviation detection | A | 🟡 Partial (per-centroid deviations live; persistence pending) |
| Is this escalating? | Action-class sequence analysis | B | 📋 Future |
| How is this being framed? | Narrative lifecycle tracking | B | 🟡 Partial (matching works, lifecycle typing future) |
| Where is this heading? | Structural balance + historical analogues | C | 📋 Future |
| How is this being distorted? | Narrative vs. event-code gap analysis | C | 📋 Future |
| What am I missing? | Anomaly detection on expected vs. observed | C | 📋 Future |

Tiers: **A** = builds on existing data with minimal schema change,
**B** = requires new data structures or pipeline phases,
**C** = requires external data or partnership (e.g., Verdant).

---

## Current focus

Two lighthouse features driving the roadmap right now. Both sit on top
of the existing pipeline (no new data ingestion) and unlock distinctive
user value the competitor set doesn't replicate.

### Trending / Global Brief (Phase 2)

Aggregates the centroid-page pattern to global scope. Answers "what's
the state of the world this period?" in ~20 seconds of scan.

**Status — 2026-04-22**: prototype at `/trending/v2` (D-068). Full-width
cross-track hero, mechanical Overview prose, 2×2 track cards with top-5
events (cross-centroid Dice dedup), fastest-growing panel
(last-7-day source increment, current-month only), top-10 Active
Narratives sidebar, reused Trending Signals. Current `/trending` kept
live with preview link.

**Remaining before promotion**:
- Editorial LLM overview — new `global_summaries` table mirroring
  D-065 (tier-0 overall + per-track JSONB, bilingual, period_kind ∈
  {rolling_30d, monthly}). Generator at
  `pipeline/phase_5/generate_global_summary.py`. Daemon Slot 4
  integration.
- Day drill-down from hero popover — deep link to a
  global-day-overview page listing top events cross-centroid for
  that day. (Currently the popover shows per-track breakdown but
  the links go nowhere meaningful.)
- Sitemap entry for `/trending/v2` (currently only `/trending`).
- Swap `/trending/v2` → `/trending`, archive the v1 page.

**Optional follow-ups once promoted**:
- Top-centroid segmentation on the hero (instead of just 4 tracks),
  as the original roadmap note anticipated.
- "Fastest-growing" v2: apply within each track rather than global, so
  the panel surfaces the hottest story per-track rather than being
  dominated by whichever mega-story is running.

### Friction Nodes (Phase 3 — lighthouse)

Auto-detected geopolitical power struggles. Narrows the global
narrative map to ~10 active "friction nodes" (US-Iran war, Ukraine,
US-China, etc.), each with cross-centroid perspectives.

**Status — 2026-04-22**: vision only.
[`FRICTION_NODES_VISION.md`](FRICTION_NODES_VISION.md) + D-052
establish the concept. `event_strategic_narratives` is healthy (87k
Render links, all four months) — the substrate is ready.

**Next step**: one-page scope doc before any build. Specifically:
- **Algorithmic definition**: when is a cluster of narratives a
  friction node? (Candidate: meta-narrative + ≥5 active strategic
  narratives + ≥5 participating centroids in a rolling window.)
- **Detection cadence**: weekly? monthly? On-demand?
- **UI shape**: dedicated page per friction node? Or a top-level
  "Friction Map" dashboard with ~10 tiles?
- **Naming / labeling**: who gives a friction node its title?
  Editorial curation vs. LLM-generated from narrative cluster.

Everything else depends on those four answers. Explicitly deferred
until scope doc lands.

---

## Layer status — detail

### Layer 1 — Event Triple Formalization (Tier A)

🟡 **Partial — core extraction done, polarity + materialized view pending.**

What's live:
- Phase 2.1 (LLM) extracts actor / action_class / target / domain /
  subject / sector / signals / industries / entity_countries /
  importance into `title_labels`. Subject required since ELO v3.0.1
  (D-048). 126K+ labels across 2026 data.
- Signal types (persons / orgs / places / commodities / policies /
  systems / named_events) normalized and queryable.

Not yet done:
- **Cooperative / conflictual polarity** — static mapping per
  action_class (~30 lines in `core/ontology.py`). Prereq for Layers
  2 / 3 / 4.
- **`mv_event_triples` materialized view** — queryable
  (title_id, actor, action_class, domain, target, polarity, tier,
  month) for downstream analytical queries.

Effort: ~1 day once we commit.

### Layer 2 — Baseline Deviation Detection (Tier A)

🟡 **Partial — per-centroid deviations rendered, persistence pending.**

What's live:
- `getCentroidDeviationsForMonth` powers the "Unusual activity" card
  on centroid pages (week-over-week spike/drop, stance shift, new
  top actor).
- `WeeklyDeviationCard` component surfaces the signals.

Not yet done (Roadmap Phase 1 #3):
- Persist monthly snapshots to `centroid_monthly_stats` so the card
  stops recomputing per request and stops showing "same value across
  months".
- Global-scope deviation view (which centroids had the biggest
  deviation this period) — could feed the Trending v2 page.

### Layer 3 — Causal Sequence Mining (Tier B)

📋 **Future.** No work done. Depends on Layer 1 polarity.

Still a good idea: mine action_class n-grams per centroid, surface as
"historical context" sidebar on event detail pages.

### Layer 4 — Relationship Tone Graph (Tier B)

📋 **Future.** No work done. Depends on Layer 1 polarity.

Related but partial: `mv_signal_graph` exists for signal-co-occurrence
visualization. Extending to per-centroid-pair tone scoring is the
specific L4 work.

### Layer 5 — Narrative Lifecycle Tracking (Tier B)

🟡 **Partial — matching infrastructure + weekly activity live; lifecycle phases not typed.**

What's live:
- 260 curated strategic narratives (`strategic_narratives`) + 9
  meta-narratives.
- Mechanical narrative matching (Phase 4.2f in v4 arch; D-067 fixed
  DOMAIN_TO_TRACK so all four live tracks are covered). 87k links
  on Render across Jan–Apr.
- `narrative_weekly_activity` table + sparklines on narrative detail
  pages.

Not yet done:
- Lifecycle phase typing: first-appearance, peak-week, decay-rate,
  replacement-frame, publisher-adoption-curve.
- Cross-centroid spread analysis (who picks up the frame first;
  which centroids are laggards).
- This overlaps heavily with Friction Nodes — the scope doc for
  Friction Nodes should settle whether lifecycle is a distinct
  feature or folded into the same surface.

### Layer 6 — External Data Integration (Tier C)

📋 **Future.** Partnership-dependent (Verdant) or offline-import
(GDELT).

- 6a Source expansion (beyond Google News RSS): scheduled API
  ingestion into Phase 1.
- 6b Entity relationship graph: Wikidata / Verdant enrichment after
  Phase 2.1.
- 6c GDELT historical depth: extended baselines for Layer 2 + pattern
  library for Layer 3 + cross-validation of WB event coding.

---

## Guiding principles

| Principle | Description |
|---|---|
| Mechanical first | Every layer uses mechanical computation on structured data. LLMs restricted to extraction and summarization. |
| Existing data first | Layers 1-5 operate on data already in the database. No new ingestion. Layer 6 is additive. |
| Incremental | Each layer builds on the previous but is independently useful. Layer 2 works without Layer 1, just less precisely. |
| Auditable | Every analytical output traces to specific event triples, titles, and dates. No black-box scoring. |
| Not prediction | Baselines detect anomalies. Sequences surface historical analogues. Balance theory flags structural tension. The analyst interprets. |
