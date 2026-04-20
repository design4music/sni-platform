# Clustering Pipeline Comparison: Current (main) vs Experimental (feat/sector-clustering)

**Created**: 2026-03-22
**Purpose**: Side-by-side comparison to guide careful calibration of the new approach.

---

## Overview

| Aspect | Current (main) | Experimental (feat/sector-clustering) |
|--------|---------------|--------------------------------------|
| **Scope** | Per-CTM (one track at a time) | Per-centroid (all tracks at once) |
| **LLM calls in clustering** | 0 for initial cluster, 3+ for post-processing | 0 |
| **Post-clustering passes** | 3 (consolidation, catchall rescue, cross-bucket merge) | 0 |
| **Intel gating** | Phase 3.3 LLM (accept/reject) | None (relies on Phase 3.3 having already run) |
| **Track assignment** | Phase 3.3 LLM per-title | Mechanical SECTOR_TO_TRACK per-cluster |
| **Geo bucketing** | Pre-clustering (titles sorted into buckets first) | Post-clustering (clusters tagged after formation) |

---

## Step-by-Step Pipeline Comparison

### Step 1: Title Selection

| | Current | Experimental |
|--|---------|-------------|
| **Source** | `title_assignments` table (titles already assigned to a specific CTM) | `titles_v3.centroid_ids` array (all titles mentioning this centroid) |
| **Filter** | `WHERE ta.ctm_id = ?` | `WHERE centroid = ANY(centroid_ids) AND processing_status = 'assigned' AND month filter` |
| **Scope** | One CTM = one track = one centroid+month slice | All tracks for a centroid+month |
| **Title count (France/March)** | 1,148 (only titles with title_assignments rows) | 1,404 (includes 242 orphaned titles with no assignment) |

**Key difference**: The current pipeline can only see titles that Phase 3.3 successfully assigned to a CTM. The experimental approach sees ALL titles with the centroid in `centroid_ids`, catching titles that Phase 3.3 dropped. This is more complete but also includes titles that may have been intentionally filtered.

---

### Step 2: Intel Gating (content filtering)

| | Current | Experimental |
|--|---------|-------------|
| **Mechanism** | Phase 3.3 LLM call: classifies each title as strategic/reject | **None** -- trusts `processing_status = 'assigned'` |
| **Sports/entertainment** | LLM prompted to reject (but leaks through) | No filter at all |
| **Prompt** | `INTEL_GATING_PROMPT`: explicit sports rejection rules | N/A |
| **Fallback** | Unclassified titles default to strategic (permissive) | All assigned titles enter clustering |

**Important clarification on `processing_status = 'assigned'`:**
- **Phase 2** (centroid matching) sets `processing_status = 'assigned'` -- this means "matched to a centroid," NOT "passed intel gating."
- **Phase 3.3** reads `assigned` titles, then either flips rejected ones to `blocked_llm` or creates a `title_assignments` row for accepted ones. The status stays `assigned` either way for accepted titles.
- The **real gating signal** is the existence of a `title_assignments` row, not the `processing_status` value.
- The 242 orphaned titles have `processing_status = 'assigned'` (set by Phase 2) but **no `title_assignments` row** -- meaning Phase 3.3 never processed them. They were never intel-gated at all.

**Two separate problems:**
1. **Ungated titles**: The experimental pipeline's broader query picks up 242 titles that Phase 3.3 never processed. These include sports content that would have been rejected.
2. **Gating leaks**: Even among the 1,148 titles that DID pass Phase 3.3, sports titles leaked through (the LLM accepted them despite the prompt saying to reject sports). This is a pre-existing bug.

**Question**: Should the experimental pipeline (a) require a `title_assignments` row, (b) re-run intel gating on ungated titles, or (c) add sector-based content exclusion as a mechanical filter?

---

### Step 3: Track Assignment

| | Current | Experimental |
|--|---------|-------------|
| **Mechanism** | Phase 3.3 LLM: assigns one track per title | `SECTOR_TO_TRACK` static map: assigns one track per cluster |
| **Granularity** | Per-title | Per-cluster |
| **Available tracks** | From `track_configs` table (centroid-specific) | Hardcoded 5 tracks (geo_politics, geo_security, geo_economy, geo_energy, geo_humanitarian) |
| **Fallback** | First track in config | geo_politics |
| **geo_information** | LLM can assign titles here | No sector maps to it -- always 0 events |

**Key difference**: Current approach lets the LLM make nuanced per-title track decisions with full centroid context. Experimental uses a deterministic mapping that can never assign to geo_information.

**Question**: Is geo_information still needed? If yes, which sectors should map to it?

---

### Step 4: Geographic Bucketing

| | Current | Experimental |
|--|---------|-------------|
| **When** | **Before** clustering (titles pre-sorted into buckets) | **After** clustering (clusters tagged post-formation) |
| **Domestic** | Title has only home centroid (+ SYS-*) | >= 50% of cluster titles have only home centroid |
| **Bilateral** | Title has exactly 1 foreign GEO centroid -> bucket by that centroid | Top foreign centroid appears in >= 50% of cluster titles |
| **Other international** | Title has 2+ foreign GEO centroids -> assigned to largest existing bucket (Pass 2) | Not handled -- no concept of OI |
| **Buckets per CTM** | Many buckets (1 domestic + N bilateral + OI) | 2 states: domestic or bilateral(top_centroid) per cluster |

**Key difference**: Current pipeline uses geo buckets as **clustering boundaries** -- titles in different buckets can never cluster together. Experimental ignores geography during clustering and only tags afterwards.

**Implication**: In the current pipeline, a France-Germany nuclear story in the domestic bucket and the Germany bilateral bucket become two separate events. In experimental, they cluster together (correct for topic coherence, but loses the geo perspective the UI was designed around).

**Question**: Is the per-cluster bilateral tag sufficient for the UI, or does the frontend need per-bucket event lists?

---

### Step 5: Clustering Algorithm

| | Current | Experimental |
|--|---------|-------------|
| **Approach** | Bottom-up incremental: titles arrive one at a time, join best-matching topic | Top-down: group by sector+subject, then split by identity |
| **Primary grouping** | Signal overlap (weighted token matching) | Sector + Subject (from LLM extraction) |
| **Secondary splitting** | N/A (single-pass) | Identity signals: shared persons/orgs/places/named_events |
| **Signal weighting** | Per-type weights from track config, 1.5x anchor boost | Unweighted -- any 1 shared identity signal = match |
| **Anchor locking** | After 5 titles, topic's anchor signals lock permanently | N/A (no anchors) |
| **Specificity gate** | Topics with 30+ titles require a specific signal match | None |
| **Discriminator check** | Hard reject if title has conflicting org/person signal | None |
| **Match threshold** | `JOIN_THRESHOLD = 0.25` (weighted overlap score) | Any overlap > 0 (1 shared signal = join) |
| **Max topic size** | 200 titles | Unlimited |
| **Emergence threshold** | 3 titles | 2 titles |
| **Orphan handling** | Unmatched titles go to catchall | No-identity titles merge into largest sub-cluster within same sector+subject group |
| **Identity exclusions** | HIGH_FREQ_ORGS, HIGH_FREQ_PERSONS | HIGH_FREQ_ORGS, CTM_PROTAGONIST |
| **Place handling** | Places are identity signals with normal weight | Places are identity signals with equal weight (Paris, Lyon connect unrelated stories) |

**Critical differences**:

1. **Sector+subject as the primary gate** is the fundamental design change. Current pipeline has no concept of "topic area" -- it relies entirely on signal co-occurrence. This means unrelated stories can cluster if they share a person (e.g., "Macron" before protagonist exclusion existed). The experimental approach prevents this by requiring same sector+subject first.

2. **Match threshold**: Current requires weighted overlap >= 0.25 with anchor/discriminator checks. Experimental joins on any 1 shared signal. This is far more permissive within a sector+subject group, which is why Paris/Lyon/Marseille connect football to concerts to elections in SOCIETY/NULL.

3. **No size limit or specificity gate**: Current pipeline has MAX_TOPIC_SIZE=200 and a specificity gate for 30+ title topics. Experimental has neither.

4. **No discriminator conflict check**: Current pipeline hard-rejects a title if it has a different org/person than the topic's anchors. Experimental does not.

---

### Step 6: Post-Clustering Refinement

| | Current | Experimental |
|--|---------|-------------|
| **Phase 4.1: Consolidation** | LLM dedup (Dice >= 0.35 pre-filter, confidence >= 0.7 merge) | **None** |
| **Phase 4.1: Catchall rescue** | LLM assigns catchall headlines to existing events (word overlap >= 2) | **None** (orphans merge into largest sub-cluster mechanically) |
| **Phase 4.1: Cross-bucket dedup** | Moves OI events into bilateral buckets | **N/A** (no OI concept) |
| **Phase 4.3: Cross-bucket merge** | LLM identifies same-story events across different buckets | **N/A** (no bucket boundaries to merge across) |
| **Phase 4.3: Anchor selection** | Domestic preferred if >= 50% of largest event's sources | N/A |
| **Total LLM calls** | 2-4 per CTM (dedup, rescue, merge) | 0 |

**Key difference**: Current pipeline uses 3 LLM passes to repair clustering mistakes. Experimental has no repair passes -- what the algorithm produces is final. This is simpler and cheaper but has no safety net for:
- Near-duplicate events (would be caught by Phase 4.1 dedup)
- Catchall titles that should belong to an event (would be rescued by Phase 4.1)
- Same story split across buckets (would be merged by Phase 4.3)

**Question**: Should the experimental pipeline add any of these passes back? The cross-bucket merge (Phase 4.3) is probably unnecessary since bucketing happens after clustering. But consolidation (Phase 4.1 dedup) and catchall rescue could still add value.

---

### Step 7: Event Title/Summary Generation

| | Current | Experimental |
|--|---------|-------------|
| **Phase 4.5a** | Same | Same (`generate_event_summaries_4_5a.py`) |
| **When** | After Phase 4.3 merge | After clustering (no post-processing) |

No difference in the generation step itself.

---

## Summary of Gaps in Experimental Pipeline

| Gap | Impact | Fix complexity |
|-----|--------|---------------|
| **No intel gating** | Sports/entertainment leaks into clusters | Low: add sector-based exclusion list |
| **No place exclusion for home country** | Paris/Lyon/Marseille connect unrelated French stories | Low: add domestic place exclusion per centroid |
| **Match threshold too low** (any 1 signal) | Unrelated stories in same sector+subject merge | Medium: require >= 2 shared signals or add weighted scoring |
| **No max topic size** | Unbounded cluster growth possible | Low: add cap |
| **No specificity gate** | Large clusters don't require specific signal matches | Medium: port from current pipeline |
| **No discriminator check** | Conflicting-identity titles can join same cluster | Medium: port from current pipeline |
| **No consolidation pass** | Near-duplicate events survive | Low: run Phase 4.1 after experimental clustering |
| **No catchall rescue** | Single-title events that could match stay isolated | Low: run Phase 4.1 after experimental clustering |
| **geo_information dead** | CTM gets 0 events | Decision: drop or map a sector |
| **SOCIETY/NULL grab-bag** | Sports, culture, social issues all merge | Medium: extract SPORTS/ENTERTAINMENT subjects, exclude from clustering |

---

## Recommended Calibration Path

**Phase A -- Critical fixes (before next --write):**
1. Add sector-based content exclusion (reject SOCIETY titles that are sports/entertainment)
2. Add domestic place exclusion (major cities of home centroid)
3. Require >= 2 shared identity signals (not 1) to join a cluster

**Phase B -- Quality parity (after Phase A):**
4. Add MAX_TOPIC_SIZE cap (200, matching current)
5. Add specificity gate for 30+ title clusters
6. Consider running Phase 4.1 consolidation as a post-pass

**Phase C -- Pipeline integration (after quality validated):**
7. Decide on geo_information track
8. Design incremental mode for daemon
9. Decide title_assignments future
