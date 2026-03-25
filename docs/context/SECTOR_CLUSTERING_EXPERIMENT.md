# Sector-Based Clustering Experiment

**Branch**: `feat/sector-clustering`
**Last Updated**: 2026-03-25
**Status**: Validated on 5 centroids. Frontend redesigned. Ready for track consolidation (6->4) then pipeline integration.

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

- **Track assignment**: mechanical SECTOR_TO_TRACK mapping per cluster
- **Geo tagging**: bilateral if top foreign centroid in >= 50% of cluster titles
- **Mechanical title merge**: Dice word overlap >= 0.40 on generated titles within same
  sector (catches "Zelensky visits Paris" split across MEDIATION vs SUMMIT subjects)

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

---

## Test Results (2026-03-25)

5 centroids tested with full clustering (no LLM title generation yet):

| Centroid | Strategic | NON_STRATEGIC | Topics | Catchall |
|----------|-----------|---------------|--------|----------|
| France | 1,104 | 263 (19%) | 98 | 2% |
| UK | 1,663 | 409 (20%) | 124 | 3% |
| Germany | 1,556 | 214 (12%) | 116 | 1% |
| Russia | 2,645 | 156 (6%) | 201 | 2% |
| Baltic | 455 | 79 (15%) | 54 | 1% |

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

2. **geo_information track gets 0 events**: no sector maps to it. Will be resolved by
   track consolidation (6 -> 4 tracks).

3. **Multi-country centroids** (Baltic): sector+subject grouping too coarse when 3 countries
   share a centroid. Each country's local stories mix. Potential fix: sub-group by country
   within the centroid before clustering.

4. **LLM merge pass not yet implemented** (Step B): mechanical merge catches obvious
   duplicates (Dice >= 0.40) but misses paraphrased variants. Planned: targeted LLM merge
   for top topics per sector+subject, reusing Phase 4.1 dedup format.

5. **Core title selection not yet wired to LLM generation**: currently display-only. The
   pipeline still sends all titles to the LLM. Planned: use the same centrality selection
   to feed only the top 10 titles to the LLM for title+description generation.

---

## Next Steps

1. **Track consolidation 6 -> 4**: Politics, Security, Economy (merge Energy), Society
   (merge Humanitarian + Information). Jan/Feb keeps 6 tracks; March+ uses 4.

2. **LLM title+description generation from core 10 titles**: wire centrality selection
   into `generate_event_summaries_4_5a.py`.

3. **LLM merge pass**: targeted dedup for top topics per sector, reusing Phase 4.1 format.

4. **Pipeline integration**: replace `incremental_clustering.py` with sector-based approach
   in the daemon. Design incremental mode (new titles only, not full rebuild).

5. **Full March rebuild**: re-extract all labels with new taxonomy, recluster all centroids,
   regenerate all LLM prose.

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
