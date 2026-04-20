# Clustering Action Plan: Mechanical-First Family Assembly

**Date**: 2026-04-10
**Scope**: AMERICAS-USA, all 4 tracks, March 2026 (frozen)
**Goal**: 10K titles -> 1400 clusters -> ~500 merged -> 100-200 topics in 20-40 families
**Companion**: See `CLUSTERING_PIPELINE_ANALYSIS.md` for full data tables

---

## Signal Inventory (What We Have & What We Use)

Every title in the pipeline generates rich structured metadata. Most of it is
discarded after Phase 3.3. This plan changes that.

### Cluster-Level Signals (on events_v3)

| Field | Coverage | Value | Currently Used |
|-------|----------|-------|----------------|
| `event_type` | 100% | bilateral vs domestic split | Clustering buckets |
| `bucket_key` | 100% of bilateral | Bilateral target centroid (e.g., MIDEAST-IRAN) | Clustering buckets |
| `tags[]` | 20% | Persons, places, orgs on cluster | Merge Pass 2 (barely works) |
| `source_batch_count` | 100% | Cluster size / prominence | Display threshold |
| `title` | 100% | LLM-generated cluster title | Merge Pass 1 (Dice) |

### Title-Level Signals (on title_labels, via event_v3_titles)

| Field | Coverage | Value | Currently Used |
|-------|----------|-------|----------------|
| `actor` | 99.99% | Who acts (US_EXECUTIVE, IR_ARMED_FORCES...) | Nothing post-Phase 3 |
| `target` | 99.99% | Who is acted upon (IR, US, NONE...) | Nothing post-Phase 3 |
| `action_class` | 99.99% | Type of action (MILITARY_OPERATION...) | Nothing |
| `sector` | 99.99% | Domain (MILITARY, DIPLOMACY...) | Track assignment only |
| `subject` | 99.99% | Topic (NAVAL, AERIAL, TRADE...) | Nothing |
| `importance_score` | 99.99% | 0.0-1.0, title significance | Nothing |
| `places[]` | 14-33% | Geographic specifics (Hormuz, Tehran...) | Nothing |
| `persons[]` | 29-73% | Named people (KHAMENEI, MUSK...) | Nothing |
| `orgs[]` | 14-51% | Organizations (FBI, NVIDIA, NATO...) | Nothing |
| `named_events[]` | <1% | Named operations (Operation Epic Fury) | Nothing |

### The Redundancy Problem

`bucket_key = 'MIDEAST-IRAN'` already encodes that a cluster is about US-Iran
bilateral relations. Yet we search for "Iran" in places[] to discover the same
fact. Similarly, `actor = US_ARMED_FORCES` + `target = IR` + `subject = NAVAL`
already tells us "US naval operations against Iran" without needing the cluster
title text.

### Track-Specific Signal Profiles

Different tracks have different "richest" entity types:

| Track | Best Spine Signal | Why |
|-------|-------------------|-----|
| geo_security | **Places** (33%) + Persons (39%) | Military ops defined by WHERE (Hormuz, Tehran, Kharg) |
| geo_politics | **Persons** (73%) | Politics defined by WHO (Trump, Netanyahu, Epstein) |
| geo_economy | **Orgs** (51%) | Economy defined by WHICH COMPANY (NVIDIA, FED, Tesla) |
| geo_society | Labels missing -- needs Phase 3.1 backfill | N/A |

The spine extraction algorithm must be track-aware: prioritize the entity type
that carries the most discriminating power per track.

---

## The Plan (7 Steps)

### Step 0: Fix geo_society Track Assignment Gap

geo_society has ZERO title_assignments globally for March 2026. Root cause:
the old LLM assigner (pre-mechanical Phase 3.3) never chose geo_society.
- 4,432 titles with sector=SOCIETY were assigned to wrong tracks by LLM
- 7,815 SOCIETY titles remain completely unassigned (part of ~36K backlog)

**Action**: Not blocking current work (we focus on geo_security first).
To fix later: delete wrong-track assignments for SOCIETY/HEALTH_ENVIRONMENT
titles, let mechanical assigner re-process them correctly.
**Dependency**: None, but not priority for this iteration.

---

### Step 1: Cluster Signal Aggregation

Build a script that, for each cluster, aggregates all its title_labels into a
single "cluster signal profile."

**Input**: events_v3 cluster -> event_v3_titles -> title_labels
**Output**: Per cluster:

```
cluster_id: uuid
event_type: bilateral | domestic
bucket_key: MIDEAST-IRAN | null
n_titles: 37
max_importance: 0.62
avg_importance: 0.31
actors: {US_ARMED_FORCES: 20, US_EXECUTIVE: 15, IR_ARMED_FORCES: 5}
targets: {IR: 30, NONE: 4, IL,US: 3}
subjects: {NAVAL: 18, BILATERAL_RELATIONS: 10, MISSILE: 7}
places: {Hormuz: 25, Gulf: 8, Indian Ocean: 3}
persons: {TRUMP: 12}   # ubiquitous -- will be filtered later
orgs: {CENTCOM: 5, IRGC: 3}
named_events: {}
```

This uses ALL existing metadata. No new extraction, no LLM calls. Pure SQL/Python
aggregation of what Phase 3.1 already produced.

**Key decisions**:
- Counts are per-title (how many titles in this cluster mention "Hormuz")
- A signal that appears in >50% of a cluster's titles is a "defining signal"
- A signal in <10% is "incidental noise" (a tangential mention)

**Deliverable**: `scripts/aggregate_cluster_signals.py` that writes results
to a working table or returns in memory.

---

### Step 2: Ubiquity Detection (Per-CTM Dynamic)

Some signals are too common to be spines. TRUMP appears in 30% of geo_security
titles -- it doesn't distinguish families. But KHAMENEI at 2% does.

**Algorithm**:
1. Count each signal across ALL clusters in the CTM
2. Mark as ubiquitous if it appears in >10% of clusters
3. The threshold is per-entity-type:
   - Persons: >10% = ubiquitous (TRUMP is the main one)
   - Places: >8% = ubiquitous ("Middle East" at 192/7700 = 2.5% -- not ubiq;
     "Hormuz" at 730/7700 = 9.5% -- borderline, but it's a REAL spine, so use
     a higher threshold for places maybe)
   - Orgs: >10% = ubiquitous (PENTAGON at 245/7700 = 3.2% -- not ubiq)
   - Actors/targets: separate treatment (below)

**The Hormuz problem**: Hormuz appears in 730/7700 titles (9.5%). That's a lot,
but it IS a genuine family spine. The difference between Hormuz and TRUMP is that
Hormuz describes a SPECIFIC geographic theater while TRUMP is a person involved
in everything.

**Simple rule**: A signal is ubiquitous if it appears in >15% of CTM titles.
For USA-security-March: TRUMP (30.4%). Everything else is below 10%.
For USA-economy-March: TRUMP (17%). For USA-politics-March: TRUMP (56%).
Only TRUMP exceeds 15% in any track. This keeps the rule trivially simple.

Additionally, filter out vague place names: "Middle East", "Gulf" (too broad
to be a spine). These are on a short static list, not dynamically computed.

**Deliverable**: Built into the aggregation script as a simple frequency check.

---

### Step 3: Spine Assignment

For each cluster, pick the ONE signal that best defines it. This is the "spine"
that determines family membership.

**Priority chain** (applies to all tracks, but weighting shifts by track):

```
1. named_event  (if any cluster title mentions a named operation -- rare but definitive)
2. specific place  (non-ubiquitous, appears in >30% of cluster's titles)
3. specific person  (non-ubiquitous, >30% of cluster's titles)
4. specific org  (non-ubiquitous, >30% of cluster's titles)
5. specific subject  (for military: NAVAL, AERIAL, GROUND_FORCES, NUCLEAR, etc.)
6. bucket_key  (fallback: the bilateral target country)
7. event_type  (last resort: "domestic" or "bilateral-IR" as bucket)
```

But the track shifts the priority. In geo_economy, org should be higher priority
than place. In geo_politics, person should be higher than org.

**Track-specific priority order:**

| Priority | geo_security | geo_politics | geo_economy | geo_society |
|----------|-------------|-------------|-------------|-------------|
| 1 | named_event | named_event | named_event | named_event |
| 2 | place | person | org | person |
| 3 | person | org | person | org |
| 4 | org | place | place | place |
| 5 | subject | subject | subject | subject |
| 6 | bucket_key | bucket_key | bucket_key | bucket_key |
| 7 | event_type | event_type | event_type | event_type |

**Tie-breaking**: If a cluster has both place:Hormuz (25 titles) and
place:Kuwait (3 titles), pick Hormuz (highest count). The Kuwait mention
is incidental.

**Place alias normalization**: Automated via substring containment.
Data shows only 3 alias pairs exist (for places with 5+ mentions):
- Hormuz / Ormuz -> Hormuz
- Kharg / Kharg Island -> Kharg
- New York / NEW YORK -> New York

Algorithm: if place_a is a case-insensitive substring of place_b, merge to
shorter form. No manual alias table needed.

**The "no spine" case -- SOLVED by compound spines**:

Data shows 522/851 clusters (61%) have specific entity spines.
The remaining 329 clusters break down as:
- 133 bilateral Iran, no specific entity -> spine = bucket_key + subject
  (e.g., "MIDEAST-IRAN:NAVAL", "MIDEAST-IRAN:AERIAL", "MIDEAST-IRAN:MISSILE")
- 96 domestic, no specific entity -> spine = domestic + subject
  (e.g., "domestic:TERRORISM", "domestic:BORDER_SECURITY")
- 100 other bilateral (Ukraine, Taiwan, etc.) -> spine = bucket_key alone
  (small enough to be families: EUROPE-UKRAINE has 12 clusters, ASIA-TAIWAN 5)

This gives ~100% mechanical spine coverage. No unresolvable pool.

**Deliverable**: Built into the main script (Steps 1-4 combined).
Output: each cluster gets `spine_type`, `spine_value`, `spine_secondary`.

---

### Step 4: Mechanical Family Assembly

Group clusters by spine. Each unique spine value = one proto-family.

```
Proto-family "Hormuz":     clusters where spine = place:Hormuz
Proto-family "Kharg":      clusters where spine = place:Kharg
Proto-family "FBI":         clusters where spine = org:FBI
Proto-family "NAVAL":       clusters where spine = subject:NAVAL (no specific place)
Proto-family "bilateral-IR": clusters with spine = bucket_key only (no specifics)
Proto-family "domestic":    domestic clusters with no specific spine
```

**Within-family merge**: After grouping, run title Dice merge WITHIN each family.
This is more accurate than global merge because we already know the clusters are
about the same entity. Lower the Dice threshold to 0.45 (from 0.55 globally).

**Family size check**: 
- Families with 1 cluster = standalone topic (no family wrapper)
- Families with 2-15 clusters = good family
- Families with 15+ clusters = needs sub-splitting (by subject or date)
- The "bilateral-IR" and "domestic" fallback families will be large -- that's OK,
  they go to the LLM in Step 6

**Expected outcome for geo_security**:
- 15-20 entity-spine families (Hormuz, Kharg, Tehran, Kuwait, FBI, ICE, etc.)
- 8-10 compound-spine families (MIDEAST-IRAN:NAVAL, MIDEAST-IRAN:AERIAL, etc.)
- 5-10 small bilateral families (Ukraine, Taiwan, China, etc.)
- 5-10 domestic compound families (domestic:TERRORISM, domestic:BORDER_SECURITY)
- Standalone topics for single-cluster spines
- ~0 clusters unassigned (100% mechanical coverage)

**Deliverable**: `scripts/build_families_mechanical.py`

---

### Step 5: Importance-Based Priority

This replaces the hard filter. Instead of removing low-importance clusters,
we tag them with a display priority that affects what gets shown.

**Cluster priority** (computed from aggregated title_labels):

```
PRIORITY A (must show): max_importance >= 0.5 OR source_batch_count >= 20
PRIORITY B (show):      max_importance >= 0.3 OR source_batch_count >= 10
PRIORITY C (compact):   max_importance >= 0.15 AND has_any_entity
PRIORITY D (hide):      max_importance < 0.15 AND no entities AND source_batch_count < 5
```

Priority affects:
- **UI display**: A and B shown with full detail, C shown as compact line, D hidden
- **LLM processing**: Only A and B clusters sent to LLM for family assignment
- **Family membership**: D clusters still belong to their spine-family but are
  not individually displayed

This keeps all data in the DB (reversible) but focuses attention on what matters.

For a 500-cluster CTM, expected distribution:
- A: ~80-120 clusters (the significant stories)
- B: ~100-150 clusters (secondary stories)
- C: ~100-150 clusters (minor mentions)
- D: ~50-100 clusters (noise/redundancy)

**Deliverable**: Priority assignment built into `aggregate_cluster_signals.py`

---

### Step 6: LLM Polish (Minimal, Targeted)

After mechanical assembly, the LLM handles three narrow tasks:

**Task 6a: Assign generic-pool clusters to existing families (or create new ones)**

Input: ~100-200 clusters with spine=NULL + list of mechanical families
Prompt: "Here are clusters that couldn't be mechanically assigned. Here are the
existing families. Assign each cluster to a family or mark as standalone."
Cost: 1 LLM call per CTM (~$0.10)

**Task 6b: Split oversized families**

If any mechanical family has >15 clusters, send it to LLM for sub-splitting.
Prompt: "These 20 clusters all relate to [spine]. Split into 2-5 sub-families
by specific incident/development."
Cost: 0-3 LLM calls per CTM (~$0.05)

**Task 6c: Generate family titles and summaries**

Input: family members (cluster titles + source counts)
Prompt: "Generate a title and 2-sentence summary for each family."
Cost: 1 LLM call per CTM (~$0.10)

**Total LLM cost: ~$0.25 per CTM** (vs current ~$0.50+ with worse results)

**Deliverable**: LLM calls integrated into `build_families_mechanical.py`

---

### Step 7: Write to DB & Frontend Display

Write the results to event_families table and update events_v3.family_id.
Preserve the existing schema -- no migration needed.

Add `priority` to events_v3 (or use a working column) for display filtering.
Frontend reads priority to decide compact vs full display.

---

## Implementation Order

```
Phase A: Data Foundation (no LLM, no UI changes)
  Step 0: Backfill geo_society labels
  Step 1: Cluster signal aggregation script
  Step 2: Ubiquity detection
  Step 5: Priority tagging

Phase B: Mechanical Assembly (no LLM)
  Step 3: Spine assignment
  Step 4: Family grouping + within-family merge

Phase C: LLM Polish
  Step 6a: Generic pool assignment
  Step 6b: Oversized family splitting
  Step 6c: Title and summary generation

Phase D: Integration
  Step 7: DB write + frontend display update
```

Phase A is pure data work -- fast, deterministic, fully reversible.
Phase B produces the core result -- families without any LLM.
Phase C improves quality at the margins.
Phase D makes it visible.

We should validate results after Phase B before moving to C.

---

## Risks & Mitigations

### Risk: Spine assignment too aggressive
Some clusters might get assigned to a spine based on a minority of their titles.
E.g., a cluster about "Trump threatens Iran" might get spine=place:Hormuz because
3/10 titles mention Hormuz.

**Mitigation**: The 30% threshold means a spine must appear in nearly a third of
the cluster's titles. Below that, it's incidental. We can tune this threshold
based on results.

### Risk: Alias normalization misses cases
Substring containment catches 3 known pairs. Others may emerge.

**Mitigation**: Run alias detection on results. If two families have high
cluster overlap (shared titles), they're candidates for merging. Log these
for review.

### Risk: Track-specific priority ordering is wrong
Maybe orgs matter more than persons in geo_politics for some stories.

**Mitigation**: The priority chain is a default, not absolute. If a cluster has
org:NATO in 60% of titles and person:RUBIO in 20%, NATO wins regardless of
track-level ordering. Track ordering only matters for ties.

### Risk: Compound spines too broad
"MIDEAST-IRAN:DEFENSE_POLICY" might still lump 46 clusters together.

**Mitigation**: If a compound-spine family exceeds 15 clusters, sub-split by
action_class (MILITARY_OPERATION vs POLITICAL_PRESSURE vs INFORMATION_INFLUENCE).
This creates a third level: bucket + subject + action_class.

---

## Success Criteria

For AMERICAS-USA geo_security March 2026:

1. **No mega-families**: No family with >15 clusters or >25% of total sources
2. **Good coverage**: >80% of display-worthy clusters assigned to a family
3. **Correct separation**: Hormuz, Tehran, Kharg, Kuwait are separate families
4. **Domestic separation**: FBI, ICE, synagogue attack are separate from Iran war
5. **Deterministic**: Same input -> same output (except LLM polish step)
6. **Fast**: Full run < 60 seconds mechanical + 30 seconds LLM

---

## Appendix: What Changes in Existing Code

### New scripts
- `scripts/build_families_mechanical.py` (Steps 1-5 combined: aggregate, spine, family, priority)

### Existing scripts (unchanged)
- `scripts/merge_clusters.py` -- runs BEFORE family assembly (already done for security)
- `scripts/build_families_final.py` -- kept as LLM-based alternative for comparison

### No changes needed
- Pipeline phases 1-4 (clustering stays as-is)
- Frontend (reads same event_families table)
- DB schema (no migrations, unless we add a priority column)
