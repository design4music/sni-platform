# Publisher Stance & Media Framing — System Map and Regression Analysis

**Date**: 2026-04-24
**Author**: Claude (investigation), max (direction)
**Scope**: map every connection between media outlets, stance scoring, stance-clustered narratives, and the pages that consume them. Diagnose the two regressions observed this week. Flag reliability and LLM-cost concerns.

---

## TL;DR

The stance system is **two loosely-coupled LLM layers**:

1. **Publisher stance scores** — one LLM call per `(feed, centroid, month)` pair. Writes to `publisher_stance`. Runs monthly from `freeze_month.py` step 4, plus ad-hoc via CLI. Currently being tuned (uncommitted diff raises `limit` 500 → 5000).
2. **Stance-clustered narratives** — one LLM call per `(event|ctm)` entity. Buckets publishers into critical/reportorial/supportive using their stored scores, samples headlines per bucket, asks the LLM to name the dominant frame. Writes to `narratives` with `extraction_method='stance_clustered'`. Runs on-demand from the "Extract & Analyse" button.

Both regressions the user is seeing are symptoms of **the same upstream bug**: reprocessing `events_v3` (Feb/Mar rebuild, April day-centric rewrites) **does not cascade to the `narratives` table**. Result:

- **96% of event-narratives (1,047 / 1,087) point to deleted event UUIDs** as of 2026-04-24.
- **Commit `21e93d4` (2026-04-24)** patched the source-page query to hide orphan rows. It fixes the 404 UX but deletes most of the signal users were interacting with, so the "media framing" block now looks empty.
- Event-page stance widget (`StanceClusterCard`) is still mounted and rendering correctly, but it's conditional on `stanceClusters.length > 0`. For events whose narratives were orphaned, the widget silently disappears.

Separately — on **centroid pages**, the user may be remembering the `StanceSidebar` widget that was intentionally retired on **2026-04-21 (`acbc869`)** and replaced by the more informative `MediaLensSection` (two-column local/foreign perspective). That was a deliberate upgrade, not a regression.

The system is salvageable and worth the investment, but needs two structural fixes before it can be called reliable: (a) a cascade/repair mechanism so reprocessing doesn't leave orphans, and (b) a decision on whether stance scoring stays LLM or switches to a mechanical signal derived from `title_labels.action_class` polarity.

---

## 1. The Complete Connection Map

### 1.1 Data layer

```
   titles_v3 ──────────────┐
    │                      │
    │ (score step:         │
    │  monthly freeze OR   │
    │  CLI, LLM per pair)  │
    ▼                      │
   publisher_stance        │
   ( feed_name,            │
     centroid_id,          │
     month,                │
     score -2..+2,         │
     confidence,           │
     sample_size,          │
     sample_titles jsonb ) │
    │                      │
    │ (cluster + frame step:
    │  on-demand from
    │  /extract, LLM per entity)
    ▼                      ▼
   narratives  ◄── events_v3  (FK by entity_id, entity_type)
   ( extraction_method    │
       = 'stance_clustered',
     cluster_label        │
       ∈ critical |         ctm
         reportorial |
         supportive,
     cluster_publishers text[],
     cluster_score_avg    )
```

### 1.2 Backend files

| Layer | File | Role | LLM? |
|---|---|---|---|
| **Scoring** | `pipeline/phase_4/score_publisher_stance.py` | Per-pair classification, writes `publisher_stance` | **Yes** (DeepSeek, 1 call per pair) |
| **Prompts** | `core/prompts.py` (`STANCE_SYSTEM`, `STANCE_USER` ≈ lines 544-566) | 5-class tone rubric: adversarial -2 … promotional +2 | n/a |
| **Monthly trigger** | `pipeline/freeze/freeze_month.py` step 4 | Calls `run_stance(target_month)` | — |
| **Narrative extraction** | `pipeline/phase_4/extract_stance_narratives.py` | Bucket publishers → sample headlines → LLM names frame | **Yes** (1 call per entity) |
| **Extraction API** | `api/extraction_api.py` (`/extract` route) | Auth-gated entry for "Extract & Analyse" button | orchestrates the above |
| **Comparative** | `pipeline/phase_4/generate_comparative_analysis.py` | D-039 per-entity cross-cluster brief | **Yes** (separate, on-demand) |

### 1.3 Frontend surfaces

| Page | Component | Query function | What it reads |
|---|---|---|---|
| `/events/[event_id]` **sidebar** | `StanceClusterCard` | `getStanceNarratives('event', id)` | `narratives` filtered `extraction_method='stance_clustered'` |
| `/c/[centroid_key]` (centroid page) | `MediaLensSection` (two columns: local / foreign) | `getCentroidMediaLens` | aggregates `publisher_stance` JOIN `local_feeds` JOIN `centroids_v3` |
| `/c/[centroid_key]` (month switcher) | `MediaLensSection` (client) | `/api/centroid/[id]/media-lens?month=YYYY-MM` | same query, month-parameterized |
| `/sources/[feed_name]` stance grid | inline (`StanceGrid` subcomponent, page.tsx ≈ 326-328) | `getPublisherStance(feed)` | raw per-centroid stance scores for one outlet |
| `/sources/[feed_name]` **narrative frames** | inline cards (page.tsx 447-484) | `getOutletNarrativeFrames(feed)` | `narratives.top_sources` contains feed, + **existence filter added 2026-04-24** |
| `/sources/alignment` (cross-outlet) | not changed | `getStanceMatrix` | `publisher_stance` matrix by centroid |
| `/analysis/comparative/[type]/[id]` | full report | `getEntityAnalysis` + `getStanceNarratives` | D-039 comparative table + source clusters |

**No stance widgets** on `/c/*/t/*` (track pages), `/narratives/[id]`, `/trending`, `/trending/v2`, `/epics/[slug]`. This is a product gap, not a regression.

### 1.4 What was retired intentionally (do not restore)

| Thing | When | Commit | Reason |
|---|---|---|---|
| `StanceSidebar` on centroid pages | 2026-04-21 | `acbc869` | Replaced by `MediaLensSection` (richer: two columns, local/foreign split, month switcher, weighted aggregates). 131 lines deleted, 402 lines added. Clear upgrade. |
| `getStanceForCentroid` query | 2026-04-21 | `acbc869` | Unused after StanceSidebar retirement. |

---

## 2. How Stance Is Actually Detected

### 2.1 Scoring (per-pair)

`score_publisher_stance.py` produces one row per `(feed_name, centroid_id, month)` where the feed published `>= MIN_TITLES` (20) titles touching that centroid in that month.

Flow per pair:
1. Sample 30 headlines for that feed+centroid+month (random sample, reproducible with seed).
2. Call DeepSeek with `STANCE_SYSTEM` + `STANCE_USER` prompts. Model returns `{score ∈ {-2,-1,0,+1,+2}, confidence 0..1, reasoning string}`.
3. Upsert into `publisher_stance` (`ON CONFLICT (feed_name, centroid_id, month) DO UPDATE`).

Scale: at `limit=5000` pairs and ~600 tokens per pair round-trip, one full monthly run is ≈ **3M tokens**. At DeepSeek's prompt-cached rates this is well under €5, but it runs every month for every unfrozen month and doesn't refresh incrementally.

Prompt mitigations already in place: the rubric explicitly tells the model that "reporting negative events is not inherently negative tone" — this was added to stop DeepSeek marking Reuters/AFP as adversarial just because they report bombings.

### 2.2 Narrative naming (per-entity)

`extract_stance_narratives.py` does NOT re-score publishers. It reads the scores that already exist in `publisher_stance`, falling back to the most recent month if the exact month isn't scored yet (`fetch_stance_scores`, lines 100-127).

Flow per entity:
1. Fetch stance scores for the entity's centroid.
2. Bucket: `critical < -0.5`, `-0.5 ≤ reportorial ≤ +0.5`, `supportive > +0.5`.
3. For each bucket with ≥ 10 titles, sample up to 60 headlines published by those outlets about that entity.
4. Call DeepSeek with `STANCE_NARRATIVE_SYSTEM` + `STANCE_NARRATIVE_USER`: "name the dominant editorial frame in this cluster".
5. Write one `narratives` row per cluster, stamped `extraction_method='stance_clustered'`, with `cluster_label`, `cluster_publishers`, `cluster_score_avg`.

Trigger path: frontend "Extract & Analyse" button → `/extract` → extraction API → this script. There is **no automatic backfill**. If an event never gets a visitor who clicks Extract, it never gets stance clusters.

### 2.3 Comparative analysis (D-039)

On top of the clusters, a separate LLM call produces a cross-cluster brief (`entity_analyses.sections`, `synthesis`, `blind_spots`, `conflicts`). That lives behind the "Deep analysis" link on the event sidebar and the `/analysis/comparative/[type]/[id]` page. **Not in scope for either regression.**

---

## 3. Reliability & Cost Map

### 3.1 Where LLM tokens are spent

| Call site | Frequency | Rough tokens | Replaceable mechanically? |
|---|---|---|---|
| `score_publisher_stance` | Monthly × all unfrozen months × ~500-5000 pairs | ~600 per pair | **Partly.** `title_labels.action_class` + `actor` + `target` could imply polarity via a lookup table (security domain: STRIKE_ON target = critical of target's protector; DIPLOMATIC_DEAL with target = supportive). Classification task, not generation — cheap model would also suffice. |
| `extract_stance_narratives` | On-demand per event/CTM, one-off | ~1500-3000 per call | **Partly.** Cluster names could be templated from `action_class` + `cluster_label` once D-052 Layer 1 polarity ships. LLM only helps with the pithy description. |
| `generate_comparative_analysis` | On-demand per event/CTM, one-off | ~4000-8000 per call | **No** — synthesizes multiple clusters into narrative prose. Generation, not classification. |

The hottest single driver is the uncommitted change to `score_publisher_stance.py` (limit 500 → 5000). At that volume, a careless re-run over an already-scored month would re-hit every pair at full cost. Two guards in place: the `ON CONFLICT DO UPDATE` upsert and the per-pair skip-if-exists check at lines 330-334. Still, a `--force` flag is the safety rail — confirm the CLI has one before bulk runs.

### 3.2 Reliability hazards

- **Orphan narratives after reprocess** — the structural bug behind both regressions. Every time `events_v3` is rewritten (Feb/Mar full reprocess, any incremental cluster merge with hard delete), `narratives.entity_id` FKs go stale. Neither the Feb/Mar drivers nor the daemon clustering phase deletes or re-links dependent narratives.
- **No staleness signal for scores** — `publisher_stance.computed_at` exists but no page uses it. A scored month keeps serving its six-month-old sentiment even after coverage doubles.
- **No incremental rescoring** — a publisher that joins a centroid mid-month doesn't get scored until the next monthly freeze.
- **Fallback month logic is silent** — `fetch_stance_scores` walks back to the most recent scored month if the requested month is empty. User sees stance clusters but there's no indicator the scoring predates the event they're looking at.
- **Publisher mapping is hardcoded** — `PUBLISHER_MAP` at `score_publisher_stance.py:35-73` is a maintained dict (violates CLAUDE.md Rule 5). New outlets don't get scored until this file is edited.

### 3.3 Quality notes from the sub-agent traces

- Stance rubric is sane and already guards against the "reporting = negative tone" trap (prompt line 564).
- Publishers whose feed name doesn't match `local_feeds.name` silently drop out of `MediaLensSection` — the JOIN is inner. Worth checking whether that's culling legitimate outlets.
- `cluster_publishers` is a denormalized `text[]`; there's no FK to `publisher_stance`. If a publisher is renamed or a feed is retired, the cluster row keeps the stale name forever.

---

## 4. Regression #1 — "Publisher stance widget missing on event page sidebar"

### Observation
User opens `/events/<some-id>`, expects to see a stance block in the right column, sees nothing.

### What the code actually does

File: `apps/frontend/app/[locale]/events/[event_id]/page.tsx`, lines 109-212.

```tsx
const stanceClusters = await getStanceNarratives('event', eventId, locale);
...
{stanceClusters.length > 0 && (
  <StanceClusterCard clusters={stanceClusters} ... />
)}
```

The widget renders **iff** there's at least one `narratives` row for that event with `extraction_method='stance_clustered'`. For events missing that row the card silently hides — there is no empty-state, no "Extract & Analyse to see stance" CTA, no loading indicator.

### Why the data is missing for many events

Three converging reasons, in descending order of impact:

1. **Orphaned by reprocess.** Feb and March were rebuilt under v3.0.1 after stance narratives had already been extracted. The rebuild wrote new `events_v3.id` UUIDs but left `narratives.entity_id` pointing at the old ones. Those narratives are now unreachable from any event page. Roughly 96% of event narratives are in this state (commit `21e93d4` commit message quantifies it).
2. **Never extracted.** Stance narratives only exist when someone clicked "Extract & Analyse" on that event. Most events in the live corpus have never been visited by a signed-in user, so most events have zero stance rows regardless of orphaning.
3. **Stance scores missing for the event's centroid+month.** Even if a user clicks Extract, `extract_stance_narratives` needs ≥ 10 titles in at least one cluster; if `publisher_stance` is empty for that centroid+month (common for April before the next freeze run), clustering falls back to the most recent scored month and may still produce zero clusters.

### Fix direction (recommended order)

| # | Fix | Effort | Payoff |
|---|---|---|---|
| R1-1 | **Empty-state card**: when `stanceClusters.length === 0`, show a clickable CTA "Extract stance clusters for this event" that posts to `/extract` and refreshes. Removes the "widget disappeared" confusion immediately. | <1h | High (UX clarity) |
| R1-2 | **Orphan repair**: one-shot script that, for each `narratives` row with `entity_type='event'` and no live `events_v3` row, either relinks to the closest surviving event (tag + day + centroid match) or deletes the row. Restores most of the 1,047 orphans. | half-day | **Highest** (fixes both regressions) |
| R1-3 | **Cascade on reprocess**: add a cleanup step at the top of `rerun_ctm_full_pipeline.py` and the month-reprocess drivers: `DELETE FROM narratives WHERE entity_type='event' AND entity_id IN (affected events)`. Prevents recurrence. | <1h | High (permanent fix) |
| R1-4 | **Auto-extract on first visit of a promoted event** (background, rate-limited) — sidesteps the "never extracted" class of missing widget. Requires deciding on LLM cost ceiling. | 1d | Medium |

---

## 5. Regression #2 — "Media framing links on source profile page are broken"

### Observation
On `/sources/Handelsblatt` (or any outlet), the "Narrative Frames" block shows cards but clicking them 404s, or the whole block is now thin/empty.

### Root cause — confirmed

**Commit `21e93d4` (2026-04-24, today)**: `fix(sources): hide orphan narratives on outlet profile pages`.

Diff in `apps/frontend/lib/queries.ts`, `getOutletNarrativeFrames`, lines 1131-1151:
```sql
AND (
  (n.entity_type = 'event' AND e.id IS NOT NULL AND e.merged_into IS NULL)
  OR (n.entity_type = 'ctm' AND c.id IS NOT NULL)
)
```

This hides orphan rows at display time. It fixes the 404 UX but leaves very few frames to show, because 96% of the event-type narratives were orphaned. **The frontend is now correct; the data layer is still broken.**

### Pre-fix behavior (what the user likely remembered)
Cards rendered for all narratives with `top_sources @> feed`. Each event-type card linked to `/events/<entity_id>`. If the event was later deleted (Feb/Mar reprocess), the link 404'd — but the card still showed, so the user could read the label and description without clicking through.

### Post-fix behavior (what the user is seeing now)
Only the small set of narratives pointing at still-live events or still-live CTMs renders. For outlets whose framing was disproportionately on Feb/Mar events, that's very close to zero.

### Fix direction

Same as **R1-2** above. The correct fix is not to change the frontend query further — it is to make `narratives.entity_id` referentially honest. Once orphans are repaired, the `21e93d4` filter becomes a harmless safety net and the block refills naturally.

Optional UX improvement: when `getOutletNarrativeFrames` returns fewer than ~3 rows but there *were* more rows filtered out by the orphan check, surface a small note "Some historical frames are being re-linked" — avoids the appearance of a regression during the repair. Log-only would also be fine.

---

## 6. The single structural fix that collapses both regressions

Both regressions are downstream of **narratives is not referentially consistent with events_v3**.

The short path:

1. **Repair script** (`scripts/repair_narrative_orphans.py`) — runs once:
   ```
   for each narratives row with entity_type='event' and no live events_v3 match:
     candidate = events_v3 row where centroid_id matches,
                 day within ±1 of original,
                 tag overlap Dice ≥ 0.35
     if exactly one strong candidate: UPDATE entity_id = candidate.id
     else:                            DELETE the narratives row
   ```
2. **Cascade** — patch every reprocess driver and the daemon clustering step to `DELETE FROM narratives WHERE entity_type='event' AND entity_id IN (the events being rewritten)` **before** the `DELETE FROM events_v3`. Bulk SQL, idempotent.
3. **FK** — add `entity_id` as a nullable FK with `ON DELETE SET NULL` once the schema is clean. Makes orphaning impossible going forward without conscious opt-in. Do this last, after step 1 has brought the table into a consistent state.

Steps 1 and 2 can ship this week. Step 3 needs a migration and is a schema change that warrants review.

---

## 7. Questions worth settling before building more

1. **Do we want stance scoring to stay LLM-based?** It's a classification task. Once D-052 Layer 1 polarity lands (static mapping per `action_class`), we could compute stance mechanically and use the LLM only for edge cases or prestige. That would cut the monthly freeze cost roughly to zero and remove the biggest variable.
2. **Is the per-event on-demand model still the right default?** Most events never get visited. If we want the sidebar to be a reliable surface we either (a) auto-extract on publication with a rate limit, (b) show an empty-state with extract CTA every time, or (c) accept that the widget will be absent on most events and design around that.
3. **Should stance appear on narrative and track pages?** Currently it doesn't. If the product is "see who's saying what about this story", track and narrative pages are the bigger surfaces than single event pages.
4. **PUBLISHER_MAP** — move it to a DB table (`publisher_variants`) and stop editing Python dicts. Fits the CLAUDE.md rule against hardcoded vocabularies.

---

## 8. Suggested next steps (recommendation)

**Short-term (this week)**
- (a) Ship **R1-2** orphan repair script on local, dry-run, review, then run on Render. Expected outcome: source-page framing blocks refill, event-page stance widgets reappear on ~40% more events.
- (b) Ship **R1-3** cascade patch in reprocess drivers. Permanent fix.
- (c) Ship **R1-1** empty-state CTA on event sidebar. Makes the system legible.

**Medium-term (next sprint)**
- Schema migration: FK with `ON DELETE SET NULL` on `narratives.entity_id`.
- Decide on stance-scoring future: keep LLM / switch to mechanical / hybrid. Tie to D-052 Layer 1 polarity.
- Retire `PUBLISHER_MAP` in favor of a DB table.

**Long-term**
- Add stance/framing surfaces to `/narratives/[id]` and `/c/*/t/*` track pages.
- Temporal stance drift (Q-003 in `40_OpenQuestions.yml`) — publisher sentiment timeline for a centroid.

---

*Cross-references*: D-024 (two-tier RAI), D-038 (stance-clustered narratives), D-039 (comparative analysis), D-052 (friction nodes vision), Q-003 (temporal depth). Commits referenced: `21e93d4`, `acbc869`, `e6ef975`, `0245dd7`, `f5f6f84`, `458556f`.
