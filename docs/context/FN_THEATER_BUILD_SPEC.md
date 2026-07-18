# Building a Theater — Calibration Spec

**Status**: evergreen reference. Read before building or re-tuning any
theater's friction nodes. This is the *methodology* spec; it complements:

- [`FRICTION_NODES_RUNBOOK.md`](FRICTION_NODES_RUNBOOK.md) — how to add an
  FN end-to-end (tables, tiers, 5-step stance scale, asset layer).
- [`FN_ANCHOR_VOCABULARY_SPEC.md`](FN_ANCHOR_VOCABULARY_SPEC.md) — the
  4-pillar / 7-rule mechanics of drafting a single `fn_anchor` bundle.

This spec answers a different question: **given a new conflict theater,
how do you carve it into atomic FNs and tune them so matching is accurate
and non-overlapping — and how do you prove it with real data?**

It was written after the Ukraine theater calibration (2026-07), which took
the theater from ~46% cross-theater leak to ~2% using only data levers
(aliases + centroid roles), no FN-specific code. Ukraine is the template;
this spec generalises it so every theater follows the same process.

**Two entry modes.** Read §0a first to pick yours:
- **Re-tune** (Ukraine template): the theater + atomics already have
  `fn_anchor` bundles and narratives — you PRUNE (§3) and re-measure.
- **Greenfield / blank** (Arctic template, 2026-07): the FN rows may exist as
  shells but there are **no bundles and no narratives** — you BUILD, then
  measure. Most new theaters are greenfield. The Arctic build added the pieces
  the Ukraine re-tune never exercised: from-scratch bundle authoring,
  theater-level narrative cards (§5.5), and the bilingual completeness fields
  (§6). Follow the ordered runbook in §0a.

---

## 0. Principles (the whole philosophy in six lines)

1. **Theaters carry no taxonomy.** A theater is a pure aggregator of its
   atomics. It has no `fn_anchor` bundle and never participates in matching.
2. **Atomics are sharp and unambiguous.** Each atomic's vocabulary should
   identify its phenomenon and nothing else.
3. **Less but better.** A small set of high-precision aliases beats a large
   promiscuous one. Prune aggressively.
4. **Precision over recall.** Phase-4 CTMs already summarise many titles;
   losing a duplicate headline costs almost nothing, a false attribution
   costs trust. Aim for representative coverage, not exhaustive capture.
5. **Only two data levers — no per-FN code.** Everything is achieved with
   (a) alias vocabularies and (b) centroid roles (participant + target).
   Never add FN-specific branches, AND-logic, or exclusion rules in code.
6. **Calibrate against real coverage.** Never tune from intuition. Measure
   which aliases match which real headlines, then cut.

---

## 0a. Greenfield runbook (blank theater, no bundles/narratives)

A cold session can execute this end-to-end. Each step links to detail below.
Work is **LOCAL and reversible** (taxonomy/narrative edits are test data;
`scripts/safe_db_migrate.py` backs the DB up before every apply). Render
promotion is a separate, explicitly-authorized step.

**Model assignment per step** (learned from `eu_cohesion_theater`,
2026-07-15 — see `project_eu_cohesion_theater` memory). The pattern: steps
that *apply* an already-made decision against a spec are Sonnet-safe; steps
that *make* the decision by reading ambiguous real-world data are where
Opus's extra reasoning earns its cost. Two concrete bugs this session were
only caught by that closer read at steps 3 and 9 — a name-gated atomic's
Kremlin narrative swept in unrelated foreign-language country news because
its `framing_required` was left off (317→12 titles once fixed), and a
stance-ambiguous framing keyword (`Zusammenarbeit mit der AfD` — appears in
both "recommends cooperation" and "warns against cooperation") was putting
pro-firewall headlines into the sovereigntist narrative. Both were found by
reading actual title samples with a skeptical eye, not by trusting a
plausible-looking count.

0. `[Sonnet]` **Read** this spec + `FN_ANCHOR_VOCABULARY_SPEC.md`. Confirm the
   theater is greenfield: `SELECT id, fn_type, is_active FROM friction_nodes
   WHERE id LIKE '<prefix>%'` and check `taxonomy_v3` (fn_anchor) +
   `narratives_v2` are empty for those ids.
1. `[Opus]` **Re-evaluate structure FIRST (§2a)** — inventory + ground against
   real *event/title* coverage; map themes→atomics; find the five defects;
   propose add/merge/split/re-scope. **PAUSE for sign-off.** Never build on a
   wrong decomposition. Watch for the dominant real-world theme having no home
   (Arctic: Greenland control was 86% of coverage yet sat in another theater;
   `eu_cohesion`: Orbán had been defeated, Brexit was dead, and Poland's real
   volume was Ukraine/Russia coverage, not internal EU friction — none of
   that is visible without reading real 2026 samples). This is the highest
   ambiguity step in the whole runbook; don't shortcut it on a cheaper model.
2. `[Sonnet]` **Apply approved structure** — `member_fn_ids` moves,
   activate/deactivate. Mechanical once approved. An atomic belongs to the ONE
   theater whose terrain defines it (move it, don't dual-home).
3. `[Opus for the drop/keep calls; Sonnet OK for drafting + applying]`
   **BUILD each atomic's `fn_anchor` bundle (§3 + vocab spec)** — draft by the
   4-pillar lens (or run `extract_fn_anchor_via_deepseek.py`), then **audit
   every alias** against real headlines, drop leak-class aliases, apply. Keep
   curated JSONs in `out/extraction/`. Reading the auditor's raw `%foreign`
   without checking *co-occurrence* is the trap: `eu_right_realignment`'s
   `Bardella` alias showed 84% "%foreign" against `MIDEAST-LEVANT`, but every
   one of those titles also carried `FRANCE` — it was benign co-mention, not a
   leak, and dropping it on the percentage alone would have cut a precise
   anchor.
   ```bash
   PYTHONIOENCODING=utf-8 python scripts/audit_fn_anchor_aliases.py --fn-id <fn> --window-days 180 --samples 1 --min-n 1
   python scripts/apply_fn_anchor_bundle.py --json out/extraction/<fn>__curated.json --mode apply
   ```
4. `[Opus for diagnosis; Sonnet for the mechanical UPDATE]` **Set centroid
   roles (§2)** — target-centric → `primary_target`; multilateral/bilateral →
   null. **Diagnose leak as a possible CENTROID GAP before blaming aliases**
   (§4): a high `%foreign` dominated by an on-side institutional centroid the
   FN omits (NATO/EU/China) is a missing participant, not a bad alias — add
   the centroid, re-audit.
5. `[Sonnet]` **Attribute events** — needs only the bundle (no narratives
   yet). Full 180-day rebuild is slow (~2 min/FN); run in background or
   per-FN.
   ```bash
   PYTHONIOENCODING=utf-8 python scripts/bootstrap_friction_node.py --fn-id <fn> --window-days 180
   ```
6. `[Opus]` **Author ATOMIC narratives (§5)** — pro/con pair per atomic, plus
   the friendly-critic (own-goal) and rift-exploitation (intra-Western)
   checks. Bilingual, every field. Getting the stance framing *right* — not
   just present — is the hard part: avoid baking in a contested label as fact
   (e.g. "far-right" is a term most such parties reject; keep it out of
   neutral FN prose and let it surface only as a matching alias and inside
   the *critical* narrative, balanced by the parties' own self-labels in the
   sympathetic narrative). Re-run `bootstrap` to fill `title_narratives`.
7. `[Opus]` **Author THEATER-level narratives (§5.5)** — required for the
   theater page to render narrative cards. Publisher-DISJOINT within each
   stance-sign bucket; same framing-nuance care as step 6.
8. `[Sonnet]` **Completeness fields (§6)** — `friction_nodes.name_de`,
   `description_en/_de`, `editorial_summary_en/_de` for the theater AND every
   atomic (bilingual). Mechanical once the facts and framing are settled in
   steps 1/6/7.
9. `[Opus]` **Measure (§4 step 6)** — leak%, within-group overlap,
   per-narrative counts; read samples; don't chase the last ~2%. Don't just
   check the counts look plausible — pull actual sample titles per narrative
   and read them. This is where both session bugs above were actually found.
10. `[Sonnet]` **Cache revalidate** to view locally
    (`POST /api/admin/revalidate-cache`); then Render promotion by state-diff
    → sync migration (separate step).

> Windows: prefix Python that prints non-Latin aliases with
> `PYTHONIOENCODING=utf-8` (cp1252 console else `UnicodeEncodeError`). Author
> DB content as `.sql` migrations run through `safe_db_migrate.py` (auto-backup),
> not raw psql.

> **If you can't switch models mid-step** (e.g. a step is a long
> back-and-forth in the main conversation and delegating to a subagent would
> lose shared context): stop at the step boundary and say so explicitly —
> "PAUSE: switch to Opus for step N, then back to Sonnet after" — rather than
> continuing on the wrong-tier model. Steps 3–4 and 9 are the ones where
> results depend most on *reading output skeptically*, not just producing it.

---

## 1. Structure: theater + atomics

```
Theater FN (aggregator, NO fn_anchor bundle)      ukraine_war_theater
   +-- Atomic FN (sharp)                          ukraine_battlefield
   +-- Atomic FN                                  ukraine_infrastructure_war
   +-- Atomic FN                                  ukraine_peace_negotiations
   +-- Atomic FN                                  ukraine_official_corruption
   +-- Atomic FN                                  western_aid_to_ukraine
```

**Theater rules**
- No `fn_anchor` row in `taxonomy_v3`. The theater view is built by rolling
  up its atomics' attributed events/titles + summary stats + samples.
- Theater-level narratives (meta-framings that cut across atomics, e.g.
  "Solidarity with Ukrainian resistance", "SMO framing", "Proxy-war
  critique") are **not** sourced from headline matching. Source them from a
  separate doctrinal/statements data layer, or from curated samples of the
  atomics. Do not give the theater a bundle just to feed them.
- `link_titles` already excludes titles claimed by an atomic when attributing
  a theater — atomics claim their content first. Keep that ordering.

**Atomic rules**
- Atomics should be *orthogonal phenomena*, but note they are not the same
  *kind* of thing (military operation vs diplomacy vs governance vs external
  support). Some structural overlap between them is unavoidable and fine —
  maximise semantic *purity* of each, don't chase zero overlap.
- Each atomic gets one high-precision `fn_anchor` bundle (this spec, §3) and
  a set of narratives (§5).

**Deactivated FNs**: mark inactive and ignore. Do not attribute or tune them
(e.g. `ukraine_proxy_war` was inactive and excluded entirely).

## 1a. Standalone atomics — when a theater is the wrong container

Not every conflict earns a theater. If real coverage supports **one** atomic
(§2a, §2 A2b), do NOT nest it under a theater: a theater is a pure aggregator
and with one member it has nothing to roll up. Deactivate the theater and let
the atomic stand alone. This is the intended shape for low-volume /
high-latency conflicts — ones that fail the volume test but pass on
supply-chain impact or escalation potential.

- **An FN cannot be both.** `fn_type` is single-valued and the two branch to
  different paths. A theater carries **no bundle and never matches titles**, so
  typing a conflict as a theater to dodge nesting gives it zero attribution.
- **The atomic detail page already supports it**: `getTheaterForAtomicFn`
  returns null for an orphan and the sibling list falls back to `[]`.
- **Navigation supports it as of 2026-07-16**: `getAllFrictionNodesByRegion`
  emits atomics in no *active* theater as `standalone: true` zones, rendered as
  a direct link. Region comes from `centroid_ids[0]`, so keep `centroid_ids`
  populated. Deactivating a theater is enough to orphan its members.
- **Homepage conflicts map supports it as of 2026-07-16**: the map API
  (`app/api/friction-nodes-map/route.ts`) `UNION`s orphan atomics into its
  theater query. The conflicts layer draws FNs with `scope='regional'` AND a
  non-null `anchor_point`. Set `anchor_point` (GeoJSON Point epicentre) and
  `affected_asset_ids` on the atomic — if a retired theater owned them, MOVE
  them to the atomic or the conflict vanishes from the map. (Dynamic
  news-evidence asset links stay theater-only —
  `compute_fn_asset_evidence.py`.)

Worked example: `scs_theater` retired 2026-07, `south_china_sea_claims` stands
alone (`db/migrations/20260716_scs_standalone_atomic.sql`).

---

## 2. Centroid roles — the two archetypes

Every atomic falls into one of two archetypes. **The archetype dictates
whether centroid roles can help, and which aliases you can afford.**

`friction_nodes` gives you two centroid levers, both pure data:
- `centroid_ids[]` — **participants**: the attribution scope. A title
  qualifies if `title.centroid_ids && fn.centroid_ids`.
- `primary_target` — **target**: an additional gate. If set, the title must
  carry that centroid (`primary_target = ANY(title.centroid_ids)`).

### Archetype A — target-centric

The phenomenon is *about one subject country*: aid **to** X, corruption
**in** X, peace **about** X, sanctions **on** X.

- Set `primary_target = <subject centroid>`.
- **The target gate is the general substitute for AND-logic.** It cross-
  filters generic domain vocabulary (`aid`, `loan`, `ceasefire`,
  `corruption`) so those single words become safe — a title only attributes
  if it also carries the subject centroid. This is why you must NOT gut the
  domain verbs from these FNs; the target gate makes them precise.
- Prune only: outright collisions (`FAB`=Brazilian Air Force, `Lancet`=the
  journal, `SBI`=State Bank of India), and cross-domain generics whose
  samples stay off-topic *even with* the subject co-tag (`fighter jets`,
  `frozen assets`, `joint venture` in aid → Gaza/Iran/Taiwan).

**Sub-case A2 — the subject's NAME is the gate (anchor == subject).** When the
subject is a *place/entity* whose proper name is highly specific and its
subject centroid is under-populated (Arctic `greenland_control`: real Greenland
titles tag `NORDIC`+`USA`, barely `EUROPE-GREENLAND`), the toponym itself is a
near-perfect gate. Then:
- Build the bundle from the **name + its translations + sub-toponyms/actors
  only** (`Greenland`/`Grönland`/`Groenlandia`/`Nuuk`/`Pituffik`/`Naleraq`).
- **Omit generic domain verbs entirely** (`buy`, `annex`, `sovereignty`,
  `control`). Aliases are OR'd, and with the subject centroid too sparse to
  gate via `primary_target`, a bare verb would leak across all participant
  news. The name carries the precision.
- Leave `primary_target` **null** and widen `centroid_ids` freely — a title
  can't contain the name without being on-topic, so wider scope only helps
  recall (Arctic `greenland_control`: `Greenland` matched 1614 titles at ~5%
  nominal foreign, nearly all legitimate European reaction).

**Sub-case A2b — the A2 gate cannot be split across atomics.** When the subject
is a *place* rather than a country (a sea, a strait, a basin), A2 forces the
theater down to **one atomic**, because:
- aliases are OR'd and there is no AND, so a second atomic must carry the same
  toponym set and will match the *identical* titles;
- `primary_target` can't substitute — there is no centroid for "the South China
  Sea" to target (this is what makes A2b different from plain Archetype A,
  where the subject *is* a centroid);
- the Arctic escape hatch — compound phrases (`Arctic shipping`, `Arctic oil`)
  — **does not generalise**. Matching is literal-substring and order-sensitive
  (vocab spec, order rule), and English says "patrol **in the** South China
  Sea". Measured: `South China Sea patrol` = 1 hit, `South China Sea drill` =
  0. Arctic only worked because "Arctic shipping" is naturally adjacent.

So before planning a multi-atomic split on a place-subject theater, **test the
compound forms against real headlines**. If they return ~0, the theater is one
atomic — and if that atomic is the only one, retire the theater and let it
stand alone (§1a). SCS 2026-07: a proposed `freedom_of_navigation` atomic died
here — FONOP/Seventh Fleet/Talisman Sabre = 0, `freedom of navigation` →
Hormuz, `Nimitz` → the Caribbean, `George Washington` → the president; only
`Balikatan` (6 titles) was clean, which is not an atomic.

### Archetype B — bilateral / symmetric

The phenomenon acts in *both directions*: battlefield (Russia hits Ukraine;
Ukraine hits Russia) and infrastructure strikes (Kyiv grid; Russian
refineries). Action legitimately occurs on either belligerent's soil.

- **No valid `primary_target`.** Setting either side deletes half the
  phenomenon (a UKRAINE target drops Ukrainian deep-strikes on Russia, which
  carry only the RUSSIA centroid; a RUSSIA target drops Russian strikes on
  Kyiv). Leave `primary_target` null.
- A "target = either A or B" set is a **no-op** here: `centroid_ids` is
  already exactly `{A, B}`, so the participant gate already means "carries A
  or B." It cannot separate the in-theater strike story from an out-of-
  theater one, because both ride the shared belligerent (RUSSIA).
- Therefore **alias purity is the only lever.** Bilateral atomics must lean
  on *fixed* nouns that don't occur in rival theaters: toponyms, named
  installations/sites, own-side org acronyms, fixed target-nouns. Generic
  verbs and shared equipment are the enemy.

> Diagnostic that confirms the archetype: attribute the FN, then measure the
> share of attributed titles lacking the subject centroid. Target-centric
> FNs sit at ~0% (the gate works). Bilateral FNs sit high — but most of that
> is *legitimate* cross-border content, so do NOT "fix" it with a centroid
> gate; fix the aliases (§3).

### On rival-theater exclusion (don't build it)

It is tempting to add "in scope only via the shared belligerent AND also
carries a rival-theater centroid ⇒ drop." Measured on Ukraine post-prune,
the rival-theater residual was **37 titles (~2%)**, and much of it is either
correct (Kursk + North-Korean-troops stories) or an irreducible core-anchor
collision (`refiner` catching "India buys Russian oil"). The alias prune
already removes the *vehicles*. Building exclusion machinery to chase ~2%
adds tuning surface and risks false-drops (e.g. "US–Russia talks on
Ukraine" carries USA+RUS). **Measure first; don't build it unless the
residual is large and rides non-core aliases.**

---

## 2a. Structural re-assessment — DO THIS FIRST, before any tuning

Before touching a single alias, confirm the atomics actually carve the
conflict correctly. Alias/centroid tuning on a wrong decomposition is wasted
effort. This step is domain-model work — **propose changes and get sign-off
before applying** (new/merged/split FNs touch `friction_nodes` +
`narratives_v2`, unlike reversible alias edits).

**Method (empirical, not from intuition):**

1. **Inventory.** List the theater + its atomics with names, `centroid_ids`,
   `primary_target`, and each atomic's narratives + coalitions:
   ```sql
   SELECT id, fn_type, centroid_ids, primary_target FROM friction_nodes
   WHERE id LIKE '<theater_prefix>%' ORDER BY fn_type, id;
   SELECT fn_id, id, stance, array_length(publishers,1) FROM narratives_v2
   WHERE fn_id LIKE '<theater_prefix>%' ORDER BY fn_id, display_order;
   ```

2. **Ground in real coverage.** Pull the theater's recent *events* (not raw
   headlines-of-the-day) via its centroid, and read the dominant real-world
   sub-conflicts/themes — the event clusters / CTMs are the signal. Ask "what
   is this conflict actually made of, this quarter?"

3. **Map themes → atomics** and look for five defects:
   - **Coverage gap** — a major, persistent theme with no atomic → *add* one
     (e.g. an information/sanctions/maritime dimension that clearly exists).
   - **Redundancy** — two atomics capturing the same phenomenon → *merge*.
   - **Impurity** — one atomic spanning two orthogonal phenomena → *split*
     (this is usually why an atomic leaks or won't prune clean).
   - **Archetype mismatch** — an atomic that is neither cleanly target-centric
     nor bilateral (§2) → *re-scope*; it's often two atomics wearing one name.
   - **Staleness / centroid error** — an atomic for a finished phase, a
     missing new phase, or participant/target sets that don't match who is
     actually involved.

4. **Sanity-check the narrative layer** while here: is any atomic an
   "own-goal" topic (corruption, humanitarian failure, military setback) where
   the supportive camp turns critic? If so it needs the three-stance
   framing-required model (§5), not a plain pro/con pair.

5. **Decide add / merge / split / re-scope, propose to the user, apply only
   after approval.** *Then* proceed to §3–§5.

---

## 3. Alias pruning — the leak-class taxonomy

Rewrite each atomic's bundle to keep only high-precision anchors. Decide
each alias by class:

### DROP — these classes leak across atomics and across theaters

| Class | Why it leaks | Ukraine examples dropped |
|---|---|---|
| **Delivery systems / munitions** | roam across atomics AND theaters (→ Iran) | `Shahed`, `Geran`, `Kalibr`, `Kinzhal`, `Flamingo` |
| **Weapon systems (equipment)** | shared with aid; equipment ≠ operations | `HIMARS`, `ATACMS`, `Patriot`, `F-16`, `Leopard`, `Lancet` |
| **Corporate / market / economic** | global commercial/sanctions/M&A reporting | `Rosatom`, `Gazprom`, `Lukoil`, `energy crisis`, `fuel prices` |
| **Cross-theater institutions** | shared with other theaters | `IAEA`, `Grossi` (→ Iran nuclear) |
| **Generic civil-domain nouns** | civil version exists everywhere | `reactor`, `nuclear plant`, `АЭС` — keep only *named* sites |
| **Generic verbs that mistranslate** | translate into unrelated conflicts | `offensive`→Mali/Israel, `breakthrough`→peace *talks* |
| **Dangerous short substrings** | non-EN path is pure substring | `gel` (⊂ `Vergeltung`, `geprügelt`) — see vocab-spec rule 6b |
| **Promiscuous venues** | shared diplomacy locations | `Doha`, `Riyadh`, `Vienna` (→ Iran/Gulf) |
| **Outright collisions** | homographs | `FAB`, `Lancet`, `SBI`, `Saab`→Venezuela |

### KEEP — these are inherently specific to the phenomenon

- **Toponyms**: front towns, strike-target cities, named installations.
  (`Pokrovsk`, `Ryazan`, `Kupiansk`, `Syzran`.)
- **Named in-theater sites**: keep the *specific* site, drop the generic
  category. (`ZNPP`/`Enerhodar`/`ЗАЭС` yes; `nuclear plant`/`АЭС` no.)
- **Own-side org acronyms** (3+ chars, unique): `ВСУ`, `GUR`, `Energoatom`,
  `NABU`, `SAPO`, `HACC`.
- **Fixed target-nouns**: `refinery`, `substation`, `oil depot`, `power
  grid`, `blackout` (the thing struck, not the weapon or the market).

Then apply the [vocabulary spec](FN_ANCHOR_VOCABULARY_SPEC.md) — 4 pillars,
7 hard rules, native-orthography, Latin-collapse-to-`en`, no country names,
no third-party leaders, no stance phrases.

---

## 4. The calibration loop (corpus-driven, reversible)

Run this for every atomic. Never skip the measurement.

> **Diagnose leak before you cut.** A high audit `%foreign` is not always an
> alias problem. If the "foreign" centroids are the FN's *own actors* it simply
> omitted from `centroid_ids` — e.g. `NON-STATE-NATO`/`NON-STATE-EU`/`ASIA-CHINA`
> on an Arctic security atomic where NATO *is* the actor — it is a **centroid
> gap**, not a bad alias. Add the participant centroid and re-audit *before*
> touching the bundle. On Arctic `arctic_military_presence` this alone took the
> bare-`Arctic` `%foreign` from 42% → 7%; no alias was dropped.

**Step 1 — Baseline metrics.** Record per-FN title counts, cross-theater
leak (share lacking the subject centroid, or carrying a rival-theater
centroid), and within-group overlap (titles on 2+ atomics).

**Step 2 — Per-alias audit.**
```bash
python scripts/audit_fn_anchor_aliases.py --fn-id <fn> --window-days 180
```
For each alias it reports, against real headlines in the FN's centroid
scope: `n` matched, `%foreign` (share carrying a region the FN doesn't
belong to), the top "extra" centroids, and sample titles. This is the
"check vocab against real data" engine. Rank by `%foreign` then volume; the
top of the list is your drop candidates, confirmed by reading the samples.

> Caveat: the auditor applies the *participant* gate but NOT `primary_target`.
> For target-centric FNs it therefore *overstates* `%foreign` (the real
> attribution is tighter). Read it as a promiscuity ranking, not a leak rate,
> for those FNs.

**Step 3 — Prune.** Encode the drop set (all languages, exact strings) and
apply surgically — remove listed strings, keep the rest, back up originals
first. Pattern in `scripts/prune_ukraine_bundles.py` (dry-run / apply /
restore modes; prints "drop strings NOT found" to catch typos in non-Latin
lists). Treat taxonomy edits as reversible test data.

**Step 4 — Set centroid roles.** Confirm `primary_target` on target-centric
atomics; leave it null on bilateral ones (§2).

**Step 5 — Re-attribute (full rebuild).**
```bash
python scripts/bootstrap_friction_node.py --fn-id <fn> --window-days 180
```
Full (non-incremental) run DELETEs + rebuilds, clearing stale leak
attributions. The daemon's incremental `fn_refresh` then keeps it current
automatically (it reads `taxonomy_v3` live — no code deploy needed).

**Step 6 — Re-measure and compare.** Re-run Step 1 + Step 2. Confirm the
cross-theater residual is small AND that what remains is legitimate
(read the samples). Do not chase the last ~2%.

**Acceptance targets** (Ukraine achieved): cross-theater rival-centroid leak
≤ ~3% per bilateral FN; within-group overlap cut by half or more; target-
centric FNs at ~0% leak with domain vocab intact.

---

## 5. Narratives & the friendly-critic caveat

Narratives on an atomic are usually a pro/con pair, each backed by a
disjoint publisher coalition, so **publisher alone disambiguates stance**
and `framing_keywords` are not a hard filter (see
`bootstrap_friction_node.link_titles`).

**This assumption — stance correlates with publisher alignment — breaks for
"own-goal" topics**: corruption, humanitarian failures, military setbacks,
mismanagement. On these, the *normally-supportive* coalition (Western
outlets on Ukraine) is itself highly critical. Symptom, from the Ukraine
corruption FN:

- `reform_in_progress` (supportive) had ALL Western mainstream publishers
  (Spiegel, SZ, Telegraph, BBC, WaPo…).
- `zelensky_regime_corruption` (critical) had ONLY the pro-Russian bloc.
- Result: alarmed Western corruption headlines ("Wie korrupt ist Kyjiw?",
  "Der tiefe Fall des Jermak", "Zelensky survives… for now") get filed as
  *supportive* purely because the outlet is Western. There are really three
  stances — reform-works / Western-alarmed-systemic / pro-Russian-kleptocracy
  — collapsed into two by a publisher-only model.

**Mechanism (implemented):** `narratives_v2.framing_required boolean`
(default false). When true, a title attributes to that narrative only if it
matches the publisher coalition **and** at least one `framing_keywords`
entry (ILIKE substring, multilingual — put EN + DE + … phrases in the flat
array). Handled uniformly in `bootstrap_friction_node.link_titles`; opt-in
per narrative like `primary_target`, so every default-false narrative is
unchanged. Do NOT make framing a global hard filter — some shared-publisher
narratives legitimately *co-apply* (e.g. Sudan humanitarian + proxy-critique)
and must not be force-split.

**Rule for own-goal topics:**
1. Detect them: if a topic's critical coverage spans *both* camps, the
   publisher-coalition assumption is invalid.
2. Build a **three-stance gradient**: supportive / friendly-critic / adversary.
   Give the supportive and friendly-critic narratives the *same* supportive-
   camp publishers, both `framing_required=true`, with disjoint framing
   keywords (reform-positive vs systemic-alarm). The adversary narrative
   keeps its disjoint propaganda coalition and stays `framing_required=false`.
3. Tuning: a title matching neither framing is dropped (precision over
   recall); broaden the framing keywords to recover neutral coverage if the
   drop is too large.
4. Do not rely on publisher coalitions alone for corruption, war-crimes-by-
   own-side, mobilisation failures, or aid mismanagement.

**Worked example (Ukraine corruption, 2026-07):** `reform_in_progress` (+1)
/ `western_systemic_alarm` (−1, NEW) share the Western coalition;
`zelensky_regime_corruption` (−2) keeps the pro-Russian coalition. Result: the
17 alarmed Western titles (Spiegel/BBC/WaPo Yermak coverage) route to the
alarm narrative instead of being misfiled as "reform working."

### The rift-exploitation caveat (intra-Western disputes)

The mirror trap, for atomics whose conflict is **intra-Western** (US vs
EU/Denmark on Greenland, transatlantic tariffs, EU strategic autonomy):
pro-Kremlin (RT/TASS/Sputnik) and Chinese state media (CGTN/Global Times) are
**NOT supportive of either Western side**, even though they cover one side's
claims heavily. Their stance is rift-exploitation — cast the aggressor Western
actor as imperialist, amplify the intra-Western split, expose hypocrisy, deny
any "Russia/China threat" pretext. It is schadenfreude, not endorsement.

- **Do not** file them on the dispute's own pro/con axis (e.g. as
  "pro-US-takeover" because they report Trump's Greenland claims). Publisher
  coalitions are disjoint so they *route* correctly regardless — the damage is
  to the **label**: a card reading "Russia backs US annexation of Greenland" is
  false and corrosive.
- Give the pro-Kremlin/Beijing bloc its **own narrative on a different axis** —
  "Western cohesion / hypocrisy" — labelled as imperial-overreach critique +
  rift-exploitation + pretext-denial, `framing_required=false` (publisher
  suffices). Arctic `greenland_western_hypocrisy` (−2) held 209 titles, the
  single largest narrative on the atomic, correctly labelled.

---

## 5.5. Theater-level narrative cards (the roll-up)

The theater page (`/friction-nodes/<theater>`) renders narrative cards **only
if the theater FN has its own `narratives_v2` rows** (`fn_id = <theater>`).
These are the cross-cutting meta-framings — they are *not* the atomics'
narratives. A greenfield theater has none, so the cards are missing until you
author them.

**How the cards get headlines (no bundle, no matching).** A theater carries no
`fn_anchor` bundle, so its narratives never attribute titles directly. Instead
`THEATER_ROLLUP_SQL` (`apps/frontend/lib/friction-nodes.ts`) sources each
card's sample headlines + count from the **member atomics' `title_narratives`**,
where a title qualifies iff:
- it is attributed to a member-atomic narrative whose **stance sign** equals the
  theater narrative's stance sign (`sign(atomic.stance) = sign(theater.stance)`),
  **and**
- its publisher ∈ the theater narrative's `publishers[]`.
`framing_keywords` only *rank* samples (framing strength), they don't filter.
`match_count` is the uncapped distinct-title count over that match.

**The one hard rule: publisher-DISJOINT within a sign bucket.** Because the
count is uncapped over (sign, publisher), two theater narratives of the *same
sign* whose publisher lists overlap will double-count the same titles. Signs
have only two buckets (+/−), so design coalitions like Ukraine did — three
disjoint blocs across the two negative-capable cards:

| theater narrative | stance | publisher bloc |
|---|---|---|
| Western consensus | +2 | Western mainstream + business |
| Russia/China counter | −2 | Russian + Chinese state |
| Western critical (sovereignty/climate) | −1 | Western/green |

The two negatives (−2, −1) share the negative sign but are publisher-disjoint
(Russian/Chinese vs Western/green), so their counts partition cleanly. A
positive card and a negative card *may* share publishers — opposite signs pull
different-signed atomic titles, so no title double-counts. Note a Western
**negative** atomic narrative (e.g. `greenland_sovereignty_defense`, −1, 90
titles) is homeless unless a negative Western-publisher theater card exists —
so the −1 "Western critical" card is what surfaces the dominant sovereignty
response (and, via framing-strength ranking, the climate headlines too).

Author theater narratives with the full bilingual field set (same columns as
atomic narratives); `framing_required` is irrelevant here (`false`). No
`bootstrap` run is needed — the roll-up is computed live at query time; just
revalidate the frontend cache.

---

## 6. Per-theater checklist

- [ ] **Structural re-assessment done FIRST** (§2a): inventory + real-coverage
      map; add/merge/split/re-scope decided and approved before any tuning.
- [ ] Theater has **no** `fn_anchor` bundle; it aggregates atomics.
- [ ] Each atomic classified: target-centric (set `primary_target`, or the
      anchor==subject sub-case A2) or bilateral/multilateral (leave null).
- [ ] Each atomic bundle **built** (greenfield) or **pruned** (re-tune) by the
      leak-class taxonomy (§3) + vocab spec.
- [ ] Ran `audit_fn_anchor_aliases.py`; changes justified by real samples;
      **centroid gaps ruled out before dropping aliases** (§4).
- [ ] Bundles applied reversibly (curated JSONs saved; DB backed up).
- [ ] Full re-attribution run (events need only the bundle); daemon maintains
      incrementally after.
- [ ] **Atomic narratives** authored: pro/con, plus friendly-critic (own-goal)
      and rift-exploitation (intra-Western) checks; bilingual, all fields.
- [ ] **Theater narratives** authored (§5.5) so the theater page renders cards;
      publisher-disjoint within each sign bucket; roll-up counts verified.
- [ ] **Completeness fields** set bilingually on the theater AND every atomic:
      `name_de`, `description_en/_de`, `editorial_summary_en/_de`.
- [ ] Before/after measured: leak% down, overlap down, residual inspected;
      per-narrative + per-card counts sane, samples read.
- [ ] Inactive FNs excluded.
- [ ] Frontend cache revalidated to view locally.
- [ ] (When promoting to production) same `taxonomy_v3` + `friction_nodes` +
      `narratives_v2` changes applied on Render via state-diff → sync migration
      — a separate, explicit step.

---

## Worked example — Ukraine (2026-07)

| FN | archetype | bundle | titles | rival-leak |
|---|---|---|---|---|
| infrastructure_war | bilateral | 239→99 | 1598→605 | 736→**13** |
| battlefield | bilateral | 294→226 | 1533→1353 | 553→**24** |
| peace_negotiations | target (UKR) | 217→207 | 948→832 | 0→0 |
| western_aid | target (UKR) | 241→209 | 504→347 | 0→0 |
| official_corruption | target (UKR-only) | 228→205 | 102→96 | 0→0 |

Within-group overlap 325→103 titles (−68%). Tools:
`scripts/audit_fn_anchor_aliases.py`, `scripts/prune_ukraine_bundles.py`
(reversible), `scripts/bootstrap_friction_node.py`. Audits archived in
`out/fn_tuning/`.

## Worked example — Arctic (2026-07, greenfield)

Built from blank shells (no bundles, no narratives). Structure: `greenland_control`
moved in from `europe_us_theater` (an atomic lives in the ONE theater that defines
its terrain); China kept as a near-Arctic competitor; 4 atomics.

| atomic | archetype | events | atomic narratives (titles) |
|---|---|---|---|
| greenland_control | A2 anchor==subject (null target) | 684 | manifest-destiny 2 / sovereignty-defense 90 / self-determination 5 / **rift-exploitation 209** |
| arctic_military_presence | multilateral (hosts bare `Arctic`) | 232 | deterrence 110 / militarization 45 |
| arctic_resources_competition | multilateral | 35 | development 14 / **warming-emergency 4** |
| arctic_shipping_routes | multilateral | 27 | opportunity 13 / route-threat 4 |

Overlap ~90% single-atomic / 10% dual / 0 triple. Key levers: bare-`Arctic` leak
42%→7% via a **centroid gap** fix (add NATO/EU/China), not alias prunes;
`greenland_control` toponym-only bundle (no verbs, no target). Theater cards (§5.5):
Western-consensus (+2, 114) / Russia-China-counter (−2, 250) / Western-sovereignty-
&-climate (−1, 76). Migrations: `db/migrations/20260714_arctic_*.sql`. Full
build notes in the `project_arctic_theater` memory.

## Worked example — South China Sea (2026-07, greenfield → standalone atomic)

The first theater the structural assessment (§2a) **shrank to a single
standalone atomic** (§1a). Coverage is ~135 titles/180d and flat (no escalation
curve). Three of four draft atomics had zero corpus — fisheries/militia 0,
nine-dash 0, named reefs empty (Mischief Reef 1, Fiery Cross 0) — and the
claims/freedom-of-navigation split was not expressible at all (§2 A2b).

| | |
|---|---|
| `south_china_sea_claims` | A2b, standalone, null target, 56 aliases → 149 events / 183 titles |
| narratives | `chinese_sovereignty_claim` (+2, 86) / `rules_based_maritime_order` (−2, 97) |
| coalitions | Chinese state (GT 30 / CGTN 24 / China Daily 21 / People's Daily 11) vs Reuters/PH/JP/SEA — **fully disjoint, 0 titles on both** |
| retired | `scs_theater`, `scs_freedom_of_navigation`, `scs_reef_militarisation`, `scs_fisheries_conflict` |

Lessons this build added:
- **No rift-exploitation card here** (contrast Arctic §5): that caveat is for
  *intra-Western* disputes where Russia/China are bystanders amplifying a split.
  China is a **principal party** to the SCS, so its coverage belongs on the
  dispute's own pro/con axis. Check who is a *party* before reaching for it.
- **Non-English substring collisions are live, not theoretical** (vocab rule
  6b): bare zh `南海` matches Japanese `南海トラフ` (Nankai Trough megaquake) —
  and the CJK corpus is 99.7% Japanese, because Chinese state media publish in
  English. Latin ones too: `Subi` ⊂ Mitsubishi (109 hits), `Scarborough` ⊂ Joe
  Scarborough, `Meiji` = the Japanese era.
- **A bundle audit is not enough — pre-audit the draft**: `UNCLOS` resolved to
  the Thailand–Cambodia MOU44 dispute and `arbitral` to Botafogo football
  arbitration. Conversely `Xisha`/`Paracel` at 100%/67% `%foreign` were the
  **Dutch warship** story — benign co-mention, correctly kept.

Migrations: `db/migrations/20260716_scs_*.sql`. Full notes in the
`project_scs_theater` memory; the open ASEAN centroid bug that surfaced during
this build is in `lessons_asean_centroid_bug`.

## Worked example — Australia (2026-07, greenfield → re-scoped off its dyad)

The first theater the structural assessment (§2a) moved **off a dyad onto a
subject anchor**. `australia_china_theater` was a stale draft; the corpus refused
its premise: **AUKUS carries the China centroid in only 3 of 70 titles** (29 carry
Australia alone), and critical minerals in only 12 of 68 — Australia's two largest
strategic themes are Australia-**US**, while the AUS∩CHINA dyad is just 334
titles/180d. Renamed `australia_theater` ("Australia as a contested middle
power"), following `turkey_theater` / `iran_theater` / `cuba_theater`.

| atomic | gate | events | narratives (titles) |
|---|---|---|---|
| `pacific_island_contest` | terrain = island centroids, null target | 32 | western-partnership 29 / china-cooperation 5 |
| `australia_china_trade_leverage` | dyad AND: `{ASIA-CHINA}` + target `OCEANIA-AUSTRALIA` | 55 | de-risking 48 / mutual-benefit 8 |
| `aukus_alliance_reliability` | A2 on `AUKUS`, `{OCEANIA-AUSTRALIA}` only | 63 | necessity 9 / **capability-doubt 28** / bloc-confrontation 1 |
| `china_threat_assessment` (NEW) | dyad AND | 32 | substantiated 33 / fabricated 7 |

Theater cards (§5.5): western-consensus (+2, 117) / alliance-scepticism (−1, 28) /
china-counter (−2, 21); negative bucket verified disjoint (0 shared titles).
Overlap 164 single-atomic / 1 dual.

Lessons this build added:
- **§2 A2 does NOT generalise from Greenland — test it.** Bare Pacific toponyms
  (`Fiji`/`Vanuatu`/`Solomon`) are only **~63% on-topic** (earthquakes, cyclones,
  the Nauru name change, a waste incinerator) versus `Greenland` at ~95%. The
  A2 escape is available only when the subject's coverage *is* the dispute. Here
  the design inverted: **gate on the terrain centroids and put the phenomenon in
  the bundle, with NO toponyms** — a bare `Fiji` would re-admit every cyclone.
  Corollary: the *other* participants (AUSTRALIA/CHINA) must be OUT of
  `centroid_ids`, since the OR-gate would otherwise admit any Australia-only
  title carrying `pact`.
- **A suspiciously LOW narrative count is a recall gap, not disjointness.**
  `pacific_china_cooperation` sat at 1 title with 17 Chinese-state titles in
  scope: the bundle had been drafted from *Western* headlines. Chinese state media
  write "co-op", "defense agreement", "one-China principle", "seabed minerals".
  **Draft phenomenon vocabulary from both camps' headlines.**
- **The event gate has two SEPARATE `EXISTS` clauses** — one member title supplies
  the centroid, a *different* one matches an alias. A polluted centroid therefore
  drags whole foreign events in. This is how Israel/Iran events reached a Pacific
  atomic (see below).
- **Rule 6b bites `centroid_anchor` rows too, and length alone won't catch it.**
  `OCEANIA-PAPUANEWGUINEA` was 97% garbage (390 tagged / 13 real) because `ラエ`
  (Lae) ⊂ `イスラエル` (Israel). Fixed. The same trap hit this build's own bundle:
  `vin` (fr) matched "Kevin"/"driving"/"savings", and `litio` (es) matched
  "Coalition" at **5 characters**. Check `titles_v3.matched_aliases` — it names the
  firing alias — and measure every short Latin-script non-EN alias against
  `detected_language='en'` titles, where any hit is a false positive.

Migrations: `db/migrations/20260717_australia_theater_*.sql` +
`20260717_fix_png_centroid_lae_collision*.sql`. Full notes in
`project_australia_theater`; the centroid-alias class in
`lessons_centroid_short_alias_collisions`.

## Worked example — South Asia (2026-07, greenfield → two theaters MERGED)

The first build to **merge two draft theaters into one region**. `india_china_theater`
+ `india_pakistan_theater` → `south_asia_theater`, 5 atomics / 576 events.

| atomic | gate | events | narratives (titles) |
|---|---|---|---|
| `pakistan_afghanistan_border` **(NEW)** | dyad AND: `{ASIA-PAKISTAN}` + target `ASIA-AFGHANISTAN` | 225 | counterterror-necessity 65 / afghan-sovereignty 128 / civilian-harm 136 |
| `kashmir_dispute` | A2, null target | 157 | integral-to-India 12 / disputed-territory 15 / unrest-both-sides 8 |
| `india_pakistan_militancy` | A2 (named groups), null target | 95 | pak-sponsorship 94 / indian-pretext 5 |
| `balochistan_insurgency` **(NEW)** | A2, null target | 67 | foreign-backed 9 / rights-repression 25 / internal-failure 39 |
| `indus_water_sharing` | A2 (named treaty), null target | 32 | treaty-obsolete 18 / water-weaponisation 15 |

Overlap 538 single / 19 dual / 0 triple. Theater cards: **five**, not three.
Migrations `db/migrations/20260717_south_asia_*.sql`; notes in
`project_south_asia_theater`.

Lessons this build added:

- **THE EN MATCHER IS WORD-START, NOT WHOLE-WORD.** `_WORD_START_MATCH` is
  `~* '\m' || kw` with **no trailing `\M`** — the prefix behaviour is deliberate
  (`dron` → drone/dronow) but it silently makes short nouns false-positive engines:
  `Indus` → **industry/industrial** (37 real vs 409 matched), `Jaish` →
  **Jaishankar**, India's foreign minister (5 vs 115), `LeT` → let/letter/lethal,
  `LoC` → local/location, `dam` → damage/dampen. The `^[A-Z0-9][A-Z0-9-]{0,3}$`
  acronym path (case-SENSITIVE whole word) rescues `BLA`/`TTP`/`IWT`/`ISI` — but
  **only all-caps ≤4 chars**; a single lowercase letter (`LeT`, `JeM`, `LoC`)
  drops the alias back onto the prefix path. **Pre-audit every alias against the
  real matcher semantics, not `\m…\M`** — a plain word-boundary count understates
  the damage and will tell you an alias is clean when it is not.
- **A theater can have TWO PRINCIPALS, and then it needs 2 cards per sign.** The
  §5.5 three-card pattern (Arctic/Ukraine/us_china) works because every atomic
  shares one axis. Here the acting state differs by atomic — India acts in
  Kashmir/Indus/militancy, Pakistan acts in Afghanistan/Balochistan — so each
  national bloc legitimately appears on BOTH signs (claimant + / critic −).
  Five publisher-disjoint cards; `korea_theater` already showed `[2,2,-2,-2]`.
  Blocs that switch sides by atomic (Turkish/Gulf: Pakistani-side on Kashmir,
  neutral on Pak-Afg) belong on NO theater card — homeless beats mislabelled.
- **A multi-dyad theater is a legitimate archetype**, not a broken bilateral: at
  3+ dyads it is a regional-instability theater (`sahel`, `horn_africa`, `balkan`,
  `great_lakes`). Adding the third dyad is what resolved the archetype objection.
- **§2a caught an unhomed war for the third build running.** Pakistan-Afghanistan
  (726 titles/180d) outweighed both draft dyads combined and had no FN anywhere in
  the system. Arctic (Greenland) and eu_cohesion (Orbán/Brexit dead) were the same
  shape. The draft decomposition is training-data-aged by default; ground it.
- **A2's `primary_target=null` has a cost worth naming.** `link_events` uses two
  SEPARATE `EXISTS` clauses, so one title supplies the centroid and a *different*
  one matches the alias — 13 of kashmir's 157 events are 59–142-title mega-clusters
  ("Elon Musk merges xAI with SpaceX") where some title says "Kashmir". Only
  `primary_target`'s 50%-of-event-titles rule filters these, and setting one here
  would drop real Pakistan-administered-Kashmir events and silently redefine a
  divided-territory atomic as one side's. Accepted the artifact; it is systemic
  across every A2 atomic and needs an event-gate change, not a data lever.
