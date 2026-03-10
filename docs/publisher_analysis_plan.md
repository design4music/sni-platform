# Publisher-Level Analysis Plan

**Status:** Reviewed -- ready for implementation in sequence
**Created:** 2026-03-10
**Reviewed:** 2026-03-10

---

## Motivation

Current `/sources/[feed_name]` page is descriptive but passive -- it says "CNN wrote about X" but not "how CNN framed X" or "how CNN differs from Reuters on X." Individual media outlet bias is hard to expose with the current outlet-agnostic narrative extraction.

**Goal:** Go more granular on media outlets. Enable narrative analysis by publisher and by centroid, expose editorial alignment patterns, and enrich publisher profile pages with analytical depth.

---

## Phase 1: Publisher Analytics Dashboard (Option C) -- SQL-Only

**What:** Purely statistical metrics computed from existing data. No LLM needed.

| Metric | Description | Data Source |
|---|---|---|
| Track distribution | % military, diplomacy, economy, etc. | `title_assignments.track` |
| Geographic focus (HHI) | Concentration across centroids (0=spread, 1=mono-focus) | `title_assignments.centroid_id` |
| Actor frequency | Top-N actors this publisher covers | `title_labels.actor` |
| Narrative diversity index | Count distinct narrative frames publisher appears in | `narratives.top_sources` |
| Coverage concentration | Gini coefficient across centroids | `title_assignments.centroid_id` |
| Temporal pattern | Publication cadence, peak hours, day-of-week | `titles_v3.pub_date` |
| Signal richness | Avg persons/orgs/places per title | `title_labels` signal columns |

**Implementation:**
- All SQL aggregations, materializable as `mv_publisher_stats`.
- Daemon computes during Slot 3 (after clustering), refreshes monthly windows.
- Cheapest and fastest option to build (~1-2 days).

**UI:**
- Enhance existing `/sources/[feed_name]` page with these stats.
- Add sortable columns to `/sources` directory page (focus, diversity, etc.).
- Comparison mode deferred to future version.

---

## Phase 2: Publisher Stance Scoring (Option B)

**What:** For each (publisher, centroid, month) tuple, compute a sentiment/stance score.
*"How does CNN cover Russia this month?" -> Score from -2 (hostile) to +2 (supportive).*

**How:**
- Collect all publisher titles assigned to a given centroid within a month.
- LLM scores a sample batch for tone/framing on a 5-point scale.
- Store in new table: `publisher_stance(publisher_name, centroid_id, month, score, confidence, sample_size, computed_at)`.

**Monthly cadence (part of freeze process):**
- Computed per-month, integrated into the monthly freeze workflow.
- Enables tracking sentiment shifts over time (e.g., CNN's Russia coverage hardening after Feb 2026).
- Current month displays last month's score until new month freezes.

**Media conglomerate detection:**
- Compute stance vectors (one score per centroid) for each publisher.
- Cluster publishers by cosine similarity of their stance vectors.
- Similarity > 0.85 likely indicates shared editorial alignment.

**Cost estimate:**
- ~400 feeds x ~50 active centroids = 20K pairs.
- Filter to pairs with 20+ titles -> likely ~2-3K viable pairs per month.
- At ~$0.001/pair with DeepSeek -> ~$3 total per monthly run.

**UI:**
- Publisher page: stance map (color-coded score per centroid).
- Centroid page: "Publisher Sentiment" tab (all outlets ranked by stance).
- Media alignment page nested under `/sources/alignment` (heatmap + clustering).
- If quality is confirmed adequate (manual check): display stance score everywhere we show centroid+outlet together.

---

## Phase 3: Publisher-Scoped Narrative Extraction (Option A)

**What:** Extract one dominant narrative per publisher for a given entity (CTM, event, or epic).

**Scope:**
- Top 10 publishers by title count for each entity.
- Minimum threshold: 10+ titles per publisher for that entity.
- Start with epics (most data available), then extend to large events.

**How:**
- Filter entity's titles to a single publisher.
- LLM extracts 1 dominant narrative frame.
- Store in `narratives` table with new column `publisher_filter TEXT` (NULL = all sources).
- Pipeline-generated (batch), not on-demand.

**Quality gate:**
- Manual review of initial results required before broad rollout.
- If quality is good: include publisher narratives everywhere in pipeline generation and consider phasing out current generic (outlet-agnostic) narrative extraction.
- RAI analysis remains on-demand regardless.

**UI (to decide after quality review):**
- Options: event sidebar, accordion tabs per publisher, or dedicated section.
- Decision deferred until we see actual output quality.

---

## Phase 4 (Future): Comparative Framing Analysis (Option D)

**What:** Compare how different publishers frame the *same* event.
*"5 publishers covered the Iran strike -- here's how their framing diverged."*

**How:**
- For events with 3+ publishers each having 5+ titles.
- LLM receives all titles grouped by publisher.
- Prompt: "Compare how each outlet framed this event. Note differences in emphasis, attribution, and tone."
- Output: structured comparative analysis with divergence score.

**Deferred.** Documented for future implementation. Revisit after Phase 3 quality is confirmed.

---

## Resolved Questions

| # | Question | Decision |
|---|---|---|
| Q1 | Stance scoring: per-month or rolling? | **Per-month, part of freeze process.** Enables temporal tracking. |
| Q2 | Option A granularity? | **Epic first** (most data), then large events. Top 10 publishers, 10+ titles. |
| Q3 | Auth-gated or public? | **Decide later.** First confirm product quality. |
| Q4 | Media alignment page location? | **Nested under `/sources`** for now. |

## Open Questions

- UI for publisher narratives: sidebar vs accordion vs dedicated section? (decide after Phase 3 quality review)
- If publisher narratives are good enough, do we fully replace generic narratives or keep both?
