# WorldBrief — Narratives & Friction Nodes Architecture (v2 Concept)

**Date**: 2026-05-07 (sections 1-10 written 2026-05-06; section 12 "Production lessons" added 2026-05-07 after FN2-FN4 deployed live).
**Status**: Live in production at `/friction-nodes/[slug]` as a shadow route.
**Companions**:
- [`out/narrative_consolidation_pass1_v2.md`](narrative_consolidation_pass1_v2.md) — the framing-explicit narrative draft this rests on
- [`docs/context/FRICTION_NODES_RUNBOOK.md`](../docs/context/FRICTION_NODES_RUNBOOK.md) — operational "how to add a new FN" runbook

---

## 1. Premise

WorldBrief describes contested geopolitical reality. To do that adequately the system needs to separate:

- **What happened** (factual record)
- **How actors frame what happened** (interpretive layer)
- **Which phenomena are persistently contested** (structural layer)

Today we have the first layer (events) and a partial second layer (260 narratives in the legacy schema). We don't yet have the third. This document defines the three layers, the entities at each, and how they connect.

---

## 2. The three-layer analytical framework

| Layer | Question it answers | Entity | Status |
|---|---|---|---|
| **Facts** | What happened? | Events (Layer 1, day-clusters of headlines) | Live |
| **Interpretation** | How is it being framed? | Strategic narratives (worldview-with-loaded-vocabulary) | Rebuilding (v2 in progress) |
| **Structure** | What's persistently contested? | Friction nodes (contested phenomena) | New — does not yet exist |

The three-layer framing is the spine of the whole system. Each layer answers a question the others cannot.

---

## 3. Five levels of resolution

Within the three layers, the system actually resolves at five levels:

```
META-NARRATIVES (~9, exist already)
  ─ Enduring forces: Multipolar World, Liberal International Order,
    Sovereign Resistance, Security Order, ...
  ─ Their pairwise opposition IS the macro-friction.
  ─ No new entity needed; collisions are derived from `opposes[]`.
        ↕

STRATEGIC NARRATIVES (~30 after v2 consolidation)
  ─ Actor-coalition-specific worldviews with unified loaded vocabulary.
  ─ Each tagged with its `meta_narrative_id`.
  ─ Curated, hand-composed. Not data-derived.
        ↕

FRICTION NODES (~25, NEW)
  ─ Contested phenomena: Taiwan, Iran nuclear, Arctic, AI sovereignty,
    Russia-Ukraine territory, climate regulation regime, semiconductors, ...
  ─ Each defined by ≥2 narratives applying with incompatible prescriptions.
  ─ Curated initially. Data may nominate additions later.
        ↕

THEATERS (computed, not stored)
  ─ Transient groupings of FNs sharing actor coalitions + meta-collision +
    simultaneous activity.
  ─ Example: "Iran War 2026" = Iran nuclear + Houthi shipping +
    Israel-Hezbollah + US-Iran direct strikes.
  ─ Computed view. No table.
        ↕

EVENTS (live, daily flow)
  ─ Day-centric clusters of headlines from titles_v3.
```

**Three of the five exist already. One is new (FN). One is a UI computation (theater).** This keeps the "lesser is more" principle.

---

## 4. Friction nodes — definition

A **friction node** is a *contested phenomenon* — a territory, resource, technology, institution, or normative regime — where ≥2 strategic narratives apply with mutually incompatible prescriptions, sustained over time.

### What it is, what it isn't

| It IS | It is NOT |
|---|---|
| Atomic (one phenomenon per FN) | A "hot zone" of activity |
| Persistent (Taiwan endures even when "cool") | Transient (Iran War 2026 can dissolve when war ends) |
| Curated (we hand-pick the canonical list) | Auto-detected from heat |
| Defined by *narrative incompatibility* | Defined by *cross-country breadth* |
| The analytical primitive | The discovery surface |

### Examples

| Friction node | Competing narratives | Why it's structural |
|---|---|---|
| Taiwan | west_china_strategic_competition ↔ multipolar_anti_us_hegemony ↔ china_pla_modernisation_defensive | Same island, three incompatible reads of every PLA exercise, every chip restriction, every transit |
| Iran nuclear program | west_iran_proxy_threat (nuclear slice) ↔ multipolar_anti_us_hegemony | Same enrichment levels, "existential threat" vs "sovereign right" |
| Arctic | arctic_coastal_sovereignty ↔ russia_defensive_imperialism ↔ us_hemispheric_primacy ↔ china_alternative_order (polar Silk Road) | Same ice-melt geography, four converging coalitions |
| AI sovereignty | west_china_strategic_competition (tech slice) ↔ china_alternative_order ↔ (missing: EU digital sovereignty narrative) | Same chip-control regimes, three frames |
| Climate regulation regime | (missing: EU green-deal narrative) ↔ multipolar_anti_us_hegemony (Global South sovereignty) ↔ (missing: US energy-security narrative) | Same regulatory texts, multiple incompatible positions |

The "missing" notes above are useful: the FN test surfaces narrative gaps that pure narrative-first work would miss.

### What FN is for

A FN page answers: *"This phenomenon is contested. Here are the frames being applied. Here's the event flow each frame is feeding on. Here's the intensity over time."*

The "perspectives" view (clicking an FN and seeing each coalition's read of the same facts side-by-side) is the killer UX, regardless of granularity choice.

### Minimal v0 schema (provisional)

Mirrors the existing `strategic_narratives` shape:

- `id` (text slug)
- `name`, `description`
- `centroid_ids[]` (where the phenomenon manifests geographically)
- `topic_keywords[]` (event filter — same role as in v2 narrative worksheet)
- `competing_narratives[]` (FK to strategic_narratives)
- `is_active`

Don't build the table yet. Draft 8–12 FNs in markdown first; schema falls out once the format stabilizes.

---

## 5. The model we rejected (and why)

The April vision (`FRICTION_NODES_VISION.md`, two Asana tickets from 2026-04-01/02) defined friction nodes as **active conflict zones** detected from cross-country activity heat: "Iran War" (28 countries), "US-China Competition" (18 countries), etc. Maybe 5–10, transient, auto-detected.

We rejected this *as the database object* for three reasons:

1. **Misses important contested phenomena that don't have heat breadth.** AI sovereignty, climate regulation regime, semiconductor supply — all structurally contested, none with the cross-country profile of "Iran War". The April model would not surface them.
2. **Confuses analytical unit with discovery surface.** A discovery surface needs to be transient and reactive. An analytical unit needs to be stable and persistent. Same word, different jobs.
3. **Loses precision.** "Iran War" as one bucket conflates four genuinely distinct contests (nuclear, Houthi, Israel-Hezbollah, US-Iran direct), each with its own narrative collision pattern.

What survives from the April thinking:
- The **perspectives view** (multi-coalition side-by-side on the same facts) is gold. Carry it into the new model.
- The **explanation ladder** ("Headlines → events → contested phenomena → forces shaping world order") is the right user-facing story.
- The **deprecation list** (epics, signals page, entity-level "narratives") still applies.
- The **detection logic** (strategic narratives co-firing across centroids) is reused as a *nomination* mechanism — data suggests candidate FNs; humans approve or reject.

---

## 6. The granularity rule for narratives

A narrative consolidation that's directionally good (the v2 worksheet) needs a sharper rule for granularity. Here it is:

> **A narrative is one worldview's framing of an actor/phenomenon, identified by a unified loaded vocabulary. The vocabulary is the diagnostic. A narrative can apply to many friction nodes; that doesn't split it.**

### Worked examples

**N4 `russia_defensive_imperialism` — correctly merged.**

Russia-about-Ukraine vocabulary (*SMO*, *denazification*, *protection of Russian-speakers*, *Russky Mir*, *near abroad*) and Russia-about-West vocabulary (*NATO encirclement*, *NATO encroachment*, *Western escalation*, *informational warfare*) interlock by design. Russian state messaging never separates them ("we had to launch the SMO BECAUSE of NATO encirclement"). One worldview, one interlocking vocabulary, applies to many FNs (Ukraine territory + Baltic + Arctic + gas + cyber). One narrative.

**N1 `west_russia_threat_response` — correctly merged.** Same logic by symmetry. *Full-scale invasion* + *sabre-rattling* + *energy weaponisation* + *revanchism* is one Western worldview applied across many FNs.

**N3 `west_iran_proxy_threat` — likely too coarse, candidate for split.**

Iran-nuclear vocabulary (*existential threat*, *enrichment*, *preemptive strike*, *breakout time*) and Iran-proxy vocabulary (*Axis of Resistance*, *terror infrastructure*, *human shields*, *Hezbollah tunnels*) overlap partially but practically diverge. Israeli sources talking about Natanz vs. Israeli sources talking about Lebanon use measurably different language. Same coalition (Israel-US-Saudi), different phenomena, different (overlapping but distinct) vocabularies. Recommend split into:
- `west_iran_nuclear_threat`
- `west_iran_proxy_network_threat`

This split also maps cleanly to two distinct FNs (Iran nuclear vs Iran shadow war).

### Diagnostic for "should this be split?"

Would the two pieces ever fire WITHOUT each other in real source coverage? If yes (different headlines use only A or only B vocabulary in serious quantity), split. If no (vocabularies always co-fire), one narrative.

This rule turns granularity from an aesthetic question into an empirical one.

---

## 7. The all-in / stand-by rule (generic vs FN-specific narratives)

A second granularity rule, complementary to the unity rule. The unity rule asks: *is this really one narrative or two?* The all-in / stand-by rule asks: *should this narrative exist FN-specific, or fold into a generic cross-FN narrative?*

> **A narrative is FN-specific if and only if its loaded vocabulary is FN-specific. Generic political postures applied across many FNs get generic narratives, not per-FN ones.**

### Two narrative types, both legitimate

**All-in narratives** are FN-specific. The vocabulary is tuned to one phenomenon, doesn't appear elsewhere, and the actor's whole posture on this FN is articulated through that vocabulary. The actor is "all in" — this FN is a defining commitment.

Examples:
- Iran on its nuclear program: *NPT Article IV*, *Khamenei fatwa against nuclear weapons*, *JCPOA betrayal*, *sovereign enrichment*. Vocabulary appears nowhere else. → `iran_nuclear_sovereign_right` is its own narrative.
- Israel on Iran's nuclear program: *existential threat*, *preemptive strike*, *Begin doctrine*, *prevention not deterrence*. → the nuclear half of N3 after split.
- Ukraine on its territorial integrity: *unprovoked invasion*, *Russian imperialism*, *decisive weapons*, *Western hesitation*. → N9.

**Stand-by narratives** are generic political postures applied across many FNs with the same vocabulary. The actor isn't FN-specifically committed — they apply a default doctrine wherever it fits.

Examples:
- EU diplomatic preservation norm: *preserve diplomacy*, *snapback*, *off-ramp*, *dialogue framework*. Same words apply to E3 on Iran, Russia-Ukraine, Israel-Palestine, China-Taiwan. → one `eu_diplomatic_preservation_norm` narrative attaches to all relevant FNs.
- Multipolar systemic alternative: *sovereign right*, *anti-sanctions*, *BRICS*, *Global South*. China-Russia-Iran-DPRK alignment applies this across many FNs without FN-specific tuning. → one narrative covers many FNs.
- US energy security and dominance: *LNG dominance*, *permit liberalisation*, *energy independence*. Same vocabulary across FN10, FN3 (gas displacement), FN6 (Red Sea oil flows). → one narrative, multiple FNs.

### Why the rule matters

Without it, the FN-first audit produces narrative inflation. Every FN has 4-6 coalitions with positions; if every coalition gets an FN-specific narrative, you end up with hundreds of narratives, mostly variants of generic postures applied to specific cases.

The same actor can be all-in on some FNs and stand-by on others. Russia is all-in on Ukraine territory and the Baltic flank (N4); Russia is stand-by on Iran nuclear (just generic multipolar support attaches). The narrative type is a property of the (actor × FN) pair, not the actor alone.

### Diagnostic

For a given (FN, coalition) pair:

1. List the loaded vocabulary the coalition uses on this FN.
2. Ask: does this vocabulary appear in this coalition's framing of other FNs?
   - **No** (FN-specific) → all-in. Either find an existing FN-specific narrative or create one.
   - **Yes** (same vocabulary, same prescriptions across many FNs) → stand-by. Attach the existing generic narrative; do not create FN-specific.
3. If unclear, sample 5-10 actual headlines from this coalition on this FN, then on 2 other FNs. Compare vocabularies side by side.

### Implication for v2

Most v2 narratives are correctly typed. N1, N4, N9, N10, N11, N17, N18, N19, N22, N28 are all-in (deep, FN-tuned). N5 is generic stand-by. N6 (china_alternative_order) is generic stand-by. The hybrid mix is healthy: the system wants both depth (all-in for actors with defining commitments) and parsimony (stand-by for generic postures applied broadly).

Missing narratives surfaced by FN unpacking are mostly all-in (Iran self-frame on nuclear, EU on tech sovereignty, EU on green deal, US on energy security, Palestinian self-frame). One missing narrative is generic stand-by: `eu_diplomatic_preservation_norm`. That distribution is what the rule predicts.

---

## 7.5. Calibrating framing_keywords against primary-source headlines

A practical extension of the all-in / stand-by rule. When you draft a narrative's framing_keywords from your own knowledge of the coalition's loaded vocabulary, those keywords are often *correct in spirit but absent in headline language* — primary sources use different phrasing than the abstract framing language an analyst writes down. Result: the matcher under-catches real coverage, and the narrative looks empty even when there's plenty of on-frame material.

The fix is mechanical: **after drafting a narrative, scan the actual headline corpus from that coalition's primary sources, extract recurring 2-3-word phrases, and add the strong ones to framing_keywords**. Same goes for topic_keywords (named officials, venues, programs that surface in primary coverage).

### The calibration loop

For each new narrative:

1. **Identify the coalition's primary sources** — the outlets that actually carry that coalition's framing (not Western reportage about them). For Iran on its nuclear program: Press TV, IRNA, Fars News, Tasnim. For Israel on the same FN: Times of Israel, Jerusalem Post, Haaretz, JNS, Israel Hayom. For E3 diplomacy: ANSA (Italy), Le Monde, FAZ, BBC, EU statements.

2. **Filter that subset to the FN's topic** — `WHERE publisher_name IN (...) AND title_display ILIKE ANY (topic_keyword_set)`. ~50-150 titles is enough to see patterns.

3. **Extract recurring loaded vocabulary** — phrases that appear repeatedly and carry the framing (not generic verbs). Rule of thumb: if the phrase makes you say "yes, that's how they talk about it", add it. If it could appear in any neutral coverage, skip it.

4. **Add to framing_keywords + topic_keywords** — UPDATE narratives_v2.

5. **Re-bootstrap and verify** — count and sample what's now matched.

### Worked example: iran_nuclear_sovereign_right

Original framing_keywords (drafted from analyst knowledge): 14 keywords including *NPT Article IV*, *Khamenei fatwa*, *we honored the deal*, *deterrence hedge*. Result on local: **1 matching headline**.

After calibration against Press TV / IRNA / Fars / Tasnim coverage: added *peaceful nuclear*, *right to enrich*, *enrichment rights*, *inalienable right*, *rights enshrined in NPT*, *language of force*, *big lie*, *civilian atomic*, *Israeli sabotage*, *attacks on Iran*, *fair nuclear deal*, *religious beliefs*, plus Iranian official names (*Larijani*, *Baqaei*, *Gharibabadi*, *Eslami*) to topic_keywords.

Result on local: **12 matching headlines**, all on-frame. Sample: "Iran will not compromise on enrichment rights" (IRNA), "Russia backs Iran's 'inalienable right' to uranium enrichment" (Press TV), "Pezeshkian: nation rejects language of force".

The 12-fold increase came not from loosening (lower-quality matches) but from learning what loaded language actually *is* in the corpus. The narrative was correctly scoped; the analyst's keyword list just didn't intersect what publishers wrote.

### Why this is a discipline, not a one-off

Every newly created narrative should pass through this calibration step before going live. It's a 10-15 minute job per narrative with the helper script (`scripts/calibrate_narrative_keywords.py`). It's not a pipeline component — it's curation infrastructure, run interactively when narratives are added or when coverage shifts noticeably.

It also produces a useful artifact: a record of *which loaded phrases the coalition actually uses* in the current period. That's its own intelligence product.

---

## 8. How narratives and FNs are drafted (the hybrid approach)

Two pure approaches and why neither alone works:

- **Narratives-first only** (current path): granularity drifts toward source-data shape, not analytical purpose. Polishing becomes aesthetic.
- **FN-first only** (top-down): you'd specify FNs without knowing whether realistic narrative sets can fill them.

**Hybrid: use a small seed FN list as the acceptance test for narratives.**

1. Pick 8–12 obvious seed FNs (Taiwan, Iran nuclear, Ukraine territory, Arctic, Greenland, AI sovereignty, NATO eastern flank, semiconductors, climate regulation regime, Israel-Palestine, Korean peninsula, South China Sea — refine as needed).
2. For each, write a short test paragraph: "this phenomenon is contested; coalition X reads it as A with vocabulary X1,X2; coalition Y reads it as B with vocabulary Y1,Y2; …".
3. Audit v2 narratives FN by FN. The questions become concrete:
   - Does any v2 narrative cover frame A on this FN with the right vocabulary?
   - Are there narratives present here that overlap so completely they should merge?
   - Are there frames present in real coverage that no v2 narrative captures? (Missing-narrative gaps.)
4. Polish narratives in response. Add missing ones.

The FN seed list is the *test*, not just the next deliverable. Both directions move in parallel; the FNs constrain the narrative work.

---

## 9. What this means for current work

### In flight
- **Narrative consolidation v2** (`out/narrative_consolidation_pass1_v2.md`) — 30 framing-explicit narratives covering GPC + Security Order. Status: drafted, not yet reviewed item by item.
- **Multi-actor coalition support** (commit `5468127`) — `actor_centroids[]` column added; matcher updated. Schema-ready for the v2 narratives.

### Next concrete moves (probably tomorrow)
1. Draft the seed FN list (8–12 markdown entries in same style as v2 worksheet)
2. Audit v2 narratives against the unity rule. Surface 3–5 split-candidates and 0–N missing narratives.
3. Cross-reference: mark which narratives apply on which seed FNs.
4. Decide whether v2 (consolidation) plus FN seed list is enough to move to schema + matching changes, or whether a Pass 2 (LIO + Plural World Order narratives) needs to land first.

### Deprecations (April plan, still applies, not urgent)
- `epics` table → replaced by friction nodes
- `mv_centroid_signals` page → metadata on FNs/narratives, not a standalone surface
- entity-level "narratives" → rename to "media perspective"; reserve "narrative" for strategic level only (D-046 already decided)
- `event_families` → already deprecated D-059

### Reuses
- Existing `strategic_narratives.meta_narrative_id` field links each strategic narrative to its meta. The macro-friction (meta ↔ meta opposition) is queryable from existing schema — no new entity.
- Existing `aligned_with[]` and `opposes[]` columns can extend to meta-narratives for the same purpose.

---

## 10. Open questions

1. **Seed FN list composition.** Which 8–12 FNs are the right starting set? Heavily Russia/China-weighted, or geographically distributed?
2. **Top-down vs bottom-up FN drafting.** Draft from a typology (territorial / technological / normative / institutional)? Or from your existing knowledge of what's contested?
3. **`framing_keywords` vs `topic_keywords` schema.** Two columns or one? The v2 worksheet introduces this split as a content distinction; the matching code needs to use them differently (topic = pre-filter, framing = confirm).
4. **Pass 2 timing.** Migrate Pass 1 (30 narratives) alone first as a sanity check, accepting a mixed state for a few weeks? Or wait for Pass 2 (LIO + PWO) and migrate together?
5. **Where do narratives that don't fit any FN go?** Some narratives (e.g., regional security like N15 mexico_cartel_sovereignty) might not collide with anyone — they're standalone positions. Are these "monocular" narratives, treated differently in the UI? Or is "no FN" itself a useful signal?

---

## 11. Production lessons (2026-05-07, after FN2-FN4 went live)

The first three FNs shipped to production today: `iran_nuclear_program`,
`iran_proxy_network`, `iran_regime_legitimacy_contest`. Several
architectural choices that were theoretical when sections 1-10 were
written are now empirically validated, and a few new patterns surfaced.

### 11.1 Publisher-stance bucketing > pure text matching

The original v2 worksheet treated framing-keyword vocabulary as the
primary attribution signal. In practice, **publisher editorial stance
is the more reliable primary signal**, with framing keywords serving as
the gate for stand-by narratives whose publishers are aggregators.

A title from Press TV is intrinsically the Iranian frame, regardless of
which words it uses. A title from BBC needs framing-keyword evidence
because BBC covers everything from many angles. The clean rule:

  - **all_in narratives**: publisher + topic match is sufficient.
  - **stand_by narratives**: publisher + topic + framing keyword,
    UNLESS publisher is in `editorial_organ_publishers` (state media
    or ideologically-aligned outlet) — those bypass framing.

This sits in the bootstrap (`scripts/bootstrap_friction_node.py`) and
in the schema (`narratives_v2.editorial_organ_publishers TEXT[]`).
Replaces the original framing-only matching from May 6 drafts.

### 11.2 Topic_keywords need to be specific or false positives explode

Lesson surfaced when FN4 (`iran_regime_legitimacy_contest`) initially
included generic words like *crackdown*, *topple*, *overthrow*, *the
regime* alone in topic_keywords. These caught BBC's *"Google
crackdown"*, FT's *"Hungary delivers regime change"*, Guardian's *"Trump
fraud crackdown"*, Guardian's *"North Korea regime serves only itself"*.
Topic-match counts inflated to 545; actual on-FN coverage was much
smaller.

Rule: topic_keywords must be either multi-word phrases (*"Iranian
regime"*, *"regime change in Iran"*) or genuinely-distinctive proper
nouns (*Khamenei*, *Pahlavi*, *MEK*, *Mahsa Amini*). Single common
words alone (*regime*, *crackdown*, *opposition*) over-trigger.

Same lesson applies to event-title gates (the `event_actor_markers` /
`event_topic_markers` / `event_title_anchors` tuple on `friction_nodes`).

### 11.3 Multi-language framing keywords are non-negotiable

European mainstream media (BBC English, Le Monde French, Der Spiegel
German, La Repubblica Italian, El País Spanish) covers a single
phenomenon in its native language. The diplomatic-preservation frame on
the Iran war shows up as:

  - English: *ceasefire / fragile ceasefire / mediation / Macron urges /
    Pope appeals / deal can be done*
  - French: *cessez-le-feu / dialogue avec / négociation / diplomatie*
  - German: *Waffenruhe / Verhandlung / Diplomatie / Friedensgespraech*
  - Italian: *tregua / cessate il fuoco / negoziato / mediazione*
  - Spanish: *alto el fuego / negociación / mediación*

An English-only framing keyword set would have dropped the EU diplomacy
narrative on FN4 from a real ~164 matches to ~50. Always calibrate
against the publisher's native-language headlines.

### 11.4 Calibration is iterative, not one-shot

The calibration helper (`scripts/calibrate_narrative_keywords.py`)
should be run multiple times per narrative as it touches new FNs.
Each FN brings its own headline corpus; the framing language that
proves useful is FN-specific. Example: EU diplomacy on Iran nuclear
uses *Vienna talks / snapback / JCPOA-plus*; on Iran regime legitimacy
uses *ceasefire / Macron urges / Pope Leo*. Same narrative, different
recurring vocabulary by FN.

Workflow: when a new FN is added and a stand-by narrative attaches with
visibly low match count, re-run calibration for that narrative against
that FN's publisher subset. Add the new keywords. Re-bootstrap.

### 11.5 Recurrence != loadedness

Calibration produces RECURRING phrases. Not all of them are loaded
(diagnostic). Common phrases like *"uranium enrichment"* or *"nuclear
talks"* recur in everyone's coverage of Iran nuclear, regardless of
frame. Including them in framing_keywords means everyone's coverage
attaches to whatever narrative carries the keyword.

The analyst's job in the calibration loop is to filter the recurring
phrases for genuinely-loaded ones. *"preemptive strike"* is loaded
(diagnostic of Israeli/US threat doctrine). *"nuclear talks"* is not
(everyone uses it). The helper surfaces candidates; the human
distinguishes.

### 11.6 Fat-FN consolidation works

The early concept-doc draft (sections 1-10) was unsure whether the Iran
cluster should be 5-6 thin FNs (regime, war, decapitation, sanctions,
sanctions enforcement, diaspora opposition) or 3 fat ones. Production
validated 3 fat FNs:

  - `iran_nuclear_program` — the program itself
  - `iran_proxy_network` — Iran's regional armed-group network
  - `iran_regime_legitimacy_contest` — the right of Iran to exist as
     a state, spanning diplomatic / sanctions / soft-power / kinetic
     phases

The Khamenei killing, Larijani killing, Mahsa Amini protests, Pahlavi
diaspora rallies, MEK activity, and the 2025-2026 war all live in FN3
(regime legitimacy) as different phases of the same contest. Smaller
FNs would have artificially split connected events.

Rule: a fat FN spans many phenomena IF they share an underlying
contested question. Three thin FNs would each have 4-5 narratives that
mostly overlap; one fat FN has 4 narratives that each meaningfully
distinguish.

### 11.7 Related-FN linkage activates with the second FN

The "theater grouping" view from section 3 was empty for FN2 alone
(no other FNs to link to). It activated automatically when FN3 landed:
both FNs share `eu_diplomatic_preservation_norm` +
`multipolar_systemic_alternative` (≥2 shared narratives = qualifies as
related). With FN4 each Iran FN points at the other two.

No code added for this — it's a query over `friction_node_narratives`.
The architecture pays off as the FN library grows. The first FN is
expensive (full schema + bootstrap); subsequent FNs are mostly data.

### 11.8 Production-readiness checklist (validated)

For a new FN to be production-ready:

  1. friction_nodes row with: name, description, editorial_summary,
     centroid_ids, topic_keywords, event_actor_markers,
     event_topic_markers, event_title_anchors (all bilingual where
     applicable)
  2. New narratives drafted with FN-specific framing_keywords +
     calibration pass against actual publisher headlines (multi-language)
  3. Existing stand-by narratives' framing_keywords expanded if they
     attach to this FN (run calibration helper against this FN's
     publisher subset)
  4. friction_node_narratives links with stance_label per (FN, narrative)
     pair
  5. Run `python scripts/bootstrap_friction_node.py --fn-id <slug>` —
     verify volumes are credible (not 5 when you'd expect 100; not 5000
     from generic-keyword false positives)
  6. Sanity-sample 10 headlines per narrative — they should be
     visibly on-frame
  7. Apply on Render, run bootstrap on Render, bust frontend cache

The runbook at `docs/context/FRICTION_NODES_RUNBOOK.md` codifies this.

---

## 12. The user-facing summary (for whenever the front page rewrite happens)

> WorldBrief tracks global news through 75 country lenses.
> Headlines cluster into events.
> Events accumulate around contested phenomena — friction nodes.
> Each friction node is read differently by different actors — strategic narratives.
> Above all of it sit the enduring forces shaping world order — meta-narratives.
>
> You can enter at any level: the big forces, the contested phenomena, a specific country's view, or the daily headlines from 200+ publishers.

Five levels. One sentence each. The product is intelligible.
