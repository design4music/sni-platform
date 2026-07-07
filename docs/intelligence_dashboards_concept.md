# Intelligence Dashboards: Concept Proposal

Status: concept draft, 2026-07-07. Companion to `fn_map_data_sources.md`
(data provenance) and the fn-map branch implementation. Purpose: define how
WorldBrief evolves from "a map on the home page" into a set of intelligence
products that business analysts, corporate risk managers, politologists and
media professionals would pay for -- without departing from the current
architecture.

---

## 1. The thesis: pressure x exposure

WorldBrief now owns two datasets that almost no competitor combines:

1. **A live politics engine.** The news pipeline ingests every 12h, matches
   events to friction nodes (conflicts pinned to `centroids_v3`), scores
   importance, extracts narratives and media framing. This is *dynamic
   pressure*: what is happening, how hard, and how it is being told.
2. **A source-anchored economic terrain.** 340 strategic assets (registry-
   driven: chokepoints, ports, fields, refineries, LNG, power plants, mines,
   crop belts, fabs, cables) plus directed `asset_flows` with via-chokepoint
   routing. This is *static exposure*: what the world runs on and which
   narrow passages it runs through.

The product is the multiplication of the two:

```
event stream -> FN intensity -> asset stress -> flow exposure -> WHO IS AFFECTED
(pipeline)     (exists)         (exists)        (exists, oil pilot)  (the product)
```

Every step up to the last one already exists in the schema
(`friction_nodes.affected_asset_ids`, `asset_flows.via_asset_ids`). The
dashboards proposed below are different windows onto that one chain,
each shaped for a persona.

**Positioning.** Enterprise risk platforms (Verisk Maplecroft, S&P Country
Risk, Seerist, RANE, Kpler, Sayari) sell to Fortune-500 security teams at
enterprise price points and quarterly-refresh country scores. Nobody serves
the analyst, the mid-market risk manager, the journalist, or the researcher
at an accessible tier with *news-cadence* (2x/day) risk updates and
transparent sourcing. That underserved middle is the market. WorldBrief's
differentiators against all of them:

- **Freshness**: risk state derives from the last 12h of global coverage,
  not last quarter's analyst review.
- **Narrative layer**: nobody else shows *how the same risk is framed*
  across media systems (media lens, stance analysis). Unique to us.
- **Transparency**: every asset and flow carries its ranking authority and
  rank note; the platform asserts the report, not the fact.

---

## 2. Raw material inventory (what we build from)

| Layer | Table(s) | State |
|---|---|---|
| Geographic entities | `centroids_v3` (96+ active) | production |
| Conflicts / frictions | `friction_nodes` (+ `event_friction_nodes` counts, anchor points, `affected_asset_ids`) | production |
| Strategic assets | `strategic_assets` (340, registry-driven, subcategory + provenance on every row) | fn-map branch |
| Supply flows | `asset_flows` (oil pilot, 23 rows, via-chokepoint routing, status/as_of/source) | fn-map branch |
| Events + importance | pipeline tables, importance scoring, monthly archives since 2026-01 | production |
| Narratives + framing | narratives_v2, media lens, stance analysis, RAI engine | production |
| Prose generation | event prose, daily briefs, comparative analysis (EN+DE) | production |

Everything below is a recombination of this inventory plus, in later
phases, a small number of free external feeds.

---

## 3. Persona-driven dashboard concepts

### 3.1 Corporate risk manager -- "My Exposure"

*Job to be done: "Tell me when the world starts threatening MY supply
chain, not the world in general."*

- **Watchlist portfolio.** User selects assets, flows, chokepoints,
  countries (e.g. "Hormuz, Suez, Taiwan Strait, our Rotterdam-bound
  flows, Vietnam"). Everything else in the product filters to this lens.
- **Exposure dashboard.** Pressure trend per watched item (event-count
  derived, we have monthly history), current stress state, flows-at-risk
  list ("3 of your 7 watched flows transit a pressed chokepoint").
- **Threshold alerts.** "Hormuz pressure crossed threshold" / "flow status
  changed to suspended" -> email/webhook. The daemon already computes the
  underlying numbers 2x/day; alerting is a diff + notify step.
- **Weekly exposure brief.** Auto-generated prose (the pipeline already
  writes briefs) scoped to the watchlist: what happened near your assets
  this week, in five paragraphs, EN or DE. This artifact alone justifies a
  subscription -- it is the thing a risk manager forwards to their boss.

### 3.2 Business analyst -- "Commodity Lens"

*Job: "I cover copper / LNG / wheat. Give me the standing page I check
every morning."*

- **Per-commodity dashboard** (the `subcategory` dimension, already in the
  DB, finally earns its keep): map filtered to one commodity's production
  clusters, chokepoints, flows; event feed filtered to FNs pressing those
  assets; active narratives touching the commodity.
- **Commodity pressure index.** Aggregate stress across a commodity's
  asset set, weighted by criticality -- a single 0-100 number with a
  trend line and a documented, transparent formula. Coarse by design (no
  pretend precision); its value is *consistency over time*, which our
  monthly archives can already backfill for 2026.
- **"What changed" diffs.** Week-over-week: new flows suspended, stress
  risers/fallers, new events on watched clusters. Analysts live on deltas.

### 3.3 Politologist / researcher -- "Theater Briefing Room"

*Job: "Deep context on one conflict, with evidence I can cite."*

- **FN deep-dive page** (extends what exists): participants and capitals,
  event timeline with importance-weighted highlights, affected assets and
  their downstream flows, editorial summary, and -- the unique part --
  **media framing comparison**: how outlet clusters frame this theater
  (media lens + stance data we already compute).
- **Cross-theater comparison.** Two FNs side by side: intensity curves,
  narrative divergence, asset exposure overlap.
- **Export.** CSV/JSON of event counts, pressure series, asset lists,
  with source citations. Researchers cite what they can download; every
  export is an advertisement.

### 3.4 Media professional -- "Story Radar + Context Packs"

*Job: "Find the under-told story; give me instant, citable context."*

- **Story radar.** Importance scoring vs. coverage volume exposes the gap:
  events that are materially significant but under-covered (or the
  reverse -- saturation stories losing material significance). That
  contrast is itself a story generator.
- **Context pack.** One click on any event/FN/asset -> auto-assembled
  brief: map snippet, affected assets and flows with rank notes ("Qatar's
  QAFCO alone is ~14% of global urea trade -- IFPRI/Rystad"), historical
  timeline, framing summary. Everything sourced, everything quotable.
- **Embeddable map widgets.** An interactive chokepoint or theater map
  embed with "Source: WorldBrief" attribution. Distribution and marketing
  in one feature -- every embed is a backlink.

### 3.5 (Adjacent, later) Comms / public-affairs teams

The narrative layer (framing, stance) serves a fifth persona -- corporate
communications monitoring how their sector's crisis is being framed across
media systems. Noted, not designed here; it falls out of 3.3/3.4.

---

## 4. Product surfaces (concrete, ranked by build-cost-over-existing)

| # | Surface | One-liner | Builds on | New ingredients |
|---|---|---|---|---|
| A | **Chokepoint Monitor** | A standing public page per systemic chokepoint (Hormuz, Suez, Malacca, Taiwan...): live pressure, transiting flows, who depends, event feed | FN pressure + via_asset_ids + registry rank notes | none -- pure recombination |
| B | **Commodity Lens** | Per-commodity dashboard + pressure index | subcategory column + asset stress | index formula (transparent) |
| C | **Change Feed** | "What changed this week" across the whole map; the diff is the product | daemon state, 2x/day snapshots | snapshot-diff job |
| D | **Exposure Watchlist** | Portfolio -> filtered dashboard + alerts + weekly auto-brief | auth (NextAuth), brief generation, stress chain | watchlist table, alert job |
| E | **Theater Briefing Room** | FN deep-dive with media framing comparison | centroid pages, media lens, narratives | layout + framing join |
| F | **Disruption View** | "Suspend Hormuz" toggle -> every dependent flow reddens, affected endpoints listed. Topological, not econometric -- honest about what it is | via_asset_ids propagation (already renders on selection) | a UI toggle + endpoint rollup |
| G | **Context Packs / API / embeds** | Machine-readable exposure data + embeddable widgets | API routes exist | keys, rate limits, embed loader |

A, C and F are near-free: they expose relationships already computed.
D is the monetization anchor. E is the differentiation anchor. A is the
distribution anchor (SEO: "strait of hormuz status" searches land on us).

---

## 5. External data sources to consider

Ranked by (license x integration effort x insight gained). Guiding rule:
free, structured, and joinable to an existing entity beats rich-but-paid.

### Tier 1 -- quick wins (free, API, direct join to existing entities)

| Source | What it adds | Joins to |
|---|---|---|
| **IMF PortWatch** | Satellite-AIS port calls + chokepoint transit volumes, weekly, free. Turns our chokepoint "pressure" (media attention) into *observed traffic* -- the single highest-value addition: attention vs. reality on one chart | chokepoints, ports |
| **UN Comtrade** | Official bilateral trade values -- sizes our flows (coarse classes stay, but calibrated) and enables country-level dependence ratios | asset_flows, centroids |
| **Consolidated sanctions lists (OFAC/EU/UK)** | Sanction flags on assets/flows/countries; auto-annotates "sanctioned trade" flows we currently hand-note | assets, flows, centroids |
| **FRED / public commodity prices** | Price series next to pressure series -- "did the market react to what the news pressure shows?" Pure overlay, no advice | commodity lens |
| **Cloudflare Radar** | Internet disruption/outage signals, free -- pressure ground-truth for the cable/data layer | tech assets |

### Tier 2 -- medium effort, high credibility

| Source | What it adds | Notes |
|---|---|---|
| **ACLED** | Curated conflict event data (fatalities, actors, locations) -- corroborates/enriches FN intensity with a citable academic standard | license terms need review for commercial use |
| **GDELT** | Massive free event/tone firehose -- second opinion on attention volume; noisy, use as corroboration only | free |
| **GEM power/coal/steel trackers** | Deepen power + add steel plants; same CC BY licensing we already credit | already integrated for pipelines |
| **Lloyd's Joint War Committee listed areas** | War-risk insurance zones -- the insurance market's revealed risk assessment; strong, quotable signal | public announcements, low volume |
| **Baltic Dry / Drewry WCI (headline values)** | Freight-cost context for corridor pressure | quotable headline numbers |
| **FAO/USDA PSD APIs** | Crop production/stock updates for agriculture assets (we anchor to them already; APIs automate refresh) | free |

### Tier 3 -- aspirational / paid (only when revenue justifies)

| Source | What it adds |
|---|---|
| Commercial AIS (Kpler, Spire, MarineTraffic) | Real vessel-level flow observation -- upgrade flows from "reported" to "observed" |
| TeleGeography | Authoritative submarine cable geometry/capacity |
| Sayari / corporate registries | Ownership graphs -- company-level exposure (currently out of scope by design) |
| Prediction markets (Polymarket) | Market-implied probabilities on geopolitical events -- creative overlay, handle with care |

**Deliberate non-additions:** company-level supply chains (scope trap),
anything requiring "real-time" claims (12h freshness ceiling is a
documented feature, not a bug), proprietary scores we cannot explain.

---

## 6. Monetization structure (pragmatic)

| Tier | Contents | Role |
|---|---|---|
| **Public** | Map, chokepoint monitor pages, weekly global brief, story radar teaser | SEO + distribution + credibility; embeds carry attribution |
| **Pro (analyst seat)** | Watchlists, alerts, commodity lenses, change feed, full history, exports, weekly exposure brief | The subscription core; priced for individuals/mid-market, an order of magnitude under enterprise platforms |
| **Team / API** | API keys, embeddable widgets without attribution, multi-seat, custom watchlist briefs | Growth tier |
| **Custom reports** | The existing two-tier RAI comparative-analysis machinery, aimed at exposure questions ("assess our Red Sea exposure") | High-touch revenue, already half-built |

Sequencing matters more than pricing precision: public tier first (traffic
and trust), Pro when watchlist + alerts exist, API/embeds when someone asks.

Guardrails (already in our disclaimer draft): editorial intelligence
product, not an operational dataset; no investment advice; coarse classes,
no invented precision; every claim carries source + as-of.

---

## 7. Phasing (each phase ships something visible; no big-bang)

**Phase 1 -- expose what exists (no new data, fn-map branch).**
Chokepoint Monitor pages (A), commodity filter wired to the existing
subcategory column (B without the index), Disruption View toggle (F),
Change Feed (C, from daemon snapshots). Outcome: the home-page map becomes
five product surfaces.

**Phase 2 -- the subscription core.**
Watchlist table + exposure dashboard + threshold alerts + weekly
auto-brief (D). Commodity pressure index with published formula (B
complete). This is the moment a paywall becomes defensible.

**Phase 3 -- external calibration.**
IMF PortWatch join (attention vs. observed traffic on chokepoint pages --
the credibility jump), Comtrade flow sizing, sanctions flags, price
overlays. Expand asset_flows beyond oil (gas next; the Europe LNG
dependency web is the strongest demo).

**Phase 4 -- distribution and depth.**
API + embeds (G), Theater Briefing Rooms with framing comparison (E),
context packs for media (3.4), ACLED/GDELT corroboration layers.

Standing prerequisite before any paid tier: the verification sweep of
agent-drafted asset/flow facts (tracked in `fn_map_data_sources.md`).

---

## 8. Risks and honest limits

| Risk | Mitigation |
|---|---|
| Credibility: one wrong "suspended" flow in front of a paying risk manager | status/as_of/source on every row; PortWatch ground-truth; verification sweep before paywall; correction policy |
| Attention is not severity (media-derived pressure) | say so, everywhere; pair with observed signals (PortWatch, war-risk zones) as they land |
| Alert fatigue | thresholds on *changes*, weekly digest as default, per-item mute |
| License drift (ACLED, GEM CC-BY, Comtrade terms) | licensing table in fn_map_data_sources.md is already the register; extend per source |
| Solo-maintainer bandwidth | every surface must be a view over the existing daemon output -- nothing that adds a new manual curation duty without a revenue reason |
| Enterprise incumbents moving down-market | speed + narrative layer + transparency are the moats; do not compete on data breadth |

---

## 9. Open questions (for discussion, not blockers)

1. **Which persona first?** Recommendation: analyst/risk-manager (3.1/3.2)
   for revenue, with the public Chokepoint Monitor (A) built first as the
   demo and SEO engine -- it serves all four personas at once.
2. **Index formula governance.** The commodity pressure index formula
   becomes a public commitment once analysts track it; version it like an
   API (v1, documented, changelog).
3. **DE localization scope for dashboards** -- default yes per project
   rule, but decide whether Pro-tier prose (weekly exposure briefs) ships
   bilingual from day one.
4. **Anonymous vs. account-gated** boundary for Phase-1 surfaces --
   chokepoint pages public, disruption toggle behind a free account
   (email capture)?
5. **Naming** -- these surfaces deserve a product name distinct from
   "the map" (working candidates: WorldBrief Exposure, WorldBrief Terrain).
