# Analytical Expansion Roadmap (L2)

Next-generation analytical capabilities beyond the current pipeline (ingest -> classify -> cluster -> summarize -> narrate). The current system answers "What is the world talking about?" -- the expansion answers:

| Question | Mechanism | Tier |
|---|---|---|
| What changed this week? | Baseline deviation detection | A |
| Is this escalating? | Action-class sequence analysis | B |
| How is this being framed? | Narrative lifecycle tracking | B |
| Where is this heading? | Structural balance + historical analogues | C |
| How is this being distorted? | Narrative vs. event-code gap analysis | C |
| What am I missing? | Anomaly detection on expected vs. observed coverage | C |

Tiers: **A** = builds on existing data with minimal schema change,
**B** = requires new data structures or pipeline phases,
**C** = requires external data or partnership (e.g., Verdant Intelligence).

---

## Layer 1: Event Triple Formalization (Tier A)

LLM already extracts ACTOR -> ACTION_CLASS -> DOMAIN (-> TARGET) with 17 actor types, 26 action classes, 7 domains. Stored in `title_labels`. What's missing:

| Missing Piece | Change | Effort |
|---|---|---|
| Target consistency | Make TARGET required in prompt (use "NONE" for non-directed events) | ~1 line in `core/prompts.py` |
| Actor-person linkage | Link actor field to persons signal (e.g., US_EXECUTIVE[Trump]) | Extraction prompt update |
| Cooperative/conflictual polarity | Static COOPERATIVE/CONFLICTUAL/NEUTRAL mapping per action class | ~30 lines in `core/ontology.py` |
| Queryable triple storage | `mv_event_triples` materialized view (title_id, actor, action_class, domain, target, polarity, tier, month) | ~50 lines in `pipeline/phase_4/` |

Backfill: ~95K rows. **Total: ~1 day. No schema migration needed if using a view.**

---

## Layer 2: Baseline Deviation Detection (Tier A)

Detect deviations from "normal" per centroid using rolling 3-month baselines.

**Baseline metrics (per centroid, rolling 3-month window):**
- Events per week (mean, stddev)
- Mean importance score
- Action class distribution (% per tier)
- Top 5 recurring actors
- Cooperative/conflictual ratio (from Layer 1 polarity)
- Source diversity (mean publisher count per event)

**Implementation:**
- Compute baselines in daemon (Phase 4.2c), flag when |z-score| > 2
- Store in `mv_centroid_baselines` (centroid_id, week, metrics JSONB)
- Frontend: deviation alerts on centroid page or "Watchboard"
- **Depends on: Layer 1 (polarity), but can start without it using raw event counts**
- **Estimate: 2-3 days**

---

## Layer 3: Causal Sequence Mining (Tier B)

Sequential pattern mining on action_class time series per centroid. Not prediction -- empirical pattern discovery from historical data. Extract n-grams with configurable gap tolerance (e.g., 7-day window) to find recurring sequences like ECONOMIC_PRESSURE -> STRATEGIC_REALIGNMENT.

When a new event arrives, match against known sequence prefixes and surface historical completions (e.g., "In 3 of 4 previous instances where X followed Y, Z followed within 30 days"). Clearly labeled as historical analogue retrieval.

**Implementation:**
- Mine patterns from 4+ months of event_triples (offline script)
- Store in `analytical_patterns` table; match new events in daemon
- Surface on event detail page as "Historical Context" sidebar
- **Depends on: Layer 1. Estimate: 3-4 days**

---

## Layer 4: Relationship Tone Graph (Tier B)

Monthly "relationship tone" between centroid pairs from bilateral events. Ratio of cooperative to conflictual events (Layer 1 polarity) produces -1.0 to +1.0 score per pair per month.

**What this enables:**
- **Relationship trajectory**: bilateral tone over 6 months as a sparkline
- **Structural balance detection**: unbalanced triads (two hostile + one friendly) flagged as "watch"
- **Alliance shift detection**: tone sign changes flagged as significant events

**Implementation:**
- Compute in daemon (Phase 4.2d), store in `mv_relationship_tone`
- Frontend: relationship graph visualization (nodes = centroids, edges = tone)
- **Depends on: Layer 1. Estimate: 3-4 days compute, 2-3 days visualization**

---

## Layer 5: Narrative Lifecycle Tracking (Tier B)

Track narrative frames as competing organisms with birth, peak, decay, and replacement dynamics. For each frame, track: first appearance, peak week, decay rate, replacement frame, publisher adoption curve, and cross-centroid spread.

Requires re-extraction of narratives with temporal anchoring (which titles contributed to which frame, with dates). New table: `narrative_lifecycle` (narrative_id, frame, week, title_count, publisher_breakdown JSONB).

**Depends on: existing narrative extraction + temporal title linkage. Estimate: 4-5 days**

---

## Layer 6: External Data Integration (Tier C)

### 6a: Source Expansion
Ingest from sources beyond Google News RSS (regional outlets, think tanks, government press releases). Scheduled API pull into Phase 1.

### 6b: Entity Relationship Graph
Enrich signals with relationship context from Wikidata, Verdant's knowledge graph, or static curated tables. Post-Phase 3.1 enrichment step.

### 6c: Historical Depth (GDELT)
Billions of coded events back to 1979, free. Provides extended baselines for Layer 2, deeper pattern library for Layer 3, and validation of WB event coding. Offline import only.

---

## Implementation Priority

| Phase | Layers | Focus | Estimate |
|---|---|---|---|
| I: Foundation | 1 + 2 | Event triples + baseline deviation. Low-hanging fruit, existing data. | 3-4 days |
| II: Temporal Intelligence | 3 + 4 | Causal sequences + relationship tone. Requires Layer 1 polarity. | 6-8 days |
| III: Narrative Dynamics | 5 | Narrative lifecycle. Requires rethinking extraction model. | 4-5 days |
| IV: Data Expansion | 6 | External data. Partnership-dependent (Verdant) or public (GDELT). | TBD |

---

## Guiding Principles

| Principle | Description |
|---|---|
| Mechanical first | Every layer uses mechanical computation on structured data. LLMs restricted to extraction and summarization. |
| Existing data first | Layers 1-5 operate on data already in the database. No new ingestion or dependencies. Layer 6 is additive. |
| Incremental | Each layer builds on the previous but is independently useful. Layer 2 works without Layer 1, just less precisely. |
| Auditable | Every analytical output traces to specific event triples, titles, and dates. No black-box scoring. |
| Not prediction | Baselines detect anomalies. Sequences surface historical analogues. Balance theory flags structural tension. The analyst interprets. |
