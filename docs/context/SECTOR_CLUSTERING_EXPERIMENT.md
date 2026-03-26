# Sector-Based Clustering Experiment

**Branch**: `feat/sector-clustering`
**Last Updated**: 2026-03-26
**Status**: Temporal hard mode + mechanical merge + incremental mode built and tested. Ready for content review, then LLM title generation + pipeline integration.

---

## Motivation

The Iran war spike (4-5x daily ingestion) exposed clustering fragility. The existing Phase 4
incremental clustering (`incremental_clustering.py`) uses anchor signals to group titles within
track buckets. Under volume spikes, generic signals like "Iran" pull hundreds of unrelated titles
into mega-events (2K+ titles on a single event).

Root cause: clustering happens per-track using raw signal overlap with no semantic grouping layer.

## Algorithm: 4-Level Hierarchical Clustering

`cluster_topdown()` in `pipeline/phase_4/rebuild_centroid.py`

```
L1:   sector + subject          (semantic domain gate)
L1.5: directional target split  (>UA = home attacks Ukraine, <UA = Ukraine attacks home)
L2:   anchor keyword split      (specific frequent signals, e.g., "Druzhba", "IEA")
L3:   Louvain community detect  (identity label Jaccard similarity)
```

### L1: Sector + Subject

Groups titles by controlled vocabulary extracted in Phase 3.1. 12 sectors, ~80 subjects.
Subject is required (was optional). 6 subjects added in this experiment:
BILATERAL_RELATIONS, SUMMIT, DEFENSE_POLICY, LAW_ENFORCEMENT, R_AND_D, PROTEST.

NON_STRATEGIC sector (SPORTS, ENTERTAINMENT, CELEBRITY, LIFESTYLE, LOCAL_CRIME, WEATHER)
filtered before clustering. France/March: 263 titles filtered (19%).

Groups with <= 3 titles become single topics. Groups < LOUVAIN_SPLIT_THRESHOLD (50) stay
as single topics. Groups >= 50 proceed to L1.5.

### L1.5: Directional Target Split

Separates story axes by who-does-what-to-whom:
- `>IR`: home country actor targets Iran
- `<UA`: foreign actor (Ukraine) targets home country
- `DOMESTIC`: no foreign target or actor

This prevents mixing "Russia strikes Ukraine" with "Ukraine strikes Russia" in the same topic.
Uses actor prefix (UA_ARMED_FORCES -> country UA) as fallback when target is self.

TARGET_SPLIT_MIN = 3. Groups with < 3 titles for a target absorb into remainder.

### L2: Anchor Keyword Split

Within large groups, finds specific frequent signals (>= 8 titles, < 40% of group) that
indicate distinct sub-stories. Titles sharing an anchor form sub-groups before Louvain.

Excludes: protagonist persons (MACRON for France, PUTIN for Russia), home cities (PARIS,
MOSCOW), and self-target country codes (TGT:RU for Russia).

Example: Russia ENERGY/OIL_GAS (359 titles) splits into TGT:EU, TGT:IN, PER:DMITRIEV,
PLC:HORMUZ sub-groups.

### L3: Louvain Community Detection

Builds a graph of titles connected by shared identity labels (persons, orgs, places,
named_events, target) with Jaccard similarity as edge weight. Louvain finds communities.

Zero-label titles (no identity signals after filtering) merge into the largest community
within their group.

### Post-Clustering

- **Temporal hard split** (2026-03-26): clusters spanning > 5 days are split at natural
  temporal gaps (>= 3 days between consecutive titles). Falls back to fixed 5-day windows
  if no natural gaps. Produces event-level topics (median 3-day spread) instead of
  month-spanning thematic buckets.
- **Coherence gate**: dissolves incoherent clusters (core feature count < 3) to catchall
- **Mechanical cluster merge**: same sector + date overlap within 3 days + >= 3 shared
  identity labels (Jaccard >= 0.20). Excludes protagonist persons and ubiquitous targets
  (>25% of sector clusters). Catches same-entity duplicates from Louvain fragmentation.
- **Track assignment**: mechanical SECTOR_TO_TRACK mapping per cluster
- **Geo tagging**: bilateral if top foreign centroid in >= 50% of cluster titles
- **Mechanical title merge**: Dice word overlap >= 0.40 on generated titles within same
  sector (catches "Zelensky visits Paris" split across MEDIATION vs SUMMIT subjects)

### Incremental Mode (2026-03-26)

`incremental_update()` in `rebuild_centroid.py` -- for daemon use:
1. Loads only unlinked titles (not yet in any event for this centroid+month)
2. Clusters with full pipeline (sector+subject -> temporal hard -> coherence -> merge)
3. Matches each new cluster against existing events by sector + date + label overlap
4. Matched titles join existing events (preserving event IDs). Unmatched create new events.
5. Old events untouched -- stable IDs for bookmarks, narrative links, sagas.

Handles volume spectrum: Melanesia (6 titles/month) to USA (10K+). Temporal windows
ensure clusters from different weeks don't interfere. Active window (~5 days) is the
only zone of potential reshuffling.

---

## What Worked

1. **Sector+subject as primary gate**: eliminates mega-events entirely. No cluster exceeds
   ~100 titles even for high-volume centroids like Russia (2645 strategic titles).

2. **NON_STRATEGIC filtering**: mechanically removes 12-20% of titles (sports, entertainment).
   More reliable than LLM intel gating which leaked sports through conflict language.

3. **Directional target split**: cleanly separates opposite-direction stories. Russia
   MILITARY/MISSILE: "Russia strikes Ukraine" (23 titles) vs "Ukraine strikes Russia" (20)
   are now distinct topics.

4. **Subject fill rate 100%**: expanded taxonomy with 6 new subjects eliminated all NULL
   subjects. BILATERAL_RELATIONS absorbed 51 of 64 DIPLOMACY/NULL titles.

5. **Anchor keywords**: break up large same-target groups by specific signals (Druzhba
   pipeline vs India oil exports vs IEA emergency release).

6. **Frontend unified topic list**: flat feed ordered by source count, country badges for
   bilateral topics. Cleaner than domestic/international accordion split.

7. **Core title selection**: centrality-based selection shows the 10 most representative
   source headlines per topic (highest word overlap with cluster corpus).

## What Didn't Work

1. **L2 actor+action_class hard partition** (removed): split groups into 85% tiny fragments
   (<=3 titles). Same story labeled DIPLOMATIC_PRESSURE by one source and POLICY_CHANGE by
   another became separate groups. Replaced by Louvain which handles fuzzy boundaries.

2. **Louvain resolution tuning for merging**: tried resolution 0.5, 0.3, 0.1 -- Louvain
   fundamentally splits MILITARY/NUCLEAR into EU-target vs FR-target communities at every
   resolution because the graph has a natural structural cut. No resolution fixes this.

3. **Min-community absorb + dominant-label merge**: attempted to merge small Louvain
   communities into large neighbors, then merge communities sharing dominant labels. The
   cascading merge was unpredictable -- sometimes correctly merged nuclear topics, sometimes
   incorrectly merged Paris+Marseille elections because both shared PER:MACRON in top-3.

4. **Threshold-only approach** (LOUVAIN_SPLIT_THRESHOLD = 100): kept groups < 100 as single
   topics. Worked for France but would flatten small centroids into one-topic-per-subject.

5. **Title word overlap for merging nuclear topics**: generated titles paraphrase too
   aggressively. "Macron proposes European nuclear protection plan" vs "France announces
   plans to increase nuclear arsenal" share only 1 content word after stop-word removal.
   Mechanical title merge works for obvious duplicates but not for paraphrased variants.

6. **Diversity-based core title selection**: picking one title per language scattered
   unrelated headlines. A cluster about Bushehr nuclear plant showed Finland nuclear,
   Ukraine nuclear, EU deterrence headlines because each was from a different language.

7. **Soft temporal mode**: edge weight decay (0.07/day) on Louvain graph barely moved
   results. Label-based Jaccard dominates; temporal decay can't overcome structural
   graph cuts. Hard temporal split is far more effective.

8. **Mechanical merge over-merging via protagonist**: PER:MACRON appears in every French
   cluster; combined with any one shared target it triggered false merges. Fixed by
   excluding protagonist persons + ubiquitous targets (>25% of sector clusters) from
   merge label matching.

9. **Mechanical merge cannot catch paraphrased duplicates**: Macron nuclear speech split
   into TGT:EU vs TGT:GB communities by Louvain. Without PER:MACRON, zero shared labels.
   Needs LLM merge pass.

---

## Test Results (2026-03-26, temporal=hard + mechanical merge)

| Centroid | Strategic | Topics | Catchall | Merges | Median spread |
|----------|-----------|--------|----------|--------|---------------|
| France | 1,104 | 132 | 14% | 17 | 3 days |
| Russia | 2,645 | 300 | 22% | 28 | 3 days |

Previous results (no temporal, no merge):

| Centroid | Strategic | Topics | Catchall |
|----------|-----------|--------|----------|
| France | 1,104 | 84 | 23% |
| Russia | 2,645 | 164 | 34% |

Temporal hard mode roughly doubles topic count (event-level vs thematic-bucket), drops
catchall significantly, and produces median 3-day temporal spread (was 10-12 days).

---

## Frontend Changes (this branch)

1. **Unified topic list**: removed domestic/international accordion split. Single feed
   ordered by source count. Country badges (flag + name) on bilateral topics, linked to
   that country's CTM page.

2. **"Load 10 more" pagination**: incremental, replaces binary show-all toggle.

3. **Core title selection**: centrality-based (word overlap with cluster corpus). Top 10
   most representative headlines shown under each topic.

4. **Sidebar TOC removed**: only had 2 items, not useful.

5. **CTM summary prompt**: no more Domestic/International section headers. Unified 2-3
   paragraph digest. Frozen Jan/Feb summaries with `### Domestic` headers still render.

---

## Known Issues (open)

1. **Signal normalization bugs**: AIR FRANCE -> FRANCE, Coupe de France -> Tour de France.
   Causes false signal matches. Not blocking but should fix before production.

2. **Multi-country centroids** (Baltic): sector+subject grouping too coarse when 3 countries
   share a centroid. Each country's local stories mix. Potential fix: sub-group by country
   within the centroid before clustering.

3. **LLM merge pass not yet implemented**: mechanical merge (label-based) catches same-entity
   duplicates but misses paraphrased variants (e.g., nuclear speech with TGT:EU vs TGT:GB).
   Planned: targeted LLM merge for top topics per sector.

4. **Core title selection not yet wired to LLM generation**: currently display-only. The
   pipeline still sends all titles to the LLM. Planned: use the same centrality selection
   to feed only the top 10 titles to the LLM for title+description generation.

5. **geo_society track is a catch-all for soft content**: MEDIA_PRESS, EDUCATION, etc. mix
   with strategic content like HUMAN_RIGHTS, MIGRATION, PROTEST. Needs taxonomy review.

6. **CTM_PROTAGONIST and CTM_HOME_CITIES are hardcoded dicts**: should move to DB or
   derive from centroid profiles.

---

## Next Steps

1. **Content review**: review France and Russia clusters on frontend with temporal hard mode.

2. **LLM title+description generation from core 10 titles**: wire centrality selection
   into `generate_event_summaries_4_5a.py`.

3. **LLM merge pass**: targeted dedup for paraphrased-variant duplicates (e.g., nuclear
   speech TGT:EU vs TGT:GB). Mechanical merge handles same-entity duplicates already.

4. **Pipeline integration**: wire `incremental_update()` into daemon Phase 4 slot. Replace
   `incremental_clustering.py`. Use `rebuild()` with `--temporal hard` for full month
   rebuilds, `--incremental` for daily daemon runs.

5. **Full March rebuild**: re-extract labels with expanded taxonomy, recluster all centroids
   with temporal hard + merge, regenerate LLM prose. Cascade: delete narratives, analyses,
   re-run saga chaining, re-run narrative matching (4.2f/g/h).

6. **geo_society cleanup**: review MEDIA_PRESS / EDUCATION content, consider expanding
   NON_STRATEGIC or remapping strategic subjects to other tracks.

---

## Files

| File | Role |
|------|------|
| `pipeline/phase_4/rebuild_centroid.py` | Test harness: cluster + write + merge + title gen |
| `pipeline/phase_3_1/extract_labels.py` | Label extraction (sector/subject added) |
| `core/prompts.py` | Extraction prompt (expanded taxonomy), CTM summary (unified) |
| `pipeline/phase_4/generate_event_summaries_4_5a.py` | Event title/summary generation |
| `pipeline/phase_4/generate_summaries_4_5.py` | CTM digest generation (unified, no dom/intl split) |
| `apps/frontend/app/[locale]/c/[centroid_key]/t/[track_key]/page.tsx` | CTM page (unified list) |
| `apps/frontend/components/EventList.tsx` | Incremental "load 10 more" |
| `apps/frontend/components/EventAccordion.tsx` | Country badge for bilateral topics |
| `docs/context/CLUSTERING_PIPELINE_COMPARISON.md` | Side-by-side old vs new comparison |
