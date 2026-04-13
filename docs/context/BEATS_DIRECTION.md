# Beats: Temporal Event Extraction (Project Direction)

**Status**: Prototype validated on 3 CTMs (USA/security, China/economy, Baltic/security) — 2026-04-12
**Decision**: D-055
**Supersedes as primary event surface**: Phase 4.1 family assembly (D-053)

---

## What Beats is

A mechanical extraction pipeline that produces a **dated, ranked list of events** for any CTM by finding temporal anomalies inside semantically-stable lanes of headline labels. No clustering, no LLM, no family assembly.

The user-facing output for a CTM is a **Brief**: events grouped into 3-6 named **Theaters** (Iran War, Domestic, China trade, etc.) or rendered as a flat list when the CTM is small.

---

## Why

Clustering and family assembly produce **themes** — bags of similar headlines that smear across time. What a reader actually wants is **events** — specific things that happened on specific dates, ordered as a story.

The existing pipeline's granularity problem is structural:
- A cluster is a similarity bag, not a story-beat
- A family is a bag of clusters, inheriting the same ambiguity
- Mega-stories (Iran war, NPC Two Sessions) either fragment into arbitrary sub-clusters or collapse into opaque blobs
- Clustering quality varies unpredictably (precision, granularity, vector)

Diagnostic on USA/security/March: 75 families across 4 bilateral buckets, 45 of them describing the same Iran war. No family granularity is "correct" — the axis of grouping (similarity) is wrong.

**The real event granularity lives one level below the cluster**, at the intersection of
`(actor → action → target) × date × top non-ubiquitous entity`. That tuple isn't a fuzzy match — it's a ground-truth structural fact extracted by Phase 3.1.

---

## The algorithm (5 passes)

### Pass 1 — Build beats
Group every title with `title_labels` into **beats** keyed by `(actor, action_class, target)`. Each beat is a stable lane, typically active 1-30 days per month.

### Pass 2 — Detect spike days
For each beat:
- Compute daily title counts
- Compute `median` and `P75` of the lane's daily counts
- A day is a spike if: `count >= max(ABS_FLOOR, P75) AND count >= 1.5 × median`
- Drops to absolute floor only (no P75) for small lanes with flat distributions

This finds days where the beat fired unusually strongly — the mechanical signature of an event.

### Pass 3 — Name the event (entity extraction)
For each spike day, pick the top non-ubiquitous, non-blocked entity from the action-class-preferred field:
- `MILITARY_OPERATION`, `SECURITY_INCIDENT` → `places[]` first (where the strike happened)
- `POLITICAL_PRESSURE`, `POLICY_CHANGE` → `orgs[]` first (which institution/brand)
- `INFORMATION_INFLUENCE` → `orgs[]` then `persons[]`

Filters:
- **Ubiquity filter** (per-CTM, >12% of titles) drops entities that appear everywhere. On USA/security/March this drops `TRUMP`. Same mechanism as D-049 faceted clustering, applied at the naming layer.
- **Generic blocklist**: broad geographies ("Middle East", "Gulf"), news publishers leaking as orgs (CNN, Global Times), US actor-default orgs that name the actor not the event (Pentagon, CIA, DoD).

If no entity meets the absolute floor, the event still fires as an untagged spike (the date anomaly is enough signal). This is how China NPC Two Sessions was caught despite sparse labels.

### Pass 4 — Multi-event-per-day + cross-beat dedup
- A spike day can produce **up to 3 distinct events** if secondary entities also meet the absolute floor AND ≥35% of the top count. (Mar 14 USA: Kharg strike + Hormuz escort warning = two events, one day, one beat.)
- **Cross-beat dedup**: merge events where `(actor, action_class, date, entity)` match across different targets (e.g., `KP>MIL_OP>KR,US` and `KP>MIL_OP>NONE` about the same Mar 14 missile test).

### Pass 5 — Span merge + theater classification
- Merge consecutive spike days (≤2-day gap) in the same `(beat, entity)` into event spans
- Route each event through a per-centroid theater config (`THEATER_RULES`) that maps `(actor, action, target)` to a named theater
- Cap each lane at 15 events to prevent mega-lanes from dominating

---

## Mode A / Mode B (display rule)

If a CTM produces **≥15 events** → **Mode A** (theater-grouped brief).
Otherwise → **Mode B** (flat list sorted by date).

This is the degradation path for small CTMs: Baltic March produces 4 events, which render as a simple list; USA security March produces 143, which render as a 6-theater brief.

---

## Pipeline position (proposed)

```
Phase 1: Ingestion
Phase 2: Centroid matching
Phase 3.1: Label + signal extraction (LLM)          <-- Beats consumes this
Phase 3.2: Entity centroid backfill
Phase 3.3: Intel gating + track assignment (LLM)
Phase 4:   Incremental topic clustering (mechanical)  <-- kept as structural infrastructure
Phase 4.1: Family assembly (mechanical spine)         <-- kept, secondary lens
Phase 4.5: LLM summaries (optional for Beats output)
Phase 4.6: BEATS EXTRACTION (new)                     <-- primary user-facing product
  - Reads title_labels + pubdate
  - Writes events into new `beats_events` table
  - Idempotent, incremental-friendly
```

Clustering does **not** go away. Beats uses `events_v3` rows for two things:
- Source-count weighting when scoring headline representativeness
- Fallback headline picker when the English title in a cluster is richer than any single title

Families survive as a secondary lens for users who want the thematic view.

---

## Vocabulary

| Term | Meaning |
|---|---|
| **Beat** | `(actor, action_class, target)` triple. A stable narrative lane across a CTM. |
| **Event** | `(beat, date, entity)` — one story-beat occurrence. The atomic user-facing unit. |
| **Event Span** | Consecutive-day events with the same `(beat, entity)`, merged into a range. |
| **Theater** | A named group of beats for a given centroid (Iran War, Domestic, etc.). |
| **Brief** | The theater-grouped list of events for one CTM. User-facing product. |
| **Lane** | Synonym for beat when used in UI/timeline context. |

---

## Known limitations (to be fixed)

### Taxonomy (Phase 3.1) — deepest issue
- Action classes are security-biased. Economic domain defaults to `POLICY_CHANGE` / `RESOURCE_ALLOCATION` / `ECONOMIC_DISRUPTION` — categories of nothing.
- No economic entity slots: `sectors[]`, `products[]`, `technologies[]` are missing. Brands like BYD, CATL, Xiaomi either land in `orgs[]` (without LLM guidance to extract them) or are not captured at all.
- `POLITICAL_PRESSURE` and `DIPLOMATIC_PRESSURE` should merge (existing Asana).
- `POLICY_CHANGE` should split into `TARIFF_CHANGE`, `SUBSIDY`, `REGULATION`, `INDUSTRIAL_POLICY`, `MONETARY_POLICY`.

### Baseline
- Within-CTM median + P75 works for retrospective analysis but fails at month boundaries and for mega-conflict CTMs where every day is above normal.
- V2 needs a **rolling 14-day window** per beat, computed on `titles_v3.pubdate_utc` rather than CTM partition.

### Entity quality
- Publisher leakage in Phase 2 (known Asana issue) pollutes `orgs[]` with CNN, Global Times, CGTN.
- Ubiquity filter at 12% is pragmatic; on small CTMs even TRUMP fails to cross it. Consider a global ubiquity registry shared across CTMs.

### Frontend
- No UI yet. Current prototype is a Python script writing CSVs at `out/whale/`.
- Need a Beats view component: Mode A (theater timelines) + Mode B (flat list).

---

## Success criteria

1. **Recall of events, not titles**: we don't care if 30% of titles fall outside any beat or spike. We care that the significant developments of the month all appear in the Brief.
2. **Stable across CTM shapes**: same algorithm must work on mega-conflict (USA/security, 7700 titles), abstract domain (China/economy, 1200 titles), and small coverage (Baltic/security, 142 titles).
3. **Mechanical and auditable**: no LLM in the extraction loop. Every event is traceable to a `(beat, date, entity)` tuple backed by title_labels rows.
4. **Degrades gracefully**: low-volume CTMs produce fewer events, not worse events. No fabrication.

Prototype as of 2026-04-12 meets all four on the three test CTMs.

---

## See also

- `scripts/prototype_whale_extraction.py` — reference implementation
- `out/whale/*.csv` — current outputs for USA, China, Baltic
- D-055 — DecisionLog entry adopting Beats as the primary event surface
- `docs/context/CLUSTERING_ACTION_PLAN.md` — prior (now secondary) direction
