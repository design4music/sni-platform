# Clustering Pipeline Analysis: USA geo_security March 2026

**Date**: 2026-04-10
**Purpose**: Trace data through every pipeline stage, quantify losses/opportunities, define a path from 10K titles to 100-200 meaningful topics.

---

## The Goal

```
7,701 raw titles
  -> ~1,400 mechanical clusters (Layer 1 -- WORKS)
  -> ~500 merged clusters (smart merge -- PARTIALLY WORKS, currently 857)
  -> 100-200 topics grouped into families or standalone
  -> 20-40 families (narrative story threads)
```

Principles: mechanical first (fast, cheap, deterministic), LLM only to polish.

---

## Stage 0: Raw Titles (7,701)

### Volume & Language
| Language | Count | % |
|----------|-------|---|
| English | 5,691 | 73.9% |
| Russian | 702 | 9.1% |
| German | 466 | 6.1% |
| Arabic | 230 | 3.0% |
| Spanish | 199 | 2.6% |
| Other (10 langs) | 413 | 5.4% |

### Weekly Volume
| Week | Titles |
|------|--------|
| Feb 23 (partial) | 529 |
| Mar 2 | 2,187 |
| Mar 9 | 1,670 |
| Mar 16 | 2,270 |
| Mar 23 (partial) | 1,045 |

Spike on Mar 16 week -- likely escalation in Iran conflict.

### Title Length
| Range | Count | % |
|-------|-------|---|
| Very short (<30 chars) | 20 | 0.3% |
| Short (30-60) | 1,982 | 25.7% |
| Medium (61-100) | 5,127 | 66.6% |
| Long (>100) | 572 | 7.4% |

No garbage -- even the 20 very short titles are real headlines.

### Label Coverage
| Metric | Count | % |
|--------|-------|---|
| Has labels | 7,700 | 99.99% |
| Has actor | 7,700 | 99.99% |
| Has target | 7,700 | 99.99% |
| Has importance | 7,700 | 99.99% |

Near-perfect extraction rate. But the QUALITY of extraction varies (see signals below).

### Importance Score
| Range | Count | % |
|-------|-------|---|
| Low (<0.3) | 4,307 | 56.0% |
| Medium-low (0.3-0.49) | 2,617 | 34.0% |
| Medium-high (0.5-0.69) | 738 | 9.6% |
| High (>=0.7) | 32 | 0.4% |

**90% of titles score below 0.5.** Only 770 titles (10%) cross the importance threshold.

> **OPPORTUNITY 1: Pre-filter by importance.** Titles with importance < 0.2 (likely ~40% of corpus) contain little unique information. They're generic commentary ("Trump's war faces challenges", "Iran conflict escalates") that add noise without specifics. Filtering these before clustering would cut 7,700 -> ~4,600 titles and dramatically reduce cluster fragmentation.

### Sector & Subject Distribution
| Sector | Count | % |
|--------|-------|---|
| MILITARY | 4,208 | 54.6% |
| SECURITY | 1,213 | 15.7% |
| DIPLOMACY | 1,200 | 15.6% |
| GOVERNANCE | 291 | 3.8% |
| SOCIETY | 216 | 2.8% |
| INTELLIGENCE | 203 | 2.6% |
| TECHNOLOGY | 142 | 1.8% |
| Other | 228 | 3.0% |

Top subjects: BILATERAL_RELATIONS (973), DEFENSE_POLICY (971), AERIAL (849), NAVAL (786), MISSILE (587), TERRORISM (582), GROUND_FORCES (500).

### Action Classes
| Action Class | Count | % |
|--------------|-------|---|
| MILITARY_OPERATION | 2,481 | 32.2% |
| POLITICAL_PRESSURE | 1,355 | 17.6% |
| SECURITY_INCIDENT | 923 | 12.0% |
| INFORMATION_INFLUENCE | 632 | 8.2% |
| DIPLOMATIC_PRESSURE | 540 | 7.0% |
| POLICY_CHANGE | 384 | 5.0% |
| LAW_ENFORCEMENT_OPERATION | 306 | 4.0% |
| CAPABILITY_TRANSFER | 290 | 3.8% |
| Other | 789 | 10.2% |

---

## Stage 0b: Entity Signals (The Spine Candidates)

This is the critical data for mechanical family assignment.

### Persons (title_labels)
| Person | Titles | % of corpus | Spine? |
|--------|--------|-------------|--------|
| TRUMP | 2,342 | 30.4% | NO -- ubiquitous |
| KHAMENEI | 154 | 2.0% | YES -- specific story |
| HEGSETH | 114 | 1.5% | YES |
| NETANYAHU | 66 | 0.9% | YES |
| NOEM | 56 | 0.7% | YES |
| KENT | 47 | 0.6% | YES |
| RUBIO | 45 | 0.6% | YES |
| MULLIN | 35 | 0.5% | YES |
| ZELENSKY | 27 | 0.4% | YES |
| STARMER | 26 | 0.3% | YES |
| LARIJANI | 23 | 0.3% | YES |

**Rule: person in >10% of titles = ubiquitous (not a spine). <10% = potential spine signal.**

### Places (title_labels)
| Place | Titles | % | Spine? |
|-------|--------|---|--------|
| Hormuz | 730 | 9.5% | YES -- THE dominant place spine |
| Middle East | 192 | 2.5% | NO -- too broad |
| Iraq | 115 | 1.5% | YES |
| Gulf | 114 | 1.5% | MAYBE -- overlaps Hormuz |
| Kuwait | 101 | 1.3% | YES -- specific incident |
| Kharg + Kharg Island | 137 | 1.8% | YES -- specific target |
| Tehran | 90 | 1.2% | YES -- specific target |
| Baghdad | 53 | 0.7% | YES |
| Oslo | 53 | 0.7% | YES -- diplomatic track |
| New York | 45 | 0.6% | YES -- domestic incident |
| LaGuardia | 41 | 0.5% | YES -- specific incident |
| Riyadh | 37 | 0.5% | YES -- embassy attack |
| Dubai | 36 | 0.5% | YES |
| Bahrain | 36 | 0.5% | YES |
| California | 32 | 0.4% | YES -- domestic |
| Michigan | 31 | 0.4% | YES -- synagogue attack |
| Texas | 30 | 0.4% | YES -- bar shooting |
| Natanz | 30 | 0.4% | YES -- nuclear target |
| Lanka | 30 | 0.4% | YES -- submarine incident |
| Taiwan | 25 | 0.3% | YES -- separate theater |
| Diego Garcia | 22 | 0.3% | YES |
| Greenland | 21 | 0.3% | YES -- separate theater |
| Lebanon | 20 | 0.3% | YES |

> **OPPORTUNITY 2: Place-based spine assignment.** 25 places with 20+ titles. Each defines a natural family anchor. Titles mentioning "Hormuz" go to the Hormuz family. Titles mentioning "Kharg" or "Kharg Island" go to the Kharg family. This is mechanical, fast, and accurate. Combined these 25 places cover ~2,500+ title-to-place associations (some titles have multiple places).

### Organizations
| Org | Titles | Spine? |
|-----|--------|--------|
| PENTAGON | 245 | NO -- generic US military |
| NATO | 164 | YES -- alliance dimension |
| FBI | 129 | YES -- domestic investigations |
| ICE | 125 | YES -- immigration enforcement |
| IRGC | 105 | MAYBE -- Iranian military generic |
| CENTCOM | 65 | NO -- generic US military |
| DHS | 57 | MAYBE |
| CIA | 52 | YES |
| TSA | 46 | YES -- airport security |
| ANTHROPIC | 33 | YES -- AI security |
| HEZBOLLAH | 25 | YES |

### Named Events (very sparse)
| Event | Titles |
|-------|--------|
| Operation Epic Fury | 34 |
| True Promise 4 | 12 |

Only 2 named events extracted. This field is underutilized.

### Actor -> Target Pairs (top 10)
| Pair | Count | % |
|------|-------|---|
| US_EXECUTIVE -> IR | 1,531 | 19.9% |
| US_ARMED_FORCES -> IR | 891 | 11.6% |
| US_EXECUTIVE -> NONE | 496 | 6.4% |
| NONE -> NONE | 435 | 5.6% |
| IR_ARMED_FORCES -> US | 305 | 4.0% |
| US_ARMED_FORCES -> NONE | 273 | 3.5% |
| IR_EXECUTIVE -> US | 233 | 3.0% |
| US_LAW_ENFORCEMENT -> NONE | 163 | 2.1% |
| NONE -> IR | 162 | 2.1% |
| NONE -> US | 157 | 2.0% |

US->IR dominates but is too broad for family assignment. The interesting pairs are:
- **US_LAW_ENFORCEMENT -> NONE** (163) = domestic law enforcement stories
- **IR_ARMED_FORCES -> US** (305) = Iranian retaliation stories

### THE GAP: Missing Entity Extraction

| Metric | Count | % |
|--------|-------|---|
| Titles with NO places | 5,161 | 67.0% |
| Titles with NO entities at all | 2,169 | 28.2% |

**67% of titles have no place extracted.** But sampling the "no entity" titles reveals they clearly contain extractable entities:
- "Sources: Russia providing info to Iran that will help Iran kill U.S. service members"
- "Jordan cracks down on opponents as it joins US, Israel in intercepting Iranian strikes"
- "US State Department OKs possible military sales to UAE, Jordan, Kuwait amid Iran war"

These titles mention Iran, Russia, Jordan, Iraq, Kuwait -- but the label extraction didn't capture them as places.

> **OPPORTUNITY 3: Fix place extraction gap.** If we could improve place extraction from 33% to 70%+, the mechanical spine-based grouping would cover most of the corpus instead of a third. Options: (a) re-run extraction with better prompt, (b) supplement with simple text search for known place names, (c) use the cluster's tags instead of individual title labels.

### Keyword Text Match vs Label Match

| Keyword | Text match | Label match | Delta |
|---------|-----------|-------------|-------|
| Hormuz | 579 | 730 | Labels +26% (infers from context) |
| Tehran | 122 | 90 | Labels -26% (misses some) |
| Kuwait | 140 | 101 | Labels -28% |
| Khamenei | 129 | 154 | Labels +19% |
| Kharg | 114 | 137 | Labels +20% |
| FBI | 119 | 129 | Labels +8% |
| ICE | 105 | 125 | Labels +19% |
| submarine | 36 | N/A | Text only |
| embassy | 136 | N/A | Text only |
| Natanz | 25 | 30 | Labels +20% |

Labels sometimes over-count (inferring Hormuz from context) and sometimes under-count (missing Tehran mentions). For spine assignment, **combining text match + label match** gives the best coverage.

---

## Stage 1: Mechanical Clustering (1,413 non-catchall + 416 catchall)

### How It Works (Current)
Phase 4 groups titles into clusters by signal overlap within bilateral/domestic buckets.
Each cluster gets an LLM-generated title and summary.

### Size Distribution (pre-merge)
| Sources | Clusters | % | Cumulative titles |
|---------|----------|---|-------------------|
| 1 | 508 | 35.9% | ~508 |
| 2 | 286 | 20.2% | ~1,080 |
| 3-5 | 295 | 20.9% | ~2,260 |
| 6-9 | 108 | 7.6% | ~3,028 |
| 10-19 | 104 | 7.4% | ~4,468 |
| 20-49 | 75 | 5.3% | ~6,718 |
| 50-99 | 18 | 1.3% | ~8,018 |
| 100+ | 19 | 1.3% | ~10,118 |

**56% of clusters have only 1-2 sources.** These tiny clusters contain little unique information -- often a single headline that didn't match anything else.

### Catchall
- 416 catchall events with 416 titles (1:1 -- each is a single unmatched title)

### Event Type
| Type | Clusters | Sources |
|------|----------|---------|
| bilateral | 1,098 (77.7%) | 12,383 |
| domestic | 315 (22.3%) | 1,960 |

### Bilateral Targets (bucket_key)
| Bucket | Clusters | Sources | % of bilateral src |
|--------|----------|---------|-------------------|
| MIDEAST-IRAN | 615 | 9,895 | **79.9%** |
| MIDEAST-GULF | 32 | 525 | 4.2% |
| MIDEAST-IRAQ | 29 | 291 | 2.3% |
| MIDEAST-ISRAEL | 70 | 228 | 1.8% |
| EUROPE-NORDIC | 8 | 117 | 0.9% |
| EUROPE-UKRAINE | 36 | 113 | 0.9% |
| ASIA-SOUTHKOREA | 20 | 110 | 0.9% |
| Other (13 buckets) | 288 | 1,104 | 8.9% |

Iran-bilateral clusters contain **80% of all bilateral sources**. This is why the mega-family forms -- the LLM sees 615 Iran clusters and lumps them together.

### Tag Coverage (CRITICAL GAP)

| Metric | Count | % |
|--------|-------|---|
| Clusters with tags | 169 | 19.9% |
| Clusters with NO tags | 682 | **80.1%** |

**80% of visible clusters have zero tags.** Tags are cluster-level signals (person:trump, place:hormuz, org:fbi). They're generated during Phase 4.5a (event summary generation) and only populated for clusters that have been summarized. Most small clusters never get summarized, so they have no tags.

> **OPPORTUNITY 4: Use title_labels instead of cluster tags.** Each cluster contains titles that DO have labels (actors, targets, places, persons, orgs). We can aggregate title_labels per cluster to get rich signal coverage. For each cluster, the union of its titles' places/persons/orgs gives us the spine signals. This sidesteps the 80% tag gap entirely.

---

## Stage 2: Merge (1,413 -> 857 visible, current)

### How It Works
`scripts/merge_clusters.py` runs three passes:
1. **Title Dice** (>= 0.55): Near-identical cluster titles
2. **Tag overlap** (>= 2 shared tags): Same signals
3. **Small-into-large absorption** (word overlap >= 0.35): Absorb tiny into nearest large

### Results
- Pass 1 (Dice): 1413 -> ~1100
- Pass 2 (Tags): limited impact (80% have no tags)
- Pass 3 (Absorption): absorbs small into large
- **Final: 857 visible clusters**

### Post-Merge Size Distribution
| Sources | Clusters | % |
|---------|----------|---|
| 1-2 (tiny) | 463 | 54.0% |
| 3-5 (small) | 165 | 19.3% |
| 6-9 (medium) | 37 | 4.3% |
| 10-19 (good) | 60 | 7.0% |
| 20-49 (strong) | 87 | 10.2% |
| 50-99 (big) | 21 | 2.4% |
| 100+ (mega) | 24 | 2.8% |

**Still 54% tiny.** The merge reduces count from 1413 to 857 (39% merge rate) but doesn't collapse the long tail of singletons.

> **OPPORTUNITY 5: More aggressive merge using title_labels.** Pass 2 (tag overlap) barely works because 80% of clusters have no tags. If we aggregate title_labels per cluster and compare THOSE signals (places, persons, orgs), we'd find many more merge candidates. Two clusters about "Tehran airstrikes" that have different title wording but both contain place:Tehran + subject:AERIAL should merge.

### Top 15 Post-Merge Clusters
| Sources | Members | Title |
|---------|---------|-------|
| 2,713 | 8 | Iran's military says it attacked US bases and an aircraft carrier |
| 709 | 1 | Trump mobilizes forces and pressures allies over Strait of Hormuz |
| 376 | 1 | U.S. military action against Iran escalates over several days |
| 366 | 2 | Trump says war with Iran will continue for several weeks |
| 312 | 7 | US and Israel conduct airstrikes on targets in Tehran |
| 290 | 3 | US fighter jet crashes in Kuwait near American airbase |
| 281 | 8 | Trump says US strikes killed Iranian leaders, claims new government wants talks |
| 253 | 23 | Trump discusses possibility of sending US ground troops to Iran |
| 248 | 2 | Trump escalates threats against Iran, vows to avenge US troops |
| 246 | 14 | US sending thousands of Marines to the Middle East |
| 205 | 11 | Iran's Supreme Leader Khamenei killed in reported US-Israeli strikes |
| 184 | 6 | Iran threatens retaliation after Trump postpones military strikes |
| 183 | 1 | Trump describes conflict with Iran as a minor engagement |
| 172 | 11 | Trump says US bombed Iranian oil island Kharg |
| 160 | 3 | FBI investigates Texas bar shooting as possible act of terrorism |

Even after merge, the top cluster has 2,713 sources -- a mega-cluster that is itself multiple stories (Iranian retaliation is different from US strikes on bases).

---

## Stage 3: Family Assembly (current state -- 19 families)

### How It Works
`scripts/build_families_final.py`:
1. Filter to display-worthy topics (>= 10 src for 500+ cluster CTMs)
2. Send titles to LLM: "group into families"
3. LLM returns JSON with family assignments
4. Orphan rescue by word overlap
5. Write to DB

### Current Result
| Family | Topics | Sources |
|--------|--------|---------|
| **US-Iran conflict: Military strikes** | **77** | **6,902** |
| Strait of Hormuz tensions | 15 | 1,063 |
| US military logistics and deployments | 9 | 439 |
| Kuwait friendly fire incident | 2 | 399 |
| Attacks on US embassies/consulates | 8 | 286 |
| FBI investigations and security breaches | 10 | 215 |
| ICE deployment to airports | 4 | 213 |
| US military plane crash in Iraq | 2 | 96 |
| International reactions and diplomatic fallout | 5 | 95 |
| Israel's strikes and role in Iran conflict | 5 | 90 |
| Michigan synagogue attack | 2 | 87 |
| Natanz nuclear facility strikes | 4 | 84 |
| US anti-drug ops in Latin America | 3 | 79 |
| North Korea missiles during drills | 3 | 65 |
| Iranian retaliation on US/UK bases | 3 | 60 |
| US intelligence on China and Taiwan | 3 | 51 |
| NY mayor's home explosive device | 2 | 50 |
| US military support for Ukraine | 2 | 43 |
| US submarine sinks Iranian warship | 2 | 24 |

**The mega-family problem:** "US-Iran conflict" has 77 topics (48% of all family topics) and 6,902 sources (68% of all family sources). It should be split into ~15 specific sub-families.

### What Should the 77 Iran Topics Split Into?

Based on the spine keywords in the data:
| Expected Family | Spine Signal | Est. Titles |
|-----------------|-------------|-------------|
| Hormuz blockade/operations | place:Hormuz | ~730 |
| Tehran airstrikes | place:Tehran | ~90 |
| Kharg Island bombing | place:Kharg | ~137 |
| Khamenei assassination | person:Khamenei | ~154 |
| Iranian retaliation (True Promise 4) | IR_ARMED_FORCES->US | ~305 |
| Submarine sinks warship | keyword:submarine + place:Lanka | ~36 |
| Trump war commentary | US_EXEC + no specific target | ~500+ |
| Ground troops debate | subject:GROUND_FORCES | ~500 |
| War funding/budget | keyword:billion/budget | ~130 |
| Diplomatic dimension (Oslo) | place:Oslo | ~53 |
| Iraq-based operations | place:Iraq/Baghdad | ~115 |
| Natanz nuclear strikes | place:Natanz | ~30 |
| Casualties/losses reporting | keyword:killed/casualties | overlaps |
| Diego Garcia base | place:Diego Garcia | ~22 |
| Bahrain operations | place:Bahrain | ~36 |

---

## The Core Problem: Two Types of Titles

Looking at the data, there are fundamentally two types of titles in the corpus:

### Type A: Specific (contain spine signals)
"US submarine sinks Iranian warship off Sri Lanka, killing 87"
"Drones attack US embassy in Saudi Arabia's capital"
"Trump says US bombed Iranian oil island Kharg"

These have: specific place, specific incident, specific entity. They cluster well mechanically.

### Type B: Generic (commentary, no specifics)
"Trump's Iran war faces challenges after one month"
"Iran conflict escalates beyond Trump's control with no clear end"
"US says Iran war may last longer than planned"

These have: no specific place, no specific incident. They're editorial/commentary. They don't belong to any one family -- they're ABOUT the war in general.

**Data point:** 2,169 titles (28%) have zero extracted entities (no places, no persons, no orgs, no named_events). Many more have only ubiquitous entities (TRUMP, IR).

> **OPPORTUNITY 6: Separate generic from specific.** Type B titles either: (a) go into a "War Commentary" family, (b) get assigned to the nearest specific family by date proximity, or (c) get filtered out entirely from the topic display. A title that adds no specificity beyond "the war continues" doesn't deserve its own cluster.

---

## Proposed Pipeline: Mechanical-First Family Assembly

### Step 1: Pre-filter (7,701 -> ~5,000 titles)

Remove titles that can't contribute to specific clusters:
- importance_score < 0.15 AND no specific entities (no places, no non-ubiquitous persons/orgs)
- Duplicate text (exact or near-exact)
- Non-English titles that are translations of already-present English titles (optional)

**Expected result:** ~5,000 titles with actual informational content.

### Step 2: Compute Spine Signals per Title

For each remaining title, extract the **most specific** signal:
1. **Place** (from title_labels.places, filtered for ubiquitous like "Middle East")
2. **Person** (from title_labels.persons, filtered for ubiquitous like "TRUMP")
3. **Org** (from title_labels.orgs, filtered for ubiquitous like "PENTAGON")
4. **Named Event** (from title_labels.named_events)
5. **Subject** (from title_labels: NAVAL, AERIAL, GROUND_FORCES, etc.)

Priority: named_event > specific place > specific person > specific org > subject

### Step 3: Mechanical Clustering (unchanged Layer 1)

Current Phase 4 clustering stays as-is. It produces ~1,400 clusters.

### Step 4: Cluster Spine Aggregation (NEW)

For each cluster, aggregate its titles' spine signals:
```
Cluster "US submarine sinks Iranian warship" (37 src):
  places: {Lanka: 30, Indian Ocean: 23}
  persons: {}
  orgs: {}
  dominant_spine: place:Lanka
```

```
Cluster "Trump discusses sending ground troops to Iran" (23 src):
  places: {Middle East: 8}
  persons: {TRUMP: 20}
  subjects: {GROUND_FORCES: 18, DEFENSE_POLICY: 12}
  dominant_spine: subject:GROUND_FORCES (TRUMP filtered as ubiquitous)
```

### Step 5: Spine-Based Family Assignment (NEW, mechanical)

Group clusters by dominant spine. Rules:
1. **Specific place** -> family (Hormuz, Tehran, Kharg, Kuwait, etc.)
2. **Specific person** -> family (Khamenei, Hegseth, Noem, etc.)
3. **Specific org** -> family (FBI, ICE, NATO, etc.)
4. **Subject-only** (no specific entity) -> "theater pool" for LLM assignment
5. **No signal at all** -> generic/commentary pool

Expected mechanical families from spine signals:
| Spine | Type | Est. Clusters |
|-------|------|---------------|
| place:Hormuz | specific | ~15 |
| place:Tehran | specific | ~8 |
| place:Kharg | specific | ~8 |
| person:Khamenei | specific | ~6 |
| place:Kuwait | specific | ~5 |
| place:Iraq/Baghdad | specific | ~10 |
| place:Riyadh | specific | ~3 |
| org:FBI | specific | ~10 |
| org:ICE | specific | ~5 |
| org:NATO | specific | ~5 |
| place:Lanka (submarine) | specific | ~3 |
| place:Oslo | specific | ~3 |
| place:Michigan | specific | ~3 |
| place:Texas | specific | ~3 |
| place:Taiwan | specific | ~3 |
| place:Greenland | specific | ~2 |
| subject:GROUND_FORCES | theater | ~5 |
| subject:NAVAL (generic) | theater | ~5 |
| No spine | generic | ~100+ |

### Step 6: Merge Within Family (mechanical)

Within each spine-family, merge near-duplicate clusters using title Dice.
This is the same merge_clusters.py logic but SCOPED to families -- more accurate because
we know the clusters are about the same topic.

### Step 7: LLM Polish (the only LLM step)

Three tasks for the LLM:
1. **Split/merge** the "theater pool" and "generic pool" clusters into families or existing families
2. **Generate family titles** for the mechanically-assembled families
3. **Generate family summaries**

This is ~1 LLM call for the theater/generic assignment + 1 call for titles/summaries.
Total: ~$0.10-0.20 per CTM instead of current ~$0.50+.

---

## Comparison: Current vs Proposed

| Metric | Current | Proposed |
|--------|---------|----------|
| Input to family assembly | 161 display topics | All 857 visible clusters |
| Mechanical pre-grouping | None (LLM does all grouping) | Spine-based (covers ~60% of clusters) |
| LLM role | Group ALL topics into families | Polish: assign generic pool + generate titles |
| Mega-family risk | HIGH (77-topic bucket) | LOW (mechanical spines prevent it) |
| Cost per CTM | ~$0.50 | ~$0.15 |
| Determinism | Low (LLM varies between runs) | High (mechanical core, LLM only at edges) |

---

## Blockers & Gaps to Address

### Gap 1: 67% of titles have no places extracted
The spine-based approach depends on entity coverage. Options:
- **Quick fix:** Supplement labels with simple text search (regex for known place names)
- **Better fix:** Re-run Phase 3.1 extraction with improved prompt for places
- **Best fix:** Both -- labels catch context-inferred places, text catches literal mentions

### Gap 2: 80% of clusters have no tags
This blocks the current merge_clusters.py Pass 2. Fix: aggregate title_labels per cluster instead of using cluster tags.

### Gap 3: Entity normalization
"Kharg" and "Kharg Island" are the same entity. "Gulf" overlaps "Hormuz". Need an alias table.

### Gap 4: Ubiquitous signal threshold
What's "ubiquitous" depends on the CTM. For USA-security-March, TRUMP and IR are ubiquitous. For France-security, they wouldn't be. Need per-CTM dynamic computation (similar to domain_stops in merge_clusters.py).

### Gap 5: Generic title handling
28% of titles have no entities. They need either:
- Assignment to nearest specific family by date + actor-target
- A dedicated "War Commentary" family
- Filtering out from display

---

## Immediate Next Steps

1. **Write a spine extraction script** that aggregates title_labels per cluster and assigns dominant spine
2. **Test on current 857 clusters**: how many get a spine, how many fall to generic pool?
3. **Build the place alias table** (Kharg = Kharg Island, Gulf ~= Hormuz, etc.)
4. **Supplement place extraction** with text regex for the 67% gap
5. **Run mechanical family assembly** on the spined clusters
6. **Compare** mechanical families to the validated EVENT_FAMILY_ASSEMBLY.md results

---

## Appendix: What "Family" and "Topic" Mean

These definitions work across volume levels:

**TOPIC** = a cluster of headlines about the same specific development.
- Defined by: specific incident + time window + consistent actors
- Examples: "US submarine sinks Iranian warship" (36 src, 2 days), "FBI investigates synagogue attack" (87 src, 5 days)
- Size: typically 10-300 sources
- A topic has ONE core event or development, even if covered from different angles

**FAMILY** = a group of topics connected by a shared geographic/institutional spine.
- Defined by: persistent specific entity (place, person, org) that threads through multiple topics
- Examples: "Hormuz Crisis" (blockade + naval confrontation + shipping disruption + diplomatic demands) = 4+ topics
- Examples: "FBI Domestic Investigations" (synagogue + bar shooting + airport plot) = 3+ topics
- Size: 2-15 topics, 50-3000+ sources
- A family has ONE spine but MULTIPLE developments/incidents

**Key distinction:** Topics are time-bounded events. Families are entity-bounded story threads.

**For the LLM prompt:** "A family is everything a reader would file under one geographic location or institution. A topic is one thing that happened at that location."
