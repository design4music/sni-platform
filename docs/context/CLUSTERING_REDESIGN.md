# Clustering Redesign — Time-Windowed Day-Atomic Beats

**Status**: Design accepted (D-056), implementation pending.
**Supersedes**: Phase 4 signal-only incremental clustering (current `incremental_clustering.cluster_incrementally()`)
**Companion to**: ELO v3.0.1 (D-055), the place-extraction tweak ships in the same cycle.

---

## Why

Two structural problems in the current Phase 4 clustering, both rooted in the same gap.

### Problem 1 — Mega-catchalls
USA security March 2026 has a single events_v3 row with **1,638 titles** titled "Trump says US is winning war with Iran and demands surrender", marked `is_catchall=true`. Plus a 596-title domestic catchall. Together ~45% of the CTM's 4,954 titles are sitting in 2 buckets that the frontend hides.

The Iranian girls' school strike (8 titles, ~165 dead) is buried inside the 1,638-title catchall. It has its own coherent story arc but no place tag (Phase 3.1 didn't extract "Minab" or "girls school" as a place), so signal-overlap clustering has nothing to grip and dumps it into the bucket catchall.

### Problem 2 — Cross-bucket fragmentation
Mar 25 Auvere power-plant drone strike in Estonia produces 3-4 separate clusters across UKRAINE/BALTIC/RUSSIA bilateral buckets because each title attributes the drone differently. Same physical event, fragmented because the bilateral bucket is part of the spine.

### Common root
Phase 4 ignores the **date** axis entirely. It treats Mar 1 and Mar 31 titles in MIDEAST-IRAN as equally close, and clusters by signal overlap alone. When 1,638 titles share `(US_ARMED_FORCES, MILITARY_OPERATION, IR)` with no sub-entity to discriminate them, they all collapse into one mega-cluster.

Patches were considered and rejected:
- "Phase 4.1c minor cluster rescue" — no, downstream patch
- "Per-action threshold tuning" — no, lookup tables grow forever
- "Date-aware Phase 4.1b extension" — no, the date check belongs in Phase 4 itself

The principle: **fix at the deepest possible layer, simplify the pipeline rather than grow it.**

---

## The new model

### Clustering rule

Two titles belong to the same cluster IF AND ONLY IF:

1. They share the same **beat triple**: `(actor, action_class, target)` exact match
2. They are within a **24-hour window**: same calendar date by `pubdate_utc`
3. They share at least one **entity** (place / person / org / named_event / industry) — OR they share a substring n-gram in title text if no entity is present

**24h is hard-coded.** No tunable, no per-track configuration. One global rule. Day = atomic clustering unit.

### Terminology (locked)

| Term | Definition |
|---|---|
| **Beat triple** | `(actor, action_class, target)` — the stable narrative lane |
| **Cluster** (a.k.a. "beat" in user shorthand) | A 1-day group of titles: beat triple × date × shared entity. The atomic event unit. Stored as one `events_v3` row. |
| **Family** | A chain of consecutive-day clusters with the same `(beat triple, entity)`. Stored as one `event_families` row. |
| **CTM** | Centroid-Track-Month container for all of the above. |

The Beats prototype's `(actor, action, target) × date × top-entity` model and the Phase 4 cluster definition are now the same thing. Beats stops being "a separate research project" and becomes "what Phase 4 produces."

### Family chaining rule (simplified from D-053 spine assembly)

Two clusters belong to the same family IF AND ONLY IF:

1. They share the same beat triple
2. They share the same dominant entity
3. Their date ranges are adjacent (gap ≤ 1 day)

Families chain transitively across the month: cluster on day N + cluster on day N+1 + cluster on day N+2 = one family with date range [N, N+2].

The fuzzy spine-search of D-053 is replaced by this exact-match chain rule.

---

## What this fixes (without adding any phase)

- **Mega-catchalls disappear.** A 1,638-title bucket becomes ~50-100 day-bounded clusters of 5-50 titles each. The girls'-school cluster forms because 8 titles on Mar 5-13 cluster on those specific days, not get lost in 30 days of noise.
- **Cross-bucket fragmentation auto-resolves.** The Mar 25 Estonia drone titles share `MILITARY_OPERATION + place=Estonia` (or named_event=Auvere, or substring "drone") on the same day → one cluster, regardless of bilateral bucket.
- **Catchalls are smaller.** A bucket-level catchall only collects titles that don't match any other cluster within their 24h window — which is a much smaller residual.

## What gets deleted

- **Phase 4.1b `merge_similar_clusters.py`** — entire module. Its purpose was to fix Phase 4 cross-bucket fragmentation. Once Phase 4 clusters correctly, this module is dead code.
- **Phase 4.1a `generate_mechanical_titles.py`** — likely removable. Its purpose was to give clusters a fallback title when Phase 4.5a hadn't run yet. If we accept "no LLM title until 4.5a runs", we delete it.

## What stays

- **Phase 4 `incremental_clustering.py`** — rewritten internally, same module name
- **Phase 4.1 `assemble_families.py`** — kept, but the `assign_spines()` and `build_families()` functions are replaced by the simpler "adjacent-day same-beat-entity chain" rule
- **Phase 4.5a `generate_event_summaries_4_5a.py`** — unchanged
- **Phase 4.5b `generate_summaries_4_5.py`** — unchanged
- **Phase 4.2 narrative matching + materializations** — unchanged

---

## Implementation outline

### Step 1 — Phase 3.1 prompt: broaden places vocabulary
Add to PART 2 of `LABEL_SIGNAL_EXTRACTION_PROMPT`:

> *"places includes named facilities (schools, hospitals, military bases, oil terminals, airports, power plants, embassies). Title case. Examples: Minab Girls School, Auvere Power Plant, Ramstein Air Base, US Embassy Karachi."*

This is the place-extraction tweak the user explicitly approved. One change in `core/prompts.py`.

### Step 2 — Phase 4 clustering rewrite
File: `pipeline/phase_4/incremental_clustering.py`
Function: `cluster_incrementally()`

New algorithm (replaces the current signal-overlap incremental matcher):

```
INPUT:  list of titles for one bucket within one CTM
        each title has: title_id, pubdate (date), actor, action_class, target,
                         persons[], orgs[], places[], named_events[], industries[]

1. Group titles by (date, actor, action_class, target) — the "day-beat"
2. For each day-beat group:
   2a. Build entity set per title from persons + orgs + places + named_events + industries
   2b. Greedy single-link clustering within the day-beat:
        - Start with each title as its own cluster
        - Merge clusters that share at least 1 entity
        - Iterate until no more merges
   2c. For titles with empty entity sets in the day-beat:
        - Compute substring n-grams (3-grams of words) from title_display
        - Merge if any title shares ≥1 distinctive n-gram with another in the same day-beat
   2d. Each surviving cluster becomes one events_v3 row with:
        - date = the day-beat's date
        - last_active = same as date (single-day clusters by definition)
        - bucket_key = (existing bilateral logic)
        - source_batch_count = number of titles
        - tags = top entities by frequency in the cluster
3. Catchall: titles in a day-beat that didn't form a cluster of size ≥ 2 → optional bucket-level catchall (or just drop them)
```

**Note**: Phase 4 currently has bucket logic (domestic / bilateral / other_international). We keep that — buckets affect which cluster a title goes INTO, but cross-bucket merging happens via the family chain in Phase 4.1, not via 4.1b dice merge.

Actually — reconsider: do we still need bucket separation if same-day same-entity clusters should merge across buckets? The Mar 25 drone case argues NO. **Open question for implementation: should buckets just be a metadata tag on the cluster, not a partition?** This is a real architectural decision. Discuss before coding.

### Step 3 — Phase 4.1 family assembly rewrite
File: `pipeline/phase_4/assemble_families.py`
Function: `process_ctm()` and helpers

Replace `assign_spines()` + `build_families()` with:

```
INPUT: list of clusters (events_v3 rows) for one CTM

1. Group clusters by (actor, action_class, target, dominant_entity)
   where dominant_entity = the most-frequent entity across the cluster's titles
2. Within each group, sort clusters by date ascending
3. Walk through, chaining adjacent dates (gap ≤ 1 day) into families
4. A "family" with only 1 cluster is a standalone (no event_families row needed)
5. Multi-cluster families get an event_families row with:
    - title = mechanical: "<dominant_entity> on <date_range>" or filled by Phase 4.5a later
    - cluster_count, source_count
    - first_seen, last_active = family date range
```

### Step 4 — Delete dead code
- Delete `pipeline/phase_4/merge_similar_clusters.py`
- Update `pipeline_daemon.py` to remove the Phase 4.1b call
- Delete `pipeline/phase_4/generate_mechanical_titles.py` if Phase 4.5a always runs after clustering (decide based on daemon flow)
- Update `pipeline_daemon.py` accordingly

### Step 5 — Re-run all 4 local CTMs
Use `out/beats_reextraction/rerun_ctm_full_pipeline.py` (already exists).
Compare cluster counts, family counts, and the girls'-school + Baltic drone test cases.

### Step 6 — Deploy to Render (the original deployment task, now waiting on this)
Once we like the local results, push to main, run Render migrations, reprocess April data on Render with the new clustering.

---

## DECISIONS LOCKED 2026-04-14 (after architectural discussion)

### LOCK-1: No bucket partition during clustering
Phase 4 clusters across all titles in the CTM regardless of bilateral bucket. Bucket becomes a metadata tag assigned post-clustering. The "make LLM clustering easier" rationale (the only reason buckets were a partition) is dead.

### LOCK-2: bucket_key assigned post-clustering (REVISED 2026-04-14 evening)
Original rule (rejected): "any title has home centroid → domestic" fired on everything because Phase 2 always tags the home centroid on every title assigned to a CTM.

**Current rule**: use foreign GEO centroids as the discriminator:
1. Compute the top foreign GEO centroid across the cluster's titles.
2. **Bilateral** only if that top foreign centroid appears in ≥ 50% of **all** cluster titles (not 50% of titles-with-foreign). Phase 2 cross-tags stories topically (Michigan synagogue → MIDEAST-ISRAEL), so a minority co-tag must not hijack the bucket.
3. Otherwise **domestic**.

Implementation: `_pick_bucket_key` in `incremental_clustering.py`.

### LOCK-3: dominant_entity stored on cluster
Each cluster stores its `dominant_entity` (most-frequent entity across persons/orgs/places/named_events/industries from its titles). This IS the spine — derived from data, not assigned by a separate phase. The frontend uses this for thematic grouping at read time.

### LOCK-4: Family chain (REVISED 2026-04-14 evening)
Original rule (rejected): same beat triple + same dominant_entity + adjacent days.

**Why revised**: in practice the beat triple changes across days of the same arc (strike → statement → sanctions → retaliation). Example: Kharg Island had 15 clusters across Mar 13–26 but only 1 chained into a family because the dominant beat shifted daily. Dropping beat from family chaining produced clean multi-day arcs (Kharg Mar 13–17 US strike arc; Kharg Mar 23–26 Iran retaliation).

**Current rule** — family chain key is `dominant_entity` only:
- Group clusters by their family anchor (see LOCK-8).
- Chain clusters on adjacent dates (gap ≤ 1 day) within each group.
- A family must contain ≥ 2 clusters; singletons become standalone.
- Beat triple is stored as family metadata (most common across its clusters) but is NOT a chain key.

Implementation: `chain_families` in `assemble_families.py`.

Clustering is still beat-strict (LOCK-3); only family chaining drops beat.

### LOCK-5: Singletons kept in DB, frontend filters by per-CTM percentile
Phase 4 stores ALL clusters including singletons (size 1). The frontend filters by source-count percentile per-CTM:
- USA security (~237 events) — hide bottom 25% (sacrifices borderline 5-6 source local events)
- Micronesia (~5 events) — hide nothing or bottom 1
- Implementation: query-time filter using `percentile_cont(0.25) WITHIN GROUP (ORDER BY source_batch_count)` per CTM, OR a small `display_min_sources` derived value computed per CTM during Phase 4.5b CTM digest

The exact percentile is tunable in the frontend (start with 0.25, see how it reads). No per-track config — one global percentile that scales naturally because each CTM has its own distribution.

**Source-count display bug** (separate fix, not blocking): the frontend currently shows the full source_batch_count from the DB while only rendering visible titles, producing "21 sources" labels next to clusters that visibly show 8. After the clustering redesign lands, fix the display to show either visible-only or both numbers. Tracked separately.

### LOCK-6: N-gram fallback parameters (prototype, tune in one round)
For titles within a day-beat that have empty entity sets:
- 3-word lowercase n-grams from title_display
- Stopwords filtered (the, a, an, of, in, on, at, to, for, with, by, from, as, is, are, was, were)
- Punctuation stripped
- N-gram must appear in ≥2 titles within the same day-beat to count as a match
- No per-track tuning

Prototype with these defaults, evaluate, adjust if needed in a single tightening pass.

### LOCK-7: Day-level cross-beat merge (ADDED 2026-04-14 evening)
After stage-1 entity-based single-link clustering within each beat group, a stage-2 pass merges clusters *across* beat triples within the same day. The LLM labels one physical event under multiple beat triples (tanker crash reported as `SECURITY_INCIDENT` + `STATEMENT` + `MILITARY_OPERATION` simultaneously), so stage-2 reunites those fragments.

**Stage-2 merge rule** — two same-day clusters merge IFF either:
1. **Same dominant place or named_event.** Dominant means most-frequent within the cluster, so a single multi-place title cannot bridge two clusters that are otherwise about different theaters. This is the "strong signal wins" rule: on a given day, one geographic anchor = one cluster, regardless of how many predicates journalists apply.
2. **Both clusters lack a dominant place AND any title pair across them has token-Dice ≥ 0.5.** Fallback for entity-empty fragments (e.g., Russia-Iran intelligence reports where no place is extracted). Dice is *not* used when either cluster already has a dominant place — otherwise the strong signal decided.

**Why this shape** (considered and rejected):
- Dropping beat triple from stage-1 entirely → overmerged unrelated same-day same-place stories
- Using `subject` or `sector` as cluster key → LLM labels them inconsistently across angles of one event (e.g., Iraq KC-135 crash splits 29 MILITARY / 28 SECURITY)
- Single-link on any shared place → transitive chaining via multi-place titles (Michigan-Virginia bridge title merged Michigan/Virginia/Hormuz/Korea into one blob)

**Tokenization for Dice**: lowercase, split on non-alpha, strip ~50 stopwords, strip `len < 3`, strip HIGH_FREQ persons/orgs as text tokens too (so "trump"/"nato" don't inflate Dice).

Implementation: `_merge_day_clusters` in `incremental_clustering.py`.

### LOCK-8: Family anchor — tiered with majority-coverage gate (ADDED 2026-04-14 evening)
Cluster-level `dominant_entity` (used for display and strong-signal merging in LOCK-7) picks the most-frequent token across all entity types equally. But for **family chaining** (LOCK-4), the anchor must be a **specific locus**, not a broad category, or DEFENSE/ENERGY/AUTOMOTIVE will absorb unrelated clusters.

**Family anchor rule**:
1. Tier preference: `places → named_events → persons → orgs → industries`.
2. Within each tier, pick the most-frequent token.
3. The picked token must cover **≥ 50% of the cluster's titles**. Otherwise fall through to the next tier.
4. If no tier produces a qualifying anchor, the cluster has no family anchor and remains **standalone**.

**Why the coverage gate**: without it, a minority place (e.g., 11/223 Karachi titles inside a 223-title Khamenei cluster) hijacked the family to `places:Karachi`. With the gate, Khamenei's 223-src cluster has:
- Karachi = 11/223 = 5% → skip places
- …all other tiers also under 50% or empty → no anchor → **standalone**.

Kharg Mar 14 (80 src, 51 Kharg titles): 51/80 = 64% → `places:Kharg`, qualifies → in family.

**Effect**: Khamenei assassination is a standalone big cluster (correctly visible on its own). Place-based families (Kharg, Hormuz, Iraq, Kuwait, Riyadh, Oslo, ICE) form cleanly. DEFENSE mega-families shrink to chains of genuinely DEFENSE-only singletons (which is acceptable as a loose "background chatter" chain).

Implementation: `load_clusters` in `assemble_families.py`.

---

## (Original open questions preserved below for reference, all now resolved by the LOCKs above)

### Q1 — Do we keep the bucket partition?
**Current**: Phase 4 clusters within `domestic / bilateral-XX / other_international` buckets separately. Cross-bucket merge is then attempted in Phase 4.1b.

**Option A — Keep bucket partition**: Phase 4 clusters within buckets as today. Cross-bucket merge happens in family assembly (Phase 4.1) by chaining adjacent days OR by recognizing same-beat-same-entity-same-day across buckets.

**Option B — Drop bucket partition**: Phase 4 clusters across all titles in the CTM regardless of bilateral bucket. Bucket becomes a tag, not a partition. The Mar 25 drone clusters auto-merge.

**My recommendation**: **B is cleaner**. Buckets exist for visualization (group by country in the frontend), not for clustering correctness. With time-windowed clustering, the bucket distinction is overhead. The frontend can group by `cluster.bucket_key` at render time without the clustering algorithm needing to enforce it.

Risk: a cluster with mixed bucket_keys is harder to display under the current frontend's country-grouped layout. We'd need to pick one (most common) for each cluster.

Counter-argument for keeping A: bucket partitioning is how the current system limits the comparison pool and makes clustering scalable. Removing it means every title is potentially compared to every other title, which is O(N²). For 5,000 titles this is fine; for 50,000 in a backfill it's slow.

**Decision needed.** I lean B but the user should confirm.

### Q2 — N-gram fallback for entity-less titles
For titles in a day-beat with no entities at all, we proposed substring n-gram matching. Specifics:

- N-gram size: 3 words? 4 words?
- Stop-word filtering (drop "the", "a", "of")?
- Normalization (lowercase, strip punctuation)?
- Minimum n-gram document frequency to be "distinctive" (e.g., must appear in ≤ 5 titles in the CTM)?

This is small but matters for robustness. **My recommendation**: 3-word n-grams, lowercase, strip punctuation, drop stopwords, minimum document frequency in the CTM = 2 (must appear in ≥2 titles, i.e., the n-gram is not unique). Let's prototype with these and tune if needed — but commit to "no per-track tuning."

### Q3 — Catchall handling
Current Phase 4 creates a per-bucket `is_catchall=true` event for unmatched titles. Frontend hides these.

Under the new model, catchall titles are: titles in a day-beat that didn't form a cluster of size ≥ 2 (i.e., singletons within their day-beat). Options:

- **Option α — Drop them**: Phase 4 only creates events for clusters of size ≥ 2. Singletons are abandoned.
- **Option β — Keep singleton events**: Each singleton becomes its own events_v3 row with size=1. Frontend may filter by source count.
- **Option γ — Day-beat catchall**: Group all singletons within a day-beat into one catchall event per (day, beat). Hides them from the main view but keeps the count.

**My recommendation**: **β (keep singletons)**. They cost nothing, the frontend already filters by `source_batch_count`, and they're useful for Beats spike detection (a singleton on a beat that normally has 0-1 titles per day is still a signal). No catchalls needed.

### Q4 — Family rollup display
If families chain N consecutive days, the frontend shows them as one row with N sub-clusters. Current `event_families` rendering already handles this. No frontend change needed unless we want the date range visible.

---

## Test cases (what success looks like)

After the rewrite, re-running USA security / 2026-03 should produce:

- **No mega-catchalls**: zero events with source_batch_count > 200
- **Iranian girls' school cluster**: at least one events_v3 row with title containing "girls' school" or "Minab", source count ≥ 5
- **Iran war families**: still 20-30 families, but each one is a coherent multi-day arc (Hormuz escalation Mar 17-25, Kharg strike Mar 13-15, etc.)

Re-running Baltic security / 2026-03:

- **Mar 25 Auvere drone**: one cluster (not three) with titles from UA/BALTIC/RUSSIA buckets, place=Auvere or place=Estonia, source count ≥ 4

---

## What this is NOT

- This is NOT a new phase. It's a rewrite of two existing phases (4 and 4.1) and the deletion of one (4.1b).
- This is NOT a Beats backend (Phase 4.6 in the Asana ticket). That ticket can be closed or absorbed — the Beats prototype's logic is now what Phase 4 produces natively.
- This is NOT a frontend change. The frontend will see cleaner clusters and richer families but the table schema is unchanged.
- This is NOT live-deployment-blocked work. It IS what live deployment is waiting for.

---

## Tracking

- Asana ticket: TBD (created from this doc)
- Code branch: continue on `feat/mechanical-families`
- Implementation order: Step 1 (place tweak) → Step 2 (Phase 4 rewrite) → Step 3 (Phase 4.1 rewrite) → Step 4 (delete dead code) → Step 5 (re-run + validate) → Step 6 (deploy)

After this lands, the deployment plan from `out/beats_reextraction/DEPLOYMENT_RUNBOOK.md` resumes, with one tweak: the v3.0.1 + clustering redesign ship as one coherent cycle, not two.
