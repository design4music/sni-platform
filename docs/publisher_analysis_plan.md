# Publisher-Level Analysis Plan

**Status:** Phase 2 complete (UI shipped, prompt recalibrated, re-score pending)
**Created:** 2026-03-10
**Last Updated:** 2026-03-10

---

## Motivation

Current `/sources/[feed_name]` page is descriptive but passive -- it says "CNN wrote about X" but not "how CNN framed X" or "how CNN differs from Reuters on X." Individual media outlet bias is hard to expose with the current outlet-agnostic narrative extraction.

**Goal:** Go more granular on media outlets. Enable narrative analysis by publisher and by centroid, expose editorial alignment patterns, and enrich publisher profile pages with analytical depth.

---

## Phase 1: Publisher Analytics Dashboard -- COMPLETE

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

**Built:**
- `mv_publisher_stats` materialized view, refreshed by daemon Slot 3
- `/sources/[feed_name]` page: stats grid, track distribution bar, coverage map, top actors, DOW chart, top topics (3-col aggregated), narrative frames (top 5)
- `/sources` directory: sortable accordion with analytics badges (HHI, signal richness, top track)
- Loading skeleton for publisher page

---

## Phase 2: Publisher Stance Scoring -- COMPLETE (re-score pending)

**What:** For each (publisher, centroid, month) tuple, compute a sentiment/stance score.

**DB table:** `publisher_stance(feed_name, centroid_id, month, score, confidence, sample_size, sample_titles, computed_at)`

**Current data:** 690 scores, 85 publishers x 47 centroids, 2 months (Jan + Feb 2026)

### Built:
- **Scoring script:** `pipeline/phase_4/score_publisher_stance.py` -- uses PUBLISHER_MAP for name variants, samples 30 titles, LLM scores on -2..+2 scale
- **Prompt:** `core/prompts.py` STANCE_SYSTEM + STANCE_USER (moved from inline)
- **Freeze integration:** Step 4 in `pipeline/freeze/freeze_month.py`
- **Publisher page:** StanceGrid component -- color-coded grid with temporal delta arrows
- **Centroid page:** StanceSidebar -- bucketed groups (Adversarial/Skeptical/Reportorial/Constructive/Promotional), top 5 per bucket, expand for more
- **Alignment page:** `/sources/alignment` -- full heatmap (publishers x centroids), cosine similarity sort, min-coverage filter
- **OutletLogo component:** `components/OutletLogo.tsx` -- img with initials fallback on error

### Known Issues:
1. **Scores need re-generation.** Original prompt had negative skew -- reporting on wars/crises was scored as "Critical" instead of neutral. Prompt recalibrated 2026-03-10:
   - Old scale: Hostile / Critical / Neutral / Favorable / Supportive
   - New scale: Adversarial / Skeptical / Reportorial / Constructive / Promotional
   - Key fix: explicit instruction that factual reporting on negative events = score 0
   - **Action needed:** TRUNCATE publisher_stance, re-run scoring for Jan + Feb
2. **Render backfill in progress.** publisher_name normalization (Option C) UPDATE running on Render via temp table. ~46k rows remaining as of last check. Do NOT start another bulk UPDATE -- wait for completion, then verify with: `SELECT COUNT(*) FROM titles_v3 t JOIN feeds f ON f.id = t.feed_id WHERE t.publisher_name <> f.name`
3. **Render deploy needed.** Latest code pushed (commit a79a19b) but Render deploy not yet triggered.

### Publisher Naming (Option C) -- COMPLETE locally, syncing to Render
- `publisher_name` now overridden with `feeds.name` at ingestion (Phase 1 `rss_fetcher.py`)
- Local backfill done (59k rows, 0 mismatches)
- Render backfill in progress via COPY pipe + temp table
- PUBLISHER_MAP in queries.ts can be removed after Render sync confirmed
- Feed renames applied: TASS Russian -> TASS, TASS (en) -> TASS (EN), rt.com -> RT, France 24 (en) -> France 24 (EN)

### Middleware fix
- `/logos/*` added to i18n middleware exclusion list (was returning 404 for all outlet logos)
- Full exclusion: `/((?!api|_next|flags/|geo/|logos/).*)`

---

## Phase 3: Stance-Clustered Narrative Extraction -- PLANNED (revised)

**Original plan:** Per-publisher narrative extraction (Option A). Extract one narrative per publisher per entity.

**Revised plan:** Extract narratives by **stance cluster** instead of individual publishers.

**Rationale:** Publishers with similar stance scores (e.g. Fox News -1.8, Telegraph -1.7 on Iran) produce near-identical narratives. Clustering by stance and extracting one narrative per cluster is cheaper and more insightful.

**Design philosophy:** This platform compresses for clarity, not exhaustive research. 1000 articles become a 250-word summary. Same principle applies here: not "how 85 publishers each covered Iran" but "here are the 3 genuinely different ways this story was told." Frames must be REAL (grounded in actual headline clusters), not hypothetical categories the LLM invents.

**Approach:**
1. For a given entity (epic, large event, or CTM), group publishers into 3-4 stance clusters using their centroid stance scores
2. Sample headlines from each cluster
3. LLM extracts one dominant narrative frame per cluster
4. Result: "How the skeptical press framed this" vs "How the constructive press framed this"

**This merges Phase 3 + Phase 4** (comparative framing) -- you get the cross-publisher comparison without per-publisher extraction as intermediate step.

**Prerequisites:**
- Re-scored stance data with calibrated prompt (Phase 2 action item)
- Enough data (2+ months) to form stable clusters

**Open questions:**
- Cluster method: simple score buckets vs k-means vs cosine similarity groups?
- Minimum cluster size for meaningful extraction?
- Where to display: entity page sidebar, dedicated tab, or inline?
- How to label clusters in the UI? By score range or by discovered characteristics?

---

## Phase 4 (Future): Comparative Framing Analysis -- DEFERRED

Subsumed into revised Phase 3. If stance-clustered narratives work well, this becomes unnecessary as a separate phase.

---

## Resolved Questions

| # | Question | Decision |
|---|---|---|
| Q1 | Stance scoring: per-month or rolling? | **Per-month, part of freeze process.** Enables temporal tracking. |
| Q2 | Option A granularity? | **Revised:** Stance-cluster based, not per-publisher. |
| Q3 | Auth-gated or public? | **Decide later.** First confirm product quality. |
| Q4 | Media alignment page location? | **`/sources/alignment`** -- shipped. |
| Q5 | Publisher naming architecture? | **Option C:** Override publisher_name with feeds.name at ingestion. PUBLISHER_MAP to be removed after full Render sync. |
| Q6 | Scoring prompt bias? | **Recalibrated.** "Reportorial" replaces "Neutral" as center of scale. Explicit instruction: factual reporting on negative events = 0. |

## Open Questions

- Phase 3 cluster method and minimum cluster size
- UI for stance-clustered narratives
- Whether to increase sample size (currently 30 titles) or add second LLM for cross-validation
- When to remove PUBLISHER_MAP from queries.ts (after Render sync confirmed + 1 month of clean ingestion)
